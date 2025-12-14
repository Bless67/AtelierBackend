from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from datetime import datetime
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from cloudinary.models import CloudinaryField


class Product(models.Model):
    CATEGORY_CHOICES = (('Kids', 'Kids'), ('Women', 'Women'), ('Men', 'Men'))
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    original_price = models.DecimalField(
        decimal_places=2, default=0, max_digits=10, null=True, blank=True)
    price = models.DecimalField(decimal_places=2, default=0, max_digits=10)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=20)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.name}'


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name='images', on_delete=models.CASCADE)
    image = CloudinaryField('image', help_text="Upload product image")
    alt_text = models.CharField(
        max_length=200, blank=True, help_text="Alternative text for accessibility")
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"

    @property
    def thumbnail_url(self):
        """Get thumbnail URL using Cloudinary transformations"""
        if self.image:
            return self.image.build_url(transformation=[
                {'width': 300, 'height': 300, 'crop': 'fill'},
                {'quality': 'auto'}
            ])
        return None

    @property
    def medium_url(self):
        """Get medium size URL"""
        if self.image:
            return self.image.build_url(transformation=[
                {'width': 600, 'height': 600, 'crop': 'limit'},
                {'quality': 'auto'}
            ])
        return None

    class Meta:
        ordering = ['-created_at']


class Cart(models.Model):
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL)
    temporary_user = models.CharField(max_length=100, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f'{self.temporary_user or self.user}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.cart}-{self.product.name}-{self.quantity}'


# models.py


class CustomerMessage(models.Model):
    name = models.CharField(max_length=30)
    email = models.EmailField(max_length=30)
    message = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Message from {self.name}"
