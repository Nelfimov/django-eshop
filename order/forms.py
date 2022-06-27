from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from .models import EUCountries


class CheckoutForm(forms.Form):
    email = forms.EmailField(required=True)
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_country = CountryField(
        countries=EUCountries, blank_label="(select country)"
    ).formfield(
        required=False,
        widget=CountrySelectWidget(attrs={"class": "custom-select d-block w-100"}),
    )
    shipping_zip = forms.CharField(required=False)
    shipping_name = forms.CharField(required=False)
    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_country = CountryField(
        countries=EUCountries, blank_label="(select country)"
    ).formfield(
        required=False,
        widget=CountrySelectWidget(attrs={"class": "custom-select d-block w-100"}),
    )
    billing_zip = forms.CharField(required=False)
    billing_name = forms.CharField(required=False)
    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)
    save_info = forms.BooleanField(required=False)


class RefundForm(forms.Form):
    ref_code = forms.CharField(required=True)
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 4,
            }
        ),
        required=True,
    )
    image = forms.ImageField(required=False)
    email = forms.EmailField(required=True)
