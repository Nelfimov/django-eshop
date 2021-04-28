from core.models import Order, OrderItem
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from .forms import PaymentForm
from .models import PayPalClient, Payment
import stripe, random, string, json


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


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
                messages.error(self.request, 'Invalid parameters were supplied')
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
                messages.error(self.request, 'Something went wrong, you were not charged. Please try again')
                return redirect('/')

            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                # send an email to ourselves

                messages.error(self.request, 'Serious error occured. We have been notified')
                return redirect('/')


# PAYPAL
class PaypalView(View):
    def get(self, *args, **kwargs):
        client_id = settings.PAYPAL_CLIENT_ID
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'client_id': client_id,
            'order': order,
            'currency': 'EUR'
        }
    
        return render(self.request, 'paypal.html', context)

    def post(self, *args, **kwargs):
        environment = SandboxEnvironment(
            client_id=settings.PAYPAL_CLIENT_ID, 
            client_secret=settings.PAYPAL_CLIENT_SECRET
            )
        client = PayPalHttpClient(environment)
        order = Order.objects.get(user=self.request.user, ordered=False)
        amount = int(order.get_total())
        currency = 'EUR'
        tax = amount * 0,19
        shipping_value = 0
        create_order = OrdersCreateRequest()
        create_order.headers['prefer'] = 'return=representation'

        create_order.request_body(
            {
            "intent": "CAPTURE",
            "application_context": {
                "brand_name": "LADENBURGER SPIELZEUGAUKTION",
                "landing_page": "NO_PREFERENCE",
                "shipping_preference": "GET_FROM_FILE",
                "user_action": "PAY_NOW",
            },
            "purchase_units": [
                {
                    "description": "Antique Toys",
                    "custom_id": "CUST-Antique Toys",
                    "soft_descriptor": "Antique Toys",
                    "amount": {
                        "currency_code": currency,
                        "value": amount,
                        # "breakdown": {
                        #     "item_total": {
                        #         "currency_code": currency,
                        #         "value": amount
                        #     },
                        #     "shipping": {
                        #         "currency_code": currency,
                        #         "value": shipping_value
                        #     },
                        #     "tax_total": {
                        #         "currency_code": currency,
                        #         "value": tax
                        #     }
                        # }
                    },
                    # "items": [
                    #     {
                    #         "name": 'Toys',
                    #         "description": 'Toys from antique',
                    #         "unit_amount": {
                    #             "currency_code": currency,
                    #             "value": (amount/1,19)
                    #         },
                    #         "tax": {
                    #             "currency_code": "EUR",
                    #             "value": tax
                    #         },
                    #         "quantity": '1',
                    #         "category": "PHYSICAL_GOODS"
                    #     }
                    # ],
                    # "shipping": {
                    #     "method": "United States Postal Service",
                    #     "name": {
                    #         "full_name":"John Doe"
                    #     },
                    #     "address": {
                    #         "address_line_1": "123 Townsend St",
                    #         "address_line_2": "Floor 6",
                    #         "admin_area_2": "San Francisco",
                    #         "admin_area_1": "CA",
                    #         "postal_code": "94107",
                    #         "country_code": "US"
                    #         }
                        # }
                    }
                ]
            }
        )

        try:
            response = client.execute(create_order)
            data = response.result.__dict__['_dict']
            order_id = response.result.__dict__['id']
            return  JsonResponse(data)

        except IOError as ioe:
            print(ioe)
            if isinstance(ioe, HttpError):
                print(ioe.status_code)


# Paypal capture the approved order
def capture(request, order_id):
    if request.method =='POST':
        order = Order.objects.get(user=request.user, ordered=False)
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
            order.save()
            messages.success(request, 'Your order was successfull')
            return render(request, 'home.html')

        except IOError as ioe:
            if isinstance(ioe, HttpError):
                print(ioe.status_code)
                print(ioe.headers)
                print(ioe)
                
            else:
                print(ioe)


def getClientId(request):
    if request.method == 'GET':
        return JsonResponse({'client_id': settings.PAYPAL_CLIENT_ID})
