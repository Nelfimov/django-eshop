from functools import cached_property

from decimal import Decimal
from django.conf import settings
from django.core import mail
from django.db import models
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext as _


class TrackingCompany(models.Model):
    name = models.CharField(max_length=120)
    tracking_link = models.CharField(max_length=240, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Tracking company")
        verbose_name_plural = _("Tracking companies")


class OrderItem(models.Model):
    item = models.ForeignKey(
        "core.Item", on_delete=models.CASCADE, verbose_name=_("Item")
    )
    quantity = models.IntegerField(default="1", verbose_name=_("Quantity"))
    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, verbose_name=_("Order")
    )

    class Meta:
        verbose_name = _("Cart Item")
        verbose_name_plural = _("Cart Items")

    def __str__(self):
        return f"{self.item.title}: {self.quantity}"

    @cached_property
    def get_total_item_price(self):
        """Total amount for this order item"""
        return self.quantity * self.item.get_final_price

    @cached_property
    def get_saving(self):
        """Total saving for this order item"""
        return self.quantity * self.item.discount


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    session_key = models.CharField(max_length=60, null=True, blank=True)
    start_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Creation date")
    )
    ordered = models.BooleanField(
        default=False, verbose_name=_("Ordered")
    )  # if False, the model acts as cart
    ordered_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Ordered date")
    )
    ref_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default="",
        verbose_name=_("Reference code"),
    )
    address = models.ForeignKey(
        "checkout.Address",
        related_name="address",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Address"),
    )
    being_delivered = models.BooleanField(
        default=False, verbose_name=_("Being delivered")
    )
    tracking_company = models.ForeignKey(
        to="TrackingCompany",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Tracking Company"),
    )
    tracking_number = models.CharField(
        max_length=240, null=True, blank=True, verbose_name=_("Tracking number")
    )
    refund_requested = models.BooleanField(
        default=False, verbose_name=_("Refund requested")
    )
    refund_granted = models.BooleanField(
        default=False, verbose_name=_("Refund granted")
    )

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ("-start_date",)
        unique_together = ("user", "session_key")

    @cached_property
    def get_delivery_total(self):
        """
        Delivery cost is not simply added up, but rather
        the max of the order items is taken with additional 20%
        """
        order_items = OrderItem.objects.filter(order=self.id).select_related("item")
        if order_items.count() > 1:
            item_delivery = []
            for item in order_items:
                item_delivery.append(item.item.delivery_price)
            delivery = round(Decimal(max(item_delivery)) * Decimal(1.2), 2)
        else:
            delivery = order_items[0].item.delivery_price
        return delivery

    @cached_property
    def get_total(self):
        """Total order amount"""
        order_items = OrderItem.objects.filter(order=self.id).select_related("item")
        total = 0
        for item in order_items:
            total += item.item.get_price_no_delivery * item.quantity
        total += self.get_delivery_total
        return total

    @cached_property
    def get_price_no_delivery(self):
        """Order amount without delivery"""
        return self.get_total - self.get_delivery_total


@receiver(models.signals.post_save, sender=Order)
def hear_signal(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Send email when status changes"""
    if kwargs.get("created"):
        return

    if instance.being_delivered:
        subject = _("Your order #") + instance.ref_code
        header = subject + _(" has been sent out")
        html_message = render_to_string(
            "emails/order_confirmation_email.html",
            {"order": instance, "header": header},
        )
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = instance.shipping_address.email
        mail.send_mail(
            subject, plain_message, from_email, [to_email], html_message=html_message
        )
        subject_admin = (
            "Order/Bestellung "
            + instance.ref_code
            + " is sent for delivery/wurde gesendet"
        )
        mail.mail_admins(
            subject=subject_admin,
            message="",
            fail_silently=False,
        )

    if instance.refund_granted:
        subject = _("Your order #") + instance.ref_code
        header = subject + _(" request for refund has been accepted")
        html_message = render_to_string(
            "emails/order_confirmation_email.html",
            {"order": instance, "header": header},
        )
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = instance.shipping_address.email
        mail.send_mail(
            subject, plain_message, from_email, [to_email], html_message=html_message
        )
        subject_admin = (
            "Order/Bestellung "
            + instance.ref_code
            + " refund granted/refund akzeptiert"
        )
        mail.mail_admins(
            subject=subject_admin,
            message="",
            fail_silently=False,
        )
