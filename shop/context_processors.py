from .cart import Cart
from .models import Category


def cart_context(request):
    """
    Context processor to provide cart and hierarchical categories to all templates.
    """
    parent_categories = Category.objects.filter(parent=None).prefetch_related('subcategories').order_by('id')
    return {
        'cart': Cart(request),
        'nav_categories': Category.objects.all(),
        'nav_parent_categories': parent_categories,
    }
