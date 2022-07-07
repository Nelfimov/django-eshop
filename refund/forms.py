from django import forms


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
