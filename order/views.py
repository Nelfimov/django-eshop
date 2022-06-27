from core.models import Item
from decouple import config
from django.conf import settings
from django.contrib import messages
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, View

from .forms import CheckoutForm, RefundForm
from .models import Address, Order, OrderItem, Refund


def is_valid_form(values):
    valid = True
    for field in values:
        if field == "":
            valid = False
    return valid


def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if item.stock <= 0:
        messages.warning(request, _("Unfortunately we do not have item on stock"))
        return redirect("core:product", slug=slug)
    if not request.user.is_authenticated and not request.session.exists(
        request.session.session_key
    ):
        request.session.create()
    order_qs = Order.objects.filter(
        ordered=False,
        user=(request.user if request.user.is_authenticated else None),
        session_key=(
            None if request.user.is_authenticated else request.session.session_key
        ),
    )
    if order_qs.exists():
        order = order_qs[0]
        order_item, created = OrderItem.objects.get_or_create(item=item, order=order)
        if not created:
            order_item.quantity += 1
            if order_item.quantity > item.stock:
                messages.warning(
                    request,
                    _("Unfortunately we do not have this " + "quantity on stock"),
                )
                return redirect("order:cart-summary")
            order_item.save()
            messages.info(request, _("Quantity was updated"))
            return redirect("order:cart-summary")
        messages.info(request, _("Quantity was updated"))
        return redirect("order:cart-summary")
    else:
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            start_date=timezone.now(),
            session_key=(
                None if request.user.is_authenticated else request.session.session_key
            ),
        )
        order_item = OrderItem.objects.create(item=item, order=order)
        messages.info(request, _("Quantity was updated"))
        return redirect("order:cart-summary")


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        ordered=False,
        user=(request.user if request.user.is_authenticated else None),
        session_key=(
            None if request.user.is_authenticated else request.session.session_key
        ),
    )
    if order_qs.exists():
        order = order_qs[0]
        order_item_qs = OrderItem.objects.filter(order=order, item=item)
        if order_item_qs.exists():
            order_item = order_item_qs[0]
            order_item.delete()
            messages.info(request, _("This item was removed from your cart"))
            return redirect("order:cart-summary")
        else:
            messages.warning(request, _("This item was not in your cart"))
            return redirect("core:product", slug=slug)
    else:
        messages.warning(request, _("Your cart is empty"))
        return redirect("core:product", slug=slug)


def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        ordered=False,
        user=(request.user if request.user.is_authenticated else None),
        session_key=(
            None if request.user.is_authenticated else request.session.session_key
        ),
    )
    if order_qs.exists():
        order = order_qs[0]
        order_item_qs = OrderItem.objects.filter(order=order, item=item)
        if order_item_qs.exists():
            order_item = order_item_qs[0]
            if order_item.quantity <= 1:
                order_item.delete()
            else:
                order_item.quantity -= 1
                order_item.save()
            messages.info(request, _("This item quantity was updated"))
            return redirect("order:cart-summary")
        else:
            messages.info(request, _("This item was not in your cart"))
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, _("You do not have an active cart"))
        return redirect("core:product", slug=slug)


class OrderView(View):
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
            context = {"order": order, "order_items": order_items}
            return render(self.request, "cart_summary.html", context)
        except ObjectDoesNotExist:
            messages.warning(self.request, _("Your cart is empty"))
            return redirect("/")


class CheckoutView(View):
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
            form = CheckoutForm()
            context = {
                "form": form,
                "order": order,
                "order_items": order_items,
                "client_id": config("PAYPAL_CLIENT_ID"),
                "currency": "EUR",
            }
            if self.request.user.is_authenticated:
                shipping_address_qs = Address.objects.filter(
                    user=self.request.user, address_type="S", default=True
                )

                if shipping_address_qs.exists():
                    context.update({"default_shipping_address": shipping_address_qs[0]})

                billing_address_qs = Address.objects.filter(
                    user=self.request.user, address_type="B", default=True
                )
                if billing_address_qs.exists():
                    context.update({"default_billing_address": billing_address_qs[0]})

            return render(self.request, "checkout.html", context)

        except ObjectDoesNotExist:
            messages.info(self.request, _("You do not have anything in cart"))
            return redirect("core:home")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
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
            if form.is_valid():
                if self.request.user.is_authenticated:

                    if form.cleaned_data.get("use_default_shipping"):
                        address_qs = Address.objects.filter(
                            user=self.request.user,
                            address_type="S",
                            default=True,
                        )
                        if address_qs.exists():
                            shipping_address = address_qs[0]
                            order.shipping_address = shipping_address
                            order.save()
                        else:
                            messages.warning(
                                self.request, _("No default shipping address available")
                            )
                            return redirect("order:checkout")

                    if form.cleaned_data.get("use_default_billing"):
                        address_qs = Address.objects.filter(
                            user=self.request.user,
                            address_type="B",
                            default=True,
                        )
                        if address_qs.exists():
                            billing_address = address_qs[0]
                            order.billing_address = billing_address
                            order.save()
                        else:
                            messages.warning(
                                self.request, _("No default billing address available")
                            )
                            return redirect("order:checkout")

                    if (
                        order.shipping_address
                        and form.cleaned_data.get("use_default_shipping")
                        and order.billing_address
                        and form.cleaned_data.get("use_default_billing")
                    ):
                        return redirect("payment:payment")

                shipping_email = form.cleaned_data.get("email")
                shipping_name = form.cleaned_data.get("shipping_name")
                shipping_address = form.cleaned_data.get("shipping_address")
                shipping_address2 = form.cleaned_data.get("shipping_address2")
                shipping_country = form.cleaned_data.get("shipping_country")
                shipping_zip = form.cleaned_data.get("shipping_zip")
                set_default_shipping = form.cleaned_data.get("set_default_shipping")
                if is_valid_form(
                    [
                        shipping_email,
                        shipping_name,
                        shipping_address,
                        shipping_country,
                        shipping_zip,
                    ]
                ):
                    shipping_address = Address.objects.create(
                        user=(
                            self.request.user
                            if self.request.user.is_authenticated
                            else None
                        ),
                        email=shipping_email,
                        name_for_delivery=shipping_name,
                        street_address=shipping_address,
                        apartment_address=shipping_address2,
                        country=shipping_country,
                        zip=shipping_zip,
                        address_type="S",
                        default=bool(set_default_shipping),
                    )
                    order.shipping_address = shipping_address
                    order.save()
                else:
                    messages.warning(
                        self.request,
                        _("Please fill in the required shipping address"),
                    )

                #  Billing address
                same_billing_address = form.cleaned_data.get("same_billing_address")
                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.address_type = "B"
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()
                else:
                    billing_name = form.cleaned_data.get("billing_name")
                    billing_address = form.cleaned_data.get("billing_address")
                    billing_address2 = form.cleaned_data.get("billing_address2")
                    billing_country = form.cleaned_data.get("billing_country")
                    billing_zip = form.cleaned_data.get("billing_zip")
                    set_default_billing = form.cleaned_data.get("set_default_billing")
                    if is_valid_form(
                        [billing_address, billing_name, billing_country, billing_zip]
                    ):
                        billing_address = Address.objects.create(
                            user=(
                                self.request.user
                                if self.request.user.is_authenticated
                                else None
                            ),
                            name_for_delivery=billing_name,
                            street_address=billing_address,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type="B",
                            default=bool(set_default_billing),
                        )
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.warning(
                            self.request,
                            _("Please fill in the required billing address"),
                        )
                        return redirect("order:checkout")

            if order.shipping_address and order.billing_address:
                return redirect("payment:payment")

            messages.warning(
                self.request,
                _("Please fill in the required fields"),
            )
            return redirect("order:checkout")

        except ObjectDoesNotExist:
            messages.warning(self.request, _("You do not have an" + " active order"))
            return redirect("order:cart-summary")


class OrdersFinishedView(ListView):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            try:
                orders = Order.objects.filter(user=self.request.user, ordered=True)
                context = {"object": orders}
                return render(self.request, "orders_finished.html", context)
            except ObjectDoesNotExist:
                messages.warning(self.request, _("You do not have any orders"))
                return redirect("/")

        messages.warning(self.request, _("You are not authorized"))
        return redirect("/")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        try:
            ref_code = self.request.GET["ref_code"]
            order = Order.objects.get(ref_code=ref_code)
            if order.user != self.request.user:
                messages.warning(
                    self.request, _("You are not the user who ordered" + " this order")
                )
                return redirect("core:home")
            form = RefundForm(
                initial={"ref_code": ref_code, "email": self.request.user.email}
            )
            context = {
                "form": form,
            }
            return render(self.request, "request_refund.html", context)

        except ObjectDoesNotExist:
            messages.warning(self.request, _("Order does not exist"))
            return redirect("core:home")

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            try:
                ref_code = form.cleaned_data.get("ref_code")
                order = Order.objects.get(ref_code=ref_code)
                if order.user != self.request.user:
                    messages.warning(
                        self.request, _("You are not the user who ordered this order")
                    )
                    return redirect("core:home")
                if order.refund_granted:
                    messages.info(
                        self.request,
                        _("You have already received refund for this order"),
                    )
                    return redirect("order:orders-finished")

                if order.refund_requested:
                    messages.info(
                        self.request,
                        _(
                            "You have already submitted a ticket. Please wait until we contact you"
                        ),
                    )
                    return redirect("order:orders-finished")

                order.refund_requested = True
                order.save()
                refund = Refund.objects.create(
                    order=order,
                    reason=form.cleaned_data.get("message"),
                    email=form.cleaned_data.get("email"),
                    image=form.cleaned_data.get("image"),
                )

                #  Send mail for confirmation of order
                subject = _("Refund request for your order #") + order.ref_code
                header = subject + _(
                    " has been received and " + "will be processed shortly"
                )
                html_message = render_to_string(
                    "emails/order_confirmation_email.html",
                    {"order": order, "header": header},
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
                    _("New refund/Neue refund ")
                    + order.ref_code
                    + _(" is requested/ist gesendet")
                )
                mail.mail_admins(
                    subject=subject_admin,
                    message=refund.message,
                    fail_silently=False,
                )
                messages.info(self.request, _("Your request was received"))
                return redirect("order:orders-finished")

            except ObjectDoesNotExist:
                messages.warning(self.request, _("This order does not exist"))
                return redirect("order:orders-finished")
