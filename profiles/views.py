# h:\Django2\UNI-FINDER-GIT\backend\profiles\views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Profile, Agent
from .serializers import ProfileSerializer, AgentRegistrationSerializer, AgentDashboardSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    # Add parsers to handle multipart form data for file uploads
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        # get_or_create is robust for users who might not have a profile yet
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


# ==================== AGENT VIEWS ====================

class AgentRegisterView(generics.CreateAPIView):
    """
    Register a new agent account.
    POST /api/agent/register/
    """
    serializer_class = AgentRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = serializer.save()

        # Generate JWT tokens for the new agent
        refresh = RefreshToken.for_user(agent.user)
        
        # Add custom claims to the token
        refresh['username'] = agent.user.username
        refresh['is_staff'] = agent.user.is_staff
        refresh['groups'] = list(agent.user.groups.values_list('name', flat=True))
        refresh['first_name'] = agent.user.first_name
        refresh['last_name'] = agent.user.last_name
        refresh['is_agent'] = True

        return Response({
            'message': 'Agent registered successfully',
            'agent': {
                'id': agent.id,
                'username': agent.user.username,
                'first_name': agent.user.first_name,
                'last_name': agent.user.last_name,
                'referral_code': agent.referral_code,
                'referral_link': agent.get_referral_link()
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)


class AgentDashboardView(APIView):
    """
    Get agent dashboard data including referral link and count.
    GET /api/agent/dashboard/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            agent = Agent.objects.get(user=request.user)
        except Agent.DoesNotExist:
            return Response({
                'error': 'You are not registered as an agent.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Update referral count based on actual referrals
        actual_count = Profile.objects.filter(referred_by__iexact=agent.referral_code).count()
        if agent.referrals_count != actual_count:
            agent.referrals_count = actual_count
            agent.save(update_fields=['referrals_count'])

        serializer = AgentDashboardSerializer(agent)
        return Response(serializer.data)


class AgentLoginView(APIView):
    """
    Login endpoint specifically for agents.
    POST /api/agent/login/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate
        
        username = request.data.get('username', '').strip().lower()
        password = request.data.get('password', '')

        if not username or not password:
            return Response({
                'error': 'Username and password are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Try to authenticate
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(username__iexact=username)
            if not user.check_password(password):
                return Response({
                    'error': 'Invalid credentials.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid credentials.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Check if user is an agent
        try:
            agent = Agent.objects.get(user=user)
        except Agent.DoesNotExist:
            return Response({
                'error': 'This account is not registered as an agent.'
            }, status=status.HTTP_403_FORBIDDEN)

        if not agent.is_active:
            return Response({
                'error': 'This agent account has been deactivated.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        refresh['username'] = user.username
        refresh['is_staff'] = user.is_staff
        refresh['groups'] = list(user.groups.values_list('name', flat=True))
        refresh['first_name'] = user.first_name
        refresh['last_name'] = user.last_name
        refresh['is_agent'] = True

        return Response({
            'message': 'Login successful',
            'agent': {
                'id': agent.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'referral_code': agent.referral_code,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def validate_referral_code(request):
    """
    Validate if a referral code exists and is active.
    GET /api/agent/validate-referral/?code=AB1234
    """
    code = request.query_params.get('code', '').strip().upper()
    
    if not code:
        return Response({
            'valid': False,
            'message': 'No referral code provided.'
        })

    try:
        agent = Agent.objects.get(referral_code__iexact=code, is_active=True)
        return Response({
            'valid': True,
            'agent_name': f"{agent.user.first_name} {agent.user.last_name}",
            'message': f"Referral code is valid! Referred by {agent.user.first_name}."
        })
    except Agent.DoesNotExist:
        return Response({
            'valid': False,
            'message': 'Invalid referral code.'
        })
