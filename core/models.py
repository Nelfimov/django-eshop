from functools import cached_property

from autoslug import AutoSlugField
from django.db import models
from django.shortcuts import reverse
from django.utils.translation import gettext as _
from embed_video.fields import EmbedVideoField

from common.models import compress, item_image_path, carousel_image_path


LABEL_CHOICES = (
    ("n", "NEW"),
    ("h", "HOT"),
)


class CategoryItem(models.Model):
    name = models.CharField(max_length=20)
    slug = AutoSlugField(populate_from="name", unique_with="id")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Item category")
        verbose_name_plural = _("Item categories")


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
        verbose_name=_("Delivery price"),
        default=0,
    )
    discount = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        blank=True,
        verbose_name=_("Discount"),
        default=0,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_title_image = self.title_image

    def save(self, *args, **kwargs):
        if self._old_title_image != self.title_image:
            self.title_image = compress(self.title_image)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:product", kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        return reverse("order:add-to-cart", kwargs={"slug": self.slug})

    def get_remove_from_cart_url(self):
        return reverse("order:remove-from-cart", kwargs={"slug": self.slug})

    @cached_property
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_image = self.image

    def save(self, *args, **kwargs):
        if self._old_image != self.image:
            self.image = compress(self.image)
        super().save(*args, **kwargs)


class Carousel(models.Model):
    img = models.ImageField(upload_to=carousel_image_path)
    title = models.CharField(max_length=120, verbose_name=_("Title"))
    body = models.TextField(verbose_name=_("Body text"))
    alt = models.TextField(verbose_name=_("Alt text"))
    index = models.IntegerField(unique=True)

    class Meta:
        verbose_name = _("Carousel")
        verbose_name_plural = _("Carousels")

    def __str__(self):
        return self.title

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_img = self.img

    def save(self, *args, **kwargs):
        if self._old_img != self.img:
            self.img = compress(self.img)
        super().save(*args, **kwargs)
