from django.db import models
from django.contrib.auth.models import User
from PIL import Image

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


class Product(models.Model):
    CATEGORY_CHOICES = (('Kids', 'Kids'), ('Women', 'Women'), ('Men', 'Men'))
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(decimal_places=2, default=0, max_digits=10)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=20)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.name}'


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='image', blank=True)

    # This is your generated square thumbnail
    thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFill(300, 300)],
        format='JPEG',
        options={'quality': 85}
    )


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


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    )

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tx_ref = models.CharField(max_length=255, unique=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer_email} - {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    quantity = models.PositiveIntegerField(default=1)


class CustomerMessage(models.Model):
    name = models.CharField(max_length=30)
    email = models.EmailField(max_length=30)
    message = models.TextField()

    def __str__(self):
        return f"{self.name}"
