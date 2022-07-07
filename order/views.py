from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, View

from .models import Order


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
