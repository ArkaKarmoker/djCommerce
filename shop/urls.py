from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Catalog & Shopping
    path('', views.home_view, name='home'),
    path('products/', views.product_list_view, name='product_list'),
    path('products/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('products/<int:product_id>/review/', views.add_review_view, name='add_review'),
    path('api/search-suggest/', views.search_suggest_view, name='search_suggest'),

    # Cart
    path('cart/', views.cart_detail_view, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add_view, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update_view, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove_view, name='cart_remove'),
    path('cart/clear/', views.cart_clear_view, name='cart_clear'),

    # Checkout & Orders
    path('checkout/', views.checkout_view, name='checkout'),
    path('order-success/<str:order_number>/', views.order_success_view, name='order_success'),
    path('track-order/', views.order_lookup_view, name='order_lookup'),
    path('contact/submit/', views.contact_submit_view, name='contact_submit'),

    # Stripe Payment Callbacks
    path('stripe/success/', views.stripe_success_view, name='stripe_success'),
    path('stripe/cancel/', views.stripe_cancel_view, name='stripe_cancel'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Customer Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/profile/', views.profile_edit_view, name='profile_edit'),
    path('dashboard/password/', views.password_change_view, name='password_change'),
    path('dashboard/address/add/', views.address_create_view, name='address_create'),
    path('dashboard/address/edit/<int:address_id>/', views.address_edit_view, name='address_edit'),
    path('dashboard/address/delete/<int:address_id>/', views.address_delete_view, name='address_delete'),
    path('dashboard/address/default/<int:address_id>/', views.address_set_default_view, name='address_set_default'),
    path('dashboard/orders/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('dashboard/orders/<str:order_number>/invoice/', views.order_invoice_view, name='order_invoice'),
]
