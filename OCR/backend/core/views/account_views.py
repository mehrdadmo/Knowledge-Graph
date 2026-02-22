from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout

from backend import settings
from consts.responses import Responses
from core.serializers import RegisterSerializer, LoginSerializer, UserSerializer


class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Responses.get_response(Responses.GENERAL.OK, {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        return Responses.get_response(Responses.GENERAL.WRONG_INPUTS)


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            username = data.get('username')
            password = data.get('password')

            if username and password:
                user = authenticate(username=username, password=password)
                if user:
                    if not user.is_active:
                        return Responses.get_response(Responses.ACCOUNT_GENERAL.DISABLED)
                else:
                    return Responses.get_response(Responses.ACCOUNT_GENERAL.INVALID_PASSWORD)
            else:
                return Responses.get_response(Responses.GENERAL.WRONG_INPUTS)

            # Optionally create session for DRF browsable API
            if settings.DEBUG:
                login(request, user)

            refresh = RefreshToken.for_user(user)
            return Responses.get_response(Responses.GENERAL.OK,{
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        return Responses.get_response(Responses.GENERAL.WRONG_INPUTS)


class LogoutView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            # Also logout session if exists
            logout(request)
            return Responses.get_response(Responses.GENERAL.OK)
        except Exception as e:
            return Responses.get_response(Responses.GENERAL.FORBIDDEN)


class ProfileView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Responses.get_response(Responses.GENERAL.OK, serializer.data)