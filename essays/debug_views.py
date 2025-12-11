from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Essay


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def debug_essays(request):
    """Debug view to check essay visibility for current user"""
    user = request.user
    
    # If POST request, fix user's essays
    if request.method == 'POST':
        user_template_essays = Essay.objects.filter(user=user, is_template=True)
        fixed_count = 0
        
        # Exclude seeded template users
        template_usernames = ['rakibul', 'miki', 'randall', 'seun', 'zeynep']
        if user.username not in template_usernames:
            for essay in user_template_essays:
                essay.is_template = False
                essay.save()
                fixed_count += 1
        
        return Response({
            'message': f'Fixed {fixed_count} essays for user {user.username}',
            'fixed_essays': [
                {
                    'id': essay.id,
                    'title': essay.title,
                    'now_template': essay.is_template,
                }
                for essay in user_template_essays
            ]
        })
    
    # GET request - show debug info
    user_essays = Essay.objects.filter(user=user)
    user_personal_essays = Essay.objects.filter(user=user, is_template=False)
    user_template_essays = Essay.objects.filter(user=user, is_template=True)
    
    # Get all essays in the system
    all_essays = Essay.objects.all()
    all_templates = Essay.objects.filter(is_template=True)
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
        'counts': {
            'user_essays_total': user_essays.count(),
            'user_personal_essays': user_personal_essays.count(),
            'user_template_essays': user_template_essays.count(),
            'all_essays_in_system': all_essays.count(),
            'all_templates_in_system': all_templates.count(),
        },
        'user_essays_all': [
            {
                'id': essay.id,
                'title': essay.title,
                'is_template': essay.is_template,
                'created_at': essay.created_at,
                'user_id': essay.user.id if essay.user else None,
                'user_username': essay.user.username if essay.user else None,
            }
            for essay in user_essays.order_by('-created_at')
        ],
        'api_endpoint_result': [
            {
                'id': essay.id,
                'title': essay.title,
                'is_template': essay.is_template,
                'created_at': essay.created_at,
                'user_id': essay.user.id if essay.user else None,
                'user_username': essay.user.username if essay.user else None,
            }
            for essay in Essay.objects.filter(user=user, is_template=False).order_by('-created_at')
        ],
        'instructions': {
            'problem': 'If you see essays in user_essays_all but not in api_endpoint_result, they are marked as templates',
            'solution': 'Send a POST request to this same endpoint to fix your essays'
        }
    })