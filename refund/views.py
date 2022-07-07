from django.utils.html import strip_tags
from django.shortcuts import render
from django.conf import settings
from django.core import mail
from django.views.generic import View
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.template.loader import render_to_string

from order.models import Order
from .forms import RefundForm
from .models import Refund


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
