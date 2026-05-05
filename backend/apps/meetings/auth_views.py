from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.meetings.models import Meeting, UserPreference

User = get_user_model()


def _get_email_notifications(user):
    try:
        return user.preferences.email_notifications
    except Exception:
        return True


def _user_payload(user):
    return {
        'id': user.id,
        'email': user.email,
        'name': (user.first_name or '').strip() or user.email.split('@')[0],
        'display_name': (user.first_name or '').strip() or user.email.split('@')[0],
        'email_notifications': _get_email_notifications(user),
    }


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Accept email + password; username in DB is the email string."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)
        self.fields['email'] = serializers.EmailField(write_only=True)

    def validate(self, attrs):
        data = super().validate({
            'username': attrs['email'],
            'password': attrs['password'],
        })
        data['user'] = _user_payload(self.user)
        return data


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    email = (request.data.get('email') or '').strip().lower()
    password = request.data.get('password') or ''
    # Accept 'username' OR 'name' for the display name (backward compatible)
    name = (request.data.get('username') or request.data.get('name') or '').strip()

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username__iexact=email).exists():
        return Response({'error': 'An account with this email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=name[:150],
    )
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': _user_payload(user),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user

    if request.method == 'PATCH':
        # Handle display_name update
        if 'display_name' in request.data:
            user.first_name = (request.data['display_name'] or '')[:150]
            user.save(update_fields=['first_name'])

        # Handle email_notifications update
        if 'email_notifications' in request.data:
            val = request.data['email_notifications']
            pref, _ = UserPreference.objects.get_or_create(user=user)
            pref.email_notifications = bool(val)
            pref.save(update_fields=['email_notifications'])

    # Build full profile payload with stats
    total_meetings = Meeting.objects.filter(owner=user).count()
    completed_meetings = Meeting.objects.filter(owner=user, status='completed').count()
    total_storage_bytes = (
        Meeting.objects.filter(owner=user).aggregate(total=Sum('file_size'))['total'] or 0
    )

    payload = _user_payload(user)
    payload.update({
        'total_meetings': total_meetings,
        'completed_meetings': completed_meetings,
        'total_storage_bytes': total_storage_bytes,
    })
    return Response(payload)
