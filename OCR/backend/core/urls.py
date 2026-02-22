from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import NotFoundViews, OCRProcessView, ProfileView, \
    RegisterView, LoginView, LogoutView
from .views.compliance_views import ComplianceView, ReportView
from .views.hitl_views import HITLView

urlpatterns = [
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # OCR
    path('ocr/process/', OCRProcessView.as_view(), name='ocr_process'),
    path('hitl/', HITLView.as_view(), name='hitl'),
    path('compliance/', ComplianceView.as_view(), name='compliance'),
    path('report/', ReportView.as_view(), name='compliance'),
    # Everything Else
    re_path(r'^.*$', NotFoundViews.as_view()),
]
