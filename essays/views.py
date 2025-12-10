from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from .models import Essay
from .serializers import (
    EssayListSerializer, 
    EssayDetailSerializer, 
    EssayCreateSerializer,
    EssayUpdateSerializer
)


class EssayListView(generics.ListAPIView):
    """List essays - each user only sees their own essays"""
    serializer_class = EssayListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # User ID is automatically extracted from the JWT token (Authorization header)
        user = self.request.user
        print(f"📝 Fetching essays for user: {user.id} ({user.username})")
        
        # Filter essays by the authenticated user only
        queryset = Essay.objects.filter(user=user).select_related('user')
        print(f"📝 Found {queryset.count()} essays for user {user.id}")
        
        return queryset


class EssayCreateView(generics.CreateAPIView):
    """Create a new essay - associated with current user"""
    serializer_class = EssayCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Always associate essay with the current authenticated user
        serializer.save(user=self.request.user, is_template=False)


class EssayDetailView(generics.RetrieveAPIView):
    """Retrieve a specific essay - only owner can view"""
    serializer_class = EssayDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # User can only view their own essays
        return Essay.objects.filter(user=self.request.user)


class EssayUpdateView(generics.UpdateAPIView):
    """Update an essay - only owner can edit"""
    serializer_class = EssayUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # User can only update their own essays
        return Essay.objects.filter(user=self.request.user)


class EssayDeleteView(generics.DestroyAPIView):
    """Delete an essay - only owner can delete"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # User can only delete their own essays
        return Essay.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Essay deleted successfully'}, 
            status=status.HTTP_204_NO_CONTENT
        )

