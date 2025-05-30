# Generated by Django 5.0.4 on 2024-12-11 05:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('producto', '0003_producto_eliminado_producto_fecha_eliminacion_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='categoria',
            name='eliminado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='categoria',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='categoria',
            name='fecha_eliminacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='categoria',
            name='fecha_modificacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='categoria',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='categorias_creadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='categoria',
            name='usuario_eliminacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='categorias_eliminadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='categoria',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='categorias_modificadas', to=settings.AUTH_USER_MODEL),
        ),
    ]
