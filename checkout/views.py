from decouple import config
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import edit
from django.utils.translation import gettext_lazy as _

from .forms import CheckoutForm
from .models import Address
from order.models import Order


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
