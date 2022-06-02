from re import UNICODE
from django.utils.translation import gettext as _
from django.conf import settings
from django.db import models
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
import sys
import os


VAT_RATES = {
        'BE': '21', 'BG': '20', 'CZ': '21', 'DK': '25', 'DE': '19',
        'EE': '20', 'IE': '23', 'GR': '24', 'ES': '21', 'FR': '20',
        'HR': '25', 'IT': '22', 'CY': '19', 'LV': '21', 'LT': '21',
        'LU': '17', 'HU': '27', 'MT': '18', 'NL': '21', 'AT': '20',
        'PL': '23', 'PT': '23', 'RO': '19', 'SI': '22', 'SK': '20',
        'FI': '24', 'SE': '25', 'NO': '25', 'LI': '8', 'CH': '7.7',
        'GB': '20',
}


class PayPalClient:
    def __init__(self):
        self.client_id = os.environ["PAYPAL_CLIENT_ID"] \
            if 'PAYPAL_CLIENT_ID' in os.environ else "<<PAYPAL-CLIENT-ID>>"
        self.client_secret = os.environ["PAYPAL_CLIENT_SECRET"] \
            if 'PAYPAL_CLIENT_SECRET' in os.environ \
            else "<<PAYPAL-CLIENT-SECRET>>"

        #    Setting up and Returns PayPal SDK environment with \
        #    PayPal Access credentials.
        #    For demo purpose, we are using SandboxEnvironment.
        #    In production this will be LiveEnvironment.
        self.environment = SandboxEnvironment(client_id=self.client_id,
                                              client_secret=self.client_secret)

        # Returns PayPal HTTP client instance with environment which \
        # has access credentials context.
        # This can be used invoke PayPal API's provided the credentials \
        # have the access to do so.
        self.client = PayPalHttpClient(self.environment)

    def object_to_json(self, json_data):
        """
        Function to print all json data in an organized readable manner
        """
        result = {}
        if sys.version_info[0] < 3:
            itr = json_data.__dict__.iteritems()
        else:
            itr = json_data.__dict__.items()
        for key, value in itr:
            # Skip internal attributes.
            if key.startswith("__") or key.startswith("_"):
                continue
            result[key] = self.array_to_json_array(value) \
                if isinstance(value, list) \
                else self.object_to_json(value) \
                if not self.is_primittive(value) \
                else value
        return result

    def array_to_json_array(self, json_array):
        result = []
        if isinstance(json_array, list):
            for item in json_array:
                result.append(self.object_to_json(item)
                              if not self.is_primittive(item)
                              else self.array_to_json_array(item)
                              if isinstance(item, list) else item)
        return result

    def is_primittive(self, data):
        return isinstance(data, str) or \
            isinstance(data, UNICODE) or \
            isinstance(data, int)


class Payment(models.Model):
    paypal_id = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL,
                             blank=True, null=True)
    amount = models.FloatField(verbose_name=_('Amount'))
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp'))

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
