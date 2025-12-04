"""
API endpoints for document uploads and management.

User Endpoints:
- GET /api/documents/categories/ - List available document categories
- GET /api/documents/ - List user's uploaded documents
- POST /api/documents/upload/ - Upload a single document
- POST /api/documents/bulk-upload/ - Upload multiple documents at once
- GET /api/documents/<id>/download/ - Download a specific document
- DELETE /api/documents/<id>/ - Delete a specific document
- GET/POST /api/documents/profile/ - Get/Update user's onboarding profile
- GET /api/documents/feedback/ - Get user's feedback

Admin Endpoints:
- GET /api/documents/admin/users/ - List all users with documents (searchable/filterable)
- GET /api/documents/admin/submissions/ - List all document submissions
- PATCH /api/documents/admin/submissions/<id>/ - Update document status
- POST /api/documents/admin/feedback/ - Send feedback to user
- POST /api/documents/admin/request/ - Request additional document from user
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count, Q, Max
from django.utils import timezone
from django.contrib.auth.models import User
import logging

from .models import (
    DocumentCategory, 
    DocumentSubmission, 
    DocumentSubmissionBatch,
    UserDocumentProfile,
    DocumentFeedback,
    DocumentRequest
)
from .serializers import (
    DocumentCategorySerializer,
    DocumentSubmissionSerializer,
    DocumentSubmissionAdminSerializer,
    DocumentSubmissionCreateSerializer,
    BulkDocumentUploadSerializer,
    DocumentSubmissionBatchSerializer,
    UserDocumentProfileSerializer,
    UserDocumentProfileCreateSerializer,
    DocumentFeedbackSerializer,
    DocumentFeedbackCreateSerializer,
    DocumentRequestSerializer,
    DocumentRequestCreateSerializer,
)

logger = logging.getLogger(__name__)


# Default document categories with their configurations
DEFAULT_DOCUMENT_CATEGORIES = {
    'high-school': [
        {
            'api_key': 'AcademicTranscripts',
            'name': 'Academic Transcripts/Records',
            'description': 'Official copies of your high school transcripts and certificates, including marks and grades',
            'required': True,
            'order': 1,
        },
        {
            'api_key': 'EnglishProficiency',
            'name': 'Proof of English Proficiency',
            'description': 'Scores from standardized language tests like IELTS or TOEFL (if applicable)',
            'required': False,
            'order': 2,
        },
        {
            'api_key': 'SOP',
            'name': 'Statement of Purpose / Personal Statement',
            'description': 'A well-written essay outlining your academic goals, reasons for choosing the course/university, and career aspirations',
            'required': True,
            'order': 3,
        },
        {
            'api_key': 'RecommendationLetter',
            'name': 'Letter of Recommendation (LOR)',
            'description': 'Academic reference from a teacher or counselor who can vouch for you',
            'required': True,
            'order': 4,
        },
        {
            'api_key': 'Passport',
            'name': 'Passport',
            'description': 'Copy of your valid passport (bio-data page)',
            'required': True,
            'order': 5,
        },
        {
            'api_key': 'Photo',
            'name': 'Passport-sized Photo (White Background)',
            'description': 'Recent passport-sized photograph with white background',
            'required': True,
            'order': 6,
        },
    ],
    'bachelor': [
        {
            'api_key': 'HighSchoolDiploma',
            'name': 'High School Diploma / School Leaving Certificate',
            'description': 'Proof that you have completed secondary education',
            'required': True,
            'order': 1,
        },
        {
            'api_key': 'OfficialTranscripts',
            'name': 'Official Academic Transcripts',
            'description': 'Detailed records showing subjects taken and grades received throughout your last few years of high school',
            'required': True,
            'order': 2,
        },
        {
            'api_key': 'Passport',
            'name': 'Passport',
            'description': 'Copy of your valid passport (bio-data page)',
            'required': True,
            'order': 3,
        },
        {
            'api_key': 'Photo',
            'name': 'Passport-Sized Photographs',
            'description': 'Recent photographs that meet specific application guidelines',
            'required': True,
            'order': 4,
        },
        {
            'api_key': 'SOP',
            'name': 'Personal Essay / Statement of Purpose',
            'description': 'A writing sample explaining your academic interests, career goals, and reasons for choosing the specific university and course',
            'required': True,
            'order': 5,
        },
        {
            'api_key': 'RecommendationLetter',
            'name': 'Letters of Recommendation (LOR)',
            'description': 'References from teachers or guidance counselors who can speak to your academic potential and character',
            'required': True,
            'order': 6,
        },
        {
            'api_key': 'StandardizedTestScores',
            'name': 'Standardized Test Scores',
            'description': 'Results from exams like SAT, ACT, A-Levels, or national university entrance exams (if required)',
            'required': False,
            'order': 7,
        },
        {
            'api_key': 'EnglishProficiency',
            'name': 'Proof of English Language Proficiency',
            'description': 'Scores from tests such as TOEFL, IELTS, or Duolingo English Test (if English is not your native language)',
            'required': False,
            'order': 8,
        },
        {
            'api_key': 'CV',
            'name': 'Curriculum Vitae (CV) / Resume',
            'description': 'A summary of your extracurricular activities, work experience, awards, and other accomplishments',
            'required': False,
            'order': 9,
        },
    ],
    'master': [
        {
            'api_key': 'OfficialTranscripts',
            'name': 'Official Academic Transcripts',
            'description': 'Records of all previous post-secondary education courses, including subjects taken and grades received',
            'required': True,
            'order': 1,
        },
        {
            'api_key': 'BachelorDegree',
            'name': "Bachelor's Degree Certificate/Diploma",
            'description': 'Proof of completion of your undergraduate degree',
            'required': True,
            'order': 2,
        },
        {
            'api_key': 'Passport',
            'name': 'Passport',
            'description': 'Copy of your valid passport (bio-data page)',
            'required': True,
            'order': 3,
        },
        {
            'api_key': 'SOP',
            'name': 'Statement of Purpose (SOP) / Personal Statement',
            'description': 'A critical essay outlining your motivation for pursuing the degree, relevant experience, academic interests, career goals, and why you are a good fit',
            'required': True,
            'order': 4,
        },
        {
            'api_key': 'RecommendationLetter1',
            'name': 'First Letter of Recommendation (LOR)',
            'description': 'Letter from a professor or employer familiar with your academic work',
            'required': True,
            'order': 5,
        },
        {
            'api_key': 'RecommendationLetter2',
            'name': 'Second Letter of Recommendation (LOR)',
            'description': 'Additional letter from a professor or employer who can comment on your potential for graduate studies',
            'required': True,
            'order': 6,
        },
        {
            'api_key': 'CV',
            'name': 'Curriculum Vitae (CV) / Resume',
            'description': 'A summary of your educational background, research experience, work history, publications, awards, and extracurricular activities',
            'required': True,
            'order': 7,
        },
        {
            'api_key': 'GRE_GMAT',
            'name': 'Standardized Test Scores (GRE/GMAT)',
            'description': 'Results from exams such as GRE or GMAT (if required by the program)',
            'required': False,
            'order': 8,
        },
        {
            'api_key': 'EnglishProficiency',
            'name': 'Proof of English Language Proficiency',
            'description': 'Scores from tests like IELTS or TOEFL (especially for international students from non-English-speaking countries)',
            'required': False,
            'order': 9,
        },
    ],
}


# ==================== USER ENDPOINTS ====================

class UserDocumentProfileView(APIView):
    """
    GET/POST /api/documents/profile/
    
    Get or update user's onboarding profile (study mode, field of study, etc.)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.document_profile
            serializer = UserDocumentProfileSerializer(profile)
            return Response(serializer.data)
        except UserDocumentProfile.DoesNotExist:
            return Response({
                'field_of_study': '',
                'highest_education': '',
                'applying_to': '',
                'phone_number': ''
            })

    def post(self, request):
        profile, created = UserDocumentProfile.objects.get_or_create(user=request.user)
        serializer = UserDocumentProfileCreateSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                UserDocumentProfileSerializer(profile).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentCategoryListView(APIView):
    """
    GET /api/documents/categories/
    
    Returns available document categories based on program type.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        program_type = request.query_params.get('program_type', 'master')
        
        if program_type not in ['high-school', 'bachelor', 'master']:
            return Response(
                {'error': 'Invalid program_type. Must be "high-school", "bachelor", or "master".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        categories = DocumentCategory.objects.filter(
            is_active=True,
            program_type__in=[program_type, 'all']
        ).order_by('order')
        
        if categories.exists():
            serializer = DocumentCategorySerializer(categories, many=True)
            return Response(serializer.data)
        
        default_categories = DEFAULT_DOCUMENT_CATEGORIES.get(program_type, [])
        return Response(default_categories)


class UserDocumentsView(APIView):
    """
    GET /api/documents/
    
    Returns all documents uploaded by the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        program_type = request.query_params.get('program_type')
        
        queryset = DocumentSubmission.objects.filter(user=request.user)
        
        if program_type:
            if program_type not in ['high-school', 'bachelor', 'master']:
                return Response(
                    {'error': 'Invalid program_type. Must be "high-school", "bachelor", or "master".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(program_type=program_type)
        
        serializer = DocumentSubmissionSerializer(
            queryset, 
            many=True, 
            context={'request': request}
        )
        
        missing_required = []
        if program_type:
            default_categories = DEFAULT_DOCUMENT_CATEGORIES.get(program_type, [])
            uploaded_keys = set(queryset.values_list('category_key', flat=True))
            for cat in default_categories:
                if cat['required'] and cat['api_key'] not in uploaded_keys:
                    missing_required.append(cat['api_key'])
        
        return Response({
            'documents': serializer.data,
            'missing_required': missing_required,
            'is_complete': len(missing_required) == 0
        })


class DocumentUploadView(APIView):
    """
    POST /api/documents/upload/
    
    Upload a single document.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DocumentSubmissionCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        program_type = serializer.validated_data['program_type']
        category_key = serializer.validated_data['category_key']
        file = serializer.validated_data['file']
        
        # Validate file size - max 1MB
        if file.size > 1 * 1024 * 1024:
            return Response(
                {'error': 'File size cannot exceed 1MB. Please compress your file and try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        category = DocumentCategory.objects.filter(api_key=category_key).first()
        
        try:
            existing = DocumentSubmission.objects.filter(
                user=request.user,
                program_type=program_type,
                category_key=category_key
            ).first()
            
            if existing:
                if existing.file:
                    existing.file.delete(save=False)
                
                existing.file = file
                existing.original_filename = file.name
                existing.file_size = file.size
                existing.content_type = file.content_type
                existing.category = category
                existing.status = 'pending'
                existing.save()
                
                submission = existing
                created = False
            else:
                submission = DocumentSubmission.objects.create(
                    user=request.user,
                    program_type=program_type,
                    category=category,
                    category_key=category_key,
                    original_filename=file.name,
                    file=file,
                    file_size=file.size,
                    content_type=file.content_type,
                )
                created = True
            
            response_serializer = DocumentSubmissionSerializer(
                submission, 
                context={'request': request}
            )
            
            return Response(
                {
                    'message': 'Document uploaded successfully',
                    'created': created,
                    'document': response_serializer.data
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to upload document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkDocumentUploadView(APIView):
    """
    POST /api/documents/bulk-upload/
    
    Upload multiple documents at once.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request):
        program_type = request.data.get('program_type')
        
        if not program_type or program_type not in ['high-school', 'bachelor', 'master']:
            return Response(
                {'error': 'Invalid or missing program_type. Must be "high-school", "bachelor", or "master".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_files = {}
        for key in request.FILES:
            if key != 'program_type':
                uploaded_files[key] = request.FILES[key]
        
        if not uploaded_files:
            return Response(
                {'error': 'No files provided for upload.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = {'success': [], 'errors': []}
        created_submissions = []
        
        for category_key, file in uploaded_files.items():
            try:
                # Validate file size - max 1MB per file
                if file.size > 1 * 1024 * 1024:
                    results['errors'].append({
                        'category_key': category_key,
                        'error': 'File size cannot exceed 1MB. Please compress your file and try again.'
                    })
                    continue
                
                allowed_types = [
                    'application/pdf',
                    'image/jpeg',
                    'image/png',
                    'image/gif',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                ]
                if file.content_type not in allowed_types:
                    results['errors'].append({
                        'category_key': category_key,
                        'error': 'Invalid file type. Allowed: PDF, JPEG, PNG, GIF, DOC, DOCX.'
                    })
                    continue
                
                category = DocumentCategory.objects.filter(api_key=category_key).first()
                
                existing = DocumentSubmission.objects.filter(
                    user=request.user,
                    program_type=program_type,
                    category_key=category_key
                ).first()
                
                if existing:
                    if existing.file:
                        existing.file.delete(save=False)
                    
                    existing.file = file
                    existing.original_filename = file.name
                    existing.file_size = file.size
                    existing.content_type = file.content_type
                    existing.category = category
                    existing.status = 'pending'
                    existing.save()
                    submission = existing
                else:
                    submission = DocumentSubmission.objects.create(
                        user=request.user,
                        program_type=program_type,
                        category=category,
                        category_key=category_key,
                        original_filename=file.name,
                        file=file,
                        file_size=file.size,
                        content_type=file.content_type,
                    )
                
                created_submissions.append(submission)
                results['success'].append({
                    'category_key': category_key,
                    'filename': file.name,
                    'id': submission.id
                })
                
            except Exception as e:
                logger.error(f"Error uploading {category_key}: {str(e)}", exc_info=True)
                results['errors'].append({
                    'category_key': category_key,
                    'error': str(e)
                })
        
        batch = None
        if created_submissions:
            batch = DocumentSubmissionBatch.objects.create(
                user=request.user,
                program_type=program_type,
            )
            batch.submissions.set(created_submissions)
            
            default_categories = DEFAULT_DOCUMENT_CATEGORIES.get(program_type, [])
            all_submissions = DocumentSubmission.objects.filter(
                user=request.user,
                program_type=program_type
            )
            uploaded_keys = set(all_submissions.values_list('category_key', flat=True))
            required_keys = {cat['api_key'] for cat in default_categories if cat['required']}
            batch.is_complete = required_keys.issubset(uploaded_keys)
            batch.save()
        
        return Response({
            'message': f"Processed {len(results['success'])} files successfully, {len(results['errors'])} errors.",
            'results': results,
            'batch_id': batch.id if batch else None,
            'is_complete': batch.is_complete if batch else False,
        }, status=status.HTTP_201_CREATED if results['success'] else status.HTTP_400_BAD_REQUEST)


class DocumentDownloadView(APIView):
    """
    GET /api/documents/<id>/download/
    
    Download a specific document.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Allow admin to download any document, users can only download their own
        if request.user.is_staff:
            submission = get_object_or_404(DocumentSubmission, pk=pk)
        else:
            submission = get_object_or_404(DocumentSubmission, pk=pk, user=request.user)
        
        if not submission.file:
            raise Http404("File not found")
        
        try:
            response = FileResponse(
                submission.file.open('rb'),
                content_type=submission.content_type or 'application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{submission.original_filename}"'
            return response
        except Exception as e:
            logger.error(f"Error downloading document {pk}: {str(e)}", exc_info=True)
            raise Http404("File not found")


class DocumentDeleteView(APIView):
    """
    DELETE /api/documents/<id>/
    
    Delete a specific document.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        # Allow admin to delete any document, users can only delete their own
        if request.user.is_staff:
            submission = get_object_or_404(DocumentSubmission, pk=pk)
        else:
            submission = get_object_or_404(DocumentSubmission, pk=pk, user=request.user)
        
        try:
            submission.delete()
            return Response(
                {'message': 'Document deleted successfully.'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f"Error deleting document {pk}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to delete document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserFeedbackView(APIView):
    """
    GET /api/documents/feedback/
    
    Get feedback for the authenticated user's documents.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        feedback = DocumentFeedback.objects.filter(user=request.user).order_by('-created_at')
        serializer = DocumentFeedbackSerializer(feedback, many=True)
        return Response(serializer.data)


class UserDocumentRequestsView(APIView):
    """
    GET /api/documents/requests/
    
    Get document requests for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = DocumentRequest.objects.filter(user=request.user).order_by('-created_at')
        serializer = DocumentRequestSerializer(requests, many=True)
        return Response(serializer.data)


# ==================== ADMIN ENDPOINTS ====================

class AdminUserDocumentListView(APIView):
    """
    GET /api/documents/admin/users/
    
    List all users with document profiles. Supports search and filtering.
    
    Query params:
    - search: Search by username, email, first name, last name, or phone
    - field_of_study: Filter by field of study
    - highest_education: Filter by highest education
    - applying_to: Filter by applying to level
    - document_complete: Filter by document completion status (true/false)
    - min_documents: Minimum number of uploaded documents
    - max_documents: Maximum number of uploaded documents
    - referred_by: Filter by referral code (4-digit code)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        search = request.query_params.get('search', '')
        field_of_study = request.query_params.get('field_of_study', '')
        highest_education = request.query_params.get('highest_education', '')
        applying_to = request.query_params.get('applying_to', '')
        document_complete = request.query_params.get('document_complete', '')
        min_documents = request.query_params.get('min_documents', '')
        max_documents = request.query_params.get('max_documents', '')
        referred_by = request.query_params.get('referred_by', '')
        
        # Get users who have document profiles or document submissions
        users = User.objects.filter(
            Q(document_profile__isnull=False) | Q(document_submissions__isnull=False)
        ).distinct()
        
        # Apply search filter
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(document_profile__phone_number__icontains=search)
            )
        
        # Apply profile filters
        if field_of_study:
            users = users.filter(document_profile__field_of_study=field_of_study)
        if highest_education:
            users = users.filter(document_profile__highest_education=highest_education)
        if applying_to:
            users = users.filter(document_profile__applying_to=applying_to)
        if referred_by:
            users = users.filter(profile__referred_by__iexact=referred_by)
        
        # Annotate with document stats
        users = users.annotate(
            total_documents=Count('document_submissions'),
            pending_documents=Count('document_submissions', filter=Q(document_submissions__status='pending')),
            approved_documents=Count('document_submissions', filter=Q(document_submissions__status='approved')),
            rejected_documents=Count('document_submissions', filter=Q(document_submissions__status='rejected')),
            last_upload=Max('document_submissions__uploaded_at')
        ).order_by('-last_upload')
        
        # Apply document count filters
        if min_documents:
            try:
                users = users.filter(total_documents__gte=int(min_documents))
            except ValueError:
                pass
        if max_documents:
            try:
                users = users.filter(total_documents__lte=int(max_documents))
            except ValueError:
                pass
        
        # Build response with completion percentage calculation
        results = []
        for user in users:
            # Get referred_by from user's profile (not document_profile)
            referred_by_code = ''
            try:
                if hasattr(user, 'profile') and user.profile:
                    referred_by_code = user.profile.referred_by or ''
            except Exception:
                pass
            
            try:
                profile = user.document_profile
                profile_data = {
                    'field_of_study': profile.get_field_of_study_display(),
                    'field_of_study_key': profile.field_of_study,
                    'highest_education': profile.get_highest_education_display(),
                    'highest_education_key': profile.highest_education,
                    'applying_to': profile.get_applying_to_display(),
                    'applying_to_key': profile.applying_to,
                    'phone_number': profile.phone_number,
                    'referred_by': referred_by_code,
                }
                user_applying_to = profile.applying_to
            except UserDocumentProfile.DoesNotExist:
                profile_data = {
                    'field_of_study': '',
                    'field_of_study_key': '',
                    'highest_education': '',
                    'highest_education_key': '',
                    'applying_to': '',
                    'applying_to_key': '',
                    'phone_number': '',
                    'referred_by': referred_by_code,
                }
                user_applying_to = None
            
            # Calculate document completion percentage
            completion_percentage = 0
            required_count = 0
            uploaded_required_count = 0
            
            if user_applying_to and user_applying_to in DEFAULT_DOCUMENT_CATEGORIES:
                default_categories = DEFAULT_DOCUMENT_CATEGORIES[user_applying_to]
                required_keys = [cat['api_key'] for cat in default_categories if cat['required']]
                required_count = len(required_keys)
                
                if required_count > 0:
                    # Get uploaded document keys for this user and program type
                    uploaded_keys = set(
                        DocumentSubmission.objects.filter(
                            user=user,
                            program_type=user_applying_to
                        ).values_list('category_key', flat=True)
                    )
                    uploaded_required_count = len([key for key in required_keys if key in uploaded_keys])
                    completion_percentage = round((uploaded_required_count / required_count) * 100)
            
            is_complete = completion_percentage == 100
            
            results.append({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                **profile_data,
                'total_documents': user.total_documents,
                'pending_documents': user.pending_documents,
                'approved_documents': user.approved_documents,
                'rejected_documents': user.rejected_documents,
                'last_upload': user.last_upload,
                'required_documents': required_count,
                'uploaded_required': uploaded_required_count,
                'completion_percentage': completion_percentage,
                'is_complete': is_complete,
            })
        
        # Filter by document completion after calculating
        if document_complete == 'true':
            results = [r for r in results if r['is_complete']]
        elif document_complete == 'false':
            results = [r for r in results if not r['is_complete']]
        
        # Get filter options for frontend
        filter_options = {
            'field_of_study': UserDocumentProfile.FIELD_OF_STUDY_CHOICES,
            'highest_education': UserDocumentProfile.EDUCATION_LEVEL_CHOICES,
            'applying_to': UserDocumentProfile.APPLYING_TO_CHOICES,
        }
        
        # Calculate stats
        complete_count = len([r for r in results if r['is_complete']])
        incomplete_count = len(results) - complete_count
        
        return Response({
            'users': results,
            'total_count': len(results),
            'complete_count': complete_count,
            'incomplete_count': incomplete_count,
            'filter_options': filter_options
        })


class AdminSubmissionListView(APIView):
    """
    GET /api/documents/admin/submissions/
    
    List all document submissions with filtering.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        status_filter = request.query_params.get('status')
        program_type = request.query_params.get('program_type')
        
        queryset = DocumentSubmission.objects.select_related('user', 'category', 'reviewed_by')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if program_type:
            queryset = queryset.filter(program_type=program_type)
        
        queryset = queryset.order_by('-uploaded_at')
        
        serializer = DocumentSubmissionAdminSerializer(
            queryset, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'submissions': serializer.data,
            'total_count': queryset.count()
        })


class AdminSubmissionDetailView(APIView):
    """
    GET/PATCH /api/documents/admin/submissions/<id>/
    
    Get or update a specific document submission.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        submission = get_object_or_404(DocumentSubmission, pk=pk)
        serializer = DocumentSubmissionAdminSerializer(submission, context={'request': request})
        
        # Also get feedback for this submission
        feedback = DocumentFeedback.objects.filter(submission=submission).order_by('-created_at')
        feedback_serializer = DocumentFeedbackSerializer(feedback, many=True)
        
        return Response({
            'submission': serializer.data,
            'feedback': feedback_serializer.data
        })

    def patch(self, request, pk):
        submission = get_object_or_404(DocumentSubmission, pk=pk)
        
        # Update allowed fields
        if 'status' in request.data:
            submission.status = request.data['status']
            submission.reviewed_by = request.user
            submission.reviewed_at = timezone.now()
        
        if 'admin_notes' in request.data:
            submission.admin_notes = request.data['admin_notes']
        
        submission.save()
        
        serializer = DocumentSubmissionAdminSerializer(submission, context={'request': request})
        return Response(serializer.data)


class AdminSendFeedbackView(APIView):
    """
    POST /api/documents/admin/feedback/
    
    Send feedback to a user about their documents.
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        data = request.data.copy()
        data['admin'] = request.user.id
        
        serializer = DocumentFeedbackCreateSerializer(data=data)
        if serializer.is_valid():
            feedback = serializer.save(admin=request.user)
            return Response(
                DocumentFeedbackSerializer(feedback).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminRequestDocumentView(APIView):
    """
    POST /api/documents/admin/request/
    
    Request an additional document from a user.
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = DocumentRequestCreateSerializer(data=request.data)
        if serializer.is_valid():
            doc_request = serializer.save(admin=request.user)
            return Response(
                DocumentRequestSerializer(doc_request).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminDocumentRequestListView(APIView):
    """
    GET /api/documents/admin/requests/
    
    List all document requests.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        status_filter = request.query_params.get('status')
        
        queryset = DocumentRequest.objects.select_related('user', 'admin')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        queryset = queryset.order_by('-created_at')
        
        serializer = DocumentRequestSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminDocumentStatsView(APIView):
    """
    GET /api/documents/admin/stats/
    
    Get document management statistics.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_submissions = DocumentSubmission.objects.count()
        pending = DocumentSubmission.objects.filter(status='pending').count()
        approved = DocumentSubmission.objects.filter(status='approved').count()
        rejected = DocumentSubmission.objects.filter(status='rejected').count()
        resubmit = DocumentSubmission.objects.filter(status='resubmit').count()
        
        total_users = User.objects.filter(document_submissions__isnull=False).distinct().count()
        users_with_complete = DocumentSubmissionBatch.objects.filter(is_complete=True).values('user').distinct().count()
        
        # Recent activity
        recent_submissions = DocumentSubmission.objects.order_by('-uploaded_at')[:5]
        recent_serializer = DocumentSubmissionSerializer(recent_submissions, many=True)
        
        return Response({
            'total_submissions': total_submissions,
            'by_status': {
                'pending': pending,
                'approved': approved,
                'rejected': rejected,
                'resubmit': resubmit,
            },
            'total_users': total_users,
            'users_with_complete_submissions': users_with_complete,
            'recent_submissions': recent_serializer.data,
        })


class DocumentBatchListView(APIView):
    """
    GET /api/documents/batches/
    
    List all document batches for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        batches = DocumentSubmissionBatch.objects.filter(
            user=request.user
        ).prefetch_related('submissions')
        
        serializer = DocumentSubmissionBatchSerializer(batches, many=True)
        return Response(serializer.data)
