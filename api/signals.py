from django.dispatch import receiver
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from .models import ProductImage
import cloudinary.uploader
import cloudinary.api


@receiver(pre_delete, sender=ProductImage)
def delete_image_and_thumbnails(sender, instance, **kwargs):
    """Delete image and all its generated thumbnails from Cloudinary"""
    if instance.image:
        try:
            public_id = instance.image.public_id
            if public_id:
                # Delete the main image
                cloudinary.uploader.destroy(public_id)

                # Delete derived images (thumbnails) - optional
                # This deletes all transformations of this image
                cloudinary.api.delete_derived_resources([public_id])

                print(
                    f"Deleted image and thumbnails from Cloudinary: {public_id}")
        except Exception as e:
            print(f"Error deleting image from Cloudinary: {e}")
