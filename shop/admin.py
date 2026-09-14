from django.contrib import admin
from .models import (
    Category, Product, ProductVariant, ProductImage,
    Customer, Address, Order, Payment, Review
)

# Register your models here.


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'price', 'quantity', 'is_featured', 'created_at']
    list_filter = ['category', 'brand', 'is_featured', 'created_at']
    search_fields = ['name', 'brand', 'description', 'short_description']
    list_editable = ['price', 'quantity', 'is_featured']
    inlines = [ProductVariantInline, ProductImageInline]
    list_per_page = 20


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'color', 'stock', 'price_adjustment']
    list_filter = ['product', 'color']
    search_fields = ['name', 'color', 'product__name']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'created_at']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['address_line', 'city', 'country', 'postal_code', 'is_default']
    search_fields = ['address_line', 'city', 'country']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'first_name', 'last_name', 'phone', 'email', 'user', 'created_at']
    search_fields = ['name', 'first_name', 'last_name', 'phone', 'email', 'address']
    list_per_page = 20


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'product', 'variant', 'quantity', 'total_price', 'status', 'payment_method', 'order_date']
    list_filter = ['status', 'payment_method', 'order_date']
    search_fields = ['order_number', 'customer__name', 'customer__phone', 'product__name']
    list_editable = ['status']
    list_per_page = 20


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order', 'amount', 'method', 'status', 'created_at']
    list_filter = ['method', 'status']
    search_fields = ['transaction_id', 'order__order_number']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'customer', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'customer__name', 'comment']


