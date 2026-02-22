from typing import Optional

from django.http import HttpRequest, HttpResponse
from rest_framework import permissions, status
from rest_framework.views import APIView

from consts.responses import Responses


class NotFoundViews(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request: HttpRequest, format: Optional[str] = None) -> HttpResponse:
        return Responses.get_response(Responses.GENERAL.NOT_FOUND)
