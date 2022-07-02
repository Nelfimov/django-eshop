from django.shortcuts import render
from django.views.generic import DetailView, View

from .models import Carousel, Item


class HomeView(View):
    def get(self, *args, **kwargs):
        paginate_by = 8
        recently_added_items = (
            Item.objects.select_related("category").all().order_by("created_date")
        )
        categories = {item.category for item in recently_added_items}
        if self.request.GET.get("category"):
            category_filter = self.request.GET.get("category")
            recently_added_items = recently_added_items.filter(category=category_filter)

        if self.request.GET.get("search"):
            search = self.request.GET.get("search")
            recently_added_items = recently_added_items.filter(title__icontains=search)

        bestseller_items = recently_added_items.filter(ordered_counter__gt=0).order_by(
            "-ordered_counter"
        )[:8]
        carousel_slides = Carousel.objects.order_by("index").all()
        context = {
            "carousel_slides": carousel_slides,
            "recently_added_items": recently_added_items,
            "bestseller_items": bestseller_items,
            "paginate_by": paginate_by,
            "categories": categories,
        }

        return render(self.request, "home.html", context)


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"

    def get_object(self, queryset=None):
        return (
            self.model.objects.select_related("category")
            .prefetch_related("images")
            .get(slug=self.kwargs["slug"])
        )
