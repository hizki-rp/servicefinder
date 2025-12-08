# h:\Django2\UNI-FINDER-GIT\backend\profiles\serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Profile, Agent

# A read-only serializer for the user to be nested in the profile GET response
class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')

class ProfileSerializer(serializers.ModelSerializer):
    # Use the read-only serializer for the 'user' field in GET responses
    user = UserDataSerializer(read_only=True)
    
    # Add write-only fields to accept flat data for user updates during PATCH
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Profile
        fields = ('user', 'bio', 'phone_number', 'profile_picture', 'preferred_intakes', 'first_name', 'last_name')
        read_only_fields = ('user',)

    def update(self, instance, validated_data):
        # The request is passed in the context by DRF's generic views
        request = self.context.get('request')
        user = instance.user

        # Update User model fields from the flat validated_data
        if 'first_name' in validated_data:
            user.first_name = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            user.last_name = validated_data.pop('last_name')
        user.save()

        # Handle clearing the profile picture from FormData
        if request and request.data.get('clear_profile_picture') == 'true':
            instance.profile_picture.delete(save=False)
            validated_data['profile_picture'] = None

        # Let super().update handle the regular Profile model fields
        return super().update(instance, validated_data)


# ==================== AGENT SERIALIZERS ====================

class AgentRegistrationSerializer(serializers.Serializer):
    """Serializer for agent registration - uses Serializer (not ModelSerializer) 
    since we're creating both User and Agent objects"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20)
    cbe_account_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_username(self, value):
        """Check for case-insensitive username uniqueness"""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already taken. Please choose another.")
        return value.lower()

    def create(self, validated_data):
        # Extract user-related fields
        username = validated_data.get('username')
        password = validated_data.get('password')
        first_name = validated_data.get('first_name')
        last_name = validated_data.get('last_name')
        phone_number = validated_data.get('phone_number')
        cbe_account_number = validated_data.get('cbe_account_number', '')

        # Create the User
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            # Agents don't require email for registration
            email=f"{username}@agent.addistemari.com"
        )

        # Add user to 'agent' group
        try:
            agent_group, created = Group.objects.get_or_create(name='agent')
            user.groups.add(agent_group)
        except Exception as e:
            pass

        # Create the Agent profile
        agent = Agent.objects.create(
            user=user,
            phone_number=phone_number,
            cbe_account_number=cbe_account_number if cbe_account_number else None
        )

        return agent


class AgentDashboardSerializer(serializers.ModelSerializer):
    """Serializer for agent dashboard data"""
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    referral_link = serializers.SerializerMethodField()
    referred_users = serializers.SerializerMethodField()
    total_registrations = serializers.SerializerMethodField()
    successful_referrals_count = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'phone_number', 'cbe_account_number', 'referral_code', 'referral_link',
            'referrals_count', 'total_registrations', 'successful_referrals_count',
            'referred_users', 'created_at', 'is_active'
        ]
        read_only_fields = ['id', 'referral_code', 'referrals_count', 'created_at']

    def get_referral_link(self, obj):
        return obj.get_referral_link()

    def get_total_registrations(self, obj):
        """Get total number of users who registered with this agent's referral code (paid and unpaid)"""
        return Profile.objects.filter(referred_by__iexact=obj.referral_code).count()

    def get_successful_referrals_count(self, obj):
        """Get count of successful referrals (users who paid)"""
        return obj.get_paid_referrals_count()

    def get_referred_users(self, obj):
        """
        Get list of users who registered using this agent's referral code
        with detailed payment and subscription status.
        """
        return obj.get_paid_referred_users()


class AdminAgentSerializer(serializers.ModelSerializer):
    """Serializer for admin agent management with detailed referral information"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    referral_link = serializers.SerializerMethodField()
    referred_users = serializers.SerializerMethodField()
    total_registrations = serializers.SerializerMethodField()
    successful_referrals_count = serializers.SerializerMethodField()
    cbe_account_number = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'cbe_account_number', 'referral_code', 'referral_link',
            'referrals_count', 'total_registrations', 'successful_referrals_count',
            'referred_users', 'created_at', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'referral_code', 'referrals_count', 'created_at']

    def get_referral_link(self, obj):
        try:
            return obj.get_referral_link()
        except Exception:
            return ""

    def get_cbe_account_number(self, obj):
        """Get CBE account number, handling case where field doesn't exist yet"""
        try:
            return obj.cbe_account_number or ""
        except AttributeError:
            return ""

    def get_total_registrations(self, obj):
        """Get total number of users who registered with this agent's referral code"""
        try:
            return Profile.objects.filter(referred_by__iexact=obj.referral_code).count()
        except Exception:
            return 0

    def get_successful_referrals_count(self, obj):
        """Get count of successful referrals (users who paid or have active subscription)"""
        try:
            return obj.get_paid_referrals_count()
        except Exception:
            return 0

    def get_referred_users(self, obj):
        """Get list of referred users with their status"""
        try:
            return obj.get_paid_referred_users()
        except Exception:
            return []
