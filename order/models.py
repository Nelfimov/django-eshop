from functools import cached_property

from django.conf import settings
from django.core import mail
from django.db import models
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext as _
from django_countries import Countries
from django_countries.fields import CountryField


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
        return self.quantity * self.item.get_final_price

    @cached_property
    def get_saving(self):
        return self.quantity * self.item.discount


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    session_key = models.CharField(max_length=60, null=True, blank=True)
    start_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Creation date")
    )
    ordered = models.BooleanField(default=False, verbose_name=_("Ordered"))
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
        "Address",
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

    def get_total(self):
        total = 0
        for cart_item in OrderItem.objects.filter(order=self.id):
            total += cart_item.get_total_item_price
        return total


class EUCountries(Countries):
    only = [
        "BE",
        "BG",
        "CZ",
        "DK",
        "DE",
        "EE",
        "IE",
        "GR",
        "ES",
        "FR",
        "HR",
        "IT",
        "CY",
        "LV",
        "LT",
        "LU",
        "HU",
        "MT",
        "NL",
        "AT",
        "PL",
        "PT",
        "RO",
        "SI",
        "SK",
        "FI",
        "SE",
        "NO",
        "LI",
        "CH",
        "GB",
    ]


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )
    email = models.EmailField()
    shipping_name = models.CharField(
        max_length=120, verbose_name=_("Shipping full name")
    )
    shipping_street_address = models.CharField(
        max_length=100, verbose_name=_("Shipping street address")
    )
    shipping_apartment_address = models.CharField(
        max_length=100, verbose_name=_("Shipping apartment address")
    )
    shipping_city = models.CharField(max_length=100, verbose_name=_("Shipping city"))
    shipping_country = CountryField(
        multiple=False, countries=EUCountries, verbose_name=_("Shipping country")
    )
    shipping_zip = models.CharField(max_length=10)
    billing_name = models.CharField(max_length=120, verbose_name=_("Billing full name"))
    billing_street_address = models.CharField(
        max_length=100, verbose_name=_("Billing street address")
    )
    billing_apartment_address = models.CharField(
        max_length=100, verbose_name=_("Billing apartment address")
    )
    billing_city = models.CharField(max_length=100, verbose_name=_("Billing city"))
    billing_country = CountryField(
        multiple=False, countries=EUCountries, verbose_name=_("Billing country")
    )
    billing_zip = models.CharField(max_length=10)
    default = models.BooleanField(
        default=False, verbose_name=_("Save for future usage"), blank=True
    )

    def __str__(self):
        return str(self.shipping_country)

    class Meta:
        verbose_name_plural = _("Addresses")


class Refund(models.Model):
    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, verbose_name=_("Order")
    )
    reason = models.TextField(verbose_name=_("Reason"))
    accepted = models.BooleanField(default=False, verbose_name=_("Accepted"))
    image = models.ImageField(upload_to="refund/", verbose_name="Image", null=True)
    email = models.EmailField(null=True)

    def __str__(self):
        return f"{self.pk}"


#  Send email when status changes
@receiver(models.signals.post_save, sender=Order)
def hear_signal(sender, instance, **kwargs):
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
