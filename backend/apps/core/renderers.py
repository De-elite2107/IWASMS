from rest_framework.renderers import JSONRenderer
import json


class IWASMSRenderer(JSONRenderer):
    """Wrap all API responses in {data, meta, error} envelope."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None
        status_code = response.status_code if response else 200

        # If already wrapped (e.g. paginated), pass through
        if isinstance(data, dict) and 'data' in data and 'meta' in data:
            return super().render(data, accepted_media_type, renderer_context)

        if status_code >= 400:
            wrapped = {
                'data': None,
                'meta': {},
                'error': data,
            }
        else:
            wrapped = {
                'data': data,
                'meta': {},
                'error': None,
            }

        return super().render(wrapped, accepted_media_type, renderer_context)
