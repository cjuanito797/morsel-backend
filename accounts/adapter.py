from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_app(self, request, provider, client_id=None):
        host = request.get_host()

        try:
            site = Site.objects.get(domain=host)
        except Site.DoesNotExist:
            raise ImproperlyConfigured(f"[Adapter] No matching Site for domain: {host}")

        try:
            app = SocialApp.objects.get(provider=provider, sites=site)
            return app
        except SocialApp.DoesNotExist:
            # If nothing matched, fallback to ANY Google app
            try:
                fallback = SocialApp.objects.filter(provider=provider).first()
                if fallback:
                    return fallback
                raise ImproperlyConfigured(f"[Adapter] No SocialApp found for provider '{provider}'")
            except Exception as e:
                raise ImproperlyConfigured(f"[Adapter] Unexpected failure: {e}")