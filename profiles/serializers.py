# h:\Django2\UNI-FINDER-GIT\backend\profiles\serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

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
