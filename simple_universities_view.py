from django.http import JsonResponse
from universities.models import University

def simple_universities_view(request):
    try:
        universities = University.objects.all()
        data = []
        for uni in universities:
            data.append({
                'id': uni.id,
                'name': uni.name,
                'country': uni.country,
                'city': uni.city,
                'tuition_fee': float(uni.tuition_fee) if uni.tuition_fee else None
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)