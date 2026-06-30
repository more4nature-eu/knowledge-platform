from django.contrib import messages
from django.shortcuts import redirect
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from m4n_knowledge_platform.utils.models import NewsletterSettings
from m4n_knowledge_platform.utils.services import subscribe_to_mailchimp

def mailchimp_newsletter_signup(request):
    if request.method == "POST":
        errors = {}

        name = request.POST.get("name")
        organization = request.POST.get("organization")
        email = request.POST.get("email", "").strip()

        if not email:
            errors["email"] = "Email is required"
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors["email"] = "Invalid email"

        if errors:
            request.session["newsletter_errors"] = errors
            request.session["newsletter_data"] = request.POST.dict()
            return redirect(request.META.get("HTTP_REFERER", "/"))

        try:
            newsletter_settings = NewsletterSettings.load(request_or_site=request)
            subscribe_to_mailchimp(
                {
                    "email": email,
                    "name": name,
                    "organization": organization,
                },
                newsletter_settings.newsletter_mailchimp_api_key,
                newsletter_settings.newsletter_mailchimp_audience_id,
            )

        except:
            request.session["newsletter_global_error"] = "An error occurred, try again later."
        else:
            request.session["newsletter_success"] = "Thanks for subscribing!"

    return redirect(request.META.get("HTTP_REFERER", "/"))