# Payment Integration - Technical Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
│  ┌─────────────┬──────────────┬────────────┬──────────────┐  │
│  │cart.html    │checkout.html │success.html│cancel.html   │  │
│  │             │              │            │myorder.html  │  │
│  └──────┬──────┴──────┬───────┴────────┬───┴──────────────┘  │
└─────────┼─────────────┼────────────────┼───────────────────────┘
          │ HTTP POST   │ JavaScript     │ AJAX Fetch
          │ (form)      │ (Stripe.js)    │ (JSON)
┌─────────▼─────────────▼────────────────▼───────────────────────┐
│                   Django Backend                              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ URL Router (urls.py)                                     │ │
│  │ ├─ /checkout/          → checkout()                      │ │
│  │ ├─ /create-checkout-session/ → create_checkout_session()│ │
│  │ ├─ /success.html/      → success()                       │ │
│  │ ├─ /cancel.html/       → cancel()                        │ │
│  │ └─ /myorder/           → myorder()                       │ │
│  └────────────┬───────────────────────────────────────────┬─┘ │
│               │                                           │    │
│  ┌────────────▼────────────────────────────────────────┐ │    │
│  │ View Functions (views.py)                          │ │    │
│  │ ├─ checkout()                                      │ │    │
│  │ ├─ create_checkout_session()  ← Stripe API Call   │ │    │
│  │ ├─ success()                  ← Order Creation     │ │    │
│  │ ├─ cancel()                                        │ │    │
│  │ ├─ myorder()                                       │ │    │
│  │ └─ send_payment_confirmation_email()               │ │    │
│  └────────────┬────────────────────────────────────────┘ │    │
│               │                                           │    │
│  ┌────────────▼────────────────────────────────────────┐  │   │
│  │ Models (models.py)                                 │  │   │
│  │ ├─ User                                            │  │   │
│  │ ├─ Product                                         │  │   │
│  │ ├─ Cart                                            │  │   │
│  │ └─ Order (NEW) ✨                                  │  │   │
│  │   ├─ user (ForeignKey)                             │  │   │
│  │   ├─ stripe_session_id                             │  │   │
│  │   ├─ stripe_payment_intent                         │  │   │
│  │   ├─ total_amount                                  │  │   │
│  │   ├─ order_status                                  │  │   │
│  │   ├─ created_at                                    │  │   │
│  │   └─ updated_at                                    │  │   │
│  └────────────┬────────────────────────────────────────┘  │   │
└──────────────┼────────────────────────────────────────────────┘
               │ SQL Queries
┌──────────────▼────────────────────────────────────────────────┐
│                   Database (SQLite)                           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Tables                                                   │ │
│  │ ├─ myapp_user                                           │ │
│  │ ├─ myapp_product                                        │ │
│  │ ├─ myapp_cart                                           │ │
│  │ ├─ myapp_wishlist                                       │ │
│  │ └─ myapp_order (NEW) ✨                                 │ │
│  │   └─ Stores all payment transactions                    │ │
│  └──────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘

               ↔ HTTP HTTPS
┌───────────────────────────────────────────────────────────────┐
│                   External Services                           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Stripe API                                               │ │
│  │ ├─ checkout.Session.create()                             │ │
│  │ ├─ checkout.Session.retrieve()                           │ │
│  │ └─ Payment Processing                                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Email Service (Gmail SMTP)                              │ │
│  │ └─ Confirmation emails                                  │ │
│  └──────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

---

## Class Diagram - Order Model

```
┌─────────────────────────────────────────────┐
│              Order                          │
├─────────────────────────────────────────────┤
│ id: Integer (PK)                            │
│ user: ForeignKey(User)                      │
│ stripe_session_id: CharField (500, unique)  │
│ stripe_payment_intent: CharField (500)      │
│ total_amount: DecimalField                  │
│ order_status: CharField (choices)           │
│   - pending                                 │
│   - completed                               │
│   - failed                                  │
│   - cancelled                               │
│ created_at: DateTimeField (auto_now_add)    │
│ updated_at: DateTimeField (auto_now)        │
├─────────────────────────────────────────────┤
│ Methods:                                    │
│ + __str__()                                 │
│ + get_order_status_display()                │
│ + Meta: ordering = ['-created_at']          │
└─────────────────────────────────────────────┘
         │
         │ ForeignKey
         ▼
┌─────────────────────────────────────────────┐
│              User                           │
├─────────────────────────────────────────────┤
│ id: Integer                                 │
│ fname: CharField                            │
│ lname: CharField                            │
│ email: EmailField (unique)                  │
│ password: CharField                         │
│ mobile: PositiveIntegerField                │
│ address: TextField                          │
│ profile_picture: ImageField                 │
│ usertype: CharField (buyer/seller)          │
└─────────────────────────────────────────────┘
```

---

## Request/Response Flow Diagram

### Checkout Page Request
```
Client                          Django                      Database
  │                              │                            │
  ├──GET /checkout/──────────────►│                            │
  │                              │                            │
  │                              ├──Query cart items ────────►│
  │                              │◄────── Cart Items ─────────│
  │                              │                            │
  │                              ├──Query user ──────────────►│
  │                              │◄────── User Data ──────────│
  │                              │                            │
  │◄──────checkout.html──────────│                            │
  │    (with Stripe key)         │                            │
```

### Create Checkout Session
```
Client                          Django                    Stripe API
  │                              │                           │
  ├──POST /create-checkout-──────►│                           │
  │  session/ (JSON)             │                           │
  │                              ├────Create Session────────►│
  │                              │◄────Session ID────────────│
  │                              │                           │
  │                              ├──Save Order in DB ──►    │
  │                              │                    Database
  │                              │                           │
  │◄──Session ID (JSON)──────────│                           │
  │                              │                           │
  ├──Redirect to Stripe ─────────────────────────────────────►│
  │  (with Session ID)           │                           │
```

### Success Page
```
Client                          Django                      Database/Email
  │                              │                            │
  ├──GET /success/?──────────────►│                           │
  │  session_id=...              │                           │
  │                              ├──Query Stripe Session ─┐  │
  │                              │◄──Session Data ────────┘  │
  │                              │                           │
  │                              ├──Update Order Status ─────►│
  │                              │  (pending→completed)       │
  │                              │                           │
  │                              ├──Mark Cart Paid ──────────►│
  │                              │  (payment_status=True)     │
  │                              │                           │
  │                              ├──Send Confirmation Email──►│
  │                              │  (via Gmail SMTP)          │
  │◄──success.html────────────────│                           │
  │    (with Order #)            │                           │
```

---

## Data Flow - Complete Payment Cycle

```
USER PERSPECTIVE:
1. Add Items to Cart
   └─► Cart table updated with items

2. Go to Checkout
   └─► checkout() view retrieves cart items
   └─► Displays checkout.html with cart data

3. Enter Card Details & Click Pay
   └─► JavaScript sends AJAX request to /create-checkout-session/

4. Backend Processing
   └─► create_checkout_session() creates Order record (status=pending)
   └─► Stripe API creates checkout session
   └─► Returns session ID to frontend

5. Redirect to Stripe Payment
   └─► Stripe handles payment securely
   └─► User enters card details on Stripe's server

6. Payment Result
   └─► Successful: Redirect to /success.html?session_id=...
   └─► Failed/Cancelled: Redirect to /cancel.html

7. Success Page Processing
   └─► success() view verifies payment via Stripe API
   └─► Updates Order status to completed
   └─► Marks cart items as payment_status=True
   └─► Sends confirmation email
   └─► Clears session cart_count

8. View Orders
   └─► myorder() view retrieves all completed orders
   └─► Displays in myorder.html

DATABASE TRANSACTIONS:
├─ CREATE Order (pending)
├─ SELECT Cart items
├─ UPDATE Order status → completed
├─ UPDATE Cart payment_status → True
└─ (Email service writes confirmation)
```

---

## Template Hierarchy & Inheritance

```
Base Templates (inherited by all):
├─ HTML structure
├─ CSS (Bootstrap)
├─ Navigation bar
└─ Footer

Checkout Journey:
├─ cart.html
│  └─ Shows cart items
│  └─ "Proceed to Checkout" link
│
├─ checkout.html (NEW)
│  ├─ Shows cart summary
│  ├─ Shows billing address
│  ├─ Displays Stripe card element
│  ├─ Real-time validation
│  └─ Submit button triggers create-checkout-session
│
├─ Stripe Payment Page (external)
│  └─ Hosted by Stripe
│
├─ success.html (NEW)
│  ├─ Confirmation message
│  ├─ Order details
│  └─ Next steps
│
└─ myorder.html (NEW)
   ├─ Order history
   ├─ Order details
   └─ Order statistics
```

---

## Security Architecture

```
┌────────────────────────────────────────────────┐
│           Security Layers                      │
├────────────────────────────────────────────────┤
│                                                │
│  Layer 1: HTTPS/TLS Encryption                │
│  ├─ All communication encrypted                │
│  └─ Stripe enforces HTTPS                      │
│                                                │
│  Layer 2: Django CSRF Protection               │
│  ├─ {% csrf_token %} in forms                  │
│  ├─ X-CSRFToken in AJAX requests               │
│  └─ CSRF middleware validates                  │
│                                                │
│  Layer 3: Session Management                  │
│  ├─ User authentication required               │
│  ├─ Session data server-side only              │
│  └─ Cart tied to user session                  │
│                                                │
│  Layer 4: PCI Compliance (Stripe)              │
│  ├─ Card details never touch server            │
│  ├─ Stripe.js handles card input               │
│  ├─ Stripe processes payment securely          │
│  └─ PCI Level 1 compliance                     │
│                                                │
│  Layer 5: Data Validation                      │
│  ├─ Server-side amount verification            │
│  ├─ User ownership validation                  │
│  ├─ Email validation                           │
│  └─ Order verification                         │
│                                                │
│  Layer 6: Error Handling                       │
│  ├─ No sensitive data in errors                │
│  ├─ User-friendly error messages               │
│  ├─ Logging for debugging                      │
│  └─ Graceful failure handling                  │
│                                                │
└────────────────────────────────────────────────┘
```

---

## API Integration Points

### Stripe API Calls

1. **Create Checkout Session**
```python
stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[...],
    mode='payment',
    success_url='...',
    cancel_url='...',
    customer_email='...',
    shipping_address_collection={...}
)
```

2. **Retrieve Session**
```python
stripe.checkout.Session.retrieve(session_id)
```

3. **Check Payment Status**
```python
session.payment_status  # 'paid', 'unpaid', 'no_payment_required'
```

### Email API (Gmail SMTP)

```python
send_mail(
    subject='Order Confirmation',
    message='...',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[user_email],
    fail_silently=False
)
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────┐
│         Try Block                       │
├─────────────────────────────────────────┤
│                                         │
│ Create checkout session                │
│ │                                       │
│ ├─ Success → Return session ID          │
│ │                                       │
│ └─ Error → Catch exception              │
│     │                                   │
│     └─ Return error JSON                │
│         to frontend                     │
│                                         │
│ Frontend receives error → Show message  │
│                                         │
└─────────────────────────────────────────┘
```

---

## Performance Considerations

```
Database Queries:
├─ checkout()        → 2 queries (user, cart items)
├─ create_checkout_session() → 3 queries (user, cart, create order)
├─ success()         → 4 queries (user, cart, order, update)
└─ myorder()         → 2 queries (user, orders)

Stripe API Calls:
├─ create_checkout_session() → 1 API call
├─ success()         → 1 API call (verify)
└─ Stripe webhooks (future) → async processing

Email Sending:
└─ success() → 1 email call (async recommended for production)
```

---

## Scalability Notes

**Current Setup (Development):**
- SQLite database (single file)
- Synchronous email sending
- Direct Stripe API calls
- Session-based cart storage

**For Production:**
1. Replace SQLite with PostgreSQL
2. Implement Celery for async email
3. Add caching layer (Redis)
4. Implement Stripe webhooks
5. Add monitoring/logging
6. Rate limiting on APIs
7. Load balancing

---

## Testing Strategy

```
Unit Tests:
├─ Order model creation
├─ View function logic
└─ Email sending

Integration Tests:
├─ Cart → Checkout flow
├─ Stripe session creation
└─ Success → Database update

End-to-End Tests:
├─ Full payment flow
├─ Success page display
└─ Order appearing in history
```

---

## Migration History

```
Previous State:
- Cart model with payment_status field
- Basic views (cart, add-to-cart, etc.)

After Payment Integration:
- NEW: Order model
- ENHANCED: Views (added payment processing)
- ENHANCED: Templates (added checkout flow)
- NEW: URLs (added checkout route)
- NEW: Migration 0006 (Order table)

Future Migrations Needed:
- Refund support
- Subscription model
- Payment method storage
```

---

This architecture ensures:
✅ Security (PCI compliant)
✅ Scalability (can be enhanced)
✅ Maintainability (clear separation)
✅ Reliability (error handling)
✅ Performance (optimized queries)

