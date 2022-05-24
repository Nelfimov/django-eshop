import datetime
import random
import string
from urllib.error import HTTPError

from cart.models import Cart
from core.models import Order
from decouple import config
from django.conf import settings
from django.contrib import messages
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic import View
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from paypalcheckoutsdk.orders import OrdersCaptureRequest, OrdersCreateRequest

from .models import Payment, PayPalClient


def create_ref_code():
    return ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=20))


# PAYPAL
class PaypalView(View):
    def get(self, *args, **kwargs):
        try:
            if self.request.user.is_authenticated:
                cart = Cart.objects.get(
                    user=self.request.user,
                    checked_out=False
                )
                order = Order.objects.get(
                    user=self.request.user,
                    ordered=False,
                    cart=cart
                )
            else:
                cart = Cart.objects.get(
                    user=None,
                    checked_out=False,
                    session_key=self.request.session.session_key
                )
                order = Order.objects.get(ordered=False, cart=cart)
            client_id = config('PAYPAL_CLIENT_ID')
            context = {
                'client_id': client_id,
                'order': order,
                'currency': 'EUR',
                'cart': cart,
            }
            return render(self.request, 'paypal.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order')
            return redirect('cart:cart-summary')

    def post(self, *args, **kwargs):
        environment = SandboxEnvironment(
            client_id=config('PAYPAL_CLIENT_ID'),
            client_secret=config('PAYPAL_CLIENT_SECRET')
            )
        client = PayPalHttpClient(environment)
        if self.request.user.is_authenticated:
            cart = Cart.objects.get(
                user=self.request.user,
                checked_out=False
            )
            order = Order.objects.get(
                user=self.request.user,
                ordered=False,
                cart=cart
            )
        else:
            cart = Cart.objects.get(
                user=None,
                checked_out=False,
                session_key=self.request.session.session_key
            )
            order = Order.objects.get(user=None, ordered=False, cart=cart)
        amount = round(float(order.get_total()), 2)
        currency = 'EUR'
        shipping_value = round(float(0), 2)
        items_in_order = []
        for i in order.items.all():
            shipping_value += round(
                float(
                    i.item.delivery_price * i.quantity
                ),
                2)
            items_in_order.append(
                {
                    'name': str(i.item.title),
                    'description': str(i.item.description),
                    'unit_amount': {
                        'currency_code': currency,
                        'value': round(
                            float(i.item.price - i.item.discount) / 1.19,
                            2
                        )
                    },
                    'tax': {
                        'currency_code': currency,
                        'value': round(
                            float(i.item.price - i.item.discount) * 19 / 119,
                            2
                        ),
                    },
                    'quantity': i.quantity,
                    'category': 'PHYSICAL_GOODS'
                }
            )

        create_order = OrdersCreateRequest()
        create_order.headers['prefer'] = 'return=representation'

        create_order.request_body(
            {"intent": "CAPTURE",
             "application_context": {
                "brand_name": "LADENBURGER SPIELZEUGAUKTION",
                "landing_page": "NO_PREFERENCE",
                "shipping_preference": "SET_PROVIDED_ADDRESS",
                "user_action": "PAY_NOW",
                "return_url": "https://example.com/",
                "cancel_url": "https://example.com/",
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
                                "value": round((amount-shipping_value)/1.19, 2)
                            },
                            "shipping": {
                                "currency_code": currency,
                                # Сумма только доставки
                                "value": round(shipping_value, 2)
                            },
                            "tax_total": {
                                "currency_code": currency,
                                # Сумма только налогов
                                "value": round(
                                    (amount - shipping_value) * 19 / 119,
                                    2)
                            }
                        }
                    },
                    "items": items_in_order,
                    "shipping": {
                        "method": "DHL",
                        "name": {
                            "full_name":
                            str(order.shipping_address.name_for_delivery)
                        },
                        "address": {
                            "address_line_1": "123 Townsend St",
                            "address_line_2": "Floor 6",
                            "admin_area_2": "San Francisco",
                            "admin_area_1": "CA",
                            "postal_code": str(order.shipping_address.zip),
                            "country_code": str(
                                order.shipping_address.country),
                            }
                        }
                    }
                ]
             }
        )

        try:
            response = client.execute(create_order)
            data = response.result.__dict__['_dict']
            return JsonResponse(data)

        except IOError as ioe:
            print(ioe)
            if isinstance(ioe, HTTPError):
                print(ioe.status_code)

        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order')
            return redirect('core:home')


# Paypal capture the approved order
def capture(request, order_id):
    if request.method == 'POST':
        if request.user.is_authenticated:
            cart = Cart.objects.get(user=request.user, checked_out=False)
        else:
            cart = Cart.objects.get(
                user=None, checked_out=False,
                session_key=request.session.session_key
            )
        order = Order.objects.get(cart=cart, user=cart.user)
        order_items = order.items.all()
        capture_order = OrdersCaptureRequest(order_id)
        environment = SandboxEnvironment(
            client_id=config('PAYPAL_CLIENT_ID'),
            client_secret=config('PAYPAL_CLIENT_SECRET')
        )
        client = PayPalHttpClient(environment)

        try:
            response = client.execute(capture_order)
            data = response.result.__dict__['_dict']
            payment = Payment()
            if request.user.is_authenticated:
                payment.user = request.user
            else:
                payment.user = None
            payment.amount = order.get_total()
            payment.paypal_id = order_id
            payment.save()
            order.ordered = True
            order.ref_code = create_ref_code()
            order.payment = payment
            order.ordered_date = datetime.datetime.now()
            order.save()
            cart.checked_out = True
            cart.save()
            for i in order_items:
                i.item.stock -= i.quantity
                i.item.ordered_counter += 1
                i.item.save()
                i.ordered = True
                i.save()

            #  Send mail for confirmation of order
            # subject = 'Your order at Jetztistdiebestezeit.de #' \
            #           + order.ref_code
            # html_message = render_to_string(
            #     'emails/order_confirmation_email.html',
            #     {'object': order}
            #     )
            # plain_message = strip_tags(html_message)
            # from_email = settings.EMAIL_HOST_USER
            # to = order.shipping_address.email
            # mail.send_mail(subject, plain_message, from_email,
            #                [to], html_message=html_message)

            # messages.success(request, 'Your order was successfull')
            return JsonResponse(data)

        except IOError as ioe:
            if isinstance(ioe, HTTPError):
                print(ioe.status_code)
                print(ioe.headers)
                print(ioe)
            else:
                print(ioe)


def getClientId(request):
    if request.method == 'GET':
        return JsonResponse({'client_id': config('PAYPAL_CLIENT_ID')})
