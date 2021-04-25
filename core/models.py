from autoslug import AutoSlugField
from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django_countries.fields import CountryField
# from payment.models import Payment
import os
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
import sys


# CATEGORY_CHOICES = (
#     ('BO', 'Books'),
#     ('DO', 'Dolls'),
#     ('AC', 'Accessories'),
#     ('OT', 'Others')
# )

LABEL_CHOICES = (
    ('p', 'primary'),
    ('s', 'secondary'),
    ('d', 'danger')
)

CURRENCY_CHOICES = (
    ('EUR', 'Euro'),
    ('USD', 'US Dollars'),
)

class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(decimal_places=2, max_digits=100000)
    currency = models.CharField(choices=CURRENCY_CHOICES, max_length=3)
    discount_price = models.DecimalField(decimal_places=2, max_digits=100000, blank=True, null=True)
    image = models.ImageField(null=True, blank=True)
    category = models.CharField(max_length=20)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    stock = models.IntegerField()
    slug = AutoSlugField(populate_from='title', unique_with='id')
    description = models.TextField()
    
    def __str__(self):
        return self.title
    pass

    def get_absolute_url(self):
        return reverse('core:product', kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse('core:add-to-cart', kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse('core:remove-from-cart', kwargs={
            'slug': self.slug
        })


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey(
        'BillingAddress', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'payment.Payment', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total


class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username
