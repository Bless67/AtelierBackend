# Generated by Django 5.1.7 on 2025-06-05 13:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_remove_product_image_productimage'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productimage',
            name='image',
        ),
    ]
