from django.shortcuts import redirect

OPEN = ("/login", "/static/", "/favicon.ico")


class DemoLoginRequired:
    """Single Ministry user. The real system signs in with Microsoft Entra ID (OIDC);
    the prototype simulates that button and keeps a session flag."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith(OPEN) and not request.session.get("user"):
            return redirect("/login")
        return self.get_response(request)
