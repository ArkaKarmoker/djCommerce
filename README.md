# djCommerce - Single Vendor Mobile Shop E-Commerce Website

![djCommerce Banner](static/css/style.css)

**djCommerce** is a complete, modern, responsive Single Vendor E-commerce web application specializing in **smartphones, flagship mobile devices, and gaming phones**, built strictly in accordance with the specifications in `Assignment_Single_Vendor_Ecommerce_Images.md`.

---

## 📱 Features & Highlights

### 1. Home Page (`/`)
- **Brand Identity & Header:** Responsive navigation bar with shop logo, phone category menu, live cart badge counter, user account menu (Sign In / Register / Dashboard), and quick order tracking.
- **Hero Carousel Banner:** High-impact Bootstrap 5 carousel showcasing 2026 flagships, esports gaming phones, and official warranty guarantees.
- **Category Grid:** Dynamic category navigation displaying live product counts.
- **Featured & Latest Releases:** Interactive smartphone cards loaded from the SQLite database with variant badges.
- **Perks & Value Propositions:** Highlights 100% original products, nationwide delivery, and 7-day replacement warranty.
- **Footer:** Complete store info, social links, operating hours, and customer support details.

### 2. Products Catalog (`/products/`)
- Displays **11+ realistic smartphones** across multiple categories.
- **Category Filter:** Filter by *Flagships*, *Gaming Phones*, *Foldables*, *Mid-Range*, and *Budget Phones*.
- **Search Bar:** Keyword search across phone names, brands, specifications, and descriptions.
- **Sorting Options:** Sort by *Newest First*, *Price: Low to High*, *Price: High to Low*, and *Alphabetical (A-Z)*.
- Each product card contains:
  - Product Image & Brand badge
  - Product Name & Specs preview
  - Price & Star Rating breakdown
  - Short Description
  - **View Details** button
  - **Add to Cart** button (with interactive stock checks)

### 3. Product Details Page (`/products/<id>/`)
- High-resolution smartphone preview image with interactive **Multi-angle Gallery Thumbnails**.
- **Product Variants System:** Interactive variant pills (Storage & Color options) with instant dynamic pricing, SKU, and stock count updates.
- Technical specifications table (Processor, Display, Camera, Battery, Storage, OS updates).
- **Stock Availability Badge:** Displays exact units in stock (e.g. *"5 Units In Stock"* or *"Out of Stock"*).
- Interactive quantity stepper and **Add to Cart** action for specific variants.
- **Customer Reviews & Ratings:** Verified buyer star ratings breakdown with interactive review submission form.
- **Related Products:** Recommends alternative devices in the same category.

### 4. Shopping Cart (`/cart/`)
- Session-based cart with seamless guest or authenticated checkout.
- **Variant-Aware Cart:** Distinguishes multiple variants of the same smartphone (e.g. 256GB vs 512GB).
- **Increase Quantity (`+`):** Increases item quantity with stock cap protection.
- **Decrease Quantity (`-`):** Decreases item quantity or prompts removal when reaching zero.
- **Remove Product:** Instant removal button with confirmation.
- **Dynamic JavaScript Price Recalculation:** Subtotals and grand totals update in real-time.
- Summary breakdown showing subtotal, free delivery threshold, and grand total.

### 5. Checkout Page (`/checkout/`)
- Streamlined, validated customer checkout form:
  - **Customer Name & Phone Number** (with format validation)
  - **Saved Address Selector:** Authenticated users can select one of their saved addresses with one click.
  - **Delivery Address & Email Address**
- **Dual Payment Gateways:**
  - **Stripe Credit/Debit Card:** Secure redirection to Stripe Checkout with live payment intents and receipt tracking.
  - **Cash on Delivery (COD):** Direct checkout with immediate confirmation.
- Order items summary list with thumbnail, selected variant, quantity, unit price, and subtotal.

### 6. Customer Dashboard (`/dashboard/`)
- **Profile Overview:** Customer name, phone, email, and member badge.
- **Order History Tab:** Chronological list of orders with status badges (*Pending*, *Processing*, *Shipped*, *Delivered*), payment status, and quick link to invoice.
- **Address Book Tab:** Saved shipping addresses with default address designation and one-click address addition/deletion.
- **Account Settings Tab:** Update profile details seamlessly.

### 7. Order Confirmation & Official Invoice (`/dashboard/orders/<order_number>/`)
- Prominent confirmation message: **"Order Placed Successfully!"**
- Unique order reference code (e.g. `DJ-87FF50BE`).
- Itemized invoice breakdown with variant specifics, subtotal, and payment details.
- Action buttons: **Print Official Invoice**, **Continue Shopping**, and **Track Order Status**.

### 8. User Authentication (`/login/`, `/register/`, `/logout/`)
- Clean, responsive registration with validation and automatic Customer profile creation.
- Secure login and redirection back to checkout or dashboard.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **Backend Framework** | Django 6.1 |
| **Language** | Python 3.12 |
| **Database** | SQLite3 |
| **Payment Gateway** | Stripe API (`stripe` Python SDK & Stripe Checkout) |
| **Frontend Framework** | Bootstrap 5.3.3 & Bootstrap Icons |
| **Styling** | Custom Vanilla CSS3 (`static/css/style.css`) with Google Fonts (*Outfit* & *Plus Jakarta Sans*) |
| **Interactivity** | Vanilla JavaScript ES6 (`static/js/main.js`) & Fetch API |
| **Image Processing** | Pillow (PIL) |
| **Environment Config** | `python-dotenv` |

---

## 🗄️ Database Architecture

The application contains the following database models in `shop/models.py`:

```
TimeStampMixin (Abstract)
├── created_at (DateTimeField)
└── updated_at (DateTimeField)

Category
├── name (CharField)
├── slug (SlugField)
├── icon (CharField)
└── description (TextField)

Product
├── category (ForeignKey -> Category)
├── name (CharField)
├── brand (CharField)
├── slug (SlugField)
├── price (DecimalField)
├── short_description (CharField)
├── description (TextField)
├── image (ImageField)
├── quantity (PositiveIntegerField)
├── rating (DecimalField)
└── is_featured (BooleanField)

ProductVariant
├── product (ForeignKey -> Product)
├── name (CharField, e.g. "512GB / Desert Titanium")
├── color (CharField)
├── storage (CharField)
├── additional_price (DecimalField)
├── stock (PositiveIntegerField)
└── sku (CharField)

ProductImage
├── product (ForeignKey -> Product)
├── image (ImageField)
├── alt_text (CharField)
└── is_primary (BooleanField)

Address
├── full_name, phone_number, street_address
├── city, postal_code, country
└── is_default (BooleanField)

Customer
├── user (OneToOneField -> User, optional)
├── name (CharField)
├── phone (CharField)
├── address (TextField)
├── email (EmailField)
└── addresses (ManyToManyField -> Address)

Order
├── order_number (CharField)
├── customer (ForeignKey -> Customer)
├── product (ForeignKey -> Product)
├── variant (ForeignKey -> ProductVariant, optional)
├── delivery_address (ForeignKey -> Address, optional)
├── quantity (PositiveIntegerField)
├── total_price (DecimalField)
├── payment_method (CharField: 'cod' or 'stripe')
├── stripe_payment_intent_id (CharField)
├── order_date (DateTimeField)
└── status (CharField)

Payment
├── order (ForeignKey -> Order)
├── payment_method, amount, status
└── transaction_id (CharField)

Review
├── product (ForeignKey -> Product)
├── customer (ForeignKey -> Customer)
├── rating (PositiveSmallIntegerField, 1-5)
└── comment (TextField)
```

---

## 🚀 Installation & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/ArkaKarmoker/djCommerce.git
cd djCommerce
```

### 2. Create and Activate Virtual Environment
```powershell
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables (`.env`)
Create a `.env` file in the root directory:
```ini
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

### 5. Run Migrations
```powershell
python manage.py migrate
```

### 6. Seed Catalog with Realistic Mobile Phones, Variants & Gallery
Populate categories, smartphones, storage/color variants, gallery images, and reviews:
```powershell
python manage.py seed_products
```

### 7. Run the Development Server
```powershell
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your browser. Default credentials for demo:
- **Admin:** `admin` / `admin123`

---

## 🧪 Running Automated Tests

Run the full automated test suite covering models, user authentication, customer dashboard, product variants, shopping cart logic, Cash on Delivery, and Stripe payment flows:

```powershell
python manage.py test shop --verbosity=2
```

**Output:**
```
Found 10 test(s).
test_login_and_dashboard_access (shop.tests.AuthAndDashboardTests.test_login_and_dashboard_access) ... ok
test_user_registration (shop.tests.AuthAndDashboardTests.test_user_registration) ... ok
test_cart_operations_with_variants (shop.tests.CartTests.test_cart_operations_with_variants) ... ok
test_checkout_cod_order_placement (shop.tests.CheckoutAndFlowTests.test_checkout_cod_order_placement) ... ok
test_home_and_product_list_views (shop.tests.CheckoutAndFlowTests.test_home_and_product_list_views) ... ok
test_address_and_customer_creation (shop.tests.ModelTests.test_address_and_customer_creation) ... ok
test_category_creation (shop.tests.ModelTests.test_category_creation) ... ok
test_order_and_payment_creation (shop.tests.ModelTests.test_order_and_payment_creation) ... ok
test_product_and_variant_creation (shop.tests.ModelTests.test_product_and_variant_creation) ... ok
test_review_creation (shop.tests.ModelTests.test_review_creation) ... ok

----------------------------------------------------------------------
Ran 10 tests in 2.947s

OK
```

---

## 📁 Project Structure

```
djCommerce/
├── Assignment_Single_Vendor_Ecommerce_Images.md
├── manage.py
├── requirements.txt
├── README.md
├── .env                        # Environment configuration (Stripe keys, Debug flag)
├── core/                       # Django project configuration folder
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py             # Settings (installed apps, media/static, Stripe keys)
│   ├── urls.py                 # Root URL router
│   └── wsgi.py
├── shop/                       # Main e-commerce shop app
│   ├── __init__.py
│   ├── admin.py                # Admin panel with inlines for Variants & Gallery
│   ├── apps.py
│   ├── cart.py                 # Variant-aware session cart engine
│   ├── context_processors.py   # Global cart & categories context
│   ├── forms.py                # UserRegisterForm, AddressForm, ReviewForm, CheckoutForm
│   ├── models.py               # TimeStampMixin, Category, Product, ProductVariant, Customer, Order, Payment, Review
│   ├── tests.py                # Comprehensive test suite (Auth, Dashboard, Cart, Checkout, Models)
│   ├── urls.py                 # Shop URL routing
│   ├── views.py                # Views for Auth, Dashboard, Catalog, Cart, Checkout, Stripe & Invoices
│   ├── migrations/             # Database migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   └── management/
│       └── commands/
│           └── seed_products.py # Management command to seed catalog, variants & images
├── static/
│   ├── css/
│   │   └── style.css           # Custom design system tokens, hero banner, glassmorphism, cards, animations
│   └── js/
│       └── main.js             # Variant pill switches, stepper controls, AJAX cart updates, address selector
├── templates/
│   ├── base.html               # Base layout with navbar, user auth dropdown, messages, footer
│   └── shop/
│       ├── home.html           # Home page with hero carousel, category pills & featured phones
│       ├── product_list.html   # Product catalog with search, category filtering & sorting
│       ├── product_detail.html # Product details with specs, variant selector, gallery & reviews
│       ├── cart.html           # Shopping cart with variant details & dynamic recalculation
│       ├── checkout.html       # Checkout form with saved address picker & Stripe/COD options
│       ├── order_success.html  # Order confirmation page with invoice link
│       ├── order_lookup.html   # Order tracking by phone number
│       ├── order_detail.html   # Official purchase invoice view
│       ├── dashboard.html      # Customer dashboard (Profile, Orders, Address book)
│       ├── login.html          # Clean branded login page
│       └── register.html       # Clean branded customer registration page
└── media/
    └── products/               # Seeded high-quality smartphone images
```

---

## 📄 License
This project was developed for educational purposes as part of the Django Web Development Single Vendor E-commerce Assignment.

