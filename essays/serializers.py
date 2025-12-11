from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Essay


class EssayListSerializer(serializers.ModelSerializer):
    """Serializer for essay list view"""
    user = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Essay
        fields = ['id', 'title', 'description', 'createdAt', 'user']
    
    def get_user(self, obj):
        """Return user information"""
        if obj.user:
            return {
                'id': obj.user.id,
                'name': obj.user.get_full_name() or obj.user.username
            }
        return {
            'id': None,
            'name': 'System'
        }


class EssayDetailSerializer(serializers.ModelSerializer):
    """Serializer for essay detail view"""
    user = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    
    class Meta:
        model = Essay
        fields = ['id', 'title', 'description', 'content', 'createdAt', 'updatedAt', 'user']
    
    def get_user(self, obj):
        """Return user information"""
        if obj.user:
            return {
                'id': obj.user.id,
                'name': obj.user.get_full_name() or obj.user.username
            }
        return {
            'id': None,
            'name': 'System'
        }


class EssayCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating essays"""
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Essay
        fields = ['id', 'title', 'description', 'content', 'createdAt', 'user']
    
    def create(self, validated_data):
        """Create essay - associated with authenticated user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        # NEVER allow user essays to be templates - force to False
        validated_data['is_template'] = False
        return super().create(validated_data)
    
    def get_user(self, obj):
        """Return user information"""
        if obj.user:
            return {
                'id': obj.user.id,
                'name': obj.user.get_full_name() or obj.user.username
            }
        return {
            'id': None,
            'name': 'System'
        }


class EssayUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating essays"""
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Essay
        fields = ['id', 'title', 'description', 'content', 'createdAt', 'updatedAt', 'user']
        read_only_fields = ['createdAt', 'updatedAt']
    
    def update(self, instance, validated_data):
        """Override update to ensure content is properly saved"""
        # Update all fields including content
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.content = validated_data.get('content', instance.content)
        
        # SAFETY: Never allow user essays to be marked as templates during update
        template_usernames = ['rakibul', 'miki', 'randall', 'seun', 'zeynep']
        if instance.user and instance.user.username not in template_usernames:
            instance.is_template = False
            
        instance.save()
        return instance
    
    def get_user(self, obj):
        """Return user information"""
        if obj.user:
            return {
                'id': obj.user.id,
                'name': obj.user.get_full_name() or obj.user.username
            }
        return {
            'id': None,
            'name': 'System'
        }

