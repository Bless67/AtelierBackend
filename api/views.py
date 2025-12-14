from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Product, CustomerMessage
from .serializers import (
    CartItemSerializer,
    ProductSerializer,
    SingleProductSerializer,
    SingleCartItemSerializer,
    CustomerMessageSerializer
)
from rest_framework.permissions import AllowAny


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
        temporary_user = request.headers.get('X-Temporary-User')
        cart = self.get_cart(request, temporary_user)

        cart_items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(cart_items, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        temporary_user = request.headers.get('X-Temporary-User')
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
        temporary_user = request.headers.get('X-Temporary-User')
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
        temporary_user = request.headers.get('X-Temporary-User')
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
        temporary_user = request.headers.get('X-Temporary-User')

        try:
            cart = self.get_cart(request, temporary_user)
            product = Product.objects.get(id=id)
            cart_items = CartItem.objects.get(cart=cart, product=product)
            serializer = SingleCartItemSerializer(cart_items)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except:
            return Response({}, status=status.HTTP_200_OK)


class CustomerMessageView(APIView):
    def post(self, request):
        serializer = CustomerMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Message sent successfully"}, status=status.HTTP_201_CREATED)
        return Response({"error": "Message not sent successfully"}, status=status.HTTP_400_BAD_REQUEST)
