from core.models import Item
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from .models import Cart, CartItem


def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if (not request.user.is_authenticated and
            not request.session.exists(request.session.session_key)):
        request.session.create()

    cart_item, created = CartItem.objects.get_or_create(
        item=item,
        ordered=False
    )
    cart_qs = Cart.objects.filter(
        checked_out=False,
        user=(
            request.user if request.user.is_authenticated
            else None
        ),
        session_key=(
            None if request.user.is_authenticated
            else request.session.session_key
        ),
    )
    if cart_qs.exists():
        cart = cart_qs[0]
        if cart.items.filter(item__slug=item.slug).exists():
            cart_item.quantity += 1
            if cart_item.quantity > item.stock:
                messages.warning(
                    request, _('Unfortunately we do not have this ' +
                               'quantity on stock')
                )
                return redirect('cart:cart-summary')

            cart_item.save()
            messages.info(request, _('Quantity was updated'))
            return redirect('cart:cart-summary')
        else:
            if item.stock <= 0:
                messages.warning(
                    request, _('Unfortunately we do not have item on stock')
                )
                return redirect('core:product', slug=slug)

            cart.items.add(cart_item)
            messages.info(request, _('Quantity was updated'))
            return redirect('cart:cart-summary')
    else:
        if item.stock == 0:
            messages.warning(
                request,
                _('Unfortunately we do not have item on stock')
            )
            return redirect('core:product')

        cart = Cart.objects.create(
            user=request.user if request.user.is_authenticated else None,
            creation_date=timezone.now(),
            session_key=(
                None if request.user.is_authenticated
                else request.session.session_key
            ),
        )
        cart.items.add(cart_item)
        messages.info(request, _('Quantity was updated'))
        return redirect('cart:cart-summary')


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    cart_qs = Cart.objects.filter(
        checked_out=False,
        user=(
            request.user if request.user.is_authenticated
            else None
        ),
        session_key=(
            None if request.user.is_authenticated
            else request.session.session_key
        ),
    )
    if cart_qs.exists():
        cart = cart_qs[0]
        if cart.items.filter(item__slug=item.slug).exists():
            cart_item = CartItem.objects.filter(
                item=item,
                ordered=False
            )[0]
            cart.items.remove(cart_item)
            cart_item.delete()
            messages.info(
                request,
                _('This item was removed from your cart')
            )
            return redirect('cart:cart-summary')
        else:
            messages.warning(request, _('This item was not in your cart'))
            return redirect('core:product', slug=slug)
    else:
        messages.warning(request, _('Your cart is empty'))
        return redirect('core:product', slug=slug)


def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    cart_qs = Cart.objects.filter(
        checked_out=False,
        user=(
            request.user if request.user.is_authenticated
            else None
        ),
        session_key=(
            None if request.user.is_authenticated
            else request.session.session_key
        ),
    )
    if cart_qs.exists():
        cart = cart_qs[0]
        if cart.items.filter(item__slug=item.slug).exists():
            cart_item = CartItem.objects.filter(
                item=item,
                ordered=False
            )[0]
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart.items.remove(cart_item)
                cart_item.delete()
            messages.info(request, _('This item quantity was updated'))
            return redirect('cart:cart-summary')
        else:
            messages.info(request, _('This item was not in your cart'))
            return redirect('core:product', slug=slug)
    else:
        messages.info(request, _('You do not have an active cart'))
        return redirect('core:product', slug=slug)


class CartView(View):
    def get(self, *args, **kwargs):
        try:
            cart = Cart.objects.get(
                checked_out=False,
                user=(
                    self.request.user
                    if self.request.user.is_authenticated
                    else None
                ),
                session_key=(
                    None if self.request.user.is_authenticated
                    else self.request.session.session_key
                ),
            )
            context = {'object': cart}
            return render(self.request, 'cart_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, _('Your cart is empty'))
            return redirect('/')
