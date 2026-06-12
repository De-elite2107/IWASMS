from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

    def get_paginated_response(self, data):
        from rest_framework.response import Response
        return Response({
            'data': data,
            'meta': {
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
            },
            'error': None,
        })
