import subprocess
from django.conf import settings
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Path to your MJML templates directory
MJML_TEMPLATE_DIR = Path(settings.BASE_DIR) / 'communication' / 'templates' / 'mjml'

# Jinja2 environment for MJML templates
jinja_env = Environment(
    loader=FileSystemLoader(str(MJML_TEMPLATE_DIR)),
    autoescape=select_autoescape(['mjml', 'html', 'xml'])
)

def render_mjml_template(template_name: str, context: dict = {}) -> str:
    template_path = MJML_TEMPLATE_DIR / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"MJML template not found: {template_path}")

    # Render with Jinja2
    template = jinja_env.get_template(template_name)
    mjml_rendered = template.render(context)

    # Pipe the Jinja-rendered MJML to npx mjml
    result = subprocess.run(
        ['npx', 'mjml', '--stdin', '-s'],
        input=mjml_rendered,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8'
    )

    if result.returncode != 0:
        raise RuntimeError(f"MJML Render Error:\n{result.stderr}")

    return result.stdout