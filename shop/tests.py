from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal

from .models import (
    Category, Product, ProductVariant, ProductImage,
    Customer, Address, Order, Payment, Review,
    FeaturedProduct, NewProduct, OfferProduct
)
from .cart import Cart
from .forms import CheckoutForm, UserRegisterForm

# Create your tests here.


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='Password123'
        )
        self.category = Category.objects.create(
            name='Flagships',
            slug='flagships',
            icon='bi-stars'
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Pixel 9 Pro',
            brand='Google',
            short_description='Tensor G4 powerhouse',
            description='Detailed specs here',
            is_featured=True
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            name='Pixel 9 Pro (Hazel / 256GB)',
            price=Decimal('999.00'),
            quantity=5,
            is_default=True
        )
        self.address = Address.objects.create(
            address_line='House 10, Road 5, Banani',
            city='Dhaka',
            country='Bangladesh',
            postal_code='1213',
            is_default=True
        )
        self.customer = Customer.objects.create(
            user=self.user,
            name='John Doe',
            phone='01711223344',
            address='Dhaka, Bangladesh',
            email='john@example.com'
        )
        self.customer.addresses.add(self.address)

    def test_category_creation(self):
        self.assertEqual(str(self.category), 'Flagships')
        self.assertEqual(self.category.slug, 'flagships')

    def test_product_and_variant_creation(self):
        self.assertEqual(str(self.product), 'Pixel 9 Pro')
        self.assertTrue(self.product.in_stock)
        self.assertEqual(self.variant.quantity, 5)
        self.assertIn('Hazel', str(self.variant))

    def test_address_and_customer_creation(self):
        self.assertEqual(str(self.customer), 'John Doe (01711223344)')
        self.assertEqual(self.customer.addresses.count(), 1)
        self.assertEqual(self.customer.addresses.first().city, 'Dhaka')

    def test_order_and_payment_creation(self):
        order = Order.objects.create(
            order_number='DJ-TEST1234',
            customer=self.customer,
            product=self.product,
            variant=self.variant,
            quantity=2,
            total_price=Decimal('2098.00'),
            status='Paid',
            payment_method='Stripe'
        )
        payment = Payment.objects.create(
            order=order,
            transaction_id='ch_test_123456789',
            amount=Decimal('2098.00'),
            method='Stripe',
            status='succeeded'
        )
        self.assertEqual(order.variant, self.variant)
        self.assertEqual(order.status, 'Paid')
        self.assertEqual(payment.amount, Decimal('2098.00'))

    def test_review_creation(self):
        review = Review.objects.create(
            customer=self.customer,
            product=self.product,
            rating=5,
            comment='Outstanding camera and clean software!'
        )
        self.assertEqual(review.rating, 5)
        self.assertIn('John Doe', str(review))


class CartTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Smartphones', slug='smartphones')
        self.product = Product.objects.create(
            category=self.category,
            name='iPhone 16',
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            name='iPhone 16 (Black 256GB)',
            price=Decimal('1000.00'),
            quantity=10,
            is_default=True
        )
        self.variant2 = ProductVariant.objects.create(
            product=self.product,
            name='iPhone 16 (Black 512GB)',
            price=Decimal('1100.00'),
            quantity=5,
            is_default=False
        )
        self.client = Client()

    def test_cart_operations_with_variants(self):
        session = self.client.session
        session.save()

        class DummyRequest:
            def __init__(self, s):
                self.session = s

        req = DummyRequest(session)
        cart = Cart(req)

        # Add product with default variant
        cart.add(self.product, quantity=1)
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart.get_total_price(), Decimal('1000.00'))

        # Add with second variant ($1100)
        cart.add(self.product, quantity=2, variant=self.variant2)
        self.assertEqual(len(cart), 3)
        self.assertEqual(cart.get_total_price(), Decimal('3200.00'))

        # Clear cart
        cart.clear()
        self.assertEqual(len(cart), 0)


class AuthAndDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Flagships', slug='flagships')
        self.product = Product.objects.create(
            category=self.category,
            name='Galaxy S25',
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            name='Standard',
            price=Decimal('1200.00'),
            quantity=10,
            is_default=True
        )

    def test_user_registration(self):
        reg_url = reverse('shop:register')
        post_data = {
            'first_name': 'New',
            'last_name': 'Customer',
            'username': 'newuser',
            'email': 'newuser@example.com',
            'phone': '01799887766',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!'
        }
        response = self.client.post(reg_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(Customer.objects.filter(phone='01799887766').exists())
        customer = Customer.objects.get(phone='01799887766')
        self.assertEqual(customer.first_name, 'New')
        self.assertEqual(customer.last_name, 'Customer')
        self.assertEqual(customer.name, 'New Customer')

    def test_login_and_dashboard_access(self):
        User.objects.create_user(username='tester', email='tester@example.com', password='TestPassword123')
        login_url = reverse('shop:login')
        response = self.client.post(login_url, {
            'email': 'tester@example.com',
            'password': 'TestPassword123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # Access dashboard
        dashboard_url = reverse('shop:dashboard')
        dash_response = self.client.get(dashboard_url)
        self.assertEqual(dash_response.status_code, 200)
        self.assertContains(dash_response, 'Dashboard')


class CheckoutAndFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Flagships', slug='flagships')
        self.product = Product.objects.create(
            category=self.category,
            name='iPhone 16 Pro Max',
            brand='Apple',
            short_description='Titanium powerhouse',
            description='Specs info',
            is_featured=True
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            name='256GB - Natural Titanium',
            price=Decimal('1199.00'),
            quantity=10,
            is_default=True
        )

    def test_home_and_product_list_views(self):
        home_resp = self.client.get(reverse('shop:home'))
        self.assertEqual(home_resp.status_code, 200)
        self.assertContains(home_resp, 'iPhone 16 Pro Max')

        list_resp = self.client.get(reverse('shop:product_list'))
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, 'iPhone 16 Pro Max')

    def test_checkout_cod_order_placement(self):
        user = User.objects.create_user(username='checkoutuser', email='arka@example.com', password='Password123')
        self.client.force_login(user)

        # 1. Add to cart
        self.client.post(reverse('shop:cart_add', args=[self.product.pk]), {'quantity': 1})

        # 2. Post checkout with COD
        checkout_url = reverse('shop:checkout')
        post_data = {
            'street_address': 'House 12, Road 4, Banani',
            'city': 'Dhaka',
            'postal_code': '1213',
            'country': 'Bangladesh',
            'payment_method': 'cod'
        }
        response = self.client.post(checkout_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Order Placed Successfully!')

        # Check DB
        order = Order.objects.filter(product=self.product).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_price, Decimal('1199.00'))
        self.assertEqual(order.payment_method, 'Cash on Delivery')
        self.assertEqual(order.status, 'Pending')


class VariantAndAdminTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Gadgets', slug='gadgets')
        self.product = Product.objects.create(
            category=self.category,
            name='Smart Watch Ultra',
            slug='smart-watch-ultra'
        )

    def test_single_default_variant_enforcement(self):
        var1 = ProductVariant.objects.create(
            product=self.product,
            name='Silver / 44mm',
            price=Decimal('299.00'),
            is_default=True
        )
        self.assertTrue(var1.is_default)
        self.assertEqual(self.product.price, Decimal('299.00'))

        # Create second variant as default
        var2 = ProductVariant.objects.create(
            product=self.product,
            name='Black / 49mm',
            price=Decimal('399.00'),
            is_default=True
        )
        var1.refresh_from_db()
        var2.refresh_from_db()
        self.assertFalse(var1.is_default)
        self.assertTrue(var2.is_default)
        self.assertEqual(self.product.price, Decimal('399.00'))

        # Switch default back to var1
        var1.is_default = True
        var1.save()
        var1.refresh_from_db()
        var2.refresh_from_db()
        self.assertTrue(var1.is_default)
        self.assertFalse(var2.is_default)

    def test_product_admin_change_view(self):
        admin_user = User.objects.create_superuser(username='adminuser', email='admin@example.com', password='AdminPassword123')
        self.client.force_login(admin_user)
        url = reverse('admin:shop_product_change', args=[self.product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class CuratedProductsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.prod_featured = Product.objects.create(category=self.category, name='Featured Watch')
        ProductVariant.objects.create(product=self.prod_featured, name='Default', price=Decimal('250.00'), is_default=True)

        self.prod_new = Product.objects.create(category=self.category, name='New Arrival Drone')
        ProductVariant.objects.create(product=self.prod_new, name='Default', price=Decimal('500.00'), is_default=True)

        self.prod_offer = Product.objects.create(category=self.category, name='Mega Discount Camera')
        ProductVariant.objects.create(product=self.prod_offer, name='Default', price=Decimal('700.00'), regular_price=Decimal('1000.00'), is_default=True)

    def test_curated_tables_appear_on_homepage(self):
        # Create curated entries
        FeaturedProduct.objects.create(product=self.prod_featured, order=1)
        NewProduct.objects.create(product=self.prod_new, order=1)
        OfferProduct.objects.create(product=self.prod_offer, order=1)

        response = self.client.get(reverse('shop:home'))
        self.assertEqual(response.status_code, 200)
        
        featured_list = response.context['featured_products']
        new_list = response.context['new_products']
        offer_list = response.context['best_offers']

        self.assertIn(self.prod_featured, featured_list)
        self.assertIn(self.prod_new, new_list)
        self.assertIn(self.prod_offer, offer_list)




