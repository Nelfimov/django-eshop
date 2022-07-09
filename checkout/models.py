from django.db import models
from django.conf import settings
from django_countries import Countries
from django_countries.fields import CountryField
from django.utils.translation import gettext as _


class EUCountries(Countries):
    """Defining only countries to be available in checkout form"""

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
    )  # If True, address will be offered to user in future checkouts as initials

    def __str__(self):
        return str(self.shipping_country)

    class Meta:
        verbose_name_plural = _("Addresses")
