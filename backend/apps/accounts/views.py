"""
Accounts app — JWT Auth views
"""
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'data': None, 'meta': {}, 'error': 'Username and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {'data': None, 'meta': {}, 'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'data': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
            },
            'meta': {},
            'error': None,
        })


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({'data': {'message': 'Logged out'}, 'meta': {}, 'error': None})


class MeView(APIView):
    def get(self, request):
        user = request.user
        return Response({
            'data': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'meta': {},
            'error': None,
        })
