"""Browser policy shared by settings and the isolated, third-party ReDoc view."""

from django.utils.csp import CSP

# Start in report-only mode; validate deployed pages before enforcing the policy.
DEFAULT_POLICY = {
    'default-src': [CSP.SELF],
    'base-uri': [CSP.SELF],
    'object-src': [CSP.NONE],
    'frame-ancestors': [CSP.NONE],
    'form-action': [CSP.SELF],
    'script-src': [CSP.SELF, CSP.NONCE],
    # Motion, Swagger, and admin widgets set inline styles. This does not allow
    # inline scripts or event handlers, and avoids weakening script-src.
    'style-src': [CSP.SELF, CSP.UNSAFE_INLINE],
    'img-src': [CSP.SELF, 'data:'],
    'font-src': [CSP.SELF],
    'connect-src': [CSP.SELF],
}

# Keep the official ReDoc template working without allowing its third-party
# scripts, fonts, or blob workers on the landing page, Swagger, or admin.
REDOC_POLICY = {
    **DEFAULT_POLICY,
    'script-src': [CSP.SELF, 'https://cdn.jsdelivr.net'],
    'style-src': [CSP.SELF, CSP.UNSAFE_INLINE, 'https://fonts.googleapis.com'],
    'font-src': [CSP.SELF, 'https://fonts.gstatic.com'],
    'img-src': [CSP.SELF, 'data:', 'https://cdn.redoc.ly'],
    'worker-src': [CSP.SELF, 'blob:'],
}
