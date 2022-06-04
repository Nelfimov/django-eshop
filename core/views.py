from datetime import datetime

from cart.models import Cart, CartItem
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, View

from .models import Carousel, CategoryItem, Item


class HomeView(View):
    def get(self, *args, **kwargs):
        paginate_by = 8
        recently_added_items = Item.objects.all().order_by('created_date')
        categories = CategoryItem.objects.all()
        if self.request.GET.get('category'):
            category_filter = self.request.GET.get('category')
            recently_added_items = recently_added_items.filter(
                category=category_filter)

        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            recently_added_items = recently_added_items.filter(
                title__icontains=search)

        bestseller_items = Item.objects.filter(ordered_counter__gt=0).order_by(
            '-ordered_counter')[:8]
        carousel_slides = Carousel.objects.order_by('index').all()
        context = {
            'carousel_slides': carousel_slides,
            'recently_added_items': recently_added_items,
            'bestseller_items': bestseller_items,
            'paginate_by': paginate_by,
            'categories': categories,
        }

        return render(self.request, 'home.html', context)


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'
