from django.urls import path
from . import views

app_name = 'court'

urlpatterns = [
    # Case management URLs
    path('cases/', views.case_list, name='case_list'),
    path('cases/create/', views.case_create, name='case_create'),
    path('cases/templates/', views.case_templates, name='case_templates'),
    path('cases/<int:case_id>/', views.case_detail, name='case_detail'),
    path('cases/<int:case_id>/edit/', views.case_edit, name='case_edit'),
    path('cases/<int:case_id>/assign/', views.case_assign, name='case_assign'),
    path('cases/<int:case_id>/sentence/', views.case_sentence, name='case_sentence'),
    
    # Evidence management URLs
    path('cases/<int:case_id>/evidence/', views.evidence_list, name='evidence_list'),
    path('cases/<int:case_id>/evidence/add/', views.evidence_add, name='evidence_add'),
    path('evidence/<int:evidence_id>/', views.evidence_detail, name='evidence_detail'),
    
    # Hearing management URLs
    path('hearings/', views.hearing_list, name='hearing_list'),
    path('hearings/create/', views.hearing_create, name='hearing_create'),
    path('hearings/<int:hearing_id>/', views.hearing_detail, name='hearing_detail'),
    path('hearings/<int:hearing_id>/edit/', views.hearing_edit, name='hearing_edit'),
    
    # Report management URLs
    path('reports/', views.report_list, name='report_list'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),
    
    # AJAX endpoints
    path('api/judges/', views.get_judges, name='get_judges'),
    path('api/cases/<int:case_id>/status/', views.update_case_status, name='update_case_status'),
]

