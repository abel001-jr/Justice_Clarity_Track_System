from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import date, timedelta, datetime
import json

from .models import UserProfile, Notification, AuditLog


def csrf_failure_view(request, reason=""):
    """Custom CSRF failure view"""
    messages.error(request, f'CSRF verification failed: {reason}. Please try refreshing the page.')
    return redirect('login')


def test_csrf_view(request):
    """Test view to verify CSRF tokens are working"""
    if request.method == 'POST':
        return JsonResponse({'status': 'success', 'message': 'CSRF token is working'})
    return render(request, 'core/csrf_test.html')


def login_view(request):
    """User login view with enhanced security and logging"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Regenerate CSRF token after successful login
            from django.middleware.csrf import get_token
            get_token(request)
            
            # Log the login action
            AuditLog.objects.create(
                user=user,
                action='login',
                model_name='User',
                description=f'User {username} logged in',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Login successful!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    """User logout view with enhanced logging"""
    # Log the logout action
    AuditLog.objects.create(
        user=request.user,
        action='logout',
        model_name='User',
        description=f'User {request.user.username} logged out',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:login')


@login_required
def dashboard_view(request):
    """Main dashboard view - routes to role-specific dashboards with enhanced security"""
    try:
        user_profile = request.user.profile
        role = user_profile.role
        
        # Route to appropriate dashboard based on user role
        if role == 'clerk':
            return redirect('core:clerk_dashboard')
        elif role == 'judge':
            return redirect('core:judge_dashboard')
        elif role == 'prison_officer':
            return redirect('core:prison_officer_dashboard')
        else:
            messages.error(request, 'Invalid user role. Please contact administrator.')
            return redirect('core:login')
            
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found. Please contact administrator.')
        return redirect('core:login')


@login_required
def clerk_dashboard(request):
    """Enhanced Clerk dashboard view with comprehensive statistics and workflow data"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'clerk':
        messages.error(request, 'Access denied. Clerk role required.')
        return redirect('core:dashboard')
    
    from court.models import Case, CaseReport, Hearing
    from prison.models import Inmate, InmateReport
    
    # Calculate time periods
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Enhanced statistics for clerk workflow
    total_cases = Case.objects.count()
    pending_cases = Case.objects.filter(status='pending').count()
    assigned_cases = Case.objects.filter(status='assigned').count()
    completed_cases = Case.objects.filter(status='decided').count()
    
    # Recent activity statistics
    recent_cases_week = Case.objects.filter(filing_date__gte=week_ago).count()
    recent_cases_month = Case.objects.filter(filing_date__gte=month_ago).count()
    
    # Cases needing attention (pending for more than 30 days)
    cases_needing_attention = Case.objects.filter(
        status='pending',
        filing_date__lte=month_ago
    ).count()
    
    # Upcoming hearings
    upcoming_hearings = Hearing.objects.filter(
        scheduled_date__gte=today,
        is_completed=False,
        is_cancelled=False
    ).order_by('scheduled_date')[:5]
    
    # Total hearings today
    total_hearings_today = Hearing.objects.filter(scheduled_date=today).count()
    
    # Prison-related statistics for cross-department coordination
    total_inmates = Inmate.objects.filter(status='active').count()
    urgent_reports = InmateReport.objects.filter(priority='urgent', is_reviewed=False)[:5]
    upcoming_releases = Inmate.objects.filter(
        status='active',
        expected_release_date__isnull=False
    ).order_by('expected_release_date')[:5]
    
    # Workflow progress indicators
    workflow_stats = {
        'cases_filed_today': Case.objects.filter(filing_date=today).count(),
        'hearings_scheduled_today': Hearing.objects.filter(
            created_at__gte=timezone.make_aware(datetime.combine(today, datetime.min.time())),
            created_at__lt=timezone.make_aware(datetime.combine(today + timedelta(days=1), datetime.min.time()))
        ).count(),
        'reports_submitted_today': CaseReport.objects.filter(submission_date=today).count(),
        'cases_assigned_today': Case.objects.filter(assigned_date=today).count(),
    }
    
    context = {
        'user_role': 'clerk',
        'total_cases': total_cases,
        'pending_cases': pending_cases,
        'assigned_cases': assigned_cases,
        'completed_cases': completed_cases,
        'total_inmates': total_inmates,
        'recent_cases': Case.objects.order_by('-filing_date')[:5],
        'urgent_reports': urgent_reports,
        'notifications': Notification.objects.filter(recipient=request.user, is_read=False)[:10],
        'upcoming_releases': upcoming_releases,
        'recent_cases_week': recent_cases_week,
        'recent_cases_month': recent_cases_month,
        'upcoming_hearings': upcoming_hearings,
        'cases_needing_attention': cases_needing_attention,
        'total_hearings_today': total_hearings_today,
        'workflow_stats': workflow_stats,
        'case_status_distribution': {
            'pending': pending_cases,
            'assigned': assigned_cases,
            'in_progress': Case.objects.filter(status='in_progress').count(),
            'decided': completed_cases,
            'closed': Case.objects.filter(status='closed').count(),
        }
    }
    
    return render(request, 'core/clerk_dashboard.html', context)


@login_required
def judge_dashboard(request):
    """Enhanced Judge dashboard view with comprehensive case management data"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'judge':
        messages.error(request, 'Access denied. Judge role required.')
        return redirect('core:dashboard')
    
    from court.models import Case, CaseReport, Hearing, Evidence
    
    # Calculate time periods
    today = date.today()
    
    # Enhanced statistics for judge workflow
    assigned_cases = Case.objects.filter(assigned_judge=request.user).count()
    pending_decisions = Case.objects.filter(assigned_judge=request.user, status='in_progress').count()
    completed_cases = Case.objects.filter(assigned_judge=request.user, status='decided').count()
    sentencing_queue_count = Case.objects.filter(assigned_judge=request.user, status='in_progress').count()
    
    # Evidence review statistics
    pending_evidence = Evidence.objects.filter(
        case__assigned_judge=request.user,
        is_approved__isnull=True
    ).count()
    
    # Hearing management
    upcoming_hearings = Hearing.objects.filter(
        judge=request.user,
        is_completed=False,
        is_cancelled=False
    ).order_by('scheduled_date')[:5]
    
    # Today's hearings
    today_hearings = Hearing.objects.filter(
        judge=request.user,
        scheduled_date=today,
        is_completed=False
    )
    today_hearings_count = today_hearings.count()
    
    # Workflow progress indicators
    workflow_stats = {
        'assigned': assigned_cases,
        'review': Case.objects.filter(
            assigned_judge=request.user,
            status='in_progress'
        ).count(),
        'hearing': Hearing.objects.filter(
            judge=request.user,
            is_completed=False,
            is_cancelled=False
        ).count(),
        'decision': Case.objects.filter(
            assigned_judge=request.user,
            status='in_progress'
        ).count(),
        'report': CaseReport.objects.filter(
            submitted_by=request.user,
            submission_date__gte=timezone.make_aware(datetime.combine(today, datetime.min.time())),
            submission_date__lt=timezone.make_aware(datetime.combine(today + timedelta(days=1), datetime.min.time()))
        ).count(),
        'completed': completed_cases,
        'cases_reviewed_today': Case.objects.filter(
            assigned_judge=request.user,
            last_updated__gte=timezone.make_aware(datetime.combine(today, datetime.min.time())),
            last_updated__lt=timezone.make_aware(datetime.combine(today + timedelta(days=1), datetime.min.time()))
        ).count(),
        'evidence_reviewed_today': Evidence.objects.filter(
            case__assigned_judge=request.user,
            reviewed_date=today
        ).count(),
        'sentences_passed_today': Case.objects.filter(
            assigned_judge=request.user,
            status='decided',
            decision_date=today
        ).count(),
    }
    
    # Case priority distribution
    case_priority_distribution = {
        'high': Case.objects.filter(assigned_judge=request.user, priority='high').count(),
        'medium': Case.objects.filter(assigned_judge=request.user, priority='medium').count(),
        'low': Case.objects.filter(assigned_judge=request.user, priority='low').count(),
    }
    
    # Monthly statistics
    month_start = today.replace(day=1)
    monthly_stats = {
        'cases_completed': Case.objects.filter(
            assigned_judge=request.user,
            status='decided',
            decision_date__gte=month_start
        ).count(),
        'sentences_passed': Case.objects.filter(
            assigned_judge=request.user,
            status='decided',
            decision_date__gte=month_start
        ).count(),
        'hearings_conducted': Hearing.objects.filter(
            judge=request.user,
            is_completed=True,
            scheduled_date__gte=month_start
        ).count(),
        'reports_submitted': CaseReport.objects.filter(
            submitted_by=request.user,
            submission_date__gte=month_start
        ).count(),
    }
    
    # Recent activities (simplified for now)
    recent_activities = []
    
    context = {
        'user_role': 'judge',
        'assigned_cases': assigned_cases,
        'pending_decisions': pending_decisions,
        'completed_cases': completed_cases,
        'sentencing_queue_count': sentencing_queue_count,
        'pending_evidence': pending_evidence,
        'my_cases': Case.objects.filter(assigned_judge=request.user).order_by('-filing_date')[:10],
        'upcoming_hearings': upcoming_hearings,
        'today_hearings': today_hearings,
        'today_hearings_count': today_hearings_count,
        'notifications': Notification.objects.filter(recipient=request.user, is_read=False)[:10],
        'recent_reports': CaseReport.objects.filter(submitted_by=request.user).order_by('-submission_date')[:5],
        'workflow_stats': workflow_stats,
        'case_priority_distribution': case_priority_distribution,
        'case_status_distribution': {
            'pending': Case.objects.filter(assigned_judge=request.user, status='pending').count(),
            'in_progress': pending_decisions,
            'decided': completed_cases,
            'closed': Case.objects.filter(assigned_judge=request.user, status='closed').count(),
        },
        'monthly_stats': monthly_stats,
        'recent_activities': recent_activities
    }
    
    return render(request, 'core/judge_dashboard.html', context)


@login_required
def prison_officer_dashboard(request):
    """Enhanced Prison Officer dashboard view with comprehensive inmate management data"""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'prison_officer':
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    from prison.models import Inmate, InmateReport, InmateProgram, VisitorLog
    
    # Calculate time periods
    today = date.today()
    
    # Enhanced statistics for prison officer workflow
    total_inmates = Inmate.objects.filter(assigned_officer=request.user, status='active').count()
    active_inmates = Inmate.objects.filter(assigned_officer=request.user, status='active').count()
    medical_cases = Inmate.objects.filter(assigned_officer=request.user, status='active', medical_attention_required=True).count()
    disciplinary_cases = Inmate.objects.filter(assigned_officer=request.user, status='active', disciplinary_issues=True).count()
    
    # Report statistics
    reports_due = InmateReport.objects.filter(
        submitted_by=request.user,
        report_type='regular'
    ).count()
    urgent_reports = InmateReport.objects.filter(
        submitted_by=request.user,
        priority='urgent'
    ).count()
    pending_reports = InmateReport.objects.filter(
        submitted_by=request.user,
        status='pending'
    ).count()
    
    # Upcoming releases
    upcoming_releases = Inmate.objects.filter(
        assigned_officer=request.user,
        status='active',
        expected_release_date__lte=today + timedelta(days=7),
        expected_release_date__gte=today
    )
    upcoming_releases_count = upcoming_releases.count()
    
    # Program statistics
    active_programs = InmateProgram.objects.filter(
        inmate__assigned_officer=request.user,
        status='active'
    ).count()
    
    # Visitor statistics
    today_visitors = VisitorLog.objects.filter(
        inmate__assigned_officer=request.user,
        visit_date__gte=timezone.make_aware(datetime.combine(today, datetime.min.time())),
        visit_date__lt=timezone.make_aware(datetime.combine(today + timedelta(days=1), datetime.min.time()))
    ).count()
    
    # Workflow progress indicators
    workflow_stats = {
        'reports_submitted_today': InmateReport.objects.filter(
            submitted_by=request.user,
            submission_date=today
        ).count(),
        'visits_logged_today': today_visitors,
        'programs_updated_today': InmateProgram.objects.filter(
            inmate__assigned_officer=request.user,
            updated_at__gte=timezone.make_aware(datetime.combine(today, datetime.min.time())),
            updated_at__lt=timezone.make_aware(datetime.combine(today + timedelta(days=1), datetime.min.time()))
        ).count(),
        'inmates_checked_today': Inmate.objects.filter(
            assigned_officer=request.user,
            last_health_check=today
        ).count(),
    }
    
    # Inmate status distribution
    inmate_status_distribution = {
        'active': active_inmates,
        'medical': medical_cases,
        'disciplinary': disciplinary_cases,
        'protective_custody': Inmate.objects.filter(assigned_officer=request.user, status='active', protective_custody=True).count(),
    }
    
    context = {
        'user_role': 'prison_officer',
        'total_inmates': total_inmates,
        'active_inmates': active_inmates,
        'medical_cases': medical_cases,
        'disciplinary_cases': disciplinary_cases,
        'reports_due': reports_due,
        'urgent_reports': urgent_reports,
        'pending_reports': pending_reports,
        'upcoming_releases_count': upcoming_releases_count,
        'active_programs': active_programs,
        'today_visitors': today_visitors,
        'my_inmates': Inmate.objects.filter(assigned_officer=request.user, status='active')[:10],
        'upcoming_releases': upcoming_releases[:5],
        'recent_reports': InmateReport.objects.filter(submitted_by=request.user).order_by('-submission_date')[:5],
        'notifications': Notification.objects.filter(recipient=request.user, is_read=False)[:10],
        'workflow_stats': workflow_stats,
        'inmate_status_distribution': inmate_status_distribution,
        'report_status_distribution': {
            'pending': pending_reports,
            'reviewed': InmateReport.objects.filter(submitted_by=request.user, status='reviewed').count(),
            'approved': InmateReport.objects.filter(submitted_by=request.user, status='approved').count(),
            'rejected': InmateReport.objects.filter(submitted_by=request.user, status='rejected').count(),
        },
        # Additional context variables for template
        'new_inmates_week': Inmate.objects.filter(
            assigned_officer=request.user,
            admission_date__gte=today - timedelta(days=7)
        ).count(),
        'overdue_reports': InmateReport.objects.filter(
            submitted_by=request.user,
            priority='urgent',
            is_reviewed=False
        ).count(),
        'next_release_date': upcoming_releases.first().expected_release_date if upcoming_releases.exists() else None,
        # Workflow step counts
        'intake_count': Inmate.objects.filter(
            assigned_officer=request.user,
            admission_date__gte=today - timedelta(days=30)
        ).count(),
        'assessment_count': Inmate.objects.filter(
            assigned_officer=request.user,
            status='active',
            medical_attention_required=True
        ).count(),
        'program_count': active_programs,
        'monitoring_count': Inmate.objects.filter(
            assigned_officer=request.user,
            status='active',
            disciplinary_issues=True
        ).count(),
        'processing_count': Inmate.objects.filter(
            assigned_officer=request.user,
            status='active'
        ).count(),
        'release_count': Inmate.objects.filter(
            assigned_officer=request.user,
            status='released',
            actual_release_date__gte=today - timedelta(days=30)
        ).count(),
    }
    
    return render(request, 'core/prison_officer_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a notification as read with enhanced logging"""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.mark_as_read()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='read',
            model_name='Notification',
            object_id=notification.id,
            description=f'Notification "{notification.title}" marked as read',
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'})


@login_required
def get_notifications(request):
    """Get user notifications via AJAX with enhanced filtering"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:20]
    
    notifications_data = []
    unread_count = 0
    for notification in notifications:
        if not notification.is_read:
            unread_count += 1
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'priority': notification.priority,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count,
        'count': len(notifications_data)
    })


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def profile_view(request):
    """Enhanced user profile view with role-specific functionality"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            # Update user fields
            if 'first_name' in request.POST:
                request.user.first_name = request.POST['first_name']
            if 'last_name' in request.POST:
                request.user.last_name = request.POST['last_name']
            if 'email' in request.POST:
                request.user.email = request.POST['email']
            
            # Update profile fields
            if 'phone_number' in request.POST:
                profile.phone_number = request.POST['phone_number']
            if 'department' in request.POST:
                profile.department = request.POST['department']
            
            # Save both user and profile
            request.user.save()
            profile.save()
            
            # Log the profile update
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='UserProfile',
                object_id=profile.id,
                description=f'Profile updated by {request.user.username}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({'status': 'success', 'message': 'Profile updated successfully'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to update profile: {str(e)}'})
    
    # GET request - show profile with role-specific data
    context = {
        'profile': profile,
        'user': request.user,
        'user_role': profile.role
    }
    
    # Add role-specific context data
    if profile.role == 'judge':
        from court.models import Case, Hearing
        context.update({
            'total_cases_assigned': Case.objects.filter(assigned_judge=request.user).count(),
            'total_hearings_conducted': Hearing.objects.filter(judge=request.user, is_completed=True).count(),
            'recent_activity': Case.objects.filter(assigned_judge=request.user).order_by('-last_updated')[:5],
        })
    elif profile.role == 'clerk':
        from court.models import Case, Hearing
        context.update({
            'total_cases_processed': Case.objects.count(),
            'total_hearings_scheduled': Hearing.objects.count(),
            'recent_activity': Case.objects.order_by('-filing_date')[:5],
        })
    elif profile.role == 'prison_officer':
        from prison.models import Inmate, InmateReport
        context.update({
            'total_inmates_assigned': Inmate.objects.filter(assigned_officer=request.user, status='active').count(),
            'total_reports_submitted': InmateReport.objects.filter(submitted_by=request.user).count(),
            'recent_activity': InmateReport.objects.filter(submitted_by=request.user).order_by('-submission_date')[:5],
        })
    
    return render(request, 'core/profile.html', context)


@login_required
def get_dashboard_stats(request):
    """Get dashboard statistics via AJAX for real-time updates"""
    try:
        user_profile = request.user.profile
        role = user_profile.role
        today = date.today()
        
        if role == 'judge':
            from court.models import Case, Hearing, Evidence
            stats = {
                'assigned_cases': Case.objects.filter(assigned_judge=request.user).count(),
                'pending_decisions': Case.objects.filter(assigned_judge=request.user, status='in_progress').count(),
                'upcoming_hearings': Hearing.objects.filter(
                    judge=request.user,
                    is_completed=False,
                    is_cancelled=False
                ).count(),
                'pending_evidence': Evidence.objects.filter(
                    case__assigned_judge=request.user,
                    is_approved__isnull=True
                ).count(),
            }
        elif role == 'clerk':
            from court.models import Case, Hearing, CaseReport
            stats = {
                'total_cases': Case.objects.count(),
                'pending_cases': Case.objects.filter(status='pending').count(),
                'upcoming_hearings': Hearing.objects.filter(
                    scheduled_date__gte=today,
                    is_completed=False,
                    is_cancelled=False
                ).count(),
                'recent_reports': CaseReport.objects.filter(submission_date=today).count(),
            }
        elif role == 'prison_officer':
            from prison.models import Inmate, InmateReport
            stats = {
                'total_inmates': Inmate.objects.filter(assigned_officer=request.user, status='active').count(),
                'urgent_reports': InmateReport.objects.filter(
                    submitted_by=request.user,
                    priority='urgent',
                    is_reviewed=False
                ).count(),
                'upcoming_releases': Inmate.objects.filter(
                    assigned_officer=request.user,
                    status='active',
                    expected_release_date__lte=today + timedelta(days=7),
                    expected_release_date__gte=today
                ).count(),
            }
        else:
            stats = {}
        
        return JsonResponse({'status': 'success', 'stats': stats})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
