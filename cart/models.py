from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _


class CartItem(models.Model):
    ordered = models.BooleanField(default=False, verbose_name=_('ordered'))
    item = models.ForeignKey('core.Item', on_delete=models.CASCADE,
                             verbose_name=_('item'))
    quantity = models.IntegerField(default='1', verbose_name=_('quantity'))

    class Meta:
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')

    def __str__(self):
        return f"{self.item.title}: {self.quantity}"

    def get_total_item_price(self):
        return self.quantity * self.item.get_final_price()

    def get_saving(self):
        return self.quantity * self.item.discount


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                             on_delete=models.CASCADE, blank=True)
    creation_date = models.DateTimeField(
        verbose_name=_('creation date'),
        auto_now_add=True,
    )
    checked_out = models.BooleanField(default=False,
                                      verbose_name=_('checked out'))
    items = models.ManyToManyField('CartItem', blank=True,
                                   verbose_name=_('items'))
    session_key = models.CharField(max_length=60, null=True, blank=True)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')
        ordering = ('-creation_date',)
        unique_together = ('user', 'session_key')

    def __str__(self):
        return f'Session key: {self.session_key} with {self.items.count()}\
             items in it'

    def get_total(self):
        total = 0
        for cart_item in self.items.all():
            total += cart_item.get_total_item_price()
        return total
