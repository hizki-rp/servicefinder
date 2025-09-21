# h:\Django2\UNI-FINDER-GIT\backend\profiles\views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Profile
from .serializers import ProfileSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    # Add parsers to handle multipart form data for file uploads
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        # get_or_create is robust for users who might not have a profile yet
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile
