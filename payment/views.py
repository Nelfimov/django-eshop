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
from order.models import Order, OrderItem
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from paypalcheckoutsdk.orders import OrdersCaptureRequest, OrdersCreateRequest

from .models import Payment


def create_ref_code():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=20))


class PaypalView(View):
    def get(self, *args, **kwargs):
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
            order_items = OrderItem.objects.filter(order=order)
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
        environment = SandboxEnvironment(
            client_id=config("PAYPAL_CLIENT_ID"),
            client_secret=config("PAYPAL_CLIENT_SECRET"),
        )
        client = PayPalHttpClient(environment)
        order = Order.objects.get(
            ordered=False,
            user=(self.request.user if self.request.user.is_authenticated else None),
            session_key=(
                None
                if self.request.user.is_authenticated
                else self.request.session.session_key
            ),
        )
        amount = round(float(order.get_total()), 2)
        currency = "EUR"
        shipping_value = round(float(0), 2)
        items_in_order = []
        for i in OrderItem.objects.filter(order=order):
            shipping_value += round(float(i.item.delivery_price * i.quantity), 2)
            items_in_order.append(
                {
                    "name": str(i.item.title),
                    "description": str(i.item.description),
                    "unit_amount": {
                        "currency_code": currency,
                        # 'value': round(
                        #     float(i.item.price - i.item.discount) / 1.19,
                        #     2
                        # )
                        "value": round(float(i.item.price - i.item.discount), 2),
                    },
                    "tax": {
                        "currency_code": currency,
                        # 'value': round(
                        #     float(i.item.price - i.item.discount) * 19 / 119,
                        #     2
                        # ),
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
                            "value": amount,  # Сумма заказа с НДС и доставкой
                            "breakdown": {
                                "item_total": {
                                    "currency_code": currency,
                                    # Сумма только товаров без доставки и налогов
                                    # "value":round((amount-shipping_value)/1.19,2)
                                    "value": round((amount - shipping_value), 2),
                                },
                                "shipping": {
                                    "currency_code": currency,
                                    # Сумма только доставки
                                    "value": round(shipping_value, 2),
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
                            "name": {
                                "full_name": str(
                                    order.shipping_address.name_for_delivery
                                )
                            },
                            "address": {
                                "address_line_1": str(
                                    order.shipping_address.street_address
                                ),
                                "address_line_2": str(
                                    order.shipping_address.apartment_address
                                ),
                                "admin_area_2": "asdf",
                                "admin_area_1": "asdf",
                                "postal_code": str(order.shipping_address.zip),
                                "country_code": str(order.shipping_address.country),
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


# Paypal capture the approved order
def capture(request, order_id):
    if request.method == "POST":
        order = Order.objects.get(
            ordered=False,
            user=request.user if request.user.is_authenticated else None,
            session_key=(
                None if request.user.is_authenticated else request.session.session_key
            ),
        )
        order_items = OrderItem.objects.filter(order=order)
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
                amount=order.get_total(),
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
            to_email = order.shipping_address.email
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
