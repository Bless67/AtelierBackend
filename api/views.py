from .models import Order
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Product, Order, OrderItem, CustomerMessage
from .serializers import CartItemSerializer, ProductSerializer, SingleProductSerializer, SingleCartItemSerializer, CustomerMessageSerializer, OrderSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.mail import send_mail, BadHeaderError
from django.core.exceptions import ImproperlyConfigured
from smtplib import SMTPAuthenticationError, SMTPConnectError, SMTPRecipientsRefused, SMTPException
from django_ratelimit.decorators import ratelimit
import requests
from django.core.mail import send_mail, EmailMessage
import uuid
import random
from django.core.cache import cache


class ProductView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        product = Product.objects.all()
        product_serializer = ProductSerializer(product, many=True)
        return Response(product_serializer.data, status=status.HTTP_200_OK)


class SingleProductView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({"message": "product is not found"}, status=status.HTTP_404_NOT_FOUND)
        product_serializer = SingleProductSerializer(product)
        return Response(product_serializer.data, status=status.HTTP_200_OK)


class CartView(APIView):
    def get_cart(self, request, temporary_user):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            cart, _ = Cart.objects.get_or_create(temporary_user=temporary_user)
        return cart

    def get(self, request):
        temporary_user = request.COOKIES.get('temporary_user')
        cart = self.get_cart(request, temporary_user)

        cart_items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(cart_items, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        temporary_user = request.COOKIES.get('temporary_user')
        cart = self.get_cart(request, temporary_user)

        product_id = request.data.get('productId')
        quantity = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response({'message': 'Cart item added successfully'}, status=status.HTTP_201_CREATED)

    def put(self, request):

        temporary_user = request.COOKIES.get('temporary_user')
        cart = self.get_cart(request, temporary_user)

        product_id = request.data.get('productId')
        new_quantity = int(request.data.get('quantity', 1))

        if new_quantity < 1:
            return Response({'error': 'Quantity must be at least 1'}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)
        cart_item = get_object_or_404(CartItem, cart=cart, product=product)

        cart_item.quantity = new_quantity
        cart_item.save()

        return Response({'message': 'Cart item quantity updated'}, status=status.HTTP_200_OK)

    def delete(self, request):
        temporary_user = request.COOKIES.get('temporary_user')
        cart = self.get_cart(request, temporary_user)

        if cart is None:
            return Response({'error': 'Temporary user ID is missing'}, status=status.HTTP_400_BAD_REQUEST)

        product_id = request.query_params.get('productId')

        if not product_id:
            return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        CartItem.objects.filter(cart=cart, product=product).delete()

        serializer = CartItemSerializer(
            CartItem.objects.filter(cart=cart), many=True)
        return Response({'message': 'Item deleted successfully'}, status=status.HTTP_200_OK)


class SingleCartView(APIView):
    permission_classes = [AllowAny]

    def get_cart(self, request, temporary_user):
        if request.user.is_authenticated:
            cart = Cart.objects.get(user=request.user)
        else:
            cart = Cart.objects.get(temporary_user=temporary_user)
        return cart

    def get(self, request, id):
        temporary_user = request.COOKIES.get('temporary_user')

        try:
            cart = self.get_cart(request, temporary_user)
            product = Product.objects.get(id=id)
            cart_items = CartItem.objects.get(cart=cart, product=product)
            serializer = SingleCartItemSerializer(cart_items)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except:
            return Response({}, status=status.HTTP_200_OK)


class PayStackPaymentInitView(APIView):

    def post(self, request):
        customer_name = request.data.get('customer_name')
        customer_email = request.data.get('customer_email')
        customer_phone = request.data.get('customer_phone')
        cart = request.data.get('cart', [])

        if not all([customer_name, customer_email, customer_phone]):
            return Response({"error": "Missing customer details"}, status=status.HTTP_400_BAD_REQUEST)

        if not cart:
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
        if not cache.get(f"email_verified_{customer_email}"):
            return Response({"error": "Email not verified"}, status=403)

        tx_ref = f"tx-{uuid.uuid4().hex[:10]}"
        total_amount = 0

        # Calculate total and create order items
        try:
            order = Order.objects.create(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                amount=0,  # placeholder
                tx_ref=tx_ref,
                status='pending'
            )

            for item in cart:
                product_id = item['product']['id']
                quantity = item.get('quantity', 1)

                product = Product.objects.get(id=product_id)
                total_amount += product.price * quantity

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity
                )

            # Update the order with calculated total
            order.amount = total_amount
            order.save()

        except Product.DoesNotExist:
            order.delete()
            return Response({"error": "One or more products not found"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            order.delete()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Paystack expects amount in kobo
        amount_kobo = int(total_amount * 100)

        payload = {
            "email": customer_email,
            "amount": amount_kobo,
            "reference": tx_ref,
            "callback_url": settings.PAYSTACK_CALLBACK_URL,
        }

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{settings.PAYSTACK_BASE_URL}/transaction/initialize",
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                return Response({"payment_link": data['data']['authorization_url']})

        except:
            order.status = "Failed"
            order.save()
            return Response({"error": "Payment initialization failed"}, status=status.HTTP_400_BAD_REQUEST)


class PayStackVerifyPaymentView(APIView):

    def get(self, request, reference):
        if not reference:
            return Response({"error": "No reference provided"}, status=status.HTTP_400_BAD_REQUEST)

        temporary_user = request.COOKIES.get('temporary_user')
        if not temporary_user:
            return Response({"error": "Temporary user not identified"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
        }

        verify_url = f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}"
        response = requests.get(verify_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            data_json = data.get('data')

            if data_json and data_json.get('status') == 'success':
                try:
                    order = Order.objects.get(tx_ref=reference)
                    order.status = 'Paid'
                    order.transaction_id = data_json['id']
                    order.save()
                    cache.delete(f"email_verified_{order.customer_email}")
                    # Clear user's cart
                    cart = Cart.objects.get(temporary_user=temporary_user)
                    cart.delete()

                    return Response({"message": "Payment successful"}, status=status.HTTP_200_OK)

                except Order.DoesNotExist:
                    return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

                except Cart.DoesNotExist:
                    return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

            else:
                return Response({"error": "Payment was not successful"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            print(response.json())
            return Response({"error": "Failed to verify payment"}, status=status.HTTP_400_BAD_REQUEST)

# SEND verification_code


class SendVerificationCodeView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        # Rate limiting
        if cache.get(f"verification_code_cooldown_{email}"):
            return Response({"error": "Try again after 1 minute."}, status=429)

        verification_code = random.SystemRandom().randint(100000, 999999)
        cache.set(f"verification_code_{email}", verification_code, timeout=300)
        cache.set(f"verification_code_cooldown_{email}", True, timeout=60)

        try:
            # Test email configuration first
            from django.core.mail import get_connection
            connection = get_connection()
            connection.open()
            print("✅ Email connection successful")

            subject = 'Your Yabuwat Atelier Verification Code'
            from_email = settings.EMAIL_HOST_USER

            html_content = f"""
            <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;border:1px solid #ddd;padding:20px;">
                <h2 style="color:#2c3e50;">Yabuwat Atelier</h2>
                <p style="font-size:16px;">Hello,</p>
                <p style="font-size:16px;">
                    Your verification code is:
                    <strong style="font-size:24px;color:#2980b9;">{verification_code}</strong>
                </p>
                <p style="font-size:14px;color:#555;">
                    Please enter this code to complete your verification.
                </p>
                <p style="font-size:14px;color:#555;">
                    If you didn't request this, please ignore this email.
                </p>
                <p style="font-size:14px;color:#999;">Thank you,<br>Yabuwat Atelier Team</p>
            </div>
            """

            email_message = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=from_email,
                to=[email],
                connection=connection
            )
            email_message.content_subtype = "html"

            # Send the email
            result = email_message.send()
            print(f"✅ Email send result: {result}")

            connection.close()

        except SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication Error: {e}")
            return Response({"error": "Email authentication failed. Check email credentials."}, status=500)
        except SMTPRecipientsRefused as e:
            print(f"❌ SMTP Recipients Refused: {e}")
            return Response({"error": "Invalid recipient email address."}, status=400)
        except SMTPConnectError as e:
            print(f"❌ SMTP Connect Error: {e}")
            return Response({"error": "Cannot connect to email server."}, status=500)
        except SMTPException as e:
            print(f"❌ SMTP Error: {e}")
            return Response({"error": f"SMTP error: {str(e)}"}, status=500)
        except BadHeaderError as e:
            print(f"❌ Bad Header Error: {e}")
            return Response({"error": "Invalid email header"}, status=400)
        except ImproperlyConfigured as e:
            print(f"❌ Improperly Configured: {e}")
            return Response({"error": "Email not configured properly"}, status=500)
        except Exception as e:
            print(f"❌ General Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return Response({"error": f"Failed to send email: {str(e)}"}, status=500)

        return Response({"message": "verification code sent."}, status=200)
# VERIFY verification_code


class VerifyVerificationCodeView(APIView):
    def post(self, request):
        email = request.data.get("email")
        entered_verification_code = request.data.get("verification_code")

        if not email or not entered_verification_code:
            return Response({"error": "Missing fields"}, status=400)

        saved = cache.get(f"verification_code_{email}")
        if str(saved) == str(entered_verification_code):
            cache.set(f"email_verified_{email}", True, timeout=900)
            cache.delete(f"verification_code_{email}")
            return Response({"message": "Email verified"}, status=200)
        return Response({"error": "Invalid verification code"}, status=400)


class GuestOrderLookupView(APIView):
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        orders = Order.objects.filter(
            customer_email=email)

        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)


class CustomerMessageView(APIView):

    # @ratelimit(key="ip", rate="3/d", block=True)
    def post(self, request):

        serializer = CustomerMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Message sent successfully"}, status=status.HTTP_201_CREATED)
        return Response({"error": "Message not sent successfully"}, status=status.HTTP_400_BAD_REQUEST)


"""class MergeCartView(APIView):
    def post(self, request):
        
        if not request.user.is_authenticated:
            return Response({"error": "User must be logged in to merge cart"}, status=status.HTTP_400_BAD_REQUEST)

        temporary_user = request.COOKIES.get('temporary_user')
        if not temporary_user:
            return Response({"error": "No temporary cart found"}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve carts
        cart = Cart.objects.filter(temporary_user=temporary_user).first()
        if not cart:
            return Response({"error": "No temporary cart to merge"}, status=status.HTTP_400_BAD_REQUEST)

        user_cart, created = Cart.objects.get_or_create(user=request.user)

        try:
            with transaction.atomic():
                for item in cart.cartitem_set.all():  # << Corrected here
                    user_cart_item, created = CartItem.objects.get_or_create(
                        cart=user_cart,
                        product=item.product,
                        defaults={"quantity": item.quantity}
                    )
                    if not created:
                        user_cart_item.quantity += item.quantity
                        user_cart_item.save()

                cart.delete()

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Cart merged successfully"}, status=status.HTTP_200_OK)


class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            data = response.data
            access = data.get('access')
            refresh = data.get('refresh')

            if access and refresh:
                response.set_cookie(
                    key='access_token',
                    value=access,
                    httponly=True,
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
                )

                response.set_cookie(
                    key='refresh_token',
                    value=refresh,
                    httponly=True,
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
                )
                return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        request.data['refresh'] = refresh_token
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            data = response.data
            access = data['access']

            response.set_cookie(
                key='access_token',
                value=access,
                httponly=True,
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH']
            )
            return response


class LogoutView(APIView):
    def post(self, request):
        response = Response({'message': 'Logout successfull'},
                            status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


class GetUser(APIView):

    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            user_serializer = UserSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response()
"""
