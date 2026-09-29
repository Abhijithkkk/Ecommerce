from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('add-to-cart/<int:product_id>/',
         views.add_to_cart,
         name='add_to_cart'),

    path('cart/',
         views.cart,
         name='cart'),

    path('remove-from-cart/<int:product_id>/',
         views.remove_from_cart,
         name='remove_from_cart'),

path('signup/', views.signup, name='signup'),
path('login/', views.user_login, name='login'),
path('logout/', views.user_logout, name='logout'),
path('create-order/', views.create_order, name='create_order'),
path('orders/', views.orders, name='orders'),
path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
]