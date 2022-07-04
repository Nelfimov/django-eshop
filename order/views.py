from decouple import config
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, View, edit

from core.models import Item
from .forms import CheckoutForm, RefundForm
from .models import Address, Order, OrderItem, Refund


def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if item.stock <= 0:
        messages.warning(request, _("Unfortunately we do not have item on stock"))
        return redirect("core:product", slug=slug)
    if not request.user.is_authenticated and not request.session.exists(
        request.session.session_key
    ):
        request.session.create()
    order = Order.objects.filter(
        ordered=False,
        user=(request.user if request.user.is_authenticated else None),
        session_key=(
            None if request.user.is_authenticated else request.session.session_key
        ),
    ).first()
    if order is not None:
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
    order = (
        Order.objects.filter(
            ordered=False,
            user=(request.user if request.user.is_authenticated else None),
            session_key=(
                None if request.user.is_authenticated else request.session.session_key
            ),
        )
        .prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.filter(item=item))
        )
        .first()
    )
    if order is not None:
        order_item = order.orderitem_set.first()

        if order_item is not None:
            order_item.delete()
            messages.info(request, _("This item was removed from your cart"))
            return redirect("order:cart-summary")

        messages.warning(request, _("This item was not in your cart"))
        return redirect("core:product", slug=slug)

    messages.warning(request, _("Your cart is empty"))
    return redirect("core:product", slug=slug)


def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order = (
        Order.objects.filter(
            ordered=False,
            user=(request.user if request.user.is_authenticated else None),
            session_key=(
                None if request.user.is_authenticated else request.session.session_key
            ),
        )
        .prefetch_related(
            Prefetch("orderitem_set", queryset=OrderItem.objects.filter(item=item))
        )
        .first()
    )
    if order is not None:
        order_item = order.orderitem_set.all().first()
        if order_item is not None:
            if order_item.quantity <= 1:
                order_item.delete()
            else:
                order_item.quantity -= 1
                order_item.save()
            messages.info(request, _("This item quantity was updated"))
            return redirect("order:cart-summary")

        messages.info(request, _("This item was not in your cart"))
        return redirect("core:product", slug=slug)

    messages.info(request, _("You do not have an active cart"))
    return redirect("core:product", slug=slug)


class OrderView(View):
    def get(self, *args, **kwargs):
        try:
            order = (
                Order.objects.only("ordered", "user", "session_key")
                .filter(
                    ordered=False,
                    user=(
                        self.request.user
                        if self.request.user.is_authenticated
                        else None
                    ),
                    session_key=(
                        None
                        if self.request.user.is_authenticated
                        else self.request.session.session_key
                    ),
                )
                .prefetch_related("orderitem_set")
                .first()
            )
            context = {
                "order": order,
                "order_items": order.orderitem_set.all(),
                "order_total": order.get_total(),
            }
            return render(self.request, "cart_summary.html", context)
        except (IndexError, ObjectDoesNotExist, AttributeError):
            messages.warning(self.request, _("Your cart is empty"))
            return redirect("/")


class CheckoutView(edit.FormView):
    template_name = "checkout.html"
    form_class = CheckoutForm
    success_url = reverse_lazy("payment:payment")

    def get_form(self, *args, **kwargs):
        form = super().get_form(self.form_class)
        if not self.request.user.is_authenticated:
            form.fields.pop("default")
        return form

    def form_valid(self, form):
        action = form.save(commit=False)
        if self.request.user.is_authenticated:
            action.user = self.request.user
        action.save()
        order = (
            Order.objects.filter(
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
            .select_related("address")
            .first()
        )
        order.address = action
        order.save()
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            default_address = Address.objects.filter(
                user=self.request.user, default=True
            ).first()
            if default_address is not None:
                initial.update(
                    {
                        "email": default_address.email,
                        "shipping_name": default_address.shipping_name,
                        "shipping_street_address": default_address.shipping_street_address,
                        "shipping_apartment_address": default_address.shipping_apartment_address,
                        "shipping_city": default_address.shipping_city,
                        "shipping_country": default_address.shipping_country,
                        "shipping_zip": default_address.shipping_zip,
                        "billing_name": default_address.billing_name,
                        "billing_street_address": default_address.billing_street_address,
                        "billing_apartment_address": default_address.billing_apartment_address,
                        "billing_city": default_address.billing_city,
                        "billing_country": default_address.billing_country,
                        "billing_zip": default_address.billing_zip,
                    }
                )
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "client_id": config("PAYPAL_CLIENT_ID"),
                "currency": "EUR",
            }
        )
        try:
            order = (
                Order.objects.filter(
                    ordered=False,
                    user=(
                        self.request.user
                        if self.request.user.is_authenticated
                        else None
                    ),
                    session_key=(
                        None
                        if self.request.user.is_authenticated
                        else self.request.session.session_key
                    ),
                )
                .select_related("address")
                .prefetch_related("orderitem_set")
                .first()
            )
            order_items = order.orderitem_set.all()
            if order is not None:
                context["order"] = order
                context["order_items"] = order_items
                if order.address:
                    context["order_has_address"] = True
        except AttributeError:
            messages.info(self.request, _("You do not have anything in cart"))
            return redirect("core:home")
        return context


class OrdersFinishedView(LoginRequiredMixin, ListView):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(self.request, _("You have to authorize for this view"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        try:
            orders = Order.objects.filter(
                user=self.request.user, ordered=True
            ).select_prefetched("orderitem_set")
            order_items = orders.orderitem_set.all()
            context = {"object": orders, "order_items": order_items}
            return render(self.request, "orders_finished.html", context)
        except (ObjectDoesNotExist, AttributeError):
            messages.warning(self.request, _("You do not have any orders"))
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
