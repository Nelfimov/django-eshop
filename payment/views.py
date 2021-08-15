from urllib.error import HTTPError
from core.models import Order, UserProfile
from django.conf import settings
from django.contrib import messages
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic import View
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from .forms import PaymentForm
from .models import PayPalClient, Payment, VAT_RATES
import datetime
import stripe
import random
import string


def create_ref_code():
    return ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=20))


# Stripe
class StripeView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
                'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
            }
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = cards['data']
                if len(card_list) > 0:
                    context.update({
                        'card': card_list[0]
                    })

            return render(self.request, 'stripe.html', context)

        else:
            messages.warning(
                self.request, 'You have not added a billing address')
            return redirect('core:checkout')

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = self.request.POST.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                # alow to fetch cards
                if not userprofile.stripe_customer_id:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                        source=token,
                    )
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()
                else:
                    stripe.Customer.create_source(
                        userprofile.stripe_customer_id,
                        source=token,
                    )

                amount = int(order.get_total() * 100)

            try:
                if use_default:
                    charge = stripe.Charge.create(
                        amount=amount,
                        currency='eur',
                        customer=userprofile.stripe_customer_id,
                    )
                else:
                    charge = stripe.Charge.create(
                        amount=amount,
                        currency='eur',
                        source=token,
                    )
                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order
                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, 'Your order was successfull')
                return redirect('/')

            except stripe.error.CardError as e:
                # Since it's a decline, stripe.error.CardError will be caught

                print('Status is: %s' % e.http_status)
                print('Code is: %s' % e.code)
                # param is '' in this case
                print('Param is: %s' % e.param)
                print('Message is: %s' % e.user_message)
                return redirect('/')

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.error(self.request, 'Rate limit error')
                return redirect('/')

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                messages.error(self.request,
                               'Invalid parameters were supplied')
                return redirect('/')

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.error(self.request, 'Authentication failed')
                return redirect('/')

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.error(self.request, 'Network error')
                return redirect('/')

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.error(
                    self.request,
                    'Something went wrong, you were not charged. \
                        Please try again'
                )
                return redirect('/')

            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                # send an email to ourselves

                messages.error(
                    self.request,
                    'Serious error occured. We have been notified'
                )
                return redirect('/')


# PAYPAL
class PaypalView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            client_id = settings.PAYPAL_CLIENT_ID
            context = {
                'client_id': client_id,
                'order': order,
                'currency': 'EUR'
            }
            return render(self.request, 'paypal.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order')
            return redirect('core:home')

    def post(self, *args, **kwargs):
        environment = SandboxEnvironment(
            client_id=settings.PAYPAL_CLIENT_ID,
            client_secret=settings.PAYPAL_CLIENT_SECRET
            )
        client = PayPalHttpClient(environment)
        order = Order.objects.get(user=self.request.user, ordered=False)
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
                            float(i.item.get_final_price()) / 1.19,
                            2
                        )
                    },
                    'tax': {
                        'currency_code': currency,
                        'value': round(
                            float(i.item.get_final_price()) -
                            float(i.item.get_final_price()) /
                            1.19,
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
                "return_url": "http://127.0.0.1:8000/",
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
                                    (amount-shipping_value) -
                                    (amount-shipping_value)/1.19,
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
            # order_id = response.result.__dict__['id']
            return JsonResponse(data)

        except IOError as ioe:
            print(ioe)
            if isinstance(ioe, HTTPError):
                print(ioe.status_code)


# Paypal capture the approved order
def capture(request, order_id):
    if request.method == 'POST':
        order = Order.objects.get(user=request.user, ordered=False)
        order_items = order.items.all()
        capture_order = OrdersCaptureRequest(order_id)
        environment = SandboxEnvironment(
            client_id=settings.PAYPAL_CLIENT_ID,
            client_secret=settings.PAYPAL_CLIENT_SECRET
            )
        client = PayPalHttpClient(environment)

        try:
            response = client.execute(capture_order)
            data = response.result.__dict__['_dict']
            payment = Payment()
            payment.user = request.user
            payment.amount = order.get_total()
            payment.paypal_id = order_id
            payment.save()
            order.ordered = True
            order.ref_code = create_ref_code()
            order.payment = payment
            order.ordered_date = datetime.datetime.now()
            order.save()
            for i in order_items:
                i.item.stock -= i.quantity
                i.item.how_many_times_ordered += 1
                i.item.save()

            #  Send mail for confirmation of order
            subject = 'Your order at Jetztistdiebestezeit.de #' \
                      + order.ref_code
            html_message = render_to_string(
                '/emails/order_confirmation_email.html',
                {'object': order}
                )
            plain_message = strip_tags(html_message)
            from_email = settings.EMAIL_HOST_USER
            to = request.user.email
            mail.send_mail(subject, plain_message, from_email,
                           [to], html_message=html_message)

            messages.success(request, 'Your order was successfull')
            return redirect('/')

        except IOError as ioe:
            if isinstance(ioe, HTTPError):
                print(ioe.status_code)
                print(ioe.headers)
                print(ioe)
            else:
                print(ioe)


def getClientId(request):
    if request.method == 'GET':
        return JsonResponse({'client_id': settings.PAYPAL_CLIENT_ID})
