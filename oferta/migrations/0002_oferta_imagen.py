# Generated by Django 5.0.4 on 2024-10-31 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oferta', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='oferta',
            name='imagen',
            field=models.ImageField(blank=True, default='default_image.png', null=True, upload_to='ofertas/'),
        ),
    ]
