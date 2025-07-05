# utils/openai_image.py
import base64
import requests
from openai import OpenAI
from django.core.files.base import ContentFile
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_ingredient_image(ingredient_name):
    try:
        # Step 1: Create strong, explicit prompt
        prompt = (
            f"Create a highly realistic photo of {ingredient_name} in a small white ceramic bowl, "
            "top-down view, with even studio lighting and soft shadows. The texture should be appetizing "
            "and clearly visible, resembling a commercial food photo for a restaurant menu. "
            "Use a clean background and keep the food centered. Output with transparent background if possible."
        )

        # Step 2: Create image request (DALL·E 3 supports b64_json for direct handling)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            response_format="b64_json",
            n=1
        )

        image_b64 = response.data[0].b64_json
        if not image_b64:
            print(f"[OpenAI Image Error] Empty image returned for ingredient: {ingredient_name}")
            return None

        # Step 3: Convert to Django-friendly File
        image_data = base64.b64decode(image_b64)
        file_name = f"{ingredient_name.replace(' ', '_').lower()}.png"
        django_file = ContentFile(image_data, name=file_name)

        return django_file

    except Exception as e:
        print(f"[OpenAI Image Generation Error] Ingredient '{ingredient_name}' - {str(e)}")
        return None