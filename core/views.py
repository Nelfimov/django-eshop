from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

from .forms import CheckoutForm, RefundForm
from .models import Address, Carousel, CategoryItem, Item, Order, OrderItem, \
                    Refund


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, 'products.html', context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = CheckoutForm()
        context = {
            'form': form,
            'order': order,
        }

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
            context.update({'default_billing_address': billing_address_qs[0]})
        return render(self.request, 'checkout.html', context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print('Using default shipping address')
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        defulat=True,
                    )

                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request,
                                      'No default shipping address available')
                        return redirect('core:checkout')
                else:
                    print('User is entering a new shipping address')
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')
                    if is_valid_form([shipping_address1,
                                      shipping_country,
                                      shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()
                    order.shipping_address = shipping_address
                    order.save()
                    set_default_shipping = form.cleaned_data.get(
                        'set_default_shipping')
                    if set_default_shipping:
                        shipping_address.default = True
                        shipping_address.save()
                    else:
                        messages.info(self.request,
                                      'Please fill in the \
                                       required shipping address')
                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
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
                elif use_default_billing:
                    print('Using default billing address')
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        defulat=True,
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(self.request,
                                      'No default billing address available')
                        return redirect('core:checkout')
                else:
                    print('User is entering a new billing address')
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get(
                        'billing_zip')
                    if is_valid_form([billing_address1,
                                      billing_country,
                                      billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()
                    order.billing_address = billing_address
                    order.save()
                    set_default_billing = form.cleaned_data.get(
                        'set_default_billing')
                    if set_default_billing:
                        billing_address.default = True
                        billing_address.save()
                    else:
                        messages.info(self.request,
                                      'Please fill in the required \
                                      shipping address')
                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('payment:stripe')
                elif payment_option == 'P':
                    return redirect('payment:paypal')
                else:
                    messages.warning(self.request,
                                     'Invalid payment option selected')
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order')
            return redirect('core:order-summary')

        return redirect('core:checkout')


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
            'how_many_times_ordered')[:10]
        carousel_slides = Carousel.objects.order_by('index').all()
        context = {
            'carousel_slides': carousel_slides,
            'recently_added_items': recently_added_items,
            'bestseller_items': bestseller_items,
            'paginate_by': paginate_by,
            'categories': categories,
        }

        return render(self.request, 'home.html', context)


class OrderView(LoginRequiredMixin, ListView):
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


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order')
            return redirect('/')


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            if order_item.quantity > item.stock:
                messages.warning(
                    request,
                    'Unfortunately we do not have this quantity on stock')
                return redirect('core:order-summary')

            order_item.save()
            messages.info(request, 'Quantity was updated')
            return redirect('core:order-summary')
        else:
            if item.stock == 0:
                messages.warning(
                    request,
                    'Unfortunately we do not have item on stock')
                return redirect('core:product')

            order.items.add(order_item)
            messages.info(request, 'This item was added to your cart')
            return redirect('core:order-summary')
    else:
        if item.stock == 0:
            messages.warning(
                    request,
                    'Unfortunately we do not have item on stock')
            return redirect('core:product')

        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, 'This item was added to your cart')
        return redirect('core:order-summary')


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )

    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, 'This item was removed from your cart')
            return redirect('core:order-summary')
        else:
            messages.warning(request, 'This item was not in your cart')
            return redirect('core:product', slug=slug)
    else:
        messages.warning(request, 'You do not have an active order')
        return redirect('core:product', slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )

    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, 'This item quantity was updated')
            return redirect('core:order-summary')
        else:
            messages.info(request, 'This item was not in your cart')
            return redirect('core:product', slug=slug)
    else:
        messages.info(request, 'You do not have an active order')
        return redirect('core:product', slug=slug)


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
