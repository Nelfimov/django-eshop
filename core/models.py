from autoslug import AutoSlugField
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.shortcuts import reverse
from django_countries import Countries
from django_countries.fields import CountryField


LABEL_CHOICES = (
    ('n', 'NEW'),
    ('h', 'HOT'),
)


ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class CategoryItem(models.Model):
    name = models.CharField(max_length=20)
    slug = AutoSlugField(populate_from='name', unique_with='id')

    def __str__(self):
        return self.name


class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    delivery_price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        blank=True,
        null=True,
    )
    discount_price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        CategoryItem,
        on_delete=models.SET_NULL,
        null=True,
        default=''
        )
    label = models.CharField(
        choices=LABEL_CHOICES, max_length=1, null=True, blank=True)
    stock = models.PositiveIntegerField()
    slug = AutoSlugField(populate_from='title', unique_with='id')
    title_image = models.ImageField(
        upload_to='items/' + str(title) + '/images/')
    description = models.TextField()
    additional_information = models.TextField(blank=True, null=True)
    additional_information_image1 = models.ImageField(
        upload_to='items/' + str(title) + '/images/', blank=True, null=True)
    additional_information_image2 = models.ImageField(
        upload_to='items/' + str(title) + '/images/', blank=True, null=True)
    additional_information_image3 = models.ImageField(
        upload_to='items/' + str(title) + '/images/', blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    how_many_times_ordered = models.IntegerField(default='0')

    def __str__(self):
        return self.title

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
        return self.quantity * (self.item.price + self.item.delivery_price)

    def get_total_discount_item_price(self):
        return self.quantity * (
            self.item.discount_price + self.item.delivery_price)

    def get_amount_saved(self):
        return self.get_total_item_price() - \
            self.get_total_discount_item_price()

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
        'Address', related_name='billing_address',
        on_delete=models.SET_NULL, blank=True, null=True)
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address',
        on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'payment.Payment', on_delete=models.SET_NULL, blank=True, null=True)
    ref_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default=''
        )
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total


class EUCountries(Countries):
    only = [
        'BE', 'BG', 'CZ', 'DK', 'DE', 'EE', 'IE', 'GR', 'ES', 'FR', 'FR',
        'HR', 'IT', 'CY', 'LV', 'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL',
        'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS', 'NO', 'LI', 'CH', 'GB',
    ]


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    name_for_delivery = models.CharField(max_length=120)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False, countries=EUCountries)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'Addresses'


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"


class Carousel(models.Model):
    img = models.ImageField(upload_to='carousel/images/')
    title = models.CharField(max_length=120)
    body = models.TextField()
    alt = models.TextField()
    index = models.IntegerField(unique=True)

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title


def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance)


post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)
