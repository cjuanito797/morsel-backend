import os
from django.conf import settings
from django.template import Template, Context
from django.core.mail import EmailMultiAlternatives
from communication.utils.email_renderer import render_mjml_template
