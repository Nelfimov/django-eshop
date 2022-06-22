from datetime import date
from io import BytesIO

from autoslug import AutoSlugField
from django.core.files import File
from django.db import models
from django.shortcuts import reverse
from django.utils.translation import gettext as _
from embed_video.fields import EmbedVideoField
from PIL import Image

LABEL_CHOICES = (
    ("n", "NEW"),
    ("h", "HOT"),
)


# Image path function
def item_image_path(instance, filename):
    dt = date.today()
    return f"items/{dt.year}/{dt.month}/{instance.slug}/{filename}"


# Image compression method
def compress(image):
    im = Image.open(image)
    im_io = BytesIO()
    im.save(im_io, "JPEG", quality=60)
    new_image = File(im_io, name=image.name)
    return new_image


class CategoryItem(models.Model):
    name = models.CharField(max_length=20)
    slug = AutoSlugField(populate_from="name", unique_with="id")

    def __str__(self):
        return self.name


class Item(models.Model):
    title = models.CharField(max_length=100, verbose_name=_("Title"))
    slug = AutoSlugField(populate_from="title", unique_with="id")
    price = models.DecimalField(
        decimal_places=2, max_digits=10, verbose_name=_("Price")
    )
    delivery_price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        blank=True,
        null=True,
        verbose_name=_("Delivery price"),
    )
    discount = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        blank=True,
        null=True,
        verbose_name=_("Discount"),
    )
    category = models.ForeignKey(
        "CategoryItem",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Category"),
    )
    label = models.CharField(choices=LABEL_CHOICES, max_length=1, null=True, blank=True)
    stock = models.PositiveIntegerField(default="1", verbose_name=_("Stock"))
    title_image = models.ImageField(
        upload_to=item_image_path, verbose_name=_("Title image")
    )
    item_video = EmbedVideoField(verbose_name="Item video", blank=True)
    description = models.TextField(verbose_name=_("Description"))
    additional_information = models.TextField(
        blank=True, null=True, verbose_name=_("Additional information")
    )
    created_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Creation date")
    )
    ordered_counter = models.PositiveIntegerField(
        default="0", verbose_name=_("Ordered counter")
    )

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.title_image:
            self.image = compress(self.title_image)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:product", kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        return reverse("order:add-to-cart", kwargs={"slug": self.slug})

    def get_remove_from_cart_url(self):
        return reverse("order:remove-from-cart", kwargs={"slug": self.slug})

    def get_final_price(self):
        return self.price + self.delivery_price - self.discount


class ItemImage(models.Model):
    item = models.ForeignKey(
        "Item",
        related_name="images",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to=item_image_path, verbose_name=_("Image"))

    @property
    def slug(self):
        return self.item.slug

    class Meta:
        verbose_name = _("Item image")
        verbose_name_plural = _("Item images")

    def save(self, *args, **kwargs):
        if self.image:
            self.image = compress(self.image)
        super().save(*args, **kwargs)


class Carousel(models.Model):
    img = models.ImageField(upload_to="carousel/images/")
    title = models.CharField(max_length=120, verbose_name=_("Title"))
    body = models.TextField(verbose_name=_("Body text"))
    alt = models.TextField(verbose_name=_("Alt text"))
    index = models.IntegerField(unique=True)

    def __str__(self):
        return self.title
