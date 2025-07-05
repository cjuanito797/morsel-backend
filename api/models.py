import random
import string
import os
from contextlib import nullcontext
from enum import unique

from django.utils.timezone import now
from django.utils import timezone
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage


# Use BASE_DIR from settings.py
product_image_storage = FileSystemStorage(location=settings.BASE_DIR / 'media/')
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Extras(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='extras/',
                              blank=True,
                              null=True,
                              storage=product_image_storage)

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    extra_price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='ingredients/',
                              blank=True,
                              null=True,
                              storage=product_image_storage)
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category,
                                 on_delete=models.CASCADE, related_name='products')
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')
    extras = models.ManyToManyField(Extras, blank=True, related_name='products')
    ingredients = models.ManyToManyField(Ingredient, blank=True, related_name='products')
    available = models.BooleanField(default=True)
    popular_with_catering = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        storage=product_image_storage
    )
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    purchase_count = models.PositiveIntegerField(default=0, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

