from django.urls import path
from . import views

app_name = 'prison'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.prison_officer_dashboard, name='dashboard'),
    
    # Inmate management URLs
    path('inmates/', views.inmate_list, name='inmate_list'),
    path('inmates/create/', views.inmate_create, name='inmate_create'),
    path('inmates/<int:inmate_id>/', views.inmate_detail, name='inmate_detail'),
    path('inmates/<int:inmate_id>/edit/', views.inmate_edit, name='inmate_edit'),
    path('inmates/<int:inmate_id>/assign/', views.inmate_assign, name='inmate_assign'),
    
    # Report management URLs
    path('reports/', views.report_list, name='report_list'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),
    path('reports/<int:report_id>/review/', views.report_review, name='report_review'),
    path('inmates/<int:inmate_id>/reports/', views.inmate_reports, name='inmate_reports'),
    
    # Visitor management URLs
    path('visitors/', views.visitor_list, name='visitor_list'),
    path('visitors/create/', views.visitor_create, name='visitor_create'),
    path('visitors/<int:visitor_id>/', views.visitor_detail, name='visitor_detail'),
    path('inmates/<int:inmate_id>/visitors/', views.inmate_visitors, name='inmate_visitors'),
    
    # Program management URLs
    path('programs/', views.program_list, name='program_list'),
    path('programs/create/', views.program_create, name='program_create'),
    path('programs/<int:program_id>/', views.program_detail, name='program_detail'),
    path('programs/<int:program_id>/edit/', views.program_edit, name='program_edit'),
    path('inmates/<int:inmate_id>/programs/', views.inmate_programs, name='inmate_programs'),
    
    # Release management URLs
    path('releases/', views.release_list, name='release_list'),
    path('releases/create/', views.release_create, name='release_create'),
    path('releases/<int:release_id>/', views.release_detail, name='release_detail'),
    path('releases/<int:release_id>/edit/', views.release_edit, name='release_edit'),
    path('releases/upcoming/', views.upcoming_releases, name='upcoming_releases'),
    path('inmates/<int:inmate_id>/release/', views.inmate_release, name='inmate_release'),
    
    # Officer profile URLs
    path('profile/', views.officer_profile, name='officer_profile'),
    path('profile/edit/', views.officer_profile_edit, name='officer_profile_edit'),
    
    # AJAX endpoints
    path('api/inmates/search/', views.search_inmates, name='search_inmates'),
    path('api/reports/<int:report_id>/status/', views.update_report_status, name='update_report_status'),
]

