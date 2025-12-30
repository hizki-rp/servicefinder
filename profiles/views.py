# h:\Django2\UNI-FINDER-GIT\backend\profiles\views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from .models import Profile, Agent
from .serializers import ProfileSerializer, AgentRegistrationSerializer, AgentDashboardSerializer, AdminAgentSerializer

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
    PUT /api/agent/dashboard/ - Update agent profile (CBE account, etc.)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            agent = Agent.objects.get(user=request.user)
        except Agent.DoesNotExist:
            return Response({
                'error': 'You are not registered as an agent.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Update referral count based on PAID referrals only
        # Only users who made successful payments count as real referrals
        paid_count = agent.get_paid_referrals_count()
        if agent.referrals_count != paid_count:
            agent.referrals_count = paid_count
            agent.save(update_fields=['referrals_count'])

        serializer = AgentDashboardSerializer(agent)
        return Response(serializer.data)
    
    def put(self, request):
        """Update agent profile information"""
        try:
            agent = Agent.objects.get(user=request.user)
        except Agent.DoesNotExist:
            return Response({
                'error': 'You are not registered as an agent.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Only allow updating specific fields
        allowed_fields = ['cbe_account_number', 'phone_number']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        if not update_data:
            return Response({
                'error': 'No valid fields to update'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the agent
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        agent.save(update_fields=list(update_data.keys()))
        
        serializer = AgentDashboardSerializer(agent)
        return Response({
            'message': 'Agent profile updated successfully',
            'data': serializer.data
        })


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


# ==================== AGENT MANAGER VIEWS ====================

class AgentManagerDashboardView(APIView):
    """
    Agent Manager dashboard - view all agents and their statistics.
    Only accessible by users in the 'Agent Manager' group.
    GET /api/agent-manager/dashboard/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.groups.filter(name='Agent Manager').exists():
            return Response({'error': 'Access denied. Agent Manager role required.'}, status=status.HTTP_403_FORBIDDEN)

        agents = Agent.objects.filter(is_active=True).select_related('user')
        total_agents = agents.count()

        referral_codes = list(agents.values_list('referral_code', flat=True))
        profiles_qs = Profile.objects.filter(referred_by__in=referral_codes).values('referred_by', 'user_id')
        code_to_users = {}
        for p in profiles_qs:
            code_to_users.setdefault(p['referred_by'], []).append(p['user_id'])

        all_user_ids = {p['user_id'] for p in profiles_qs}
        paid_user_ids = set()
        try:
            from payments.models import Payment
            paid_user_ids = set(Payment.objects.filter(user_id__in=all_user_ids, status='success').values_list('user_id', flat=True).distinct())
        except Exception:
            paid_user_ids = set()
        active_sub_user_ids = set()
        try:
            from universities.models import UserDashboard
            active_sub_user_ids = set(UserDashboard.objects.filter(user_id__in=all_user_ids, subscription_status='active').values_list('user_id', flat=True).distinct())
        except Exception:
            active_sub_user_ids = set()

        success_user_ids = paid_user_ids.union(active_sub_user_ids)

        agent_data = []
        total_successful_referrals = 0
        total_registrations = 0

        to_update = []
        for agent in agents:
            users_for_code = code_to_users.get(agent.referral_code, [])
            registration_count = len(users_for_code)
            successful_count = sum(1 for uid in users_for_code if uid in success_user_ids)

            if agent.referrals_count != successful_count:
                agent.referrals_count = successful_count
                to_update.append(agent)

            agent_info = {
                'id': agent.id,
                'username': agent.user.username,
                'first_name': agent.user.first_name,
                'last_name': agent.user.last_name,
                'email': agent.user.email,
                'phone_number': agent.phone_number,
                'referral_code': agent.referral_code,
                'referral_link': agent.get_referral_link(),
                'total_registrations': registration_count,
                'successful_referrals': successful_count,
                'has_cbe_account': bool(agent.cbe_account_number),
                'cbe_account_number': agent.cbe_account_number if agent.cbe_account_number else 'Not provided',
                'created_at': agent.created_at,
                'is_active': agent.is_active
            }

            agent_data.append(agent_info)
            total_successful_referrals += successful_count
            total_registrations += registration_count

        if to_update:
            Agent.objects.bulk_update(to_update, ['referrals_count'])

        agent_data.sort(key=lambda x: x['successful_referrals'], reverse=True)

        return Response({
            'summary': {
                'total_agents': total_agents,
                'total_successful_referrals': total_successful_referrals,
                'total_registrations': total_registrations,
                'average_successful_referrals_per_agent': round(total_successful_referrals / total_agents, 2) if total_agents > 0 else 0
            },
            'agents': agent_data
        })


class AgentManagerDetailView(APIView):
    """
    Agent Manager - view detailed information about a specific agent.
    GET /api/agent-manager/agents/<agent_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, agent_id):
        # Check if user is in Agent Manager group
        if not request.user.groups.filter(name='Agent Manager').exists():
            return Response({
                'error': 'Access denied. Agent Manager role required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            agent = Agent.objects.select_related('user').get(id=agent_id)
        except Agent.DoesNotExist:
            return Response({
                'error': 'Agent not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get detailed referral information
        referred_users = agent.get_paid_referred_users()
        
        return Response({
            'agent': {
                'id': agent.id,
                'username': agent.user.username,
                'first_name': agent.user.first_name,
                'last_name': agent.user.last_name,
                'email': agent.user.email,
                'phone_number': agent.phone_number,
                'cbe_account_number': agent.cbe_account_number,
                'referral_code': agent.referral_code,
                'referral_link': agent.get_referral_link(),
                'total_registrations': len(referred_users),
                'successful_referrals': agent.get_paid_referrals_count(),
                'created_at': agent.created_at,
                'is_active': agent.is_active
            },
            'referred_users': referred_users
        })


class AgentManagerMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.groups.filter(name='Agent Manager').exists():
            return Response({'error': 'Access denied. Agent Manager role required.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            agent = Agent.objects.get(user=request.user)
        except Agent.DoesNotExist:
            return Response({'error': 'You are not registered as an agent.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = AgentDashboardSerializer(agent)
        return Response(serializer.data)

    def put(self, request):
        if not request.user.groups.filter(name='Agent Manager').exists():
            return Response({'error': 'Access denied. Agent Manager role required.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            agent = Agent.objects.get(user=request.user)
        except Agent.DoesNotExist:
            return Response({'error': 'You are not registered as an agent.'}, status=status.HTTP_403_FORBIDDEN)
        allowed_fields = ['cbe_account_number', 'phone_number']
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        if not update_data:
            return Response({'error': 'No valid fields to update'}, status=status.HTTP_400_BAD_REQUEST)
        for field, value in update_data.items():
            setattr(agent, field, value)
        agent.save(update_fields=list(update_data.keys()))
        serializer = AgentDashboardSerializer(agent)
        return Response({'message': 'Agent profile updated successfully', 'data': serializer.data})

# ==================== ADMIN AGENT MANAGEMENT VIEWS ====================

class AdminAgentListView(APIView):
    """
    Admin endpoint to list all agents with their referral stats.
    GET /api/admin/agents/
    Supports filtering by:
    - search: Search by name, username, referral code
    - is_active: Filter by active status
    - sort_by: Sort by referrals_count, created_at, etc.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # Get query parameters
            search = request.query_params.get('search', '').strip()
            is_active = request.query_params.get('is_active', '')
            sort_by = request.query_params.get('sort_by', '-referrals_count')
            
            # Base queryset
            agents_qs = Agent.objects.select_related('user').all()
            
            # Apply search filter
            if search:
                agents_qs = agents_qs.filter(
                    Q(user__username__icontains=search) |
                    Q(user__first_name__icontains=search) |
                    Q(user__last_name__icontains=search) |
                    Q(referral_code__icontains=search) |
                    Q(phone_number__icontains=search)
                )
            
            # Apply active status filter
            if is_active.lower() == 'true':
                agents_qs = agents_qs.filter(is_active=True)
            elif is_active.lower() == 'false':
                agents_qs = agents_qs.filter(is_active=False)
            
            # Apply sorting
            valid_sort_fields = ['referrals_count', '-referrals_count', 'created_at', '-created_at', 
                               'user__username', '-user__username']
            if sort_by in valid_sort_fields:
                agents_qs = agents_qs.order_by(sort_by)
            else:
                agents_qs = agents_qs.order_by('-referrals_count')
            
            # Convert to list
            agents_list = list(agents_qs)
            
            # Build response data manually to avoid serializer issues
            agents_data = []
            total_successful = 0
            
            for agent in agents_list:
                try:
                    # Get referral counts
                    total_regs = Profile.objects.filter(referred_by__iexact=agent.referral_code).count()
                    successful_count = 0
                    referred_users_list = []
                    
                    try:
                        successful_count = agent.get_paid_referrals_count()
                        referred_users_list = agent.get_paid_referred_users()
                    except Exception as e:
                        print(f"Error getting referral data for agent {agent.id}: {e}")
                    
                    total_successful += successful_count
                    
                    # Get CBE account safely
                    cbe_account = ""
                    try:
                        cbe_account = agent.cbe_account_number or ""
                    except AttributeError:
                        pass
                    
                    agents_data.append({
                        'id': agent.id,
                        'username': agent.user.username,
                        'email': agent.user.email,
                        'first_name': agent.user.first_name,
                        'last_name': agent.user.last_name,
                        'phone_number': agent.phone_number or "",
                        'cbe_account_number': cbe_account,
                        'referral_code': agent.referral_code,
                        'referral_link': f"https://addistemari.com/register?ref={agent.referral_code}",
                        'referrals_count': agent.referrals_count,
                        'total_registrations': total_regs,
                        'successful_referrals_count': successful_count,
                        'referred_users': referred_users_list,
                        'created_at': agent.created_at.isoformat() if agent.created_at else None,
                        'is_active': agent.is_active,
                        'date_joined': agent.user.date_joined.isoformat() if agent.user.date_joined else None,
                    })
                except Exception as e:
                    print(f"Error processing agent {agent.id}: {e}")
                    continue
            
            # Calculate stats
            total_agents = Agent.objects.count()
            active_agents = Agent.objects.filter(is_active=True).count()
            
            # Only count registrations that match actual agent referral codes
            all_agent_codes = list(Agent.objects.values_list('referral_code', flat=True))
            # Case-insensitive matching
            total_registrations = 0
            for code in all_agent_codes:
                total_registrations += Profile.objects.filter(referred_by__iexact=code).count()
            
            return Response({
                'agents': agents_data,
                'stats': {
                    'total_agents': total_agents,
                    'active_agents': active_agents,
                    'total_successful_referrals': total_successful,
                    'total_registrations': total_registrations,
                }
            })
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"Error in AdminAgentListView: {error_msg}")
            print(traceback.format_exc())
            return Response({
                'error': error_msg,
                'detail': traceback.format_exc(),
                'agents': [],
                'stats': {
                    'total_agents': 0,
                    'active_agents': 0,
                    'total_successful_referrals': 0,
                    'total_registrations': 0,
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminAgentDetailView(APIView):
    """
    Admin endpoint to view/update a specific agent.
    GET /api/admin/agents/<id>/
    PATCH /api/admin/agents/<id>/
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            agent = Agent.objects.select_related('user').get(pk=pk)
        except Agent.DoesNotExist:
            return Response({'error': 'Agent not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update referral count
        paid_count = agent.get_paid_referrals_count()
        if agent.referrals_count != paid_count:
            agent.referrals_count = paid_count
            agent.save(update_fields=['referrals_count'])
        
        serializer = AdminAgentSerializer(agent)
        return Response(serializer.data)

    def patch(self, request, pk):
        try:
            agent = Agent.objects.select_related('user').get(pk=pk)
        except Agent.DoesNotExist:
            return Response({'error': 'Agent not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update allowed fields
        if 'is_active' in request.data:
            agent.is_active = request.data['is_active']
        if 'phone_number' in request.data:
            agent.phone_number = request.data['phone_number']
        if 'cbe_account_number' in request.data:
            agent.cbe_account_number = request.data['cbe_account_number']
        
        agent.save()
        
        serializer = AdminAgentSerializer(agent)
        return Response(serializer.data)
