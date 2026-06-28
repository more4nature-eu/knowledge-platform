def get_newsletter_context(request):
    return {
        "newsletter_errors": request.session.pop("newsletter_errors", {}),
        "newsletter_global_error": request.session.pop("newsletter_global_error", {}),
        "newsletter_data": request.session.pop("newsletter_data", {}),
        "newsletter_success": request.session.pop("newsletter_success", None),
    }