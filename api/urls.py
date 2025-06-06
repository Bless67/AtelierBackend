from django.urls import path
from . import views
urlpatterns = [
    path('products/', views.ProductView.as_view()),
    path("product/<int:id>/", views.SingleProductView.as_view()),
    path('cart/', views.CartView.as_view()),
    path('cart/<int:id>/', views.SingleCartView.as_view()),
    path('init-payment/', views.PayStackPaymentInitView.as_view()),
    path('verify-payment/<str:reference>',
         views.PayStackVerifyPaymentView.as_view()),
    path('check-orders', views.GuestOrderLookupView.as_view()),
    path('customer-message/', views.CustomerMessageView.as_view())
]
