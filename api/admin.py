from django.contrib import admin
from .models import Product, Cart, CartItem,  ProductImage, CustomerMessage
from django.utils.html import format_html


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview', 'thumbnail_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"

    def thumbnail_preview(self, obj):
        if obj.image:
            thumbnail_url = obj.thumbnail_url
            if thumbnail_url:
                return format_html(
                    '<img src="{}" width="80" height="80" style="object-fit: cover;" />',
                    thumbnail_url
                )
        return "No thumbnail"
    thumbnail_preview.short_description = "Thumbnail"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]

    def image_count(self, obj):
        return obj.images.count()
    image_count.short_description = "Images"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview',
                    'thumbnail_preview', 'created_at']
    list_filter = ['product', 'created_at']
    readonly_fields = ('image_preview', 'thumbnail_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="200" height="200" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Image Preview"

    def thumbnail_preview(self, obj):
        if obj.image:
            thumbnail_url = obj.thumbnail_url
            if thumbnail_url:
                return format_html(
                    '<img src="{}" width="150" height="150" style="object-fit: cover;" />',
                    thumbnail_url
                )
        return "No thumbnail"
    thumbnail_preview.short_description = "Thumbnail Preview"


admin.site.register(Cart)
admin.site.register(CartItem)

admin.site.register(CustomerMessage)
