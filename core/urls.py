from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Role-specific dashboards
    path('clerk/', views.clerk_dashboard, name='clerk_dashboard'),
    path('judge/', views.judge_dashboard, name='judge_dashboard'),
    path('prison-officer/', views.prison_officer_dashboard, name='prison_officer_dashboard'),
    
    # AJAX endpoints
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # CSRF failure handling
    path('csrf-failure/', views.csrf_failure_view, name='csrf_failure'),
    path('test-csrf/', views.test_csrf_view, name='test_csrf'),
]

