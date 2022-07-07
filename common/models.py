from io import BytesIO
from datetime import date

from django.core.files import File
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener


#  HEIF/HEIC enable compression in Pillow
register_heif_opener()


# Image path function
def item_image_path(instance, filename):
    name, ext = filename.split(".")  # pylint: disable=unused-variable
    current_date = date.today()
    return f"items/{current_date.year}/{current_date.month}/{instance.slug}/{name}.webp"


# Carousel item path
def carousel_image_path(instance, filename):
    name, ext = filename.split(".")  # pylint: disable=unused-variable
    return f"carousel/images/{instance.index}/{name}.webp"


# Image compression method
def compress(image):
    im = Image.open(image)  # pylint: disable=invalid-name
    # Image auto rotation if metadata is available
    im = ImageOps.exif_transpose(im)  # pylint: disable=invalid-name
    im_io = BytesIO()
    im.save(im_io, format="webp", quality=60)
    new_image = File(im_io, name=image.name)
    return new_image
