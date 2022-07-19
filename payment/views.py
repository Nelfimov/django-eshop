import random
import string
from urllib.error import HTTPError

from decouple import config
from django.conf import settings
from django.contrib import messages
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from paypalcheckoutsdk.orders import OrdersCaptureRequest, OrdersCreateRequest

from order.models import Order
from .models import Payment


def create_ref_code():
    """Creation of unique reference code for order upon succesfull payment"""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=20))


class PaypalView(View):
    """Payment via Paypal"""

    def get(self, *args, **kwargs):
        """Get view"""
        try:
            order = Order.objects.get(
                ordered=False,
                user=(
                    self.request.user if self.request.user.is_authenticated else None
                ),
                session_key=(
                    None
                    if self.request.user.is_authenticated
                    else self.request.session.session_key
                ),
            )
            order_items = order.orderitem_set.all()
            if not order.address:
                messages.warning(self.request, _("You have no address for your order"))
                return redirect("checkout:checkout")
            client_id = config("PAYPAL_CLIENT_ID")
            context = {
                "client_id": client_id,
                "order": order,
                "order_items": order_items,
                "currency": "EUR",
            }
            return render(self.request, "payment.html", context)
        except ObjectDoesNotExist:
            messages.warning(self.request, _("You do not have anything in your cart"))
            return redirect("core:home")

    def post(self, *args, **kwargs):
        """Post view"""
        environment = SandboxEnvironment(
            client_id=config("PAYPAL_CLIENT_ID"),
            client_secret=config("PAYPAL_CLIENT_SECRET"),
        )
        client = PayPalHttpClient(environment)
        try:
            order = Order.objects.get(
                ordered=False,
                user=(
                    self.request.user if self.request.user.is_authenticated else None
                ),
                session_key=(
                    None
                    if self.request.user.is_authenticated
                    else self.request.session.session_key
                ),
            )
        except ObjectDoesNotExist:
            messages.warning(self.request, _("You do not have anything in your cart"))
            return redirect("core:home")
        currency = "EUR"
        items_in_order = []
        for i in order.orderitem_set.all().select_related("item"):
            items_in_order.append(
                {
                    "name": str(i.item.title),
                    "description": str(i.item.description),
                    "unit_amount": {
                        "currency_code": currency,
                        "value": round(float(i.item.get_price_no_delivery), 2),
                    },
                    "tax": {
                        "currency_code": currency,
                        "value": "0",
                    },
                    "quantity": i.quantity,
                    "category": "PHYSICAL_GOODS",
                }
            )
        create_order = OrdersCreateRequest()
        create_order.headers["prefer"] = "return=representation"
        create_order.request_body(
            {
                "intent": "CAPTURE",
                "application_context": {
                    "brand_name": "LADENBURGER SPIELZEUGAUKTION",
                    "landing_page": "NO_PREFERENCE",
                    "shipping_preference": "SET_PROVIDED_ADDRESS",
                    "user_action": "PAY_NOW",
                    "return_url": "http://127.0.0.1:8000/",
                    "cancel_url": "http://127.0.0.1:8000/",
                },
                "purchase_units": [
                    {
                        "description": "Antique Toys",
                        "custom_id": "CUST-Antique Toys",
                        "soft_descriptor": "Antique Toys",
                        "amount": {
                            "currency_code": currency,
                            "value": round(
                                float(order.get_total), 2
                            ),  # Сумма заказа с НДС и доставкой
                            "breakdown": {
                                "item_total": {
                                    "currency_code": currency,
                                    # Сумма только товаров без доставки и налогов
                                    # "value": round((amount - shipping_value), 2),
                                    "value": round(
                                        float(order.get_price_no_delivery), 2
                                    ),
                                },
                                "shipping": {
                                    "currency_code": currency,
                                    # Сумма только доставки
                                    "value": round(float(order.get_delivery_total), 2),
                                },
                                "tax_total": {
                                    "currency_code": currency,
                                    # Сумма только налогов
                                    # "value": round(
                                    #     (amount - shipping_value) * 19 / 119,
                                    #     2)
                                    "value": "0",
                                },
                            },
                        },
                        "items": items_in_order,
                        "shipping": {
                            "method": "DHL",
                            "name": {"full_name": str(order.address.shipping_name)},
                            "address": {
                                "address_line_1": str(
                                    order.address.shipping_street_address
                                ),
                                "address_line_2": str(
                                    order.address.shipping_apartment_address
                                ),
                                "admin_area_2": str(order.address.shipping_city),
                                # "admin_area_1": ".",
                                "postal_code": str(order.address.shipping_zip),
                                "country_code": str(order.address.shipping_country),
                            },
                        },
                    }
                ],
            }
        )

        try:
            response = client.execute(create_order)
            data = response.result.__dict__["_dict"]
            return JsonResponse(data)

        except IOError as ioe:
            print(ioe)
            if isinstance(ioe, HTTPError):
                print(ioe.status_code)

        except ObjectDoesNotExist:
            messages.warning(self.request, _("You do not have an active order"))
            return redirect("core:home")


def capture(request, order_id):
    """Capturing PayPal order for succesfull transfer of cash + sending email to admins and customer"""
    if request.method == "POST":
        order = Order.objects.get(
            ordered=False,
            user=request.user if request.user.is_authenticated else None,
            session_key=(
                None if request.user.is_authenticated else request.session.session_key
            ),
        )
        order_items = order.orderitem_set.all()
        capture_order = OrdersCaptureRequest(order_id)
        environment = SandboxEnvironment(
            client_id=config("PAYPAL_CLIENT_ID"),
            client_secret=config("PAYPAL_CLIENT_SECRET"),
        )
        client = PayPalHttpClient(environment)

        try:
            response = client.execute(capture_order)
            data = response.result.__dict__["_dict"]
            payment = Payment(
                user=(request.user if request.user.is_authenticated else None),
                amount=round(float(order.get_total), 2),
                paypal_id=order_id,
                order=order,
            )
            payment.save()
            order.ordered = True
            order.ref_code = create_ref_code()
            order.ordered_date = timezone.now()
            order.save()
            for i in order_items:
                i.item.stock -= i.quantity
                i.item.ordered_counter += 1
                i.item.save()

            #  Send mail for confirmation of order
            subject = _("Your order #") + order.ref_code
            header = subject + _(
                " has been received and " + "will be processed shortly"
            )
            html_message = render_to_string(
                "emails/order_confirmation_email.html",
                {"order": order, "header": header, "order_items": order_items},
            )
            plain_message = strip_tags(html_message)
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = order.address.email
            mail.send_mail(
                subject,
                plain_message,
                from_email,
                [to_email],
                html_message=html_message,
            )

            subject_admin = (
                "New order/Neue Bestellung "
                + order.ref_code
                + " has been paid/ist bezahlt"
            )
            mail.mail_admins(
                subject=subject_admin,
                message="",
                fail_silently=False,
            )
            messages.success(request, _("Your order was successfull"))
            return JsonResponse(data)

        except IOError as ioe:
            if isinstance(ioe, HTTPError):
                print(ioe.status_code)
                print(ioe.headers)
                print(ioe)
            else:
                print(ioe)


def getClientId(request):
    if request.method == "GET":
        return JsonResponse({"client_id": config("PAYPAL_CLIENT_ID")})
