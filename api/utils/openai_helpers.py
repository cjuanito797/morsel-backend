# utils/openai_helpers.py
from openai import OpenAI
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# utils/openai_helpers.py (continued)
def generate_product_description(product_name, ingredients=None):
    prompt = (
        f"You are writing a short, vivid, 1-paragraph food description for a menu item called '{product_name}'. "
        "Your description must be creative and persuasive, limited to 3 complete sentences. "
    )

    if ingredients:
        formatted = ", ".join(ingredients)
        prompt += (
            f"Only mention ingredients from this exact list: {formatted}. "
            "You are NOT allowed to invent or imply the presence of any other ingredients. "
            "If only one ingredient is listed, write descriptively about that one ingredient — do NOT fabricate others. "
            "Use 1–3 ingredients from the list in the description. "
        )
    else:
        prompt += "Do not mention any ingredients. Just describe the item in general terms."

    prompt += (
        "Do not trail off. Do not use ellipses or vague language. End with a confident, complete thought. "
        "You are not writing fiction — treat this as a real menu for a real business."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 if available for stricter compliance
            messages=[
                {"role": "system", "content": "You are a precise food copywriter who NEVER invents facts and follows strict instructions."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=250,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OpenAI Error] {e}")
        return None