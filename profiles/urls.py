# h:\Django2\UNI-FINDER-GIT\backend\profiles\urls.py
from django.urls import path
from .views import (
    ProfileView, 
    AgentRegisterView, 
    AgentDashboardView, 
    AgentLoginView,
    validate_referral_code,
    AgentManagerDashboardView,
    AgentManagerDetailView,
    AgentManagerMeView,
    AdminAgentListView,
    AdminAgentDetailView,
)

urlpatterns = [
    # User Profile
    path('profile/', ProfileView.as_view(), name='user-profile'),
    
    # Agent Endpoints
    path('agent/register/', AgentRegisterView.as_view(), name='agent-register'),
    path('agent/login/', AgentLoginView.as_view(), name='agent-login'),
    path('agent/dashboard/', AgentDashboardView.as_view(), name='agent-dashboard'),
    path('agent/validate-referral/', validate_referral_code, name='validate-referral-code'),
    
    # Agent Manager Endpoints
    path('agent-manager/dashboard/', AgentManagerDashboardView.as_view(), name='agent-manager-dashboard'),
    path('agent-manager/agents/<int:agent_id>/', AgentManagerDetailView.as_view(), name='agent-manager-detail'),
    path('agent-manager/me/', AgentManagerMeView.as_view(), name='agent-manager-me'),
    
    # Admin Agent Management
    path('admin/agents/', AdminAgentListView.as_view(), name='admin-agent-list'),
    path('admin/agents/<int:pk>/', AdminAgentDetailView.as_view(), name='admin-agent-detail'),
]
