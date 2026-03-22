import logging

from django.contrib.auth import update_session_auth_hash
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    UpdateProfileSerializer,
)
from .services import register_user, create_organization_for_user
from core.utils import log_event, AuditEventType

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated = serializer.validated_data
        user = register_user(
            email=validated['email'],
            password=validated['password'],
            full_name=validated['full_name'],
        )

        org_name = validated.get('organization_name', '').strip()
        organization = None
        if org_name:
            organization, _ = create_organization_for_user(user, org_name)

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        log_event(user, AuditEventType.USER_REGISTERED, {'email': user.email})

        return Response(
            {
                'data': {
                    'user': UserSerializer(user).data,
                    'access': access,
                    'refresh': str(refresh),
                    'organization': {'id': str(organization.id), 'name': organization.name} if organization else None,
                },
                'message': 'Registration successful',
                'errors': None,
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Fetch full user data
            from rest_framework_simplejwt.tokens import AccessToken
            token = AccessToken(response.data['access'])
            user_id = token['user_id']
            try:
                user = User.objects.get(id=user_id)
                response.data['user'] = UserSerializer(user).data
                # Wrap in standard format
                return Response(
                    {
                        'data': {
                            'access': response.data['access'],
                            'refresh': response.data['refresh'],
                            'user': UserSerializer(user).data,
                        },
                        'message': 'Login successful',
                        'errors': None,
                    },
                    status=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                pass
        return Response(
            {'data': None, 'message': 'Invalid credentials', 'errors': response.data},
            status=response.status_code
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'data': None, 'message': 'Refresh token is required', 'errors': {'refresh': ['This field is required.']}},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response(
                {'data': None, 'message': 'Invalid token', 'errors': {'refresh': [str(e)]}},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'data': None, 'message': 'Logged out successfully', 'errors': None},
            status=status.HTTP_200_OK
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(
            {'data': serializer.data, 'message': None, 'errors': None},
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response(
            {'data': UserSerializer(request.user).data, 'message': 'Profile updated', 'errors': None},
            status=status.HTTP_200_OK
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'message': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'data': None, 'message': 'Current password is incorrect', 'errors': {'current_password': ['Incorrect password.']}},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Blacklist old tokens - user must re-login
        return Response(
            {'data': None, 'message': 'Password changed successfully. Please log in again.', 'errors': None},
            status=status.HTTP_200_OK
        )


class TokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return Response(
                {'data': {'access': response.data['access']}, 'message': 'Token refreshed', 'errors': None},
                status=status.HTTP_200_OK
            )
        return Response(
            {'data': None, 'message': 'Token refresh failed', 'errors': response.data},
            status=response.status_code
        )
