/**
 * djCommerce - Main JavaScript
 * Handles interactive cart quantities, dynamic calculations, AJAX cart updates, and form validation.
 */

document.addEventListener('DOMContentLoaded', () => {
    initCartQuantitySteppers();
    initAjaxCartButtons();
    initCheckoutValidation();
    initSearchShortcut();
});

/**
 * Get CSRF Token from cookie
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Display modern floating notification toast
 */
function showToast(message, type = 'success') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = 'custom-toast p-3 mb-2 d-flex align-items-center justify-content-between';
    toast.style.minWidth = '280px';

    const icon = type === 'success' ? 'bi-check-circle-fill text-success' : 'bi-info-circle-fill text-primary';
    toast.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <i class="bi ${icon} fs-5"></i>
            <span class="small fw-medium">${message}</span>
        </div>
        <button type="button" class="btn-close btn-close-white btn-sm ms-2" onclick="this.parentElement.remove()"></button>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

/**
 * Format currency to remove unnecessary .00 decimal when integer
 */
function formatCartCurrency(val) {
    const num = parseFloat(val);
    if (isNaN(num)) return val;
    return (num % 1 === 0) ? Math.round(num).toString() : num.toFixed(2);
}

/**
 * Update cart badge numbers across the page
 */
function updateCartBadge(count) {
    const badges = document.querySelectorAll('.cart-count-pill, .dj-badge-counter, .dj-mobile-cart-count');
    badges.forEach(badge => {
        badge.textContent = count;
    });

    // Update cart page header count badge ("X Items" / "1 Item")
    const headerCount = document.getElementById('cart-header-count');
    if (headerCount) {
        headerCount.textContent = `${count} ${count === 1 ? 'Item' : 'Items'}`;
    }

    // Update order summary count badge ("X Items" / "1 Item")
    const summaryCount = document.getElementById('cart-summary-count');
    if (summaryCount) {
        summaryCount.textContent = `${count} ${count === 1 ? 'Item' : 'Items'}`;
    }

    // Update modal count if present
    const modalCount = document.getElementById('cart-modal-count');
    if (modalCount) {
        modalCount.textContent = count;
    }
    const modalItemWord = document.getElementById('cart-modal-item-word');
    if (modalItemWord) {
        modalItemWord.textContent = count === 1 ? 'item' : 'items';
    }

    // Update document title if on cart page (e.g. Shopping Cart (3) - djCommerce)
    if (document.title.includes('Shopping Cart')) {
        document.title = document.title.replace(/\(\d+\)/, `(${count})`);
    }
}

/**
 * Quantity Stepper for Cart page
 */
function initCartQuantitySteppers() {
    const cartTable = document.getElementById('cart-items-wrapper');
    if (!cartTable) return;

    cartTable.addEventListener('click', async (e) => {
        const btn = e.target.closest('.cart-qty-btn');
        if (!btn) return;

        e.preventDefault();
        const action = btn.dataset.action;
        const productId = btn.dataset.productId;
        const itemKey = btn.dataset.itemKey || productId;
        const input = document.getElementById(`cart-qty-${itemKey}`);
        if (!input) return;

        let currentQty = parseInt(input.value) || 1;
        if (action === 'increase') {
            currentQty += 1;
        } else if (action === 'decrease') {
            currentQty -= 1;
        }



        // Post update via AJAX
        try {
            const response = await fetch(`/cart/update/${productId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: new URLSearchParams({
                    action: action,
                    quantity: currentQty,
                    item_key: itemKey
                })
            });

            const data = await response.json();
            if (data.success) {
                if (data.item_quantity <= 0) {
                    const row = document.getElementById(`cart-row-${itemKey}`);
                    if (row) row.remove();
                } else {
                    input.value = data.item_quantity;
                    const subtotalElem = document.getElementById(`cart-subtotal-${itemKey}`);
                    if (subtotalElem) {
                        subtotalElem.textContent = `৳ ${formatCartCurrency(data.item_subtotal)}`;
                    }
                }

                // Update summary subtotal & grand total
                const itemsSubtotalElem = document.getElementById('cart-items-subtotal');
                if (itemsSubtotalElem) {
                    itemsSubtotalElem.textContent = `৳ ${formatCartCurrency(data.cart_subtotal || data.cart_total)}`;
                }
                const shippingCostElem = document.getElementById('cart-shipping-cost');
                if (shippingCostElem && data.shipping_cost !== undefined) {
                    shippingCostElem.textContent = `৳ ${formatCartCurrency(data.shipping_cost)}`;
                }
                const grandTotalElem = document.getElementById('cart-grand-total');
                if (grandTotalElem) {
                    grandTotalElem.textContent = `৳ ${formatCartCurrency(data.cart_total)}`;
                    grandTotalElem.style.whiteSpace = 'nowrap';
                }

                updateCartBadge(data.cart_count);

                if (data.is_empty) {
                    location.reload();
                }
            }
        } catch (error) {
            console.error('Cart update failed:', error);
        }
    });
}

/**
 * Handle Add-to-Cart buttons via AJAX
 */
function initAjaxCartButtons() {
    document.querySelectorAll('.ajax-add-to-cart').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalHtml = submitBtn.innerHTML;

            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> Adding...`;

            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                const data = await response.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    updateCartBadge(data.cart_count);
                }
            } catch (err) {
                // Fallback to normal form submit if fetch fails
                form.submit();
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            }
        });
    });
}

/**
 * Client-side validation for Checkout Form
 */
function initCheckoutValidation() {
    const checkoutForm = document.getElementById('checkout-form');
    if (!checkoutForm) return;

    checkoutForm.addEventListener('submit', (e) => {
        const phoneInput = document.getElementById('checkout-phone');
        const nameInput = document.getElementById('checkout-name');
        const addressInput = document.getElementById('checkout-address');

        let isValid = true;

        if (!nameInput.value.trim()) {
            nameInput.classList.add('is-invalid');
            isValid = false;
        } else {
            nameInput.classList.remove('is-invalid');
        }

        if (!phoneInput.value.trim() || phoneInput.value.trim().length < 6) {
            phoneInput.classList.add('is-invalid');
            isValid = false;
        } else {
            phoneInput.classList.remove('is-invalid');
        }

        if (!addressInput.value.trim() || addressInput.value.trim().length < 10) {
            addressInput.classList.add('is-invalid');
            isValid = false;
        } else {
            addressInput.classList.remove('is-invalid');
        }

        if (!isValid) {
            e.preventDefault();
            showToast("Please fill in all required fields properly.", "warning");
        }
    });
}

/**
 * Keyboard shortcut: press '/' to focus search input
 */
function initSearchShortcut() {
    window.addEventListener('keydown', (e) => {
        if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
            e.preventDefault();
            const searchInput = document.getElementById('main-search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });
}
