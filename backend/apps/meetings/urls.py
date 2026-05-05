from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenRefreshView

from . import auth_views, views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('auth/register/', auth_views.register, name='auth-register'),
    path('auth/token/', auth_views.EmailTokenObtainPairView.as_view(), name='auth-token'),
    path('auth/token/refresh/', TokenRefreshView.as_view(permission_classes=[AllowAny]), name='auth-token-refresh'),
    path('auth/me/', auth_views.me, name='auth-me'),
    # Meetings
    path('meetings/', views.meeting_list, name='meeting-list'),
    path('meetings/<uuid:meeting_id>/', views.meeting_detail, name='meeting-detail'),
    path('meetings/<uuid:meeting_id>/transcript/', views.meeting_transcript, name='meeting-transcript'),
    path('meetings/<uuid:meeting_id>/summary/', views.meeting_summary, name='meeting-summary'),
    path('meetings/<uuid:meeting_id>/mom/', views.meeting_mom, name='meeting-mom'),
    path('meetings/<uuid:meeting_id>/pdf/', views.meeting_pdf, name='meeting-pdf'),

    # Upload
    path('upload/init/', views.upload_init, name='upload-init'),
    path('upload/chunk/', views.upload_chunk, name='upload-chunk'),
    path('upload/complete/', views.upload_complete, name='upload-complete'),
    path('upload/<uuid:session_id>/progress/', views.upload_progress, name='upload-progress'),

    # Public share (no auth)
    path('public/<uuid:token>/', views.public_meeting, name='public-meeting'),

    # Chat
    path('chat/', views.chat, name='chat'),

    # Dashboard + insights
    path('dashboard/', views.dashboard, name='dashboard'),
    path('action-items/', views.action_items_list, name='action-items-list'),
    path('action-items/<int:item_id>/', views.action_item_toggle, name='action-item-toggle'),
    path('trending-topics/', views.trending_topics, name='trending-topics'),
]
