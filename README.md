# djCommerce — Premium Gadgets & Mobile E-Commerce Web Application

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12.10-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Django-6.1.1-092E20?style=for-the-badge&logo=django&logoColor=44B78B" alt="Django">
  <img src="https://img.shields.io/badge/SQLite-3.49-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Bootstrap-5.3.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap">
  <img src="https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/Stripe-Payment_Gateway-635BFF?style=for-the-badge&logo=stripe&logoColor=white" alt="Stripe">
  <img src="https://img.shields.io/badge/TinyMCE-6_Rich_Editor-2075F0?style=for-the-badge&logo=tinymce&logoColor=white" alt="TinyMCE">
  <img src="https://img.shields.io/badge/Pillow-12.3.0-FF69B4?style=for-the-badge&logo=python&logoColor=white" alt="Pillow">
</p>

**djCommerce** is a responsive, full-featured Single-Vendor E-Commerce platform specializing in premium smartphones, tablets, smartwatches, audio devices, and tech accessories. Built with **Django 6.1**, **Bootstrap 5.3.3**, and **Vanilla JavaScript ES6+**, it includes **75 branded products** with multi-dimensional variant pricing (`Color | Storage | Region`), multi-angle image galleries, session-based cart, dual payment gateways (**Stripe** and **Cash on Delivery**), customer dashboard, and a fully customized Django Admin suite.


---

## 📋 Table of Contents
- [Technology Stack](#technology-stack)
- [Key Features](#key-features)
- [Demo Credentials](#demo-credentials)
- [Installation & Setup](#installation--setup)
- [Automated Testing](#automated-testing)
- [Database Schema](#database-schema)
- [Directory Structure](#directory-structure)
- [Assignment Compliance](#assignment-requirements-compliance)

---

## 🛠️ Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Backend** | Django 6.1.1 | ORM, MTV architecture, auth, sessions, forms |
| **Language** | Python 3.12.10 | Core server-side runtime |
| **Database** | SQLite 3.49 | Pre-populated with products, variants, and users |
| **Frontend** | Bootstrap 5.3.3 | Responsive grid, cards, modals, forms |
| **Scripting** | JavaScript ES6+ | AJAX cart, dynamic variant switching, quantity steppers |
| **Payment** | Stripe SDK | Hosted Stripe Checkout with webhook handling |
| **Rich Text** | TinyMCE 6 | WYSIWYG specification editor in Django Admin |
| **Images** | Pillow 12.3.0 | Image validation, format normalization, gallery uploads |
| **Config** | python-dotenv 1.2.3 | `.env` management for secrets and API keys |

### Dependencies (`requirements.txt`)
```text
Django==6.1.1
Pillow==12.3.0
stripe==15.6.1
python-dotenv==1.2.3
requests==2.34.2
```

---

## ✨ Key Features

### 1. Homepage
- Sticky navbar with logo, category dropdown, live search suggestions, and AJAX cart badge.
- Bootstrap carousel banner, category bubble navigation, trust/value strip.
- **Featured Products**, **New Arrivals**, and **Best Offers & Deals** sections (8 curated products each).
- Contact form (`/#contact`) and store footer with social links and operating hours.

### 2. Product Catalog (`/products/`)
- 75 products across 6 categories and 14 smartphone brand subcategories.
- Filters: Category, Brand, Price Range, Availability (In Stock / Out of Stock).
- Sorting: Newest, Price Low–High, Price High–Low, Highest Discount, A–Z.
- Live AJAX search with thumbnail previews, paginated 12 per page.

### 3. Product Details Page
- High-resolution gallery with click-to-swap thumbnail strip.
- Variant pills (`Color | Storage | Region`) with instant JavaScript price and stock updates.
- TinyMCE-formatted specification table.
- 1–5 star customer reviews with yellow Bootstrap star icons.
- **Out of Stock Guard**: blocks adding unavailable items to cart; shows warning toast linking to `/#contact`.
- Recently Viewed sidebar via browser LocalStorage.

### 4. Shopping Cart
- Session-based, variant-aware cart — multiple variants of the same product tracked separately.
- Add, increase, decrease, remove, and clear cart operations.
- Real-time AJAX total recalculation with stock cap enforcement.

### 5. Checkout (Stripe & COD)
- **Stripe Checkout** — secure hosted payment in BDT with success/cancel webhook handling.
- **Cash on Delivery** — instant order with `Pending` status.
- Saved address selector (up to 3 addresses per customer).

### 6. Customer Dashboard
- Profile management (name, phone, avatar), password change, address book.
- Order history with status badges (`Pending`, `Paid`, `Processing`, `Shipped`, `Delivered`, `Cancelled`).
- Printable formal invoice per order.

### 7. Django Admin Customizations
- TinyMCE 6 embedded in the Specification field.
- Inline gallery image management (up to 10 photos per product).
- Separate `ProductVariant` table with default variant radio selector.
- Homepage curation tables: `FeaturedProduct`, `NewProduct`, `OfferProduct`.
- Email-first custom User Admin.

---

## 🗄️ Demo Credentials

The repository includes a pre-populated `db.sqlite3` and all product images. Clone and run immediately.

| Role | Username / Email | Password | Access |
| :--- | :--- | :--- | :--- |
| **Admin / Superuser** | `admin` / `admin@example.com` | `123456` | Full access to Django Admin Panel (`/admin/`) & Storefront |
| **Customer (Normal User)** | `customer` / `customer@example.com` | `123456` | Storefront shopping, cart, checkout & customer dashboard |
| **Customer (Normal User)** | `testuser` / `testuser@example.com` | `123456` | Storefront shopping, cart, checkout & customer dashboard |

---

## 🚀 Installation & Setup

> **Note**: The SQLite database (`db.sqlite3`) and all product/gallery images (`media/` folder) are directly included in this repository. The project is completely pre-populated and ready to run immediately with all 75 products, multi-attribute variants, and demo user accounts out of the box without requiring manual database seeding.

### 1. Clone the Repository
```bash
git clone https://github.com/ArkaKarmoker/djCommerce.git
cd djCommerce
```

### 2. Create & Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration *(Optional)*
Copy `.env.example` to `.env` for Stripe live payment testing:
```ini
SECRET_KEY=your-secret-key
DEBUG=True
STRIPE_PUBLISHABLE_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key
```
> The project runs out-of-the-box without `.env` using built-in development defaults.

### 5. Run the Server
```bash
python manage.py runserver
```

| Page | URL |
| :--- | :--- |
| Storefront | http://127.0.0.1:8000/ |
| Product Catalog | http://127.0.0.1:8000/products/ |
| Django Admin | http://127.0.0.1:8000/admin/ |

---

## 🧪 Automated Testing

```bash
python manage.py test
```

```
Ran 13 tests in 3.6s — OK
```

Covers: model properties, cart logic, variant pricing, checkout validation, and views.

---

## 📊 Database Schema

```mermaid
erDiagram
    Category ||--o{ Category : "subcategories"
    Category ||--o{ Product : "contains"
    Product ||--o{ ProductVariant : "variants"
    Product ||--o{ ProductImage : "gallery"
    Product ||--o{ Review : "reviewed by"
    Customer ||--o{ Order : "places"
    Customer ||--o{ Review : "writes"
    Customer }o--o{ Address : "saved addresses"
    Order ||--|| Product : "orders"
    Order ||--o| ProductVariant : "selected variant"
    Order ||--o| Address : "delivery"
    Order ||--o{ Payment : "transactions"
```

---

## 📁 Directory Structure

```text
djCommerce/
├── core/                        # Django project configuration
│   ├── settings.py              # Project settings
│   ├── urls.py                  # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
├── media/                       # Uploaded media
│   ├── products/                # Product images
│   ├── product_images/          # Gallery images
│   └── profile/                 # User avatars
├── shop/                        # Main application
│   ├── admin.py                 # Admin configurations
│   ├── apps.py
│   ├── cart.py                  # Shopping cart
│   ├── context_processors.py
│   ├── forms.py                 # Forms
│   ├── models.py                # Database models
│   ├── tests.py                 # Unit tests
│   ├── urls.py                  # Shop URLs
│   ├── views.py                 # Views & logic
│   ├── management/              # Custom commands
│   └── migrations/
├── static/                      # Static assets
│   ├── css/
│   │   ├── admin_custom.css
│   │   └── style.css
│   ├── images/
│   └── js/
│       ├── admin_tinymce.js
│       └── main.js
├── templates/                   # HTML templates
│   ├── base.html                # Base layout
│   └── shop/                    # Shop templates
│       ├── home.html
│       ├── product_list.html
│       ├── product_detail.html
│       ├── cart.html
│       ├── checkout.html
│       ├── order_success.html
│       ├── order_detail.html
│       ├── order_invoice.html
│       ├── order_lookup.html
│       ├── dashboard.html
│       ├── login.html
│       └── register.html
├── .env.example
├── .gitignore
├── db.sqlite3                   # Pre-populated database
├── manage.py
├── README.md
└── requirements.txt
```

---

## 📋 Assignment Requirements Compliance

| Requirement | Implementation | Status |
| :--- | :--- | :---: |
| Home Page (logo, navbar, carousel, categories, featured, footer) | Custom logo, Bootstrap carousel, category bubbles, 8-product grids, footer | ✅ |
| Product Page (image, name, price, description, view & cart) | 75 products with BDT pricing, gallery, and instant cart action | ✅ |
| Product Details Page | Gallery, variant selector, spec table, stock badge, Add to Cart | ✅ |
| Shopping Cart (add, increase, decrease, remove, total) | Session cart with AJAX updates, stock cap, grand total | ✅ |
| Checkout (name, phone, address, save order, confirmation) | Validated form, address book, Order saved, confirmation page | ✅ |
| Database Models (Product, Customer, Order) | All 3 required + ProductVariant, ProductImage, Address, Payment, Review | ✅ |
| Django Admin Product Management | TinyMCE editor, inline gallery, variant table | ✅ |
| **Bonus:** Search | Live AJAX suggestions + catalog keyword filter | ✅ |
| **Bonus:** Category Filter | 6 parent categories + 14 brand subcategories | ✅ |
| **Bonus:** Login / Register | Email login, registration, profile, password change | ✅ |
| **Bonus:** Discounts | Regular vs offer price with % OFF badge and savings pill | ✅ |
| **Bonus:** Ratings | 1–5 star reviews with yellow Bootstrap icons | ✅ |
| **Bonus:** Order History | Dashboard with status badges and printable invoices | ✅ |
| **Bonus:** Online Payment | Stripe Checkout in BDT | ✅ |

---

## 🖼️ Screenshots

Home Page:
<img width="1763" alt="Screenshot_16-9-2026_34917_127 0 0 1" src="https://github.com/user-attachments/assets/a1d7b482-28a2-44be-9d1a-87d932e7c9ea" />

Product Page:
<img width="1763" height="3490" alt="image" src="https://github.com/user-attachments/assets/aa6609a4-2d01-4f05-8d73-ec4b7049e8a4" />

Product Details Page:
<img width="1763" height="3199" alt="image" src="https://github.com/user-attachments/assets/c95359c3-731a-4bcc-b0fd-3c161d3b7387" />

Cart Page:
<img width="1763" height="1558" alt="image" src="https://github.com/user-attachments/assets/6c971c4e-7bdb-481d-80dc-35f0005644fd" />

Checkout Page:
<img width="1763" height="2334" alt="image" src="https://github.com/user-attachments/assets/ae99cc48-4db7-4bbd-b932-fb8088b757da" />

Stripe Payment Page:
<img width="1147" height="953" alt="image" src="https://github.com/user-attachments/assets/c0458db2-099c-465d-b4bd-3a97dc80c682" />

Order Placed Successfully:
<img width="1763" height="2075" alt="image" src="https://github.com/user-attachments/assets/8dd37df7-9654-4b28-99ce-4a4e688f44ad" />

Printing Invoice:
<img width="1550" height="1031" alt="image" src="https://github.com/user-attachments/assets/0950ed76-92ac-4f5d-b399-052f24c8a1cb" />

User Dashboard:
<img width="1763" height="1426" alt="image" src="https://github.com/user-attachments/assets/a496a2c0-d55d-4e00-be69-b8e9094e1bda" />

Order History:
<img width="1763" height="1652" alt="image" src="https://github.com/user-attachments/assets/cda85825-ddc5-488c-be55-f58f86dd0d0d" />

Order Details Page:
<img width="1763" height="2201" alt="image" src="https://github.com/user-attachments/assets/054861cb-8e30-4489-b236-798240cd5502" />

User Address Book:
<img width="1763" height="1349" alt="image" src="https://github.com/user-attachments/assets/0259f310-49e8-4a1a-8ad2-47fdb6c2f130" />

User Account Change Password Page:
<img width="1763" height="1349" alt="image" src="https://github.com/user-attachments/assets/e02fcc74-9fa3-4cb4-a6be-5a7dd662233f" />

Category with Subcategories:
<img width="1748" height="642" alt="image" src="https://github.com/user-attachments/assets/1f8aaf98-d62f-441e-920f-2f971f0b3e41" />

Realtime Product Search:
<img width="1765" height="772" alt="image" src="https://github.com/user-attachments/assets/a619389e-46a6-4167-a35c-bed51e57be58" />

Django Admin Panel:
<img width="1763" height="955" alt="image" src="https://github.com/user-attachments/assets/c328fcc4-9469-4e1f-bb87-45da903fee94" />

Admin Panel User Management:
<img width="1763" height="955" alt="image" src="https://github.com/user-attachments/assets/d5e5f3b0-2c9e-422c-ab15-d8c856f88e91" />


---

Developed for educational purposes. All product brand names belong to their respective trademark holders.

Thank you for taking the time to review the djCommerce project!  
Developed by [Arka Karmoker](https://github.com/ArkaKarmoker).
