from django.db import models
from django.utils.translation import gettext as _

from common.models import compress


class Refund(models.Model):
    order = models.ForeignKey(
        "order.Order", on_delete=models.CASCADE, verbose_name=_("Order")
    )
    reason = models.TextField(verbose_name=_("Reason"))
    accepted = models.BooleanField(default=False, verbose_name=_("Accepted"))
    image = models.ImageField(upload_to="refund/", verbose_name="Image", null=True)
    email = models.EmailField(null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_image = self.image

    def __str__(self):
        return f"{self.pk}"

    def save(self, *args, **kwargs):
        if self._old_image != self.image:
            self.image = compress(self.image)
        super().save(*args, **kwargs)
