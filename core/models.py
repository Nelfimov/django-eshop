from tabnanny import verbose
from autoslug import AutoSlugField
from datetime import date
from cart.models import Cart, CartItem
from django.conf import settings
from django.core import mail
from django.db import models
from django.dispatch import receiver
from django.shortcuts import reverse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext as _
from django_countries import Countries
from django_countries.fields import CountryField


LABEL_CHOICES = (
    ('n', 'NEW'),
    ('h', 'HOT'),
)


ADDRESS_CHOICES = (
    ('B', _('Billing')),
    ('S', _('Shipping')),
)


def item_image_path(instance, filename):
    dt = date.today()
    return f'items/{dt.year}/{dt.month}/{instance.slug}/{filename}'


class CategoryItem(models.Model):
    name = models.CharField(max_length=20)
    slug = AutoSlugField(populate_from='name', unique_with='id')

    def __str__(self):
        return self.name


class TrackingCompany(models.Model):
    name = models.CharField(max_length=120)
    tracking_link = models.CharField(max_length=240, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Tracking company')
        verbose_name_plural = _('Tracking companies')


class Item(models.Model):
    title = models.CharField(max_length=100, verbose_name=_('Title'))
    price = models.DecimalField(decimal_places=2, max_digits=10,
                                verbose_name=_('Price'))
    delivery_price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        blank=True,
        null=True,
        verbose_name=_('Delivery Price'),
    )
    discount = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        blank=True,
        null=True,
        verbose_name=_('Discount'),
    )
    category = models.ForeignKey(
        CategoryItem,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Category'),
    )
    label = models.CharField(
        choices=LABEL_CHOICES, max_length=1, null=True, blank=True)
    stock = models.PositiveIntegerField(default='1', verbose_name=_('Stock'))
    slug = AutoSlugField(populate_from='title', unique_with='id')
    title_image = models.ImageField(upload_to=item_image_path,
                                    verbose_name=_('Title Image'))
    description = models.TextField(verbose_name=_('Description'))
    additional_information = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Additional Information')
    )
    additional_information_image1 = models.ImageField(
        upload_to=item_image_path, blank=True, null=True)
    additional_information_image2 = models.ImageField(
        upload_to=item_image_path, blank=True, null=True)
    additional_information_image3 = models.ImageField(
        upload_to=item_image_path, blank=True, null=True)
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Creation date')
    )
    ordered_counter = models.PositiveIntegerField(
        default='0',
        verbose_name=_('Ordered counter')
    )

    class Meta:
        verbose_name = _('Item')
        verbose_name_plural = _('Items')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:product', kwargs={
            'slug': self.slug})

    def get_add_to_cart_url(self):
        return reverse('cart:add-to-cart', kwargs={
            'slug': self.slug})

    def get_remove_from_cart_url(self):
        return reverse('cart:remove-from-cart', kwargs={
            'slug': self.slug})

    def get_final_price(self):
        return self.price + self.delivery_price - self.discount


class Order(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True,
                             verbose_name=_('Cart'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, null=True, blank=True)
    items = models.ManyToManyField(CartItem, verbose_name=_('Items'))
    start_date = models.DateTimeField(auto_now_add=True,
                                      verbose_name=_('Creation date'))
    ordered_date = models.DateTimeField(null=True, blank=True,
                                        verbose_name=_('Ordered date'))
    ordered = models.BooleanField(default=False, verbose_name=_('Ordered'))
    billing_address = models.ForeignKey(
        'Address', related_name='billing_address',
        on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name=_('Billing address')
    )
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address',
        on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name=_('Shipping address')
    )
    payment = models.ForeignKey(
        'payment.Payment', on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Payment')
    )
    ref_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default='',
        verbose_name=_('Reference code')
    )
    being_delivered = models.BooleanField(
        default=False,
        verbose_name=_('Being delivered')
    )
    tracking_company = models.ForeignKey(
        to='core.TrackingCompany', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name=_('Tracking Company')
    )
    tracking_number = models.CharField(
        max_length=240, null=True, blank=True,
        verbose_name=_('Tracking number')
    )
    refund_requested = models.BooleanField(
        default=False,
        verbose_name=_('Refund requested')
    )
    refund_granted = models.BooleanField(
        default=False,
        verbose_name=_('Refund granted')
    )

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')


class EUCountries(Countries):
    only = [
        'BE', 'BG', 'CZ', 'DK', 'DE', 'EE', 'IE', 'GR', 'ES', 'FR',
        'HR', 'IT', 'CY', 'LV', 'LT', 'LU', 'HU', 'MT', 'NL', 'AT',
        'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'NO', 'LI', 'CH',
        'GB',
    ]


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField()
    name_for_delivery = models.CharField(
        max_length=120,
        verbose_name=_('Full name')
    )
    street_address = models.CharField(
        max_length=100,
        verbose_name=_('Street address')
    )
    apartment_address = models.CharField(
        max_length=100,
        verbose_name='Apartment address'
    )
    country = CountryField(
        multiple=False, countries=EUCountries,
        verbose_name=_('Country')
    )
    zip = models.CharField(max_length=100)
    address_type = models.CharField(
        max_length=1, choices=ADDRESS_CHOICES,
        verbose_name=_('Address Type')
    )
    default = models.BooleanField(
        default=False,
        verbose_name=_('Default')
    )

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = _('Addresses')


class Refund(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        verbose_name=_('Order')
    )
    reason = models.TextField(verbose_name=_('Reason'))
    accepted = models.BooleanField(
        default=False,
        verbose_name=_('Accepted')
    )
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"


class Carousel(models.Model):
    img = models.ImageField(upload_to='carousel/images/')
    title = models.CharField(
        max_length=120, verbose_name=_('Title')
    )
    body = models.TextField(verbose_name=_('Body text'))
    alt = models.TextField(verbose_name=_('Alt text'))
    index = models.IntegerField(unique=True)

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title


#  Send email when status 'Being delivered' is set to True
@receiver(models.signals.post_save, sender=Order)
def hear_signal(sender, instance, **kwargs):
    if kwargs.get('created'):
        return

    if instance.being_delivered:
        subject = _('Your order #') + instance.ref_code
        header = subject + _(' has been sent out')
        html_message = render_to_string(
            'emails/order_confirmation_email.html',
            {'order': instance, 'header': header}
        )
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        to = instance.shipping_address.email
        mail.send_mail(subject, plain_message, from_email,
                       [to], html_message=html_message)
