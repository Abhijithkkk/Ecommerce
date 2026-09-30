from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
import stripe
from .models import Product
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt



@login_required(login_url='/login/')
def home(request):
    products = Product.objects.all()
    return render(request, 'home/home.html', {'products': products})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})

    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    request.session['cart'] = cart

    return redirect('cart')


def cart(request):
    cart_data = request.session.get('cart', {})

    cart_items = []
    total = 0

    for product_id, quantity in cart_data.items():
        product = get_object_or_404(Product, id=product_id)

        item_total = product.price * quantity
        total += item_total

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'item_total': item_total
        })

    return render(request, 'home/cart.html', {
        'cart_items': cart_items,
        'total': total
    })


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session['cart'] = cart

    return redirect('cart')

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            password=password
        )

        login(request, user)

        return redirect('home')

    return render(request, 'home/signup.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('home')

        return render(request, 'home/login.html', {
            'error': 'Invalid username or password'
        })

    return render(request, 'home/login.html')


def user_logout(request):
    logout(request)
    return redirect('home')


def create_order(request):
    cart_data = request.session.get('cart', {})

    if not cart_data:
        return redirect('cart')

    total = 0

    for product_id, quantity in cart_data.items():
        product = get_object_or_404(Product, id=product_id)
        total += product.price * quantity

    order = Order.objects.create(
        user=request.user,
        total_price=total
    )
    line_items = []

    for product_id, quantity in cart_data.items():
        product = get_object_or_404(Product, id=product_id)

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )

        line_items.append({
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': product.name,
                },
                'unit_amount': int(product.price * 100),
            },
            'quantity': quantity,
        })

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        client_reference_id=str(order.id),

        success_url='http://127.0.0.1:8000/orders/',
        cancel_url='http://127.0.0.1:8000/cart/',
       
    )

    request.session['cart'] = {}

    return redirect(checkout_session.url)


def orders(request):
    user_orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(
        request,
        'home/orders.html',
        {'orders': user_orders}
    )
stripe.api_key = settings.STRIPE_SECRET_KEY


def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        order_id = session.get('client_reference_id')

        if order_id:
            order = Order.objects.get(id=order_id)
            order.status = 'Paid'
            order.save()

    return HttpResponse(status=200)