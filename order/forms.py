from django import forms
from django_countries.widgets import CountrySelectWidget

from .models import Address


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = "__all__"
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "shipping_name": forms.TextInput(attrs={"class": "form-control"}),
            "shipping_street_address": forms.TextInput(attrs={"class": "form-control"}),
            "shipping_apartment_address": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "shipping_city": forms.TextInput(attrs={"class": "form-control"}),
            "shipping_country": CountrySelectWidget(
                attrs={"class": "browser-default custom-select d-block w-100"}
            ),
            "shipping_zip": forms.NumberInput(attrs={"class": "form-control"}),
            "billing_name": forms.TextInput(attrs={"class": "form-control"}),
            "billing_street_address": forms.TextInput(attrs={"class": "form-control"}),
            "billing_apartment_address": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "billing_city": forms.TextInput(attrs={"class": "form-control"}),
            "billing_country": CountrySelectWidget(
                attrs={"class": "browser-default custom-select d-block w-100"}
            ),
            "billing_zip": forms.NumberInput(attrs={"class": "form-control"}),
        }


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
