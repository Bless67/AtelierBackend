from rest_framework import serializers
from .models import Product, Cart, CartItem,  ProductImage, CustomerMessage


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.ReadOnlyField(source='image.url')
    thumbnail_url = serializers.ReadOnlyField()
    medium_url = serializers.ReadOnlyField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url',
                  'thumbnail_url', 'medium_url', 'alt_text']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", 'original_price', "stock",
                  "price", "category", "images"]


class SingleProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "original_price", "price", "category",
                  "description", "stock", "images"]


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']


class SingleCartItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = CartItem
        fields = ['id', 'quantity']


# serializers.py


class CustomerMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerMessage
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
