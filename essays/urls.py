from django.urls import path
from . import views
from .debug_views import debug_essays
from .fix_views import fix_my_essays

urlpatterns = [
    path('essays/', views.EssayListView.as_view(), name='essay-list'),
    path('essays/create/', views.EssayCreateView.as_view(), name='essay-create'),
    path('essays/<int:pk>/', views.EssayDetailView.as_view(), name='essay-detail'),
    path('essays/<int:pk>/update/', views.EssayUpdateView.as_view(), name='essay-update'),
    path('essays/<int:pk>/delete/', views.EssayDeleteView.as_view(), name='essay-delete'),
    path('essays/debug/', debug_essays, name='essay-debug'),
    path('essays/fix/', fix_my_essays, name='essay-fix'),
]

