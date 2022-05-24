from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.views.generic import View

from .models import Cart, CartItem
from core.models import Item


def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(
            item=item,
            user=request.user,
            ordered=False
        )
        cart_qs = Cart.objects.filter(user=request.user, checked_out=False)
        if cart_qs.exists():
            cart = cart_qs[0]
            if cart.items.filter(item__slug=item.slug).exists():
                cart_item.quantity += 1
                if cart_item.quantity > item.stock:
                    messages.warning(
                        request,
                        'Unfortunately we do not have this quantity on stock'
                    )
                    return redirect('cart:cart-summary')

                cart_item.save()
                messages.info(request, 'Quantity was updated')
                return redirect('cart:cart-summary')
            else:
                if item.stock <= 0:
                    messages.warning(
                        request,
                        'Unfortunately we do not have item on stock'
                    )
                    return redirect('core:product')

                cart.items.add(cart_item)
                messages.info(request, 'This item was added to your cart')
                return redirect('cart:cart-summary')
        else:
            if item.stock == 0:
                messages.warning(
                    request,
                    'Unfortunately we do not have item on stock'
                )
                return redirect('core:product')

            cart = Cart.objects.create(user=request.user,
                                       creation_date=timezone.now())
            cart.items.add(cart_item)
            messages.info(request, 'This item was added to your cart')
            return redirect('cart:cart-summary')
    else:
        cart_item, created = CartItem.objects.get_or_create(
            user=None,
            item=item,
        )
        if not request.session.exists(request.session.session_key):
            request.session.create()

        cart_qs = Cart.objects.filter(user=None, checked_out=False,
                                      session_key=request.session.session_key)
        if cart_qs.exists():
            cart = cart_qs[0]
            if cart.items.filter(item__slug=item.slug).exists():
                cart_item.quantity += 1
                if cart_item.quantity > item.stock:
                    messages.warning(
                        request,
                        'Unfortunately we do not have this quantity on stock'
                    )
                    return redirect('cart:cart-summary')
                cart_item.save()
                return redirect('cart:cart-summary')
            else:
                cart.items.add(cart_item)
                return redirect('cart:cart-summary')
        else:
            cart, created = Cart.objects.get_or_create(
                user=None,
                session_key=request.session.session_key,
                creation_date=timezone.now()
            )
            print(request.session.session_key)
            cart.items.add(cart_item)
            messages.info(request, 'This item was added to your cart')
            return redirect('cart:cart-summary')


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:
        cart_qs = Cart.objects.filter(
            user=request.user,
            checked_out=False
        )
        if cart_qs.exists():
            cart = cart_qs[0]
            if cart.items.filter(item__slug=item.slug).exists():
                cart_item = CartItem.objects.filter(
                    items=item,
                    user=request.user,
                    checked_out=False
                )[0]
                cart.items.remove(cart_item)
                messages.info(request, 'This item was removed from your cart')
                return redirect('cart:cart-summary')
            else:
                messages.warning(request, 'This item was not in your cart')
                return redirect('core:product', slug=slug)
        else:
            messages.warning(request, 'Your cart is empty')
            return redirect('core:product', slug=slug)
    else:
        cart_qs = Cart.objects.filter(
            user=None,
            checked_out=False,
            session_key=request.session.session_key
        )
        if cart_qs.exists():
            cart = cart_qs[0]
            if cart.items.filter(item__slug=item.slug).exists():
                cart_item = CartItem.objects.filter(
                    item=item,
                    user=None,
                )[0]
                cart.items.remove(cart_item)
                messages.info(request, 'This item was removed from your cart')
                return redirect('cart:cart-summary')
            else:
                messages.warning(request, 'This item was not in your cart')
                return redirect('core:product', slug=slug)
        else:
            messages.warning(request, 'Your cart is empty')
            return redirect('core:product', slug=slug)


def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:
        cart_qs = Cart.objects.filter(
            user=request.user,
            checked_out=False
        )
        if cart_qs.exists():
            cart = cart_qs[0]
            if cart.items.filter(item__slug=item.slug).exists():
                cart_item = CartItem.objects.filter(
                    item=item,
                    user=request.user,
                    ordered=False
                )[0]
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                else:
                    cart.items.remove(cart_item)
                messages.info(request, 'This item quantity was updated')
                return redirect('cart:cart-summary')
            else:
                messages.info(request, 'This item was not in your cart')
                return redirect('core:product', slug=slug)
        else:
            messages.info(request, 'You do not have an active order')
            return redirect('core:product', slug=slug)
    else:
        cart_qs = Cart.objects.filter(
            user=None,
            checked_out=False,
            session_key=request.session.session_key
        )
        if cart_qs.exists():
            cart = cart_qs[0]
            if cart.items.filter(item__slug=item.slug).exists():
                cart_item = CartItem.objects.filter(
                    item=item,
                    user=None,
                    ordered=False
                )[0]
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                else:
                    cart.items.remove(cart_item)
                messages.info(request, 'This item quantity was updated')
                return redirect('cart:cart-summary')
            else:
                messages.info(request, 'This item was not in your cart')
                return redirect('core:product', slug=slug)
        else:
            messages.info(request, 'You do not have an active order')
            return redirect('core:product', slug=slug)


class CartView(View):
    def get(self, *args, **kwargs):
        try:
            if self.request.user.is_authenticated:
                cart = Cart.objects.get(
                    user=self.request.user,
                    checked_out=False
                )
            else:
                cart = Cart.objects.get(
                    user=None,
                    checked_out=False,
                    session_key=self.request.session.session_key
                )
            context = {
                'object': cart
            }
            return render(self.request, 'cart_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, 'Your cart is empty')
            return redirect('/')
