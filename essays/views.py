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
        # Filter essays by the authenticated user only, exclude templates
        return Essay.objects.filter(
            user=self.request.user,
            is_template=False  # Only show user's personal essays, never templates
        ).select_related('user')


class EssayCreateView(generics.CreateAPIView):
    """Create a new essay - associated with current user"""
    serializer_class = EssayCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Always associate essay with the current authenticated user
        # NEVER allow user essays to be templates
        serializer.save(user=self.request.user, is_template=False)


class EssayDetailView(generics.RetrieveAPIView):
    """Retrieve a specific essay - only owner can view"""
    serializer_class = EssayDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # User can only view their own essays, exclude templates
        return Essay.objects.filter(
            user=self.request.user,
            is_template=False  # Only show user's personal essays
        )


class EssayUpdateView(generics.UpdateAPIView):
    """Update an essay - only owner can edit"""
    serializer_class = EssayUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # User can only update their own essays, exclude templates
        return Essay.objects.filter(
            user=self.request.user,
            is_template=False  # Only allow updating personal essays
        )


class EssayDeleteView(generics.DestroyAPIView):
    """Delete an essay - only owner can delete"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # User can only delete their own essays, exclude templates
        return Essay.objects.filter(
            user=self.request.user,
            is_template=False  # Only allow deleting personal essays
        )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Essay deleted successfully'}, 
            status=status.HTTP_204_NO_CONTENT
        )

