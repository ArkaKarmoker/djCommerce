from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

# Create your models here.


class TimeStampMixin(models.Model):
    """
    Abstract timestamp mixin shared across all domain models.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Address(TimeStampMixin):
    """
    Structured delivery and billing address.
    """
    country = models.CharField(max_length=255, default='Bangladesh')
    city = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    address_line = models.CharField(max_length=500)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.address_line}, {self.city}, {self.country}"


class Category(TimeStampMixin):
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-grid', help_text="Bootstrap icon class")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            if self.parent:
                self.slug = slugify(f"{self.parent.slug}-{self.name}")
            else:
                self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def is_parent(self):
        return self.parent is None


class Product(TimeStampMixin):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    regular_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    quantity = models.PositiveIntegerField(default=10)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def in_stock(self):
        return self.quantity > 0

    @property
    def discount_amount(self):
        if self.regular_price and self.regular_price > self.price:
            return self.regular_price - self.price
        return 0

    @property
    def discount_percent(self):
        if self.regular_price and self.regular_price > self.price:
            pct = ((self.regular_price - self.price) / self.regular_price) * 100
            return int(round(pct))
        return 0

    @property
    def badge_info(self):
        """
        Returns dictionary for card badge:
        - Featured: For handpicked flagship products
        - New: For newly arrived products
        - Hot Deals: For products with active discounts
        """
        if hasattr(self, '_custom_badge'):
            return self._custom_badge
        if self.is_featured:
            return {
                'label': 'Featured',
                'icon': 'bi bi-star-fill text-warning',
                'css_class': 'featured',
            }
        elif self.discount_amount and self.discount_amount > 0:
            return {
                'label': 'Hot Deals',
                'icon': 'bi bi-lightning-fill text-warning',
                'css_class': 'hot-deal',
            }
        return None


class ProductVariant(TimeStampMixin):
    """
    Product variant representing specific phone color, storage, and stock.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=255)
    stock = models.PositiveIntegerField(default=5)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.product.name} - {self.name} ({self.color})"


class ProductImage(TimeStampMixin):
    """
    Product gallery images.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    product_image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.product.name} Image"


class Customer(TimeStampMixin):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='customer_profile'
    )
    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')
    name = models.CharField(max_length=150, blank=True, default='')
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, default='')
    email = models.EmailField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile/', blank=True, null=True)
    addresses = models.ManyToManyField(Address, blank=True, related_name='customers')

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.first_name or self.last_name:
            self.name = f"{self.first_name} {self.last_name}".strip()
        elif self.name and not self.first_name and not self.last_name:
            parts = self.name.split(' ', 1)
            self.first_name = parts[0]
            self.last_name = parts[1] if len(parts) > 1 else ''
        super().save(*args, **kwargs)

    def get_full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.name

    def __str__(self):
        return f"{self.name or self.first_name} ({self.phone})"


class Order(TimeStampMixin):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=32, blank=True, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=50, default='Cash on Delivery')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    delivery_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"Order #{self.order_number or self.id} - {self.product.name} ({self.customer.name})"


class Payment(TimeStampMixin):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, default='Stripe')
    status = models.CharField(max_length=50, default='pending')
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Payment {self.transaction_id} for Order #{self.order.order_number}"


class Review(TimeStampMixin):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.customer.name} on {self.product.name}"


