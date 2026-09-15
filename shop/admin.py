from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.urls import reverse
from .models import (
    Category, Product, ProductVariant, ProductImage,
    Customer, Address, Order, Payment, Review
)

# ─────────────────────────────────────────────
# Inline: Customer profile inside User admin
# ─────────────────────────────────────────────

class CustomerProfileInline(admin.StackedInline):
    model = Customer
    can_delete = False
    verbose_name_plural = 'Customer Profile'
    fk_name = 'user'
    fields = ['first_name', 'last_name', 'phone', 'email', 'address', 'profile_image']
    extra = 0


# ─────────────────────────────────────────────
# Enhanced User Admin
# ─────────────────────────────────────────────

class CustomUserAdmin(BaseUserAdmin):
    inlines = [CustomerProfileInline]

    # Add order + payment sections as readonly HTML fields
    readonly_fields = BaseUserAdmin.readonly_fields + ('order_history', 'payment_history')

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:  # only on existing user edit page
            fieldsets = list(fieldsets) + [
                ('📦 Order History', {'fields': ('order_history',), 'classes': ('collapse',)}),
                ('💳 Payment History', {'fields': ('payment_history',), 'classes': ('collapse',)}),
            ]
        return fieldsets

    def order_history(self, obj):
        try:
            customer = obj.customer_profile
        except (Customer.DoesNotExist, AttributeError):
            return '—'

        orders = (
            Order.objects
            .filter(customer=customer)
            .select_related('product', 'variant')
            .order_by('-order_date')
        )

        if not orders.exists():
            return mark_safe('<p style="color:#888;">No orders found.</p>')

        STATUS_COLORS = {
            'Pending':    '#f59e0b',
            'Paid':       '#10b981',
            'Processing': '#3b82f6',
            'Shipped':    '#6366f1',
            'Delivered':  '#22c55e',
            'Cancelled':  '#ef4444',
        }

        rows = ''
        seen = {}
        for o in orders:
            key = o.order_number
            if key not in seen:
                seen[key] = {'items': [], 'total': 0, 'status': o.status, 'date': o.order_date, 'method': o.payment_method}
            seen[key]['items'].append(f"{o.product.name} ×{o.quantity}")
            seen[key]['total'] += float(o.total_price)

        for num, data in seen.items():
            color = STATUS_COLORS.get(data['status'], '#888')
            items_html = '<br>'.join(data['items'])
            order_url = reverse('admin:shop_order_changelist') + f'?q={num}'
            rows += f"""
            <tr style="border-bottom:1px solid #eee;">
                <td style="padding:8px 10px;"><a href="{order_url}" target="_blank"><code>{num}</code></a></td>
                <td style="padding:8px 10px;">{data['date'].strftime('%d %b %Y, %I:%M %p')}</td>
                <td style="padding:8px 10px;font-size:0.9em;">{items_html}</td>
                <td style="padding:8px 10px;font-weight:600;">৳ {data['total']:,.0f}</td>
                <td style="padding:8px 10px;"><span style="background:{color};color:#fff;padding:3px 10px;border-radius:12px;font-size:0.8em;font-weight:500;">{data['status']}</span></td>
                <td style="padding:8px 10px;font-size:0.9em;">{data['method']}</td>
            </tr>"""

        html = f"""
        <table style="width:100%;border-collapse:collapse;font-size:0.9em;margin-top:5px;border:1px solid #e5e7eb;">
            <thead>
                <tr style="background:#f9fafb;text-align:left;border-bottom:2px solid #e5e7eb;">
                    <th style="padding:8px 10px;">Order #</th>
                    <th style="padding:8px 10px;">Date</th>
                    <th style="padding:8px 10px;">Products</th>
                    <th style="padding:8px 10px;">Total</th>
                    <th style="padding:8px 10px;">Status</th>
                    <th style="padding:8px 10px;">Payment Method</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """
        return mark_safe(html)

    order_history.short_description = 'Order History'

    def payment_history(self, obj):
        try:
            customer = obj.customer_profile
        except (Customer.DoesNotExist, AttributeError):
            return '—'

        payments = (
            Payment.objects
            .filter(order__customer=customer)
            .select_related('order')
            .order_by('-created_at')
        )

        if not payments.exists():
            return mark_safe('<p style="color:#888;">No payments found.</p>')

        STATUS_COLORS = {
            'succeeded': '#22c55e',
            'pending':   '#f59e0b',
            'failed':    '#ef4444',
            'refunded':  '#6366f1',
        }

        rows = ''
        for p in payments:
            color = STATUS_COLORS.get(p.status.lower(), '#888')
            rows += f"""
            <tr style="border-bottom:1px solid #eee;">
                <td style="padding:8px 10px;"><code>{p.transaction_id}</code></td>
                <td style="padding:8px 10px;">{p.created_at.strftime('%d %b %Y, %I:%M %p')}</td>
                <td style="padding:8px 10px;"><code>{p.order.order_number}</code></td>
                <td style="padding:8px 10px;font-weight:600;">৳ {float(p.amount):,.2f}</td>
                <td style="padding:8px 10px;">{p.method}</td>
                <td style="padding:8px 10px;"><span style="background:{color};color:#fff;padding:3px 10px;border-radius:12px;font-size:0.8em;font-weight:500;">{p.status}</span></td>
            </tr>"""

        html = f"""
        <table style="width:100%;border-collapse:collapse;font-size:0.9em;margin-top:5px;border:1px solid #e5e7eb;">
            <thead>
                <tr style="background:#f9fafb;text-align:left;border-bottom:2px solid #e5e7eb;">
                    <th style="padding:8px 10px;">Transaction ID</th>
                    <th style="padding:8px 10px;">Date</th>
                    <th style="padding:8px 10px;">Order #</th>
                    <th style="padding:8px 10px;">Amount</th>
                    <th style="padding:8px 10px;">Method</th>
                    <th style="padding:8px 10px;">Status</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """
        return mark_safe(html)

    payment_history.short_description = 'Payment History'


# Re-register User with our enhanced admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ─────────────────────────────────────────────
# Shop Models
# ─────────────────────────────────────────────

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
