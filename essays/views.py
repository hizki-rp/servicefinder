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
    """List all essays"""
    serializer_class = EssayListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # Users can see all essays (or filter by user if needed)
        queryset = Essay.objects.all()
        
        # Optional: Filter by current user's essays only
        my_essays = self.request.query_params.get('my_essays', None)
        if my_essays == 'true':
            queryset = queryset.filter(user=self.request.user)
        
        return queryset.select_related('user')


class EssayCreateView(generics.CreateAPIView):
    """Create a new essay template"""
    serializer_class = EssayCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        # Set user if authenticated, otherwise None (for templates)
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user, is_template=True)


class EssayDetailView(generics.RetrieveAPIView):
    """Retrieve a specific essay - everyone can view"""
    queryset = Essay.objects.all()
    serializer_class = EssayDetailSerializer
    permission_classes = [permissions.AllowAny]


class EssayUpdateView(generics.UpdateAPIView):
    """Update an essay - everyone can edit templates"""
    queryset = Essay.objects.all()
    serializer_class = EssayUpdateSerializer
    permission_classes = [permissions.AllowAny]


class EssayDeleteView(generics.DestroyAPIView):
    """Delete an essay - everyone can delete templates"""
    queryset = Essay.objects.all()
    permission_classes = [permissions.AllowAny]
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Essay deleted successfully'}, 
            status=status.HTTP_204_NO_CONTENT
        )

