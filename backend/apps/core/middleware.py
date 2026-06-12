"""
Core middleware — Audit Logging

Logs significant user actions to the AuditLog table (FR-12).
"""
import logging

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Paths that trigger audit logging
AUDIT_PATHS = {
    '/api/v1/auth/login/': 'login',
    '/api/v1/auth/logout/': 'logout',
    '/api/v1/classify/': 'classify',
    '/api/v1/events/classify/': 'classify',
}


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Records significant API actions to the immutable AuditLog table.
    Only logs successful state-changing requests (POST, PUT, PATCH, DELETE).
    """

    def process_response(self, request, response):
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return response

        if response.status_code >= 400:
            return response

        path = request.path
        action = None

        # Check direct path matches
        for audit_path, audit_action in AUDIT_PATHS.items():
            if path == audit_path or path.rstrip('/') == audit_path.rstrip('/'):
                action = audit_action
                break

        # Check pattern-based paths
        if action is None:
            if '/alerts/' in path and '/resolve/' in path:
                action = 'alert_resolved'
            elif '/alerts/' in path and '/false-positive/' in path:
                action = 'alert_false_positive'
            elif '/models/' in path and '/retrain/' in path:
                action = 'model_retrain'
            elif '/export' in path:
                action = 'export'

        if action:
            try:
                from apps.core.models import AuditLog
                user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
                source_ip = self._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')

                AuditLog.objects.create(
                    user=user,
                    action=action,
                    resource_type=path,
                    detail={
                        'method': request.method,
                        'path': path,
                        'status_code': response.status_code,
                    },
                    source_ip=source_ip,
                    user_agent=user_agent[:500],
                )
            except Exception as e:
                logger.debug(f"Audit log write error: {e}")

        return response

    @staticmethod
    def _get_client_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
