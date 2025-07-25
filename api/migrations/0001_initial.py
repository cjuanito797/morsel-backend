# Generated by Django 5.2 on 2025-05-09 20:28

import django.core.files.storage
import django.db.models.deletion
import pathlib
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Extras',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('available', models.BooleanField(default=True)),
                ('image', models.ImageField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location=pathlib.PurePosixPath('/Users/home/Desktop/PyCharm/Morsel Pro/slip_jab_eats_backend/media')), upload_to='extras/')),
            ],
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('extra_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('available', models.BooleanField(default=True)),
                ('image', models.ImageField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location=pathlib.PurePosixPath('/Users/home/Desktop/PyCharm/Morsel Pro/slip_jab_eats_backend/media')), upload_to='ingredients/')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('available', models.BooleanField(default=True)),
                ('popular_with_catering', models.BooleanField(default=False)),
                ('image', models.ImageField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location=pathlib.PurePosixPath('/Users/home/Desktop/PyCharm/Morsel Pro/slip_jab_eats_backend/media')), upload_to='products/')),
                ('slug', models.SlugField(blank=True, max_length=150, unique=True)),
                ('purchase_count', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='api.category')),
                ('extras', models.ManyToManyField(blank=True, related_name='products', to='api.extras')),
                ('ingredients', models.ManyToManyField(blank=True, related_name='products', to='api.ingredient')),
                ('tags', models.ManyToManyField(blank=True, related_name='products', to='api.tag')),
            ],
        ),
    ]
