from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q, F, Case, When, Value, IntegerField
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import uuid
import stripe

from .models import (
    Category, Product, ProductVariant, ProductImage, Customer, Address, Order, Payment, Review,
    FeaturedProduct, NewProduct, OfferProduct
)
from .cart import Cart
from .forms import CheckoutForm, UserRegisterForm, CustomerProfileForm, AddressForm, ReviewForm, EmailLoginForm

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.


def home_view(request):
    """
    Homepage view:
    Hero banner, 5-point trust strip, Featured Products, New Arrivals (latest),
    Best Offers (highest discounts), and SEO buyer guidance.
    """
    categories = Category.objects.all()
    
    # 1. Featured Products (Curated via FeaturedProduct table, fallback to flagged/latest)
    featured_entries = FeaturedProduct.objects.select_related('product').prefetch_related('product__variants').all()
    if featured_entries.exists():
        featured_products = [entry.product for entry in featured_entries]
    else:
        featured_products = list(Product.objects.filter(is_featured=True).prefetch_related('variants').order_by('-created_at')[:4])
        if not featured_products:
            featured_products = list(Product.objects.all().prefetch_related('variants').order_by('-created_at')[:4])

    for p in featured_products:
        p._custom_badge = {
            'label': 'Featured',
            'icon': 'bi bi-star-fill text-warning',
            'css_class': 'featured',
        }

    # 2. New Arrivals (Curated via NewProduct table, fallback to latest added)
    new_entries = NewProduct.objects.select_related('product').prefetch_related('product__variants').all()
    if new_entries.exists():
        new_products = [entry.product for entry in new_entries]
    else:
        new_products = list(Product.objects.all().prefetch_related('variants').order_by('-created_at')[:4])

    for p in new_products:
        p._custom_badge = {
            'label': 'New',
            'icon': 'bi bi-sparkles text-white',
            'css_class': 'new',
        }

    # 3. Best Offers (Curated via OfferProduct table, fallback to highest discounts)
    offer_entries = OfferProduct.objects.select_related('product').prefetch_related('product__variants').all()
    if offer_entries.exists():
        best_offers = [entry.product for entry in offer_entries]
    else:
        discounted = list(Product.objects.filter(variants__regular_price__gt=F('variants__price')).distinct().prefetch_related('variants')[:4])
        if not discounted:
            discounted = list(Product.objects.all().prefetch_related('variants').order_by('-created_at')[:4])
        best_offers = discounted

    for p in best_offers:
        p._custom_badge = {
            'label': 'Hot Deals',
            'icon': 'bi bi-lightning-fill text-warning',
            'css_class': 'hot-deal',
        }

    # Visual assets for Hero Banner
    apple_exclusive = Product.objects.filter(brand__iexact='Apple').prefetch_related('variants').order_by('-created_at')[:4]
    if not apple_exclusive.exists():
        apple_exclusive = featured_products[:4]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'new_products': new_products,
        'best_offers': best_offers,
        'apple_exclusive': apple_exclusive,
        # Backward compatibility aliases
        'latest_products': new_products,
        'exclusive_deals': best_offers,
    }
    return render(request, 'shop/home.html', context)


def product_list_view(request):
    """
    Product listing page:
    Left sidebar filters (Price min/max, in-stock only, series checkboxes, brand checkboxes),
    category top banner, sorting, 3-column product cards, and pagination.
    """
    products = Product.objects.all()
    categories = Category.objects.all()

    # Available Brands for sidebar filter
    available_brands = Product.objects.exclude(brand='').values_list('brand', flat=True).distinct().order_by('brand')

    # Category Filter
    category_slug = request.GET.get('category', '').strip()
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        if selected_category.parent is None:
            # Main parent category: include products in this category and all its subcategories
            products = products.filter(
                Q(category=selected_category) | Q(category__parent=selected_category)
            )
        else:
            # Subcategory: match either specific subcategory or matching brand under this parent category
            products = products.filter(
                Q(category=selected_category) |
                (Q(category__parent=selected_category.parent) & Q(brand__iexact=selected_category.name))
            )

    # Brand Filter
    selected_brand = request.GET.get('brand', '').strip()
    if selected_brand:
        products = products.filter(brand__iexact=selected_brand)

    # Price Range Filters
    min_price = request.GET.get('min_price', '').strip()
    if min_price and min_price.isdigit():
        products = products.filter(variants__price__gte=float(min_price)).distinct()

    max_price = request.GET.get('max_price', '').strip()
    if max_price and max_price.isdigit():
        products = products.filter(variants__price__lte=float(max_price)).distinct()

    # Availability Filter (in_stock, out_of_stock)
    availability_filter = request.GET.get('availability', '').strip()
    if availability_filter == 'in_stock':
        in_stock_ids = ProductVariant.objects.filter(quantity__gt=0, is_available=True).values_list('product_id', flat=True)
        products = products.filter(id__in=in_stock_ids)
    elif availability_filter == 'out_of_stock':
        in_stock_ids = ProductVariant.objects.filter(quantity__gt=0, is_available=True).values_list('product_id', flat=True)
        products = products.exclude(id__in=in_stock_ids)

    # Search Query
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query)
        )

    # Featured Products Filter
    if request.GET.get('featured') == '1' or request.GET.get('is_featured') == '1':
        if FeaturedProduct.objects.exists():
            products = products.filter(Q(featured_entries__isnull=False) | Q(is_featured=True)).distinct()
        else:
            products = products.filter(is_featured=True)

    # Sorting
    sort = request.GET.get('sort', 'default')
    if sort == 'price_low':
        products = products.order_by('variants__price').distinct()
    elif sort == 'price_high':
        products = products.order_by('-variants__price').distinct()
    elif sort == 'name':
        products = products.order_by('name')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'discount':
        products = products.filter(variants__regular_price__gt=F('variants__price')).distinct()
    else: # default
        products = products.order_by('-created_at')

    total_count = products.count()

    # Pagination: 12 products per page (4 rows of 3 columns)
    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Assign labels (New for new arrivals, Featured for featured, Hot Deals for discounts)
    new_product_ids = set(Product.objects.all().order_by('-created_at')[:8].values_list('id', flat=True))
    for p in page_obj.object_list:
        if p.id in new_product_ids:
            p._custom_badge = {
                'label': 'New',
                'icon': 'bi bi-sparkles text-white',
                'css_class': 'new',
            }
        elif p.is_featured:
            p._custom_badge = {
                'label': 'Featured',
                'icon': 'bi bi-star-fill text-warning',
                'css_class': 'featured',
            }
        elif p.discount_amount and p.discount_amount > 0:
            p._custom_badge = {
                'label': 'Hot Deals',
                'icon': 'bi bi-lightning-fill text-warning',
                'css_class': 'hot-deal',
            }
        else:
            p._custom_badge = None

    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': categories,
        'selected_category': selected_category,
        'available_brands': available_brands,
        'selected_brand': selected_brand,
        'availability_filter': availability_filter,
        'min_price': min_price,
        'max_price': max_price,
        'query': query,
        'sort': sort,
        'total_count': total_count,
    }
    return render(request, 'shop/product_list.html', context)


def search_suggest_view(request):
    """
    Real-time live search suggestion endpoint for navbar search bar.
    Returns JSON of matched products (max 6) with thumbnail, price, category, and total count.
    """
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 1:
        return JsonResponse({'results': [], 'total': 0, 'query': ''})

    matched_qs = Product.objects.filter(
        Q(name__icontains=q) |
        Q(brand__icontains=q) |
        Q(category__name__icontains=q) |
        Q(category__parent__name__icontains=q)
    ).distinct()

    total_matches = matched_qs.count()

    top_products = matched_qs.annotate(
        match_rank=Case(
            When(name__istartswith=q, then=Value(1)),
            When(brand__istartswith=q, then=Value(2)),
            When(name__icontains=q, then=Value(3)),
            default=Value(4),
            output_field=IntegerField()
        )
    ).order_by('match_rank', '-created_at')[:6]

    results = []
    for p in top_products:
        image_url = p.image.url if p.image else ''
        results.append({
            'id': p.id,
            'name': p.name,
            'brand': p.brand or '',
            'category': p.category.name if p.category else '',
            'price': f"{int(p.price):,}" if p.price else "0",
            'regular_price': f"{int(p.regular_price):,}" if p.regular_price and p.regular_price > p.price else None,
            'discount_percent': p.discount_percent if p.discount_percent > 0 else None,
            'image_url': image_url,
            'detail_url': reverse('shop:product_detail', args=[p.id]),
            'in_stock': p.in_stock,
        })

    return JsonResponse({
        'results': results,
        'total': total_matches,
        'query': q,
    })


def product_detail_view(request, pk):
    """
    Product details page:
    Dynamic variant selector pills with pricing, regular price, stock updates,
    dual CTA buttons ("Shop Now" + "Add To Cart"), WhatsApp contact, EMI plans,
    2-column comprehensive specifications table, and "Recently Viewed" sidebar.
    """
    product = get_object_or_404(Product, pk=pk)

    # ── Smart Contextual Related Products (Industry Best Practice) ──
    TARGET_RELATED = 4
    related_ids = []
    base_qs = Product.objects.exclude(id=product.id).prefetch_related('variants')

    # Level 1: Same Subcategory + Same Brand (Exact Match)
    if product.brand and product.category:
        l1_ids = list(base_qs.filter(
            category=product.category,
            brand__iexact=product.brand.strip()
        ).values_list('id', flat=True)[:TARGET_RELATED])
        for pid in l1_ids:
            if pid not in related_ids:
                related_ids.append(pid)

    # Level 2: Same Subcategory + Similar Price Range (±35% of price)
    if len(related_ids) < TARGET_RELATED and product.category and product.price:
        min_p = float(product.price) * 0.65
        max_p = float(product.price) * 1.35
        needed = TARGET_RELATED - len(related_ids)
        l2_ids = list(base_qs.exclude(id__in=related_ids).filter(
            category=product.category,
            variants__price__gte=min_p,
            variants__price__lte=max_p
        ).distinct().order_by('-is_featured', '-created_at').values_list('id', flat=True)[:needed])
        for pid in l2_ids:
            if pid not in related_ids:
                related_ids.append(pid)

    # Level 3: Same Subcategory (Any Price)
    if len(related_ids) < TARGET_RELATED and product.category:
        needed = TARGET_RELATED - len(related_ids)
        l3_ids = list(base_qs.exclude(id__in=related_ids).filter(
            category=product.category
        ).order_by('-is_featured', '-created_at').values_list('id', flat=True)[:needed])
        for pid in l3_ids:
            if pid not in related_ids:
                related_ids.append(pid)

    # Level 4: Same Parent Category (Sibling Categories)
    if len(related_ids) < TARGET_RELATED and product.category and product.category.parent:
        needed = TARGET_RELATED - len(related_ids)
        l4_ids = list(base_qs.exclude(id__in=related_ids).filter(
            category__parent=product.category.parent
        ).order_by('-is_featured', '-created_at').values_list('id', flat=True)[:needed])
        for pid in l4_ids:
            if pid not in related_ids:
                related_ids.append(pid)

    # Level 5: Fallback to Top-Featured or New Arrivals in Catalog
    if len(related_ids) < TARGET_RELATED:
        needed = TARGET_RELATED - len(related_ids)
        l5_ids = list(base_qs.exclude(id__in=related_ids).order_by(
            '-is_featured', '-created_at'
        ).values_list('id', flat=True)[:needed])
        for pid in l5_ids:
            if pid not in related_ids:
                related_ids.append(pid)

    # Fetch products preserving rank order
    if related_ids:
        products_dict = {p.id: p for p in Product.objects.filter(id__in=related_ids)}
        related_products = [products_dict[pid] for pid in related_ids if pid in products_dict]
    else:
        related_products = []
    new_product_ids = set(Product.objects.all().order_by('-created_at')[:8].values_list('id', flat=True))
    for p in related_products:
        if p.id in new_product_ids:
            p._custom_badge = {
                'label': 'New',
                'icon': 'bi bi-sparkles text-white',
                'css_class': 'new',
            }
        elif p.is_featured:
            p._custom_badge = {
                'label': 'Featured',
                'icon': 'bi bi-star-fill text-warning',
                'css_class': 'featured',
            }
        elif p.discount_amount and p.discount_amount > 0:
            p._custom_badge = {
                'label': 'Hot Deals',
                'icon': 'bi bi-lightning-fill text-warning',
                'css_class': 'hot-deal',
            }
        else:
            p._custom_badge = None

    gallery_images = product.images.all()
    variants = product.variants.all().order_by('-is_default', 'name')
    default_variant = product.default_variant
    reviews = product.reviews.all()
    review_form = ReviewForm()

    # SKU / Product Code
    sku_code = f"AGL{product.id + 30400}"

    context = {
        'product': product,
        'related_products': related_products,
        'gallery_images': gallery_images,
        'variants': variants,
        'default_variant': default_variant,
        'sku_code': sku_code,
        'reviews': reviews,
        'review_form': review_form,
        'specs_list': [],  # specs now come from product.description (rich text)
    }
    return render(request, 'shop/product_detail.html', context)


@login_required
def add_review_view(request, product_id):
    """
    Submit a review on a product.
    """
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            customer, _ = Customer.objects.get_or_create(
                user=request.user,
                defaults={
                    'name': request.user.get_full_name() or request.user.username,
                    'phone': '',
                    'address': '',
                    'email': request.user.email
                }
            )
            review = form.save(commit=False)
            review.customer = customer
            review.product = product
            review.save()
            messages.success(request, "Your review has been submitted successfully!")
    return redirect('shop:product_detail', pk=product.id)


def cart_detail_view(request):
    """
    Shopping Cart view: see items, adjust quantities, see total price.
    """
    cart = Cart(request)
    return render(request, 'shop/cart.html', {'cart': cart})


def cart_add_view(request, product_id):
    """
    Add product (and optional variant) to the cart.
    """
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity <= 0:
        quantity = 1

    variant_input = request.POST.get('variant_id') or request.POST.get('variant')
    variant = None
    if variant_input:
        if str(variant_input).isdigit():
            variant = ProductVariant.objects.filter(id=int(variant_input), product=product).first()
        if not variant:
            variant = ProductVariant.objects.filter(name=variant_input, product=product).first()
    if not variant:
        variant = product.default_variant

    # Check stock availability
    is_in_stock = False
    if variant:
        is_in_stock = bool(variant.is_available and variant.quantity > 0)
    else:
        is_in_stock = bool(product.in_stock)

    if not is_in_stock:
        out_of_stock_msg = "Product is not available. Contact us for pre order."

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'out_of_stock': True,
                'message': out_of_stock_msg,
                'cart_count': len(cart),
                'cart_total': str(cart.get_total_price()),
                'contact_url': '/#contact',
            })

        messages.warning(request, out_of_stock_msg)
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('shop:product_detail', pk=product.pk)

    cart.add(product=product, quantity=quantity, variant=variant)
    item_title = f"{product.name} ({variant.name})" if variant else product.name

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'"{item_title}" added to cart successfully!',
            'cart_count': len(cart),
            'cart_total': str(cart.get_total_price()),
            'cart_url': reverse('shop:cart_detail'),
        })

    messages.success(request, f'"{item_title}" added to cart successfully!')

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('shop:cart_detail')


def cart_update_view(request, product_id):
    """
    Update item quantity in cart. Supports item_key for variants.
    """
    cart = Cart(request)
    action = request.POST.get('action')
    item_key = request.POST.get('item_key') or str(product_id)

    if action == 'increase':
        # Find item in cart to get product & variant
        item_data = cart.cart.get(item_key)
        if item_data:
            prod = Product.objects.get(id=item_data['product_id'])
            var = ProductVariant.objects.filter(id=item_data['variant_id']).first() if item_data.get('variant_id') else None
            cart.add(product=prod, quantity=1, variant=var)
    elif action == 'decrease':
        cart.decrease(item_key)
    elif action == 'set':
        try:
            qty = int(request.POST.get('quantity', 1))
            item_data = cart.cart.get(item_key)
            if item_data and qty > 0:
                prod = Product.objects.get(id=item_data['product_id'])
                var = ProductVariant.objects.filter(id=item_data['variant_id']).first() if item_data.get('variant_id') else None
                cart.add(product=prod, quantity=qty, variant=var, override_quantity=True)
            else:
                cart.remove_by_key(item_key)
        except (ValueError, TypeError):
            pass

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item_data = cart.cart.get(item_key, {})
        item_qty = item_data.get('quantity', 0)
        item_subtotal = float(item_data.get('price', 0)) * item_qty

        return JsonResponse({
            'success': True,
            'item_quantity': item_qty,
            'item_subtotal': f"{item_subtotal:.2f}",
            'cart_count': len(cart),
            'cart_subtotal': f"{cart.get_subtotal():.2f}",
            'shipping_cost': f"{cart.get_shipping_cost():.2f}",
            'cart_total': f"{cart.get_grand_total():.2f}",
            'grand_total': f"{cart.get_grand_total():.2f}",
            'is_empty': len(cart) == 0,
        })

    return redirect('shop:cart_detail')


def cart_remove_view(request, product_id):
    """
    Remove item completely from cart.
    """
    cart = Cart(request)
    item_key = request.POST.get('item_key')
    if item_key:
        cart.remove_by_key(item_key)
    else:
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)

    messages.info(request, "Item was removed from your cart.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': len(cart),
            'cart_subtotal': f"{cart.get_subtotal():.2f}",
            'shipping_cost': f"{cart.get_shipping_cost():.2f}",
            'cart_total': f"{cart.get_grand_total():.2f}",
            'grand_total': f"{cart.get_grand_total():.2f}",
            'is_empty': len(cart) == 0,
        })

    return redirect('shop:cart_detail')


@require_POST
def cart_clear_view(request):
    """
    Remove all items from shopping cart.
    """
    cart = Cart(request)
    cart.clear()
    messages.info(request, "All items have been removed from your shopping cart.")
    return redirect('shop:cart_detail')


@login_required(login_url='shop:login')
def checkout_view(request):
    """
    Checkout view: requires customer login, autofills profile information,
    supports address book reuse/save, and handles Stripe payment or Cash on Delivery.
    """
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty. Please add items before checking out.")
        return redirect('shop:product_list')

    # Retrieve or create customer profile for authenticated user
    customer, _ = Customer.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'phone': '',
            'address': ''
        }
    )
    saved_addresses = customer.addresses.all()

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            street_address = form.cleaned_data['street_address'].strip()
            city = form.cleaned_data['city'].strip()
            postal_code = form.cleaned_data['postal_code'].strip()
            country = form.cleaned_data['country'].strip()
            payment_method = form.cleaned_data.get('payment_method', 'cod')
            saved_address_id = form.cleaned_data.get('saved_address_id')
            save_to_address_book = form.cleaned_data.get('save_to_address_book', False)

            # Recipient contact info from customer / user profile (non-editable in checkout)
            name = customer.get_full_name() or request.user.get_full_name() or customer.name or request.user.username
            phone = customer.phone or ''
            email = request.user.email or customer.email or ''

            formatted_address = f"{street_address}, {city} {postal_code}, {country}".strip()

            delivery_address_obj = None
            if saved_address_id:
                delivery_address_obj = customer.addresses.filter(id=saved_address_id).first()

            # If user wants to save to address book (enforce maximum 3 address limit)
            if save_to_address_book and street_address and customer.addresses.count() < 3:
                existing_addr = customer.addresses.filter(
                    address_line__iexact=street_address,
                    city__iexact=city
                ).first()
                if existing_addr:
                    delivery_address_obj = existing_addr
                elif not delivery_address_obj:
                    new_addr = Address.objects.create(
                        address_line=street_address,
                        city=city,
                        postal_code=postal_code,
                        country=country,
                        is_default=not customer.addresses.exists()
                    )
                    customer.addresses.add(new_addr)
                    delivery_address_obj = new_addr
            elif not delivery_address_obj and street_address:
                delivery_address_obj = Address.objects.create(
                    address_line=street_address,
                    city=city,
                    postal_code=postal_code,
                    country=country,
                    is_default=False
                )

            # Update customer default address text
            customer.address = formatted_address
            customer.save()

            order_number = f"DJ-{uuid.uuid4().hex[:8].upper()}"

            # Create Order entries
            created_orders = []
            for item in cart:
                product = item['product']
                variant = item.get('variant')
                quantity = item['quantity']
                item_total = item['total_price']

                order = Order.objects.create(
                    order_number=order_number,
                    customer=customer,
                    product=product,
                    variant=variant,
                    quantity=quantity,
                    total_price=item_total,
                    status='Pending',
                    payment_method='Stripe' if payment_method == 'stripe' else 'Cash on Delivery',
                    delivery_address=delivery_address_obj
                )
                created_orders.append(order)

                # Deduct stock
                if variant:
                    if variant.quantity >= quantity:
                        variant.quantity -= quantity
                    else:
                        variant.quantity = 0
                    variant.save()

            # Handle Payment Strategy
            if payment_method == 'stripe':
                line_items = []
                for item in cart:
                    line_items.append({
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"{item['product'].name} ({item['variant'].name})" if item.get('variant') else item['product'].name,
                            },
                            'unit_amount': int(item['price'] * 100),
                        },
                        'quantity': item['quantity'],
                    })

                success_url = request.build_absolute_uri(f"/stripe/success/?order_number={order_number}&session_id={{CHECKOUT_SESSION_ID}}")
                cancel_url = request.build_absolute_uri(f"/stripe/cancel/?order_number={order_number}")

                try:
                    stripe_session = stripe.checkout.Session.create(
                        payment_method_types=['card'],
                        line_items=line_items,
                        mode='payment',
                        success_url=success_url,
                        cancel_url=cancel_url,
                        customer_email=customer.email or None,
                        client_reference_id=order_number,
                    )
                    return redirect(stripe_session.url, code=303)
                except Exception as e:
                    messages.error(request, f"Stripe connection notice: {str(e)}. Proceeding with Cash on Delivery mode.")
                    for o in created_orders:
                        o.payment_method = 'Cash on Delivery'
                        o.save()
                    cart.clear()
                    return redirect('shop:order_success', order_number=order_number)
            else:
                # Cash on Delivery
                cart.clear()
                messages.success(request, "Order Placed Successfully!")
                return redirect('shop:order_success', order_number=order_number)
    else:
        # Determine default address details and ID
        default_addr = saved_addresses.filter(is_default=True).first() or saved_addresses.first()
        selected_address_id = ''
        initial_street = ''
        initial_city = ''
        initial_postal = ''
        initial_country = 'Bangladesh'

        if default_addr:
            selected_address_id = str(default_addr.id)
            initial_street = default_addr.address_line
            initial_city = default_addr.city
            initial_postal = default_addr.postal_code
            initial_country = default_addr.country or 'Bangladesh'
        elif customer.address:
            initial_street = customer.address

        initial_data = {
            'first_name': customer.first_name or request.user.first_name or '',
            'last_name': customer.last_name or request.user.last_name or '',
            'phone': customer.phone or '',
            'email': request.user.email or customer.email or '',
            'street_address': initial_street,
            'city': initial_city,
            'postal_code': initial_postal,
            'country': initial_country,
            'saved_address_id': selected_address_id,
            'save_to_address_book': True,
        }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart': cart,
        'saved_addresses': saved_addresses,
        'customer': customer,
    }
    return render(request, 'shop/checkout.html', context)


def stripe_success_view(request):
    """
    Handle successful Stripe Checkout session return.
    """
    order_number = request.GET.get('order_number')
    session_id = request.GET.get('session_id')

    orders = Order.objects.filter(order_number=order_number)
    if orders.exists():
        total_amount = sum(o.total_price for o in orders)
        # Update order status to Paid
        orders.update(status='Paid', stripe_payment_intent_id=session_id)

        # Record Payment entity
        Payment.objects.create(
            order=orders.first(),
            transaction_id=session_id or f"TXN-{uuid.uuid4().hex[:8].upper()}",
            amount=total_amount,
            method='Stripe',
            status='succeeded',
            raw_response={'session_id': session_id, 'order_number': order_number}
        )

        cart = Cart(request)
        cart.clear()

        messages.success(request, "Payment successful! Your order has been placed and paid via Stripe.")
        return redirect('shop:order_success', order_number=order_number)

    messages.error(request, "Order not found.")
    return redirect('shop:home')


def stripe_cancel_view(request):
    """
    Handle cancelled Stripe Checkout.
    """
    order_number = request.GET.get('order_number')
    if order_number:
        # Mark orders as cancelled
        Order.objects.filter(order_number=order_number, status='Pending').update(status='Cancelled')
    messages.warning(request, "Payment was cancelled. You can try checking out again anytime.")
    return redirect('shop:cart_detail')


def order_success_view(request, order_number):
    """
    Order success confirmation page showing "Order Placed Successfully!"
    """
    orders = Order.objects.filter(order_number=order_number).select_related('product', 'variant')
    if not orders.exists():
        messages.error(request, "Order not found.")
        return redirect('shop:home')

    first_order = orders.first()
    customer = first_order.customer
    subtotal = sum(order.total_price for order in orders)
    delivery_charge = 100
    vat_amount = 0
    grand_total = subtotal + delivery_charge

    # Customer payment breakdown
    if first_order.status in ['Paid', 'Delivered']:
        amount_paid = grand_total
        amount_due = 0
    else:
        amount_paid = 0
        amount_due = grand_total

    context = {
        'order_number': order_number,
        'orders': orders,
        'customer': customer,
        'first_order': first_order,
        'subtotal': subtotal,
        'delivery_charge': delivery_charge,
        'vat_amount': vat_amount,
        'grand_total': grand_total,
        'total_amount': grand_total,
        'amount_paid': amount_paid,
        'amount_due': amount_due,
        'order_date': first_order.order_date,
        'status': first_order.status,
        'payment_method': first_order.payment_method,
        'delivery_address': first_order.delivery_address,
    }
    return render(request, 'shop/order_success.html', context)


def order_lookup_view(request):
    """
    Track order page has been replaced by User Dashboard orders view.
    """
    if request.user.is_authenticated:
        return redirect('shop:dashboard')
    return redirect('shop:home')


# ==========================================
# Authentication & User Management Views
# ==========================================

def register_view(request):
    """
    Customer registration view with automatic Customer profile creation.
    """
    if request.user.is_authenticated:
        return redirect('shop:dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()

            full_name = f"{user.first_name} {user.last_name}".strip()

            # Create Customer profile linked to User
            Customer.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                name=full_name,
                phone=form.cleaned_data['phone'],
                email=user.email,
                address=''
            )

            # Log user in
            login(request, user)
            messages.success(request, f"Welcome to djCommerce, {user.first_name}! Your account has been created.")
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url or 'shop:dashboard')
    else:
        form = UserRegisterForm()

    return render(request, 'shop/register.html', {'form': form})


def login_view(request):
    """
    Customer login view using Email Address & Password.
    """
    if request.user.is_authenticated:
        next_url = request.GET.get('next') or request.POST.get('next')
        return redirect(next_url or 'shop:dashboard')

    if request.method == 'POST':
        form = EmailLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url or 'shop:dashboard')
    else:
        form = EmailLoginForm()

    return render(request, 'shop/login.html', {'form': form})


def logout_view(request):
    """
    Logout view.
    """
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('shop:home')


# ==========================================
# Customer Dashboard Views
# ==========================================

@login_required
def dashboard_view(request):
    """
    Customer personal portal showing stats, recent orders, saved addresses, and profile.
    """
    customer, _ = Customer.objects.get_or_create(
        user=request.user,
        defaults={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'phone': '',
            'address': ''
        }
    )

    all_order_items = Order.objects.filter(customer=customer).select_related('product', 'variant').order_by('-order_date')
    saved_addresses = customer.addresses.all().order_by('-is_default', '-id')

    # Aggregate multiple items in the same order into a single row per order_number
    seen_order_numbers = []
    grouped_orders = []
    for item in all_order_items:
        if item.order_number not in seen_order_numbers:
            seen_order_numbers.append(item.order_number)
            # Collect all items for this order number
            order_items = [i for i in all_order_items if i.order_number == item.order_number]
            total_for_order = sum(i.total_price for i in order_items)
            total_qty = sum(i.quantity for i in order_items)
            item_count = len(order_items)
            grouped_orders.append({
                'order_number': item.order_number,
                'order_date': item.order_date,
                'product': item.product,
                'variant': item.variant,
                'quantity': total_qty,
                'total_price': total_for_order,
                'status': item.status,
                'item_count': item_count,
                'items': order_items,
            })

    orders = grouped_orders
    total_orders = len(grouped_orders)
    completed_orders_count = sum(1 for o in grouped_orders if o['status'] in ['Delivered', 'Paid', 'Completed'])
    total_spent = sum(o['total_price'] for o in grouped_orders if o['status'] in ['Paid', 'Delivered', 'Processing'])
    profile_form = CustomerProfileForm(instance=customer)
    address_form = AddressForm()

    # User initials for fallback avatar badge
    first_char = (customer.first_name or request.user.first_name or request.user.username or 'U')[0].upper()
    last_char = (customer.last_name or request.user.last_name or '')
    user_initials = f"{first_char}{last_char[0].upper()}" if last_char else first_char

    context = {
        'customer': customer,
        'orders': orders,
        'saved_addresses': saved_addresses,
        'total_orders': total_orders,
        'completed_orders_count': completed_orders_count,
        'total_spent': total_spent,
        'profile_form': profile_form,
        'address_form': address_form,
        'user_initials': user_initials,
    }
    return render(request, 'shop/dashboard.html', context)


@login_required
def profile_edit_view(request):
    """
    Update customer profile details: First Name, Last Name, Email, Mobile, and Avatar.
    """
    customer = get_object_or_404(Customer, user=request.user)
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            cust = form.save(commit=False)
            new_email = form.cleaned_data.get('email', '').strip()
            if new_email:
                cust.email = new_email
                request.user.email = new_email
            first_name = form.cleaned_data.get('first_name', '').strip()
            last_name = form.cleaned_data.get('last_name', '').strip()
            cust.first_name = first_name
            cust.last_name = last_name
            cust.name = f"{first_name} {last_name}".strip()
            cust.save()

            # Sync with Django User
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()
            messages.success(request, "Your profile has been updated successfully!")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    return redirect('/dashboard/#account-details')


@login_required
def password_change_view(request):
    """
    Handle customer password change from dashboard.
    """
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_new_password = request.POST.get('confirm_new_password', '')

        if not current_password:
            messages.error(request, "Please enter your current password.")
            return redirect('/dashboard/#change-password')

        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect. Please try again.")
            return redirect('/dashboard/#change-password')

        if len(new_password) < 6:
            messages.error(request, "New password must be at least 6 characters long.")
            return redirect('/dashboard/#change-password')

        if new_password != confirm_new_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('/dashboard/#change-password')

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Your password has been changed successfully!")
        return redirect('/dashboard/#change-password')

    return redirect('shop:dashboard')


@login_required
def address_create_view(request):
    """
    Add a new address to customer's address book (max 3 allowed).
    """
    customer = get_object_or_404(Customer, user=request.user)
    if customer.addresses.count() >= 3:
        messages.error(request, "You cannot save more than 3 addresses in your Address Book. Please edit or delete an existing address.")
        return redirect('/dashboard/#addresses')

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save()
            if address.is_default:
                customer.addresses.update(is_default=False)
            customer.addresses.add(address)
            messages.success(request, "Delivery address added successfully!")
    return redirect('/dashboard/#addresses')


@login_required
def address_edit_view(request, address_id):
    """
    Update an existing address in customer's address book.
    """
    customer = get_object_or_404(Customer, user=request.user)
    address = get_object_or_404(Address, id=address_id, customers=customer)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            addr = form.save()
            if addr.is_default:
                customer.addresses.exclude(id=addr.id).update(is_default=False)
            messages.success(request, "Delivery address updated successfully!")
    return redirect('/dashboard/#addresses')


@login_required
def address_delete_view(request, address_id):
    """
    Remove an address from customer's address book.
    Supports both POST (from modal) and GET requests.
    """
    customer = get_object_or_404(Customer, user=request.user)
    try:
        address = customer.addresses.get(id=address_id)
    except Address.DoesNotExist:
        address = Address.objects.filter(id=address_id).first()

    if address:
        was_default = address.is_default
        customer.addresses.remove(address)
        
        # If not referenced by other customers and not used in previous orders, delete row
        if not address.customers.exists() and not address.orders.exists():
            address.delete()

        # If deleted address was default, set the next saved address as default
        if was_default:
            first_addr = customer.addresses.first()
            if first_addr:
                first_addr.is_default = True
                first_addr.save()

        # If no addresses remain, clear legacy customer.address
        if customer.addresses.count() == 0:
            customer.address = ''
            customer.save()

        messages.success(request, "Delivery address deleted successfully.")
    else:
        messages.error(request, "Address not found in your address book.")

    return redirect('/dashboard/#addresses')


@login_required
def address_set_default_view(request, address_id):
    """
    Set an existing address as the default delivery address.
    """
    customer = get_object_or_404(Customer, user=request.user)
    address = get_object_or_404(Address, id=address_id, customers=customer)
    customer.addresses.update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, f"Default delivery address updated to {address.city}.")
    return redirect('/dashboard/#addresses')


@login_required
def order_detail_view(request, order_number):
    """
    View complete order invoice and delivery status from dashboard.
    """
    customer = get_object_or_404(Customer, user=request.user)
    orders = Order.objects.filter(order_number=order_number, customer=customer)
    if not orders.exists():
        messages.error(request, "Order not found.")
        return redirect('shop:dashboard')

    first_order = orders.first()
    subtotal = sum(o.total_price for o in orders)
    delivery_charge = 100
    vat_amount = 0
    grand_total = subtotal + delivery_charge

    # Customer payment breakdown
    if first_order.status in ['Paid', 'Delivered']:
        amount_paid = grand_total
        amount_due = 0
    else:
        amount_paid = 0
        amount_due = grand_total

    context = {
        'order_number': order_number,
        'orders': orders,
        'first_order': first_order,
        'customer': customer,
        'subtotal': subtotal,
        'delivery_charge': delivery_charge,
        'vat_amount': vat_amount,
        'grand_total': grand_total,
        'total_amount': grand_total,
        'amount_paid': amount_paid,
        'amount_due': amount_due,
        'order_date': first_order.order_date,
        'status': first_order.status,
        'payment_method': first_order.payment_method,
        'delivery_address': first_order.delivery_address,
    }
    return render(request, 'shop/order_detail.html', context)


def order_invoice_view(request, order_number):
    """
    Render a clean, print-ready invoice page for a given order number.
    Auto-triggers browser print dialog on load. Accessible from dashboard & order success.
    """
    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            orders = Order.objects.filter(order_number=order_number, customer=customer)
        except Customer.DoesNotExist:
            orders = Order.objects.filter(order_number=order_number)
    else:
        orders = Order.objects.filter(order_number=order_number)

    if not orders.exists():
        messages.error(request, "Order not found.")
        return redirect('shop:home')

    first_order = orders.first()
    customer = first_order.customer
    subtotal = sum(o.total_price for o in orders)
    delivery_charge = 100
    vat_amount = 0
    grand_total = subtotal + delivery_charge

    if first_order.status in ['Paid', 'Delivered']:
        amount_paid = grand_total
        amount_due = 0
    else:
        amount_paid = 0
        amount_due = grand_total

    context = {
        'order_number': order_number,
        'orders': orders,
        'first_order': first_order,
        'customer': customer,
        'subtotal': subtotal,
        'delivery_charge': delivery_charge,
        'vat_amount': vat_amount,
        'grand_total': grand_total,
        'amount_paid': amount_paid,
        'amount_due': amount_due,
        'order_date': first_order.order_date,
        'status': first_order.status,
        'payment_method': first_order.payment_method,
        'delivery_address': first_order.delivery_address,
    }
    return render(request, 'shop/order_invoice.html', context)


def contact_submit_view(request):
    """
    Handle contact form submissions from footer with dual AJAX / standard POST support.
    """
    if request.method == 'POST':

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            messages.success(request, f"Thank you, {name}! Your message has been sent successfully. Our support team will get in touch with you shortly.")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': f"Thank you, {name}! Your message has been sent successfully. We will reply to {email} as soon as possible."
                })
        else:
            messages.error(request, "Please fill in all required fields (Name, Email, and Message).")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': "Please fill in all required fields (Name, Email, and Message)."
                }, status=400)

        redirect_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
        if '#' not in redirect_url:
            redirect_url = f"{redirect_url}#contact"
        return redirect(redirect_url)

    return redirect('shop:home')



