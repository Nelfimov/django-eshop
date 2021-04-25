from core.models import Order, OrderItem
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from .models import PayPalClient, Payment
import stripe
import json


class StripeView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'order': order,
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
        }
        return render(self.request, 'stripe.html', context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency='usd',
                source=token,
                description='Charge for Auction'
            )

            # create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            # assign the payment to the order
            order.ordered = True
            order.payment = payment
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
            'order': order
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
                "user_action": "PAY_NOW"
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
        response = client.execute(create_order)
        data = response.result.__dict__['_dict']

        print(JsonResponse(data))

        order_id = response.result.__dict__['id']

        return redirect('capture', order_id='order_id')



# def pay(request):
#     client_id = settings.PAYPAL_CLIENT_ID
#     order = Order.objects.get(user=request.user, ordered=False)
#     context = {
#         'client_id': client_id,
#         'order': order
#     }
    
#     return render(request, 'paypal.html', context)


# def create(request):
#     if request.method == 'POST':
#         environment = SandboxEnvironment(
#             client_id=settings.PAYPAL_CLIENT_ID, 
#             client_secret=settings.PAYPAL_CLIENT_SECRET
#             )
#         client = PayPalHttpClient(environment)
#         order = Order.objects.get(user=request.user, ordered=False)
#         currency = order.currency
#         amount = order.amount
#         tax = amount * 0,19
#         shipping_value = 0
#         create_order = OrdersCreateRequest()

#         create_order.request_body(
#              {
#                 "intent": "CAPTURE",
#                 "purchase_units": [
#                     {
#                         "amount": {
#                             "currency_code": "USD",
#                             "value": course.price,
#                             "breakdown": {
#                                 "item_total": {
#                                     "currency_code": "USD",
#                                     "value": course.price
#                                 }
#                                 },
#                             },                               


#                     }
#                 ]
#             }
#         )



#         response = client.execute(create_order)
#         data = response.result.__dict__['_dict']
#         return JsonResponse(data)
#     else:
#         return JsonResponse({'details': 'invalid response'})


def capture(request, order_id):
    if request.method =='POST':
        capture_order = OrdersCaptureRequest(order_id)
        environment = SandboxEnvironment(
            client_id=settings.PAYPAL_CLIENT_ID, 
            client_secret=settings.PAYPAL_CLIENT_SECRET
            )
        client = PayPalHttpClient(environment)

        response = client.execute(capture_order)
        data = response.result.__dict__['_dict']

        order.ordered = True
        order.save
        messages.success(self.request, 'Your order was successfull')


        print(JsonResponse(data))

        return 

    else:
        return JsonResponse({'details': 'invalide request'})


def getClientId(request):
    if request.method == 'GET':
        return JsonResponse({'client_id': settings.PAYPAL_CLIENT_ID})






# class PaypalView(PayPalClient):
#     @staticmethod
#     def build_request_body():
#         order = Order.objects.get(user=request.user, ordered=False)
#         amount = int(order.get_total() * 100)
#         tax = amount * 0,19
#         # TODO shipping
#         shipping_value = 0
#         currency = "EUR"
#         return \
#             {
#                 "intent": "CAPTURE",
#                 "application_context": {
#                     "brand_name": "LADENBURGER SPIELZEUGAUKTION",
#                     "landing_page": "NO_PREFERENCE",
#                     "shipping_preference": "GET_FROM_FILE",
#                     "user_action": "PAY_NOW"
#                 },
#                 "purchase_units": [
#                     {
#                         "description": "Antique Toys",
#                         "custom_id": "CUST-Antique Toys",
#                         "soft_descriptor": "Antique Toys",
#                         "amount": {
#                             "currency_code": currency,
#                             "value": amount,
#                             "breakdown": {
#                                 "item_total": {
#                                     "currency_code": currency,
#                                     "value": amount - tax - shipping_value
#                                 },
#                                 "shipping": {
#                                     "currency_code": currency,
#                                     "value": shipping_value
#                                 },
#                                 "tax_total": {
#                                     "currency_code": currency,
#                                     "value": tax
#                                 }
#                             }
#                         },
#                         "items": [
#                             {
#                                 "name": item.title,
#                                 "description": item.description,
#                                 "unit_amount": {
#                                     "currency_code": item.currency,
#                                     "value": item.price
#                                 },
#                                 "tax": {
#                                     "currency_code": "EUR",
#                                     "value": (item.price * 0,19)
#                                 },
#                                 "quantity": item.quantity,
#                                 "category": "PHYSICAL_GOODS"
#                             }
#                         ],
#                         "shipping": {
#                             "method": "United States Postal Service",
#                             "name": {
#                                 "full_name":"John Doe"
#                             },
#                             "address": {
#                                 "address_line_1": "123 Townsend St",
#                                 "address_line_2": "Floor 6",
#                                 "admin_area_2": "San Francisco",
#                                 "admin_area_1": "CA",
#                                 "postal_code": "94107",
#                                 "country_code": "US"
#                             }
#                         }
#                     }
#                 ]
#             }

#     """ This is the sample function which can be sued to create an order. It uses the
#         JSON body returned by buildRequestBody() to create an new Order."""

#     def create_order(self, debug=False):
#         request = OrdersCreateRequest()
#         request.headers['prefer'] = 'return=representation'
#         request.request_body(self.build_request_body())
#         response = self.client.execute(request)
#         if debug:
#             print ('Status Code: ', response.status_code)
#             print ('Status: ', response.result.status)
#             print ('Order ID: ', response.result.id)
#             print ('Intent: ', response.result.intent)
#             print ('Links:')
            
#             for link in response.result.links:
#                 print('\t{}: {}\tCall Type: {}'.format(link.rel, link.href, link.method))
            
#             print ('Total Amount: {} {}'.format(response.result.purchase_units[0].amount.currency_code,
#                                                response.result.purchase_units[0].amount.value))
#             json_data = self.object_to_json(response.result)
#             print ("json_data: ", json.dumps(json_data,indent=4))
#         return response
