# Generated by Django 5.1.7 on 2025-06-09 05:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_product_original_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='customermessage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
