from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Q
from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Category, SubCategory, Brand, Product, ProductVariant, ProductImage,
    Customer, Address, Order, Payment, Review,
    FeaturedProduct, NewProduct, OfferProduct
)

# ─────────────────────────────────────────────
# Inline: Customer profile inside User admin
# ─────────────────────────────────────────────

class CustomerProfileInline(admin.StackedInline):
    model = Customer
    can_delete = False
    verbose_name = 'Other info'
    verbose_name_plural = 'Other info'
    fk_name = 'user'
    fields = ['phone', 'profile_image']
    extra = 0


# ─────────────────────────────────────────────
# Enhanced User Admin
# ─────────────────────────────────────────────

class CustomUserAdmin(BaseUserAdmin):
    inlines = [CustomerProfileInline]

    list_display = ['get_email', 'first_name', 'last_name', 'is_admin', 'is_active']
    list_display_links = ['get_email']
    list_filter = ['is_superuser', 'is_staff', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'username']
    ordering = ['email']

    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }

    @admin.display(description='Email Address', ordering='email')
    def get_email(self, obj):
        return obj.email if obj.email else f"({obj.username})"

    @admin.display(boolean=True, description='Is Admin', ordering='is_staff')
    def is_admin(self, obj):
        return obj.is_staff or obj.is_superuser

    # Add saved addresses, order + payment sections as readonly HTML fields
    readonly_fields = BaseUserAdmin.readonly_fields + ('saved_addresses', 'order_history', 'payment_history')

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:  # only on existing user edit page
            fieldsets = list(fieldsets) + [
                ('📍 Saved Addresses', {'fields': ('saved_addresses',)}),
                ('📦 Order History', {'fields': ('order_history',), 'classes': ('collapse',)}),
                ('💳 Payment History', {'fields': ('payment_history',), 'classes': ('collapse',)}),
            ]
        return fieldsets

    def saved_addresses(self, obj):
        try:
            customer = obj.customer_profile
        except (Customer.DoesNotExist, AttributeError):
            return '—'

        # Fetch all addresses: both saved in address book and used in orders
        addresses = Address.objects.filter(
            Q(customers=customer) | Q(orders__customer=customer)
        ).distinct().order_by('-is_default', '-created_at')

        add_url = reverse('admin:shop_address_add')
        btn_add = f'<a href="{add_url}" target="_blank" style="display:inline-block;background:#2563eb;color:#fff;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:0.85em;font-weight:600;margin-bottom:10px;">+ Add New Address</a>'

        if not addresses.exists():
            legacy_note = f'<div style="margin-top:6px;color:#6b7280;font-size:0.9em;"><strong>Profile Address:</strong> {customer.address}</div>' if customer.address else ''
            return mark_safe(f'{btn_add}<p style="color:#888;margin-top:4px;">No structured addresses found for this user.</p>{legacy_note}')

        rows = ''
        for addr in addresses:
            is_primary_val = '<span style="font-weight:600;color:#10b981;">Yes</span>' if addr.is_default else '<span style="color:#9ca3af;">No</span>'
            edit_url = reverse('admin:shop_address_change', args=[addr.id])
            rows += f"""
            <tr style="border-bottom:1px solid #eee;">
                <td style="padding:10px 12px;font-weight:500;">{addr.address_line}</td>
                <td style="padding:10px 12px;">{addr.city}</td>
                <td style="padding:10px 12px;">{addr.postal_code or '—'}</td>
                <td style="padding:10px 12px;">{addr.country}</td>
                <td style="padding:10px 12px;">{is_primary_val}</td>
                <td style="padding:10px 12px;"><a href="{edit_url}" target="_blank" style="color:#2563eb;font-weight:600;text-decoration:none;">✏️ Edit</a></td>
            </tr>"""

        html = f"""
        <div style="margin-bottom:6px;">{btn_add}</div>
        <table style="width:100%;border-collapse:collapse;font-size:0.9em;margin-top:4px;border:1px solid #e5e7eb;background:#fff;">
            <thead>
                <tr style="background:#f9fafb;text-align:left;border-bottom:2px solid #e5e7eb;">
                    <th style="padding:8px 12px;font-weight:600;">Street Address / Road / House</th>
                    <th style="padding:8px 12px;font-weight:600;">City / Division</th>
                    <th style="padding:8px 12px;font-weight:600;">Postal Code</th>
                    <th style="padding:8px 12px;font-weight:600;">Country</th>
                    <th style="padding:8px 12px;font-weight:600;">Is Primary</th>
                    <th style="padding:8px 12px;font-weight:600;">Action</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """
        return mark_safe(html)

    saved_addresses.short_description = 'Saved Addresses'

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
            payment_url = reverse('admin:shop_payment_change', args=[p.id])
            order_url = reverse('admin:shop_order_changelist') + f'?q={p.order.order_number}'
            rows += f"""
            <tr style="border-bottom:1px solid #eee;">
                <td style="padding:8px 10px;"><a href="{payment_url}" target="_blank"><code>{p.transaction_id}</code></a></td>
                <td style="padding:8px 10px;">{p.created_at.strftime('%d %b %Y, %I:%M %p')}</td>
                <td style="padding:8px 10px;"><a href="{order_url}" target="_blank"><code>{p.order.order_number}</code></a></td>
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

class ProductVariantInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        default_count = 0
        active_count = 0
        for form in self.forms:
            if not form.is_valid():
                continue
            if self.can_delete and self._should_delete_form(form):
                continue
            cleaned = form.cleaned_data
            if not cleaned or cleaned.get('DELETE'):
                continue
            
            active_count += 1
            if cleaned.get('is_default'):
                default_count += 1

        if default_count > 1:
            raise ValidationError("Only ONE variant can be selected as default for a product. Please uncheck extra defaults.")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    formset = ProductVariantInlineFormSet
    extra = 1
    fields = ['name', 'slug', 'price', 'regular_price', 'quantity', 'is_available', 'is_default']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    verbose_name = "Additional Image"
    verbose_name_plural = "More Images (Gallery)"
    fields = ['product_image', 'alt_text']


class SubCategoryInline(admin.TabularInline):
    model = Category
    extra = 1
    verbose_name = "Subcategory"
    verbose_name_plural = "Subcategories"
    fields = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}
    fk_name = 'parent'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'subcategory_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    exclude = ['parent']
    inlines = [SubCategoryInline]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(parent__isnull=True)

    def subcategory_count(self, obj):
        return obj.subcategories.count()
    subcategory_count.short_description = "Subcategories Count"


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug', 'icon', 'created_at']
    list_filter = ['parent']
    search_fields = ['name', 'parent__name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['parent', 'name', 'slug', 'icon', 'description']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(parent__isnull=False)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = Category.objects.filter(parent__isnull=True)
            kwargs["required"] = True
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'get_default_price', 'get_regular_price', 'get_stock', 'variant_count', 'is_featured', 'created_at']
    list_filter = ['category', 'brand', 'is_featured', 'created_at']
    search_fields = ['name', 'brand', 'description', 'short_description']
    list_editable = ['is_featured']
    inlines = [ProductVariantInline, ProductImageInline]
    list_per_page = 20

    class Media:
        css = {
            'all': (
                'css/admin_custom.css',
            )
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.8.3/tinymce.min.js',
            'js/admin_tinymce.js',
        )

    @admin.display(description='Price (৳)')
    def get_default_price(self, obj):
        return f"৳ {obj.price:,.0f}" if obj.price else "—"

    @admin.display(description='Regular Price (৳)')
    def get_regular_price(self, obj):
        return f"৳ {obj.regular_price:,.0f}" if obj.regular_price else "—"

    @admin.display(description='Stock')
    def get_stock(self, obj):
        return obj.quantity

    @admin.display(description='Variants')
    def variant_count(self, obj):
        count = obj.variants.count()
        return f"{count} variants" if count else "No variants"

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.save()
        formset.save_m2m()

        # Enforce single default variant consistency
        if formset.model == ProductVariant and form.instance.pk:
            active_variants = ProductVariant.objects.filter(product=form.instance)
            default_variants = active_variants.filter(is_default=True)
            if default_variants.count() > 1:
                first_default = default_variants.first()
                active_variants.exclude(pk=first_default.pk).update(is_default=False)
            elif default_variants.count() == 0 and active_variants.exists():
                first_var = active_variants.first()
                first_var.is_default = True
                first_var.save(update_fields=['is_default'])


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'price', 'regular_price', 'quantity', 'is_available', 'is_default', 'created_at']
    list_filter = ['is_available', 'is_default', 'product']
    search_fields = ['name', 'slug', 'product__name']
    list_editable = ['price', 'regular_price', 'quantity', 'is_available', 'is_default']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 25

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_default and obj.product_id:
            ProductVariant.objects.filter(product_id=obj.product_id).exclude(pk=obj.pk).update(is_default=False)


class CustomerAddressInline(admin.TabularInline):
    model = Customer.addresses.through
    extra = 1
    verbose_name = "Linked Customer"
    verbose_name_plural = "Linked Customers"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['address_line', 'city', 'country', 'postal_code', 'is_default', 'get_customers', 'created_at']
    list_filter = ['country', 'city', 'is_default']
    search_fields = ['address_line', 'city', 'country', 'postal_code', 'customers__name', 'customers__phone', 'customers__user__username']
    inlines = [CustomerAddressInline]

    def get_customers(self, obj):
        customers = [c.name or (c.user.username if c.user else 'Customer') for c in obj.customers.all()]
        return ", ".join(customers) if customers else "—"
    get_customers.short_description = "Assigned Customer(s)"


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


@admin.register(FeaturedProduct)
class FeaturedProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'get_brand', 'get_category', 'get_price', 'order', 'created_at']
    list_editable = ['order']
    search_fields = ['product__name', 'product__brand']
    autocomplete_fields = ['product']
    ordering = ['order', '-created_at']

    @admin.display(description='Brand')
    def get_brand(self, obj):
        return obj.product.brand or '—'

    @admin.display(description='Category')
    def get_category(self, obj):
        return obj.product.category.name if obj.product.category else '—'

    @admin.display(description='Price (৳)')
    def get_price(self, obj):
        return f"৳ {obj.product.price:,.0f}" if obj.product.price else "—"


@admin.register(NewProduct)
class NewProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'get_brand', 'get_category', 'get_price', 'order', 'created_at']
    list_editable = ['order']
    search_fields = ['product__name', 'product__brand']
    autocomplete_fields = ['product']
    ordering = ['order', '-created_at']

    @admin.display(description='Brand')
    def get_brand(self, obj):
        return obj.product.brand or '—'

    @admin.display(description='Category')
    def get_category(self, obj):
        return obj.product.category.name if obj.product.category else '—'

    @admin.display(description='Price (৳)')
    def get_price(self, obj):
        return f"৳ {obj.product.price:,.0f}" if obj.product.price else "—"


@admin.register(OfferProduct)
class OfferProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'get_brand', 'get_category', 'get_price', 'order', 'created_at']
    list_editable = ['order']
    search_fields = ['product__name', 'product__brand']
    autocomplete_fields = ['product']
    ordering = ['order', '-created_at']

    @admin.display(description='Brand')
    def get_brand(self, obj):
        return obj.product.brand or '—'

    @admin.display(description='Category')
    def get_category(self, obj):
        return obj.product.category.name if obj.product.category else '—'

    @admin.display(description='Price (৳)')
    def get_price(self, obj):
        return f"৳ {obj.product.price:,.0f}" if obj.product.price else "—"

