from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Essay


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fix_my_essays(request):
    """Fix user's essays that were incorrectly marked as templates"""
    user = request.user
    
    # Don't fix seeded template users' essays
    template_usernames = ['rakibul', 'miki', 'randall', 'seun', 'zeynep']
    if user.username in template_usernames:
        return Response({
            'error': 'Cannot fix template user essays',
            'message': 'This user account contains template essays that should remain as templates'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Find user's essays that are marked as templates
    user_template_essays = Essay.objects.filter(user=user, is_template=True)
    fixed_count = 0
    fixed_essays = []
    
    for essay in user_template_essays:
        essay.is_template = False
        essay.save()
        fixed_count += 1
        fixed_essays.append({
            'id': essay.id,
            'title': essay.title,
            'created_at': essay.created_at
        })
    
    return Response({
        'success': True,
        'message': f'Successfully fixed {fixed_count} essays for {user.username}',
        'fixed_count': fixed_count,
        'fixed_essays': fixed_essays,
        'next_step': 'Refresh your essays page to see your essays'
    })