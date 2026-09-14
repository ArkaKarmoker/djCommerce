from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal

from .models import (
    Category, Product, ProductVariant, ProductImage,
    Customer, Address, Order, Payment, Review
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
            price=Decimal('999.00'),
            quantity=10,
            short_description='Tensor G4 powerhouse',
            description='Detailed specs here',
            is_featured=True
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            name='Pixel 9 Pro (Hazel / 256GB)',
            color='Hazel',
            stock=5,
            price_adjustment=Decimal('50.00')
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
        self.assertEqual(self.variant.stock, 5)
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
            price=Decimal('1000.00'),
            quantity=10
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            name='iPhone 16 (Black 256GB)',
            color='Black',
            stock=5,
            price_adjustment=Decimal('100.00')
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

        # Add product without variant
        cart.add(self.product, quantity=1)
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart.get_total_price(), Decimal('1000.00'))

        # Add with variant ($1000 + $100 = $1100)
        cart.add(self.product, quantity=2, variant=self.variant)
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
            price=Decimal('1200.00'),
            quantity=10
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
            price=Decimal('1199.00'),
            quantity=10,
            short_description='Titanium powerhouse',
            description='Specs info',
            is_featured=True
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
            'name': 'Arka Karmoker',
            'phone': '01712345678',
            'address': 'House 12, Road 4, Banani, Dhaka',
            'email': 'arka@example.com',
            'payment_method': 'cod'
        }
        response = self.client.post(checkout_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Order Placed Successfully!')
        self.assertContains(response, 'Arka Karmoker')

        # Check DB
        customer = Customer.objects.get(phone='01712345678')
        order = Order.objects.get(customer=customer, product=self.product)
        self.assertEqual(order.total_price, Decimal('1199.00'))
        self.assertEqual(order.payment_method, 'Cash on Delivery')
        self.assertEqual(order.status, 'Pending')


