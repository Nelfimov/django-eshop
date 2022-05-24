from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

import cart

from .forms import CheckoutForm, RefundForm
from .models import Address, Carousel, CategoryItem, Item, Order, Refund
from cart.models import Cart, CartItem


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            if self.request.user.is_authenticated:
                cart = Cart.objects.get(
                    user=self.request.user, checked_out=False
                )
            else:
                cart = Cart.objects.get(
                    user=None, session_key=self.request.session.session_key,
                    checked_out=False
                )
            form = CheckoutForm()
            context = {
                'form': form,
                'cart': cart,
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
            messages.info(self.request, 'You do not have an active order')
            return redirect('core:home')

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            shipping_address = Address.objects.create()
            if self.request.user.is_authenticated:
                cart = Cart.objects.get(
                    user=self.request.user, checked_out=False
                )
            else:
                cart = Cart.objects.get(
                    user=None, session_key=self.request.session.session_key,
                    checked_out=False
                )
            if form.is_valid():
                cart_items = cart.items.all()
                order, created = Order.objects.get_or_create(
                    cart=cart, user=cart.user
                )
                order.ordered_date = datetime.now()
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
                                'No default shipping address available'
                            )
                            return redirect('core:checkout')
                else:
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
                    if is_valid_form([email,
                                      shipping_address,
                                      shipping_country,
                                      shipping_name,
                                      shipping_zip]):
                        if self.request.user.is_authenticated:
                            shipping_address = Address(
                                user=self.request.user,
                                email=email,
                                name_for_delivery=shipping_name,
                                street_address=shipping_address,
                                apartment_address=shipping_address2,
                                country=shipping_country,
                                zip=shipping_zip,
                                address_type='S'
                            )
                            set_default_shipping = form.cleaned_data.get(
                                'set_default_shipping')
                            if set_default_shipping:
                                shipping_address.default = True
                                shipping_address.save()
                        else:
                            shipping_address = Address(
                                user=None,
                                email=email,
                                name_for_delivery=shipping_name,
                                street_address=shipping_address,
                                apartment_address=shipping_address2,
                                country=shipping_country,
                                zip=shipping_zip,
                                address_type='S'
                            )
                        shipping_address.save()
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.warning(
                            self.request,
                            'Please fill in the required shipping address'
                        )
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
                                'No default billing address available'
                            )
                            return redirect('core:checkout')

                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')
                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
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
                    if is_valid_form([billing_address,
                                      billing_name,
                                      billing_country,
                                      billing_zip]):
                        if self.request.user.is_authenticated:
                            billing_address = Address(
                                user=self.request.user,
                                name_for_delivery=billing_name,
                                street_address=billing_address,
                                apartment_address=billing_address2,
                                country=billing_country,
                                zip=billing_zip,
                                address_type='B'
                            )
                            set_default_billing = form.cleaned_data.get(
                                'set_default_billing')
                        else:
                            billing_address = Address(
                                user=None,
                                name_for_delivery=billing_name,
                                street_address=billing_address,
                                apartment_address=billing_address2,
                                country=billing_country,
                                zip=billing_zip,
                                address_type='B'
                            )
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.warning(
                            self.request,
                            'Please fill in the required billing address'
                        )
                        return redirect('core:checkout')

            # payment_option = form.cleaned_data.get('payment_option')
            # if payment_option == 'S':
            #     return redirect('payment:stripe')
            # elif payment_option == 'P':
            return redirect('payment:paypal')
            # else:
            #     messages.warning(self.request,
            #                      'Invalid payment option selected')
            #     return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order')
            return redirect('core:order-summary')


class HomeView(View):
    def get(self, *args, **kwargs):
        paginate_by = 8
        recently_added_items = Item.objects.all().order_by('created_date')
        categories = CategoryItem.objects.all()
        if self.request.GET.get('category'):
            category_filter = self.request.GET.get('category')
            recently_added_items = recently_added_items.filter(
                category=category_filter)

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            recently_added_items = recently_added_items.filter(
                title__icontains=search)

        bestseller_items = Item.objects.order_by(
            'ordered_counter')[:10]
        carousel_slides = Carousel.objects.order_by('index').all()
        context = {
            'carousel_slides': carousel_slides,
            'recently_added_items': recently_added_items,
            'bestseller_items': bestseller_items,
            'paginate_by': paginate_by,
            'categories': categories,
        }

        return render(self.request, 'home.html', context)


# class OrderView(LoginRequiredMixin, ListView):
class OrderView(ListView):
    def get(self, *args, **kwargs):
        try:
            orders = Order.objects.filter(user=self.request.user, ordered=True)
            context = {
                'object': orders
            }
            return render(self.request, 'orders_finished.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have any orders')
            return redirect('/')


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        if self.request.GET['ref_code']:
            ref_code = self.request.GET['ref_code']
            order = Order.objects.get(ref_code=ref_code)
            if order.user == self.request.user:
                form = RefundForm(initial={'ref_code': ref_code})
                context = {
                    'form': form,
                }
                return render(self.request, 'request_refund.html', context)
            else:
                messages.warning(self.request,
                                 'You are not the user who ordered \
                                 this order')
                return redirect('core:home')
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
                        refund = Refund()
                        refund.order = order
                        refund.reason = message
                        refund.email = email
                        refund.save()
                        messages.info(self.request,
                                      'Your request was received')
                        return redirect('core:orders-finished')

                    elif order.refund_granted:
                        messages.info(self.request,
                                      'You have already received refund \
                                          for this order')

                    else:
                        messages.info(self.request,
                                      'You have already submitted a ticket. \
                                          Please wait until we contact you')

                    return redirect('core:orders-finished')

                else:
                    messages.warning(self.request,
                                     'You are not the user who ordered \
                                         this order')
                    return redirect('core:home')

            except ObjectDoesNotExist:
                messages.warning(self.request, 'This order does not exist')
                return redirect('core:orders-finished')
