from django.shortcuts import render,redirect,get_list_or_404
from django.contrib import messages
from .models import user, product, Wishlist, Cart, Order
import random
import stripe
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import requests
import json
import os
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime

YOUR_DOMAIN = os.getenv('SITE_URL', 'http://localhost:8000').rstrip('/')
stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.
def update_wishlist_count(user_obj):
    wishlist_count = Wishlist.objects.filter(user=user_obj).count()
    return wishlist_count


def update_cart_count(user_obj):
    cart_count = Cart.objects.filter(user=user_obj).count()
    return cart_count


def index(request):
    try:
        User = user.objects.get(email=request.session['email'])
        if User.usertype == 'buyer':
            request.session['wishlist_count'] = update_wishlist_count(User)
            request.session['cart_count'] = update_cart_count(User)
            return render(request, 'index.html')
        else:
            return render(request, 'seller-index.html')
    except:
        return render(request, 'index.html')

def contact(request):
    return render(request, 'contact.html')

def shop(request):
    products = product.objects.all()
    return render(request, 'shop.html', {'products': products})
    

def signup(request):
    if request.method == "POST":
        try:
            user.objects.get(email=request.POST['email'])
            messages.error(request, "Email Already Exists")
            return render(request, 'signup.html')
        except:
            if request.POST['password'] == request.POST['cpassword']:
                user.objects.create(
                    fname=request.POST['fname'],
                    lname=request.POST['lname'],
                    email=request.POST['email'],
                    password=request.POST['password'],
                    mobile=request.POST['mobile'],
                    address=request.POST['address'],
                   profile_picture=request.FILES['profile_picture'],
                    usertype=request.POST['usertype']
                )
                messages.success(request, "User Registered Successfully")
                return render(request, 'signup.html')
            else:
                messages.warning(request, "Password and Confirm Password do not match")
                return render(request, 'signup.html')
    else:
        return render(request, 'signup.html')

def login(request):
    if request.method == "POST":
        try:
            user_obj = user.objects.get(email=request.POST['email'])
            if user_obj.password == request.POST['password']:
                request.session['email'] = user_obj.email
                request.session['fname'] = user_obj.fname
                request.session['profile_picture'] = user_obj.profile_picture.url
                if user_obj.usertype == 'buyer':
                    request.session['wishlist_count'] = update_wishlist_count(user_obj)
                    request.session['cart_count'] = update_cart_count(user_obj)
                    messages.success(request, "Log in successfully")
                    return render(request, 'index.html')
                else:
                    return render(request, 'seller-index.html')
            else:
                messages.error(request, "Incorrect Password")
                return render(request, 'login.html')
        except:
            messages.error(request, "Email does not exist")
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')

def logout(request):
    try:
        del request.session['email']
        del request.session['fname']
        del request.session['profile_picture']
        request.session.pop('wishlist_count', None)
        request.session.pop('cart_count', None)
        messages.success(request, "Logged out successfully")
        return render(request, 'login.html')
    except:
        messages.warning(request, "You are not logged in")
        return render(request, 'login.html')

def change_password(request):
    User = user.objects.get(email=request.session['email'])
    if request.method == "POST":
        if User.password == request.POST['password']:
            if request.POST['new_password'] == request.POST['CNew_password']:
                if User.password != request.POST['new_password']:
                    User.password = request.POST['new_password']
                    User.save()
                    del request.session['email']
                    del request.session['fname']
                    del request.session['profile_picture']
                    messages.success(request,"Password changed successfully. Please log in Again")
                    return render(request, 'login.html')
                else:
                    messages.error(request,"New password cannot be same as old password")
                    if User.usertype == 'buyer':
                        return render(request, 'change-password.html')
                    else:
                       return render(request, 'seller-change-password.html')
            else:
                messages.error(request,"New passwords do not match")
                if User.usertype == 'buyer':
                 return render(request, 'change-password.html')
                else:
                 return render(request, 'seller-change-password.html')
                 
        else:
            messages.error(request,"Incorrect old password")
            if User.usertype == 'buyer':
                return render(request, 'change-password.html')
            else:
               return render(request, 'seller-change-password.html')
    else:
        if User.usertype == 'buyer':
            return render(request, 'change-password.html')
        else:
            return render(request, 'seller-change-password.html')

def profile(request):
    User= user.objects.get(email=request.session['email'])
    if request.method == "POST":
        User.fname = request.POST['fname']
        User.lname = request.POST['lname']
        User.mobile = request.POST['mobile']
        User.address = request.POST['address']
        try:
            User.profile_picture = request.FILES['profile_picture']
        except:
            pass
        User.save()
        request.session['fname'] = User.fname
        request.session['profile_picture'] = User.profile_picture.url
        messages.success(request, "Profile updated successfully")
        if User.usertype == 'buyer':
            return render(request, 'profile.html', {'user':User})
        else: 
          return render(request, 'seller-profile.html', {'user':User})
    else:
        if User.usertype == 'buyer':
            return render(request, 'profile.html', {'user':User})
        else:
         return render(request, 'seller-profile.html', {'user':User})

def forgot_password(request):
    url = "https://www.fast2sms.com/dev/bulkV2"
    if request.method == "POST":
        try:
            User=user.objects.get(mobile=request.POST['mobile'])
            mobile = str(User.mobile)
            otp = random.randint(1000,9999)
            payload = {
                "route": "q",
                "message": "Your OTP For Forgot Password Is :"+ str(otp),
                "numbers": mobile
            }
            headers = {
                "accept": "application/json",
                "Authorization": "sFZjXdGH6qnkAgzQbE0mfxJpYUaor358cNCRiKtuB21evlLhIM6gHmRDq9YLXxfhjlMdGoeap0inW4FC",
                "content-type": "application/json"
            }
            response = requests.post(url, json=payload, headers=headers)
            print(response.text)
            request.session['otp'] = otp
            request.session['email_to_reset'] = User.email
            return render(request, 'otp.html')
        except:
            messages.error(request, "Mobile number does not exist")
            return render(request, 'forgot-password.html')
    else:
        return render(request, 'forgot-password.html')


def forgot_choice(request):
    # Show options to send OTP via Mobile or Email
    return render(request, 'forgot-password-choice.html')


def forgot_password_email(request):
    # Handle OTP via email
    if request.method == "POST":
        try:
            User = user.objects.get(email=request.POST['email'])
            otp = random.randint(1000, 9999)
            subject = 'OTP for Password Reset'
            message = 'Your OTP For Forgot Password Is : ' + str(otp)
            email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
            try:
                # send_mail requires EMAIL settings to be configured in settings.py
                send_mail(subject, message, email_from, [User.email], fail_silently=False)
            except Exception as e:
                messages.error(request, f'Failed to send email: {e}')
                return render(request, 'forgot-password-email.html')
            request.session['otp'] = otp
            request.session['email_to_reset'] = User.email
            messages.success(request, 'OTP sent to your email')
            return render(request, 'otp.html')
        except:
            messages.error(request, "Email does not exist")
            return render(request, 'forgot-password-email.html')
    else:
        return render(request, 'forgot-password-email.html')

def verify_otp(request):
    otp1 =int(request.session['otp'])
    otp2 =int(request.POST['otp'])
    if otp1 == otp2:
        messages.success(request, "Set new password")
        return render(request, 'new-password.html')
    else:
        messages.error(request, "Incorrect OTP...Please try again")
        return render(request, 'otp.html')

def new_password(request):
    if request.POST['new_password'] == request.POST['CNew_password']:
        User = user.objects.get(email=request.session['email_to_reset'])
        User.password = request.POST['new_password']
        User.save()
        del request.session['email_to_reset']
        messages.success(request, "Password changed successfully. Please log in Again")
        return render(request, 'login.html')
    else:
        messages.error(request, "New passwords do not match")
        return render(request, 'new-password.html')
  
def seller_add_product(request):
    User = user.objects.get(email=request.session['email'])
    if request.method == "POST":
        # accept either spelling/casing from the form to avoid MultiValueDictKeyError
        product_catagory = request.POST.get('product_catagory') or request.POST.get('product_category')
        product_name = request.POST.get('product_name') or request.POST.get('Product_name')
        product_price = request.POST.get('product_price') or request.POST.get('Product_price')
        product_desc = request.POST.get('product_desc') or request.POST.get('Product_desc')
        product_image = request.FILES.get('product_image') or request.FILES.get('Product_image')

        if not (product_catagory and product_name and product_price):
            messages.error(request, "Please fill all required fields")
            return render(request, 'seller-add-product.html')

        if not product_image:
            messages.error(request, "Please upload a product image")
            return render(request, 'seller-add-product.html')

        product.objects.create(
            seller=User,
            product_catagory=product_catagory,
            product_name=product_name,
            product_price=product_price,
            product_desc=product_desc or '',
            product_image=product_image
        )
        messages.success(request, "Product added successfully")
        return render(request, 'seller-add-product.html')
    else:
      return render(request, 'seller-add-product.html')        

def seller_view_products(request):
    seller = user.objects.get(email=request.session['email'])
    products = product.objects.filter(seller=seller)
    return render(request, 'seller-view-product.html', {'products': products})

def seller_product_details(request, pk):
    product_obj = product.objects.get(pk=pk)
    return render(request, 'seller-product-details.html', {'product': product_obj})

def product_details(request, pk):
    product_obj = product.objects.get(pk=pk)
    wishlist_flag = False
    cart_flag =False

    email = request.session.get('email')
    if email:
        user_obj = user.objects.filter(email=email).first()
        if user_obj:
            wishlist_flag = Wishlist.objects.filter(user=user_obj, product=product_obj).exists()

    return render(request, 'product-details.html', {'product': product_obj, 'wishlist_flag': wishlist_flag})

def seller_edit_product(request, pk):
    product_obj = product.objects.get(pk=pk)
    if request.method == "POST":
        product_obj.product_name = request.POST['product_name']
        product_obj.product_price = request.POST['product_price']
        product_obj.product_desc = request.POST['product_desc']
        product_obj.product_catagory = request.POST['product_catagory']
        try:
            product_obj.product_image = request.FILES['product_image'] 
        except:
            pass
        product_obj.save()
        messages.success(request, "Product updated successfully")
        return render(request, 'seller-edit-product.html', {'product': product_obj})
    else:
         return render(request, 'seller-edit-product.html', {'product': product_obj})


def seller_delete_product(request, pk):
    product_obj = product.objects.get(pk=pk)
    product_obj.delete()
    messages.success(request, "Product deleted successfully")
    return redirect('seller-view-products')

def add_to_wishlist(request, pk):
    product_obj = product.objects.get(pk=pk)
    user_obj = user.objects.get(email=request.session['email'])
    Wishlist.objects.get_or_create(user=user_obj, product=product_obj)
    request.session['wishlist_count'] = update_wishlist_count(user_obj)
    return redirect('wishlist')


def wishlist(request):
    user_obj = user.objects.get(email=request.session['email'])
    wishlist_items = Wishlist.objects.filter(user=user_obj)
    request.session['wishlist_count'] = update_wishlist_count(user_obj)
    return render(request, 'wishlist.html', {'wishlist': wishlist_items})


def remove_from_wishlist(request, pk):
    product_obj = product.objects.get(pk=pk)
    user_obj = user.objects.get(email=request.session['email'])
    wishlist_item = Wishlist.objects.get(user=user_obj, product=product_obj)
    wishlist_item.delete()
    request.session['wishlist_count'] = update_wishlist_count(user_obj)
    return redirect('wishlist')


def add_to_cart(request, pk):
    if not request.session.get('email'):
        messages.warning(request, 'Please log in to add products to cart')
        return redirect('login')

    product_obj = product.objects.get(pk=pk)
    user_obj = user.objects.get(email=request.session['email'])
    cart_item, created = Cart.objects.get_or_create(
        user=user_obj,
        product=product_obj,
        defaults={
            'product_price': product_obj.product_price,
            'product_qty': 1,
            'total_price': product_obj.product_price,
        }
    )

    if not created:
        cart_item.product_qty += 1
        cart_item.total_price = cart_item.product_price * cart_item.product_qty
        cart_item.save()

    request.session['cart_count'] = update_cart_count(user_obj)
    messages.success(request, f'{product_obj.product_name} added to cart successfully')
    return redirect('cart')


def cart(request):
    if not request.session.get('email'):
        messages.warning(request, 'Please log in to view your cart')
        return redirect('login')

    user_obj = user.objects.get(email=request.session['email'])
    cart_items = Cart.objects.filter(user=user_obj).order_by('-date')
    total_amount = sum(item.total_price for item in cart_items)
    request.session['cart_count'] = update_cart_count(user_obj)
    
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'cart.html', context)


def update_cart_qty(request, pk, action):
    if not request.session.get('email'):
        messages.warning(request, 'Please log in to update cart quantity')
        return redirect('login')

    user_obj = user.objects.get(email=request.session['email'])
    cart_item = Cart.objects.get(user=user_obj, product_id=pk)

    if action == 'increase':
        cart_item.product_qty += 1
    elif action == 'decrease':
        cart_item.product_qty = max(1, cart_item.product_qty - 1)
    else:
        messages.error(request, 'Invalid cart action')
        return redirect('cart')

    cart_item.total_price = cart_item.product_price * cart_item.product_qty
    cart_item.save()
    request.session['cart_count'] = update_cart_count(user_obj)
    messages.success(request, f'Quantity updated for {cart_item.product.product_name}')
    return redirect('cart')


def remove_from_cart(request, pk):
    product_obj = product.objects.get(pk=pk)
    user_obj = user.objects.get(email=request.session['email'])
    cart_item = Cart.objects.get(user=user_obj, product=product_obj)
    cart_item.delete()
    request.session['cart_count'] = update_cart_count(user_obj)
    messages.success(request, f'{product_obj.product_name} removed from cart')
    return redirect('cart')


def checkout(request):
    """
    Display checkout page with cart items
    """
    try:
        if not request.session.get('email'):
            messages.warning(request, 'Please log in to checkout')
            return redirect('login')
        
        user_obj = user.objects.get(email=request.session['email'])
        cart_items = Cart.objects.filter(user=user_obj, payment_status=False)
        
        if not cart_items.exists():
            messages.warning(request, 'Your cart is empty')
            return redirect('cart')
        
        total_amount = sum(item.total_price for item in cart_items)
        
        context = {
            'cart_items': cart_items,
            'total_amount': total_amount,
            'user': user_obj,
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        }
        return render(request, 'checkout.html', context)
    except Exception as e:
        print(f"Error in checkout view: {str(e)}")
        messages.error(request, 'Error loading checkout page')
        return redirect('cart')


@csrf_exempt
@require_POST
def create_checkout_session(request):
    """
    Create a Stripe checkout session for payment
    """
    try:
        # Get the total amount from request
        data = json.loads(request.body)
        total_amount = float(data.get('total_amount', 0))
        
        if total_amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        
        # Get user details
        user_obj = user.objects.get(email=request.session['email'])
        user_cart = Cart.objects.filter(user=user_obj, payment_status=False)
        
        if not user_cart.exists():
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        
        # Create order record
        order = Order.objects.create(
            user=user_obj,
            total_amount=total_amount,
            order_status='pending'
        )
        
        # Prepare line items for Stripe
        line_items = []
        for cart_item in user_cart:
            line_items.append({
                'price_data': {
                    'currency': 'inr',
                    'unit_amount': int(float(cart_item.product_price) * 100),
                    'product_data': {
                        'name': cart_item.product.product_name,
                        'description': f'Qty: {cart_item.product_qty}',
                        'images': [request.build_absolute_uri(cart_item.product.product_image.url)] if cart_item.product.product_image else [],
                    },
                },
                'quantity': cart_item.product_qty,
            })
        
        # Create Stripe session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html/?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + '/cancel.html/',
            customer_email=user_obj.email,
            shipping_address_collection={
                'allowed_countries': ['IN'],
            },
            metadata={
                'order_id': order.id,
                'user_email': user_obj.email,
            }
        )
        
        # Save session ID to order
        order.stripe_session_id = session.id
        order.stripe_payment_intent = session.payment_intent
        order.save()
        
        return JsonResponse({
            'id': session.id,
            'order_id': order.id
        })
        
    except Exception as e:
        print(f"Error in create_checkout_session: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def success(request):
    """
    Handle successful payment
    """
    try:
        session_id = request.GET.get('session_id')
        user_obj = user.objects.get(email=request.session.get('email'))
        
        if session_id:
            # Retrieve session from Stripe to verify payment
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Update order status
            try:
                order = Order.objects.get(stripe_session_id=session_id)
                if session.payment_status == 'paid':
                    order.order_status = 'completed'
                    order.save()
                    
                    # Mark all cart items as paid
                    cart_items = Cart.objects.filter(user=user_obj, payment_status=False)
                    for cart_item in cart_items:
                        cart_item.payment_status = True
                        cart_item.save()
                    
                    # Update session cart count
                    request.session['cart_count'] = 0
                    
                    # Send confirmation email
                    send_payment_confirmation_email(user_obj, order)
                    
            except Order.DoesNotExist:
                print(f"Order not found for session {session_id}")
        
        context = {
            'message': 'Payment completed successfully!',
            'order_id': order.id if 'order' in locals() else None
        }
        return render(request, 'success.html', context)
        
    except Exception as e:
        print(f"Error in success view: {str(e)}")
        messages.error(request, 'Error processing your payment')
        return redirect('cart')


def cancel(request):
    """
    Handle cancelled payment
    """
    context = {
        'message': 'Payment was cancelled. Your cart items are still saved.'
    }
    return render(request, 'cancel.html', context)


def myorder(request):
    """
    Display user's completed orders
    """
    try:
        user_obj = user.objects.get(email=request.session.get('email'))
        
        # Get all completed orders for the user
        orders = Order.objects.filter(user=user_obj, order_status='completed')
        
        # Enrich orders with cart items
        orders_with_items = []
        for order in orders:
            cart_items = Cart.objects.filter(user=user_obj, payment_status=True, date__lte=order.created_at)
            orders_with_items.append({
                'order': order,
                'items': cart_items[:order.id]  # This is a simple approach
            })
        
        context = {
            'orders': orders,
            'total_orders': orders.count()
        }
        return render(request, 'myorder.html', context)
        
    except user.DoesNotExist:
        messages.warning(request, 'Please log in to view your orders')
        return redirect('login')
    except Exception as e:
        print(f"Error in myorder view: {str(e)}")
        messages.error(request, 'Error loading your orders')
        return render(request, 'index.html')


def send_payment_confirmation_email(user_obj, order):
    """
    Send payment confirmation email to user
    """
    try:
        subject = f'Order Confirmation - Order #{order.id}'
        message = f'''
Hello {user_obj.fname},

Your payment has been successfully processed!

Order Details:
- Order ID: {order.id}
- Total Amount: ₹{order.total_amount}
- Order Date: {order.created_at.strftime('%d-%m-%Y %H:%M:%S')}
- Status: {order.get_order_status_display()}

Your items will be delivered to:
{user_obj.address}
Mobile: {user_obj.mobile}

Thank you for shopping with us!

Best regards,
Fruitables Team
        '''
        email_from = settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, email_from, [user_obj.email], fail_silently=False)
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")