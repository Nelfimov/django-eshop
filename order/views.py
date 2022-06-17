from cart.models import Cart
from decouple import config
from django.conf import settings
from django.contrib import messages
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, View

from .forms import CheckoutForm, RefundForm
from .models import Address, Order, Refund


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            cart = Cart.objects.get(
                checked_out=False,
                user=(self.request.user
                      if self.request.user.is_authenticated
                      else None),
                session_key=(None
                             if self.request.user.is_authenticated
                             else self.request.session.session_key),
            )
            form = CheckoutForm()
            context = {
                'form': form,
                'cart': cart,
                'client_id': config('PAYPAL_CLIENT_ID'),
                'currency': 'EUR',
            }
            if self.request.user.is_authenticated:
                shipping_address_qs = Address.objects.filter(
                    user=self.request.user,
                    address_type='S',
                    default=True
                )
                if shipping_address_qs.exists():
                    context.update({'default_shipping_address':
                                    shipping_address_qs[0]})

                billing_address_qs = Address.objects.filter(
                    user=self.request.user,
                    address_type='B',
                    default=True
                )
                if billing_address_qs.exists():
                    context.update({'default_billing_address':
                                    billing_address_qs[0]})
            return render(self.request, 'checkout.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, _('You do not have anything in cart'))
            return redirect('core:home')

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            shipping_address = Address.objects.create()
            cart = Cart.objects.get(
                checked_out=False,
                user=(self.request.user
                      if self.request.user.is_authenticated
                      else None),
                session_key=(None
                             if self.request.user.is_authenticated
                             else self.request.session.session_key),
            )
            if form.is_valid():
                cart_items = cart.items.all()
                order, created = Order.objects.get_or_create(
                    cart=cart, user=cart.user
                )
                order.items.set(cart_items)

                if self.request.user.is_authenticated:
                    use_default_shipping = form.cleaned_data.get(
                        'use_default_shipping')

                    if use_default_shipping:
                        address_qs = Address.objects.filter(
                            user=self.request.user,
                            address_type='S',
                            default=True,
                        )

                        if address_qs.exists():
                            shipping_address = address_qs[0]
                            order.shipping_address = shipping_address
                            order.save()
                        else:
                            messages.warning(
                                self.request,
                                _('No default shipping address available')
                            )
                            return redirect('order:checkout')

                email = form.cleaned_data.get(
                    'email')
                shipping_name = form.cleaned_data.get(
                    'shipping_name')
                shipping_address = form.cleaned_data.get(
                    'shipping_address')
                shipping_address2 = form.cleaned_data.get(
                    'shipping_address2')
                shipping_country = form.cleaned_data.get(
                    'shipping_country')
                shipping_zip = form.cleaned_data.get('shipping_zip')
                set_default_shipping = form.cleaned_data.get(
                    'set_default_shipping'
                )

                if is_valid_form([email, shipping_address,
                                  shipping_country, shipping_name,
                                  shipping_zip]):

                    shipping_address = Address(
                        user=(self.request.user
                              if self.request.user.is_authenticated
                              else None),
                        email=email,
                        name_for_delivery=shipping_name,
                        street_address=shipping_address,
                        apartment_address=shipping_address2,
                        country=shipping_country,
                        zip=shipping_zip,
                        address_type='S',
                        default=True if set_default_shipping else False,
                    )

                    shipping_address.save()
                    order.shipping_address = shipping_address
                    order.save()
                else:
                    messages.warning(
                        self.request,
                        _('Please fill in the' +
                            ' required shipping address')
                    )

                #  Billing address
                if self.request.user.is_authenticated:
                    use_default_billing = form.cleaned_data.get(
                        'use_default_billing')
                    if use_default_billing:
                        address_qs = Address.objects.filter(
                            user=self.request.user,
                            address_type='B',
                            default=True,
                        )
                        if address_qs.exists():
                            billing_address = address_qs[0]
                            order.billing_address = billing_address
                            order.save()
                        else:
                            messages.warning(
                                self.request,
                                _('No default billing address available')
                            )
                            return redirect('order:checkout')

                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')
                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()
                else:
                    billing_name = form.cleaned_data.get(
                        'billing_name')
                    billing_address = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get(
                        'billing_zip')
                    set_default_billing = form.cleaned_data.get(
                        'set_default_billing')
                    if is_valid_form([billing_address,
                                      billing_name,
                                      billing_country,
                                      billing_zip]):
                        billing_address = Address(
                            user=(self.request.user
                                  if self.request.user.is_authenticated
                                  else None),
                            name_for_delivery=billing_name,
                            street_address=billing_address,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B',
                            default=True if set_default_billing else False,
                        )
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.warning(
                            self.request,
                            _('Please fill in the required billing address')
                        )
                        return redirect('order:checkout')

            # payment_option = form.cleaned_data.get('payment_option')
            # if payment_option == 'S':
            #     return redirect('payment:payment')
            # elif payment_option == 'P':
            return redirect('payment:payment')
            # else:
            #     messages.warning(self.request,
            #                      'Invalid payment option selected')
            #     return redirect('order:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, _('You do not have an' +
                                             ' active order'))
            return redirect('cart:cart-summary')


class OrderView(ListView):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            try:
                orders = Order.objects.filter(
                    user=self.request.user,
                    ordered=True
                )
                context = {
                    'object': orders
                }
                return render(self.request, 'orders_finished.html', context)
            except ObjectDoesNotExist:
                messages.warning(self.request, _('You do not have any orders'))
                return redirect('/')

        messages.warning(self.request, _('You are not authorized'))
        return redirect('/')


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        try:
            ref_code = self.request.GET['ref_code']
            order = Order.objects.get(ref_code=ref_code)
            if order.user == self.request.user:
                form = RefundForm(initial={'ref_code': ref_code,
                                           'email': self.request.user.email})
                context = {
                    'form': form,
                }
                return render(self.request, 'request_refund.html', context)
            else:
                messages.warning(self.request,
                                 _('You are not the user who ordered' +
                                   ' this order'))
                return redirect('core:home')
        except ObjectDoesNotExist:
            messages.warning(self.request, _('Order does not exist'))
            return redirect('core:home')

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                order = Order.objects.get(ref_code=ref_code)
                if order.user == self.request.user:
                    if not order.refund_requested:
                        order.refund_requested = True
                        order.save()
                        refund = Refund.objects.create(
                            order=order, reason=message, email=email,
                        )
                        refund.save()

                        #  Send mail for confirmation of order
                        subject = (
                            _('Refund request for your order #') +
                            order.ref_code
                        )
                        header = (
                            subject + _(' has been received and ' +
                                        'will be processed shortly')
                        )
                        html_message = render_to_string(
                            'emails/order_confirmation_email.html',
                            {'order': order, 'header': header}
                        )
                        plain_message = strip_tags(html_message)
                        from_email = settings.DEFAULT_FROM_EMAIL
                        to = order.shipping_address.email
                        mail.send_mail(subject, plain_message, from_email,
                                       [to], html_message=html_message)

                        subject_admin = (
                            _('New refund/Neue refund ') +
                            order.ref_code +
                            _(' is requested/ist gesendet')
                        )
                        mail.mail_admins(
                            subject=subject_admin, message=message,
                            fail_silently=False,
                        )
                        messages.info(self.request,
                                      _('Your request was received'))
                        return redirect('order:orders-finished')

                    elif order.refund_granted:
                        messages.info(
                            self.request,
                            _('You have already received refund' +
                              'for this order')
                        )

                    else:
                        messages.info(
                            self.request,
                            _('You have already submitted a ticket.' +
                              ' Please wait until we contact you')
                        )

                    return redirect('order:orders-finished')

                else:
                    messages.warning(
                        self.request,
                        _('You are not the user who ordered this order')
                    )
                    return redirect('core:home')

            except ObjectDoesNotExist:
                messages.warning(self.request, _('This order does not exist'))
                return redirect('order:orders-finished')
