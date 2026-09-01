from bs4 import BeautifulSoup

from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from wagtail.models import Page

from m4n_knowledge_platform.utils.markdown import html_to_markdown
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


def page_export_markdown(request, page_id):
    """
    Render a page as Markdown
    """
    page = get_object_or_404(Page, pk=page_id).specific

    if not page.live:
        raise Http404

    # Avoid protected pages to be printed
    for restriction in page.get_view_restrictions():
        if not restriction.accept_request(request):
            raise Http404

    response = page.serve(request)
    if hasattr(response, "render"):
        response.render()

    soup = BeautifulSoup(response.content, "html.parser")
    content_node = soup.find(id="page-export-content")

    if content_node is not None:
        for excluded in content_node.select("[data-export-exclude]"):
            excluded.decompose()

        for img in content_node.find_all("img"):
            if img.get("src"):
                img["src"] = request.build_absolute_uri(img["src"])

    body_markdown = html_to_markdown(content_node)

    source_url = request.build_absolute_uri(page.url or "/")
    # Add source
    markdown = f"Source: {source_url}\n\n{body_markdown}\n"

    markdown_response = HttpResponse(markdown, content_type="text/markdown; charset=utf-8")
    if request.GET.get("download"):
        markdown_response["Content-Disposition"] = f'attachment; filename="{page.slug}.md"'

    return markdown_response