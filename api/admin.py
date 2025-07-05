from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Category,Product,Tag, Extras, Ingredient
# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

# Register the product model
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available', 'category', 'image')
    list_filter = ('available', 'category')
    search_fields = ('name', 'description')
    readonly_fields = ('image_preview',) # to show image preview if desired
    prepopulated_fields = {'slug': ('name',)} # automatically populate slug field from name

    # Preview the upload image within the admin interface
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="150" height="150" />')
        return "-"

    image_preview.short_description = 'Image Preview'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', )


@admin.register(Extras)
class ExtrasAdmin(admin.ModelAdmin):
    list_display = ('name', )

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', )