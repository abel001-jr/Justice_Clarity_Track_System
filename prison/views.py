from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime, date

from .models import Inmate, InmateReport, VisitorLog, InmateProgram


def check_role_access(request, required_roles):
    """Helper function to check if user has required role access"""
    if not hasattr(request.user, 'profile'):
        return False
    return request.user.profile.role in required_roles


@login_required
def prison_officer_dashboard(request):
    """Enhanced Prison Officer Dashboard with comprehensive statistics"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    user = request.user
    
    # Get assigned inmates for the current officer
    my_inmates = Inmate.objects.filter(assigned_officer=user, status='active').order_by('last_name', 'first_name')
    
    # Enhanced statistics for prison officer workflow
    total_inmates = my_inmates.count()
    active_inmates = my_inmates.count()
    medical_cases = my_inmates.filter(medical_attention_required=True).count()
    disciplinary_cases = my_inmates.filter(disciplinary_issues=True).count()
    
    # Report statistics
    reports_due = InmateReport.objects.filter(
        inmate__assigned_officer=user,
        is_reviewed=False
    ).count()
    urgent_reports = InmateReport.objects.filter(
        inmate__assigned_officer=user,
        priority='urgent',
        is_reviewed=False
    ).count()
    pending_reports = InmateReport.objects.filter(
        inmate__assigned_officer=user,
        status='pending'
    ).count()
    
    # Upcoming releases (within 7 days)
    upcoming_releases = Inmate.objects.filter(
        assigned_officer=user,
        status='active',
        expected_release_date__lte=date.today() + timedelta(days=7),
        expected_release_date__gte=date.today()
    ).order_by('expected_release_date')
    upcoming_releases_count = upcoming_releases.count()
    
    # Program statistics
    active_programs = InmateProgram.objects.filter(
        inmate__assigned_officer=user,
        status='active'
    ).count()
    
    # Visitor statistics
    today_visitors = VisitorLog.objects.filter(
        inmate__assigned_officer=user,
        visit_date__gte=timezone.make_aware(datetime.combine(date.today(), datetime.min.time())),
        visit_date__lt=timezone.make_aware(datetime.combine(date.today() + timedelta(days=1), datetime.min.time()))
    ).count()
    
    # Recent reports submitted by the officer
    recent_reports = InmateReport.objects.filter(
        submitted_by=user
    ).order_by('-submission_date')[:5]
    
    # Workflow progress indicators
    workflow_stats = {
        'reports_submitted_today': InmateReport.objects.filter(
            submitted_by=user,
            submission_date=date.today()
        ).count(),
        'visits_logged_today': today_visitors,
        'programs_updated_today': InmateProgram.objects.filter(
            inmate__assigned_officer=user,
            updated_at__gte=timezone.make_aware(datetime.combine(date.today(), datetime.min.time())),
            updated_at__lt=timezone.make_aware(datetime.combine(date.today() + timedelta(days=1), datetime.min.time()))
        ).count(),
        'inmates_checked_today': Inmate.objects.filter(
            assigned_officer=user,
            last_health_check=date.today()
        ).count(),
    }
    
    # Inmate status distribution
    inmate_status_distribution = {
        'active': active_inmates,
        'medical': medical_cases,
        'disciplinary': disciplinary_cases,
        'protective_custody': my_inmates.filter(protective_custody=True).count(),
    }
    
    context = {
        'user_role': 'prison_officer',
        'my_inmates': my_inmates,
        'upcoming_releases': upcoming_releases,
        'recent_reports': recent_reports,
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
        'workflow_stats': workflow_stats,
        'inmate_status_distribution': inmate_status_distribution,
        'report_status_distribution': {
            'pending': pending_reports,
            'reviewed': InmateReport.objects.filter(submitted_by=user, status='reviewed').count(),
            'approved': InmateReport.objects.filter(submitted_by=user, status='approved').count(),
            'rejected': InmateReport.objects.filter(submitted_by=user, status='rejected').count(),
        }
    }
    
    return render(request, 'core/prison_officer_dashboard.html', context)


@login_required
def inmate_list(request):
    """List all inmates with role-based filtering"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    # Role-based filtering - officers only see their assigned inmates
    inmates = Inmate.objects.filter(assigned_officer=request.user, status='active').order_by('last_name', 'first_name')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'medical':
            inmates = inmates.filter(medical_attention_required=True)
        elif status_filter == 'disciplinary':
            inmates = inmates.filter(disciplinary_issues=True)
        elif status_filter == 'protective':
            inmates = inmates.filter(protective_custody=True)
    
    # Filter by search query if provided
    search_query = request.GET.get('search')
    if search_query:
        inmates = inmates.filter(
            first_name__icontains=search_query
        ) | inmates.filter(
            last_name__icontains=search_query
        ) | inmates.filter(
            inmate_id__icontains=search_query
        )
    
    context = {
        'inmates': inmates,
        'user_role': request.user.profile.role,
        'total_inmates': inmates.count(),
        'medical_cases': inmates.filter(medical_attention_required=True).count(),
        'disciplinary_cases': inmates.filter(disciplinary_issues=True).count(),
        'protective_custody': inmates.filter(protective_custody=True).count(),
    }
    
    return render(request, 'prison/inmate_list.html', context)


@login_required
def inmate_create(request):
    """Create a new inmate record with enhanced validation"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            # Extract form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            date_of_birth = request.POST.get('date_of_birth')
            gender = request.POST.get('gender')
            inmate_id = request.POST.get('inmate_id')
            cell_number = request.POST.get('cell_number')
            admission_date = request.POST.get('admission_date')
            expected_release_date = request.POST.get('expected_release_date')
            crime_committed = request.POST.get('crime_committed')
            sentence_length = request.POST.get('sentence_length')
            medical_attention_required = request.POST.get('medical_attention_required') == 'on'
            disciplinary_issues = request.POST.get('disciplinary_issues') == 'on'
            protective_custody = request.POST.get('protective_custody') == 'on'
            
            # Contact information
            emergency_contact_name = request.POST.get('emergency_contact_name')
            emergency_contact_phone = request.POST.get('emergency_contact_phone')
            emergency_contact_relationship = request.POST.get('emergency_contact_relationship')
            
            # Validate required fields
            if not all([first_name, last_name, date_of_birth, gender, inmate_id, admission_date]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('prison:inmate_create')
            
            # Check if inmate ID already exists
            if Inmate.objects.filter(inmate_id=inmate_id).exists():
                messages.error(request, 'Inmate ID already exists.')
                return redirect('prison:inmate_create')
            
            # Parse dates
            try:
                dob_parsed = date.fromisoformat(date_of_birth)
                admission_date_parsed = date.fromisoformat(admission_date)
                expected_release_date_parsed = date.fromisoformat(expected_release_date) if expected_release_date else None
            except ValueError:
                messages.error(request, 'Invalid date format.')
                return redirect('prison:inmate_create')
            
            # Create inmate
            inmate = Inmate.objects.create(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob_parsed,
                gender=gender,
                inmate_id=inmate_id,
                cell_number=cell_number,
                admission_date=admission_date_parsed,
                expected_release_date=expected_release_date_parsed,
                crime_committed=crime_committed,
                sentence_length=sentence_length,
                medical_attention_required=medical_attention_required,
                disciplinary_issues=disciplinary_issues,
                protective_custody=protective_custody,
                emergency_contact_name=emergency_contact_name,
                emergency_contact_phone=emergency_contact_phone,
                emergency_contact_relationship=emergency_contact_relationship,
                assigned_officer=request.user,
                status='active'
            )
            
            messages.success(request, f'Inmate {inmate.get_full_name()} created successfully!')
            return redirect('prison:inmate_detail', inmate_id=inmate.id)
            
        except Exception as e:
            messages.error(request, f'Error creating inmate: {str(e)}')
            return redirect('prison:inmate_create')
    
    context = {
        'user_role': request.user.profile.role,
        'gender_choices': Inmate.GENDER_CHOICES,
    }
    
    return render(request, 'prison/inmate_create.html', context)


@login_required
def inmate_detail(request, inmate_id):
    """View inmate details with role-based access"""
    inmate = get_object_or_404(Inmate, id=inmate_id)
    
    # Check access permissions
    if inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. This inmate is not assigned to you.')
        return redirect('prison:inmate_list')
    
    # Get related data
    reports = inmate.reports.all().order_by('-submission_date')
    programs = inmate.programs.all().order_by('-start_date')
    visitors = inmate.visitor_logs.all().order_by('-visit_date')
    
    # Calculate inmate statistics
    inmate_stats = {
        'total_reports': reports.count(),
        'pending_reports': reports.filter(status='pending').count(),
        'total_programs': programs.count(),
        'active_programs': programs.filter(status='active').count(),
        'total_visits': visitors.count(),
        'days_until_release': (inmate.expected_release_date - date.today()).days if inmate.expected_release_date else None,
        'days_since_admission': (date.today() - inmate.admission_date).days,
    }
    
    context = {
        'inmate': inmate,
        'reports': reports[:5],
        'programs': programs[:5],
        'visitors': visitors[:5],
        'inmate_stats': inmate_stats,
        'user_role': request.user.profile.role,
        'can_edit': True,  # Assigned officer can edit
    }
    
    return render(request, 'prison/inmate_detail.html', context)


@login_required
def inmate_edit(request, inmate_id):
    """Edit inmate details with role-based permissions"""
    inmate = get_object_or_404(Inmate, id=inmate_id)
    
    # Check permissions
    if inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. You do not have permission to edit this inmate.')
        return redirect('prison:inmate_detail', inmate_id=inmate.id)
    
    if request.method == 'POST':
        try:
            # Update inmate fields
            inmate.first_name = request.POST.get('first_name', inmate.first_name)
            inmate.last_name = request.POST.get('last_name', inmate.last_name)
            inmate.cell_number = request.POST.get('cell_number', inmate.cell_number)
            inmate.expected_release_date = date.fromisoformat(request.POST.get('expected_release_date')) if request.POST.get('expected_release_date') else None
            inmate.medical_attention_required = request.POST.get('medical_attention_required') == 'on'
            inmate.disciplinary_issues = request.POST.get('disciplinary_issues') == 'on'
            inmate.protective_custody = request.POST.get('protective_custody') == 'on'
            inmate.emergency_contact_name = request.POST.get('emergency_contact_name', inmate.emergency_contact_name)
            inmate.emergency_contact_phone = request.POST.get('emergency_contact_phone', inmate.emergency_contact_phone)
            inmate.emergency_contact_relationship = request.POST.get('emergency_contact_relationship', inmate.emergency_contact_relationship)
            
            inmate.save()
            messages.success(request, 'Inmate record updated successfully!')
            return redirect('prison:inmate_detail', inmate_id=inmate.id)
            
        except Exception as e:
            messages.error(request, f'Error updating inmate: {str(e)}')
            return redirect('prison:inmate_edit', inmate_id=inmate.id)
    
    context = {
        'inmate': inmate,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/inmate_edit.html', context)


@login_required
def inmate_assign(request, inmate_id):
    """Assign officer to inmate with enhanced workflow"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    inmate = get_object_or_404(Inmate, id=inmate_id)
    
    if request.method == 'POST':
        try:
            assigned_officer_id = request.POST.get('assigned_officer')
            assignment_reason = request.POST.get('assignment_reason')
            assignment_type = request.POST.get('assignment_type')
            special_instructions = request.POST.get('special_instructions')
            
            if not assigned_officer_id:
                messages.error(request, 'Please select an officer to assign.')
                return redirect('prison:inmate_assign', inmate_id=inmate.id)
            
            # Get the officer
            try:
                assigned_officer = User.objects.get(id=assigned_officer_id, profile__role='prison_officer')
            except User.DoesNotExist:
                messages.error(request, 'Selected officer not found.')
                return redirect('prison:inmate_assign', inmate_id=inmate.id)
            
            # Update inmate assignment
            inmate.assigned_officer = assigned_officer
            inmate.assignment_date = date.today()
            inmate.assignment_reason = assignment_reason
            inmate.assignment_type = assignment_type
            inmate.special_instructions = special_instructions
            inmate.save()
            
            messages.success(request, f'Inmate assigned to Officer {assigned_officer.get_full_name()} successfully!')
            return redirect('prison:inmate_detail', inmate_id=inmate.id)
            
        except Exception as e:
            messages.error(request, f'Error assigning inmate: {str(e)}')
            return redirect('prison:inmate_assign', inmate_id=inmate.id)
    
    # Get available officers
    officers = User.objects.filter(profile__role='prison_officer').order_by('first_name', 'last_name')
    
    context = {
        'inmate': inmate,
        'officers': officers,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/inmate_assign.html', context)


@login_required
def report_list(request):
    """List all inmate reports with role-based filtering"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    # Role-based filtering - officers only see reports for their assigned inmates
    reports = InmateReport.objects.filter(inmate__assigned_officer=request.user).order_by('-submission_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    # Filter by priority if provided
    priority_filter = request.GET.get('priority')
    if priority_filter:
        reports = reports.filter(priority=priority_filter)
    
    # Filter by report type if provided
    report_type_filter = request.GET.get('report_type')
    if report_type_filter:
        reports = reports.filter(report_type=report_type_filter)
    
    context = {
        'reports': reports,
        'user_role': request.user.profile.role,
        'total_reports': reports.count(),
        'pending_reports': reports.filter(status='pending').count(),
        'urgent_reports': reports.filter(priority='urgent').count(),
        'approved_reports': reports.filter(status='approved').count(),
        'rejected_reports': reports.filter(status='rejected').count(),
    }
    
    return render(request, 'prison/report_list.html', context)


@login_required
def report_create(request):
    """Create a new inmate report with enhanced validation"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            inmate_id = request.POST.get('inmate_id')
            report_type = request.POST.get('report_type')
            title = request.POST.get('title')
            content = request.POST.get('content')
            priority = request.POST.get('priority')
            recommendations = request.POST.get('recommendations')
            incident_date = request.POST.get('incident_date')
            
            # Validate required fields
            if not all([inmate_id, report_type, title, content]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('prison:report_create')
            
            # Get inmate and check assignment
            inmate = get_object_or_404(Inmate, id=inmate_id)
            if inmate.assigned_officer != request.user:
                messages.error(request, 'You can only create reports for inmates assigned to you.')
                return redirect('prison:report_create')
            
            # Parse incident date if provided
            incident_date_parsed = None
            if incident_date:
                try:
                    incident_date_parsed = date.fromisoformat(incident_date)
                except ValueError:
                    messages.error(request, 'Invalid incident date format.')
                    return redirect('prison:report_create')
            
            # Create the report
            report = InmateReport.objects.create(
                inmate=inmate,
                report_type=report_type,
                title=title,
                content=content,
                priority=priority,
                recommendations=recommendations,
                incident_date=incident_date_parsed,
                submitted_by=request.user
            )
            
            messages.success(request, f'Report "{title}" submitted successfully for {inmate.get_full_name()}.')
            return redirect('prison:report_list')
            
        except Exception as e:
            messages.error(request, f'Error creating report: {str(e)}')
            return redirect('prison:report_create')
    
    # Get inmates assigned to the current officer
    inmates = Inmate.objects.filter(assigned_officer=request.user, status='active').order_by('last_name', 'first_name')
    selected_inmate_id = request.GET.get('inmate_id')
    
    context = {
        'inmates': inmates,
        'selected_inmate_id': selected_inmate_id,
        'report_types': InmateReport.REPORT_TYPE_CHOICES,
        'priority_choices': InmateReport.PRIORITY_CHOICES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/report_create.html', context)


@login_required
def report_detail(request, report_id):
    """View report details with role-based access"""
    report = get_object_or_404(InmateReport, id=report_id)
    
    # Check access permissions
    if report.inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. This report is not for an inmate assigned to you.')
        return redirect('prison:report_list')
    
    context = {
        'report': report,
        'user_role': request.user.profile.role,
        'can_edit': report.submitted_by == request.user,
    }
    
    return render(request, 'prison/report_detail.html', context)


@login_required
def report_review(request, report_id):
    """Review and approve report with enhanced workflow"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    report = get_object_or_404(InmateReport, id=report_id)
    
    # Check if the current user can review this report
    if report.inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. You can only review reports for inmates assigned to you.')
        return redirect('prison:report_detail', report_id=report.id)
    
    if request.method == 'POST':
        try:
            review_status = request.POST.get('review_status')
            review_notes = request.POST.get('review_notes')
            action_required = request.POST.get('action_required')
            follow_up_date = request.POST.get('follow_up_date')
            
            # Validate required fields
            if not review_status:
                messages.error(request, 'Please select a review status.')
                return redirect('prison:report_review', report_id=report.id)
            
            # Parse follow-up date if provided
            follow_up_date_parsed = None
            if follow_up_date:
                try:
                    follow_up_date_parsed = date.fromisoformat(follow_up_date)
                except ValueError:
                    messages.error(request, 'Invalid follow-up date format.')
                    return redirect('prison:report_review', report_id=report.id)
            
            # Update report
            report.status = review_status
            report.review_notes = review_notes
            report.action_required = action_required
            report.follow_up_date = follow_up_date_parsed
            report.reviewed_by = request.user
            report.reviewed_date = date.today()
            report.is_reviewed = True
            report.save()
            
            messages.success(request, 'Report reviewed successfully!')
            return redirect('prison:report_detail', report_id=report.id)
            
        except Exception as e:
            messages.error(request, f'Error reviewing report: {str(e)}')
            return redirect('prison:report_review', report_id=report.id)
    
    context = {
        'report': report,
        'review_status_choices': InmateReport.REVIEW_STATUS_CHOICES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/report_review.html', context)


@login_required
def inmate_reports(request, inmate_id):
    """List reports for specific inmate with role-based access"""
    inmate = get_object_or_404(Inmate, id=inmate_id)
    
    # Check access permissions
    if inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. This inmate is not assigned to you.')
        return redirect('prison:inmate_list')
    
    reports = inmate.reports.all().order_by('-submission_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'all':
            pass  # Show all reports
        elif status_filter == 'pending':
            reports = reports.filter(status='pending')
        elif status_filter == 'reviewed':
            reports = reports.filter(status__in=['approved', 'rejected'])
    
    context = {
        'inmate': inmate,
        'reports': reports,
        'user_role': request.user.profile.role,
        'total_reports': reports.count(),
        'pending_reports': reports.filter(status='pending').count(),
        'approved_reports': reports.filter(status='approved').count(),
        'rejected_reports': reports.filter(status='rejected').count(),
    }
    
    return render(request, 'prison/inmate_reports.html', context)


@login_required
def visitor_list(request):
    """List all visitor logs with role-based filtering"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    # Role-based filtering - officers only see visitors for their assigned inmates
    visitors = VisitorLog.objects.filter(inmate__assigned_officer=request.user).order_by('-visit_date')
    
    # Filter by date range if provided
    date_filter = request.GET.get('date_filter')
    if date_filter:
        if date_filter == 'today':
            visitors = visitors.filter(
                visit_date__gte=timezone.make_aware(datetime.combine(date.today(), datetime.min.time())),
                visit_date__lt=timezone.make_aware(datetime.combine(date.today() + timedelta(days=1), datetime.min.time()))
            )
        elif date_filter == 'week':
            visitors = visitors.filter(visit_date__gte=date.today() - timedelta(days=7))
        elif date_filter == 'month':
            visitors = visitors.filter(visit_date__gte=date.today() - timedelta(days=30))
    
    context = {
        'visitors': visitors,
        'user_role': request.user.profile.role,
        'total_visits': visitors.count(),
        'today_visits': visitors.filter(
            visit_date__gte=timezone.make_aware(datetime.combine(date.today(), datetime.min.time())),
            visit_date__lt=timezone.make_aware(datetime.combine(date.today() + timedelta(days=1), datetime.min.time()))
        ).count(),
        'week_visits': visitors.filter(visit_date__gte=date.today() - timedelta(days=7)).count(),
    }
    
    return render(request, 'prison/visitor_list.html', context)


@login_required
def visitor_create(request):
    """Create a new visitor log with enhanced validation"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            # Get form data
            inmate_id = request.POST.get('inmate_id')
            visitor_name = request.POST.get('visitor_name')
            visitor_id_number = request.POST.get('visitor_id_number')
            relationship = request.POST.get('relationship')
            visit_type = request.POST.get('visit_type')
            visit_date = request.POST.get('visit_date')
            visit_duration_minutes = int(request.POST.get('visit_duration_minutes'))
            purpose = request.POST.get('purpose')
            notes = request.POST.get('notes')
            authorized_by_id = request.POST.get('authorized_by')
            is_approved = request.POST.get('is_approved') == 'true'
            
            # Validate required fields
            if not all([inmate_id, visitor_name, relationship, visit_type, visit_date, visit_duration_minutes, purpose, authorized_by_id]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('prison:visitor_create')
            
            # Validate duration
            if visit_duration_minutes < 15 or visit_duration_minutes > 480:
                messages.error(request, 'Duration must be between 15 and 480 minutes.')
                return redirect('prison:visitor_create')
            
            # Get inmate and check assignment
            inmate = get_object_or_404(Inmate, id=inmate_id)
            if inmate.assigned_officer != request.user:
                messages.error(request, 'You can only log visits for inmates assigned to you.')
                return redirect('prison:visitor_create')
            
            # Parse visit date
            try:
                visit_date_parsed = datetime.fromisoformat(visit_date.replace('Z', '+00:00'))
                if visit_date_parsed > timezone.now():
                    messages.error(request, 'Visit date cannot be in the future.')
                    return redirect('prison:visitor_create')
            except ValueError:
                messages.error(request, 'Invalid visit date format.')
                return redirect('prison:visitor_create')
            
            # Get authorizing officer
            authorized_by = get_object_or_404(User, id=authorized_by_id)
            
            # Create visitor log
            visitor_log = VisitorLog.objects.create(
                inmate=inmate,
                visitor_name=visitor_name,
                visitor_id_number=visitor_id_number or '',
                relationship=relationship,
                visit_type=visit_type,
                visit_date=visit_date_parsed,
                visit_duration_minutes=visit_duration_minutes,
                purpose=purpose,
                notes=notes or '',
                authorized_by=authorized_by,
                is_approved=is_approved
            )
            
            messages.success(request, f'Visit logged successfully for {visitor_name} visiting {inmate.get_full_name()}.')
            return redirect('prison:visitor_list')
            
        except Exception as e:
            messages.error(request, f'Error creating visitor log: {str(e)}')
            return redirect('prison:visitor_create')
    
    # Get context data for the form
    inmates = Inmate.objects.filter(assigned_officer=request.user, status='active').order_by('last_name', 'first_name')
    officers = User.objects.filter(profile__role='prison_officer').order_by('first_name', 'last_name')
    selected_inmate_id = request.GET.get('inmate_id')
    
    context = {
        'inmates': inmates,
        'officers': officers,
        'selected_inmate_id': selected_inmate_id,
        'visit_types': VisitorLog.VISIT_TYPE_CHOICES,
        'relationship_choices': VisitorLog.RELATIONSHIP_CHOICES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/visitor_create.html', context)


@login_required
def visitor_detail(request, visitor_id):
    """View visitor log details with role-based access"""
    visitor = get_object_or_404(VisitorLog, id=visitor_id)
    
    # Check access permissions
    if visitor.inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. This visitor log is not for an inmate assigned to you.')
        return redirect('prison:visitor_list')
    
    context = {
        'visitor': visitor,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/visitor_detail.html', context)


@login_required
def inmate_visitors(request, inmate_id):
    """List visitors for specific inmate with role-based access"""
    inmate = get_object_or_404(Inmate, id=inmate_id)
    
    # Check access permissions
    if inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. This inmate is not assigned to you.')
        return redirect('prison:inmate_list')
    
    visitors = inmate.visitor_logs.all().order_by('-visit_date')
    
    context = {
        'inmate': inmate,
        'visitors': visitors,
        'user_role': request.user.profile.role,
        'total_visits': visitors.count(),
        'recent_visits': visitors.filter(visit_date__gte=date.today() - timedelta(days=30)).count(),
    }
    
    return render(request, 'prison/inmate_visitors.html', context)


@login_required
def program_list(request):
    """List all inmate programs with role-based filtering"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    # Role-based filtering - officers only see programs for their assigned inmates
    programs = InmateProgram.objects.filter(inmate__assigned_officer=request.user).order_by('-start_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        programs = programs.filter(status=status_filter)
    
    # Filter by program type if provided
    program_type_filter = request.GET.get('program_type')
    if program_type_filter:
        programs = programs.filter(program_type=program_type_filter)
    
    context = {
        'programs': programs,
        'user_role': request.user.profile.role,
        'total_programs': programs.count(),
        'active_programs': programs.filter(status='active').count(),
        'completed_programs': programs.filter(status='completed').count(),
        'upcoming_programs': programs.filter(status='upcoming').count(),
    }
    
    return render(request, 'prison/program_list.html', context)


@login_required
def program_create(request):
    """Create a new inmate program with enhanced validation"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            inmate_id = request.POST.get('inmate_id')
            program_name = request.POST.get('program_name')
            program_type = request.POST.get('program_type')
            description = request.POST.get('description')
            start_date = request.POST.get('start_date')
            expected_end_date = request.POST.get('expected_end_date')
            instructor = request.POST.get('instructor')
            notes = request.POST.get('notes')
            
            # Validate required fields
            if not all([inmate_id, program_name, program_type, description, start_date, expected_end_date]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('prison:program_create')
            
            # Get inmate and check assignment
            inmate = get_object_or_404(Inmate, id=inmate_id)
            if inmate.assigned_officer != request.user:
                messages.error(request, 'You can only create programs for inmates assigned to you.')
                return redirect('prison:program_create')
            
            # Parse dates
            start_date_parsed = date.fromisoformat(start_date)
            expected_end_date_parsed = date.fromisoformat(expected_end_date)
            
            # Validate dates
            if start_date_parsed >= expected_end_date_parsed:
                messages.error(request, 'Start date must be before expected end date.')
                return redirect('prison:program_create')
            
            # Create program
            program = InmateProgram.objects.create(
                inmate=inmate,
                program_name=program_name,
                program_type=program_type,
                description=description,
                start_date=start_date_parsed,
                expected_end_date=expected_end_date_parsed,
                instructor=instructor,
                notes=notes,
                status='upcoming' if start_date_parsed > date.today() else 'active'
            )
            
            messages.success(request, f'Program "{program.program_name}" created successfully for {inmate.get_full_name()}.')
            return redirect('prison:program_list')
            
        except Exception as e:
            messages.error(request, f'Error creating program: {str(e)}')
            return redirect('prison:program_create')
    
    # Get inmates assigned to the current officer
    inmates = Inmate.objects.filter(assigned_officer=request.user, status='active').order_by('last_name', 'first_name')
    
    context = {
        'inmates': inmates,
        'program_types': InmateProgram.PROGRAM_TYPE_CHOICES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/program_create.html', context)


@login_required
def program_detail(request, program_id):
    """View program details with role-based access"""
    program = get_object_or_404(InmateProgram, id=program_id)
    
    # Check access permissions
    if program.inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. This program is not for an inmate assigned to you.')
        return redirect('prison:program_list')
    
    # Calculate program statistics
    program_stats = {
        'days_remaining': (program.expected_end_date - date.today()).days if program.expected_end_date else None,
        'days_since_start': (date.today() - program.start_date).days if program.start_date else None,
        'progress_percentage': program.progress_percentage or 0,
    }
    
    context = {
        'program': program,
        'program_stats': program_stats,
        'user_role': request.user.profile.role,
        'can_edit': True,  # Assigned officer can edit
    }
    
    return render(request, 'prison/program_detail.html', context)


@login_required
def inmate_programs(request, inmate_id):
    """List programs for specific inmate with role-based access"""
    inmate = get_object_or_404(Inmate, id=inmate_id)
    
    # Check access permissions
    if inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. This inmate is not assigned to you.')
        return redirect('prison:inmate_list')
    
    programs = inmate.programs.all().order_by('-start_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'all':
            pass  # Show all programs
        elif status_filter == 'active':
            programs = programs.filter(status='active')
        elif status_filter == 'upcoming':
            programs = programs.filter(status='upcoming')
        elif status_filter == 'completed':
            programs = programs.filter(status='completed')
    
    context = {
        'inmate': inmate,
        'programs': programs,
        'user_role': request.user.profile.role,
        'total_programs': programs.count(),
        'active_programs': programs.filter(status='active').count(),
        'upcoming_programs': programs.filter(status='upcoming').count(),
        'completed_programs': programs.filter(status='completed').count(),
    }
    
    return render(request, 'prison/inmate_programs.html', context)


@login_required
def upcoming_releases(request):
    """List upcoming releases with role-based filtering"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    # Role-based filtering - officers only see releases for their assigned inmates
    upcoming = Inmate.objects.filter(
        assigned_officer=request.user,
        status='active',
        expected_release_date__lte=date.today() + timedelta(days=30),
        expected_release_date__gte=date.today()
    ).order_by('expected_release_date')
    
    # Filter by timeframe if provided
    timeframe_filter = request.GET.get('timeframe')
    if timeframe_filter:
        if timeframe_filter == 'week':
            upcoming = upcoming.filter(expected_release_date__lte=date.today() + timedelta(days=7))
        elif timeframe_filter == 'month':
            upcoming = upcoming.filter(expected_release_date__lte=date.today() + timedelta(days=30))
    
    # Calculate release statistics
    release_stats = {
        'total_upcoming': upcoming.count(),
        'this_week': upcoming.filter(expected_release_date__lte=date.today() + timedelta(days=7)).count(),
        'next_week': upcoming.filter(
            expected_release_date__gt=date.today() + timedelta(days=7),
            expected_release_date__lte=date.today() + timedelta(days=14)
        ).count(),
        'this_month': upcoming.filter(expected_release_date__lte=date.today() + timedelta(days=30)).count(),
    }
    
    context = {
        'inmates': upcoming,
        'user_role': request.user.profile.role,
        'release_stats': release_stats,
    }
    
    return render(request, 'prison/upcoming_releases.html', context)


@login_required
def search_inmates(request):
    """Search inmates via AJAX with role-based filtering"""
    if not check_role_access(request, ['prison_officer']):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    query = request.GET.get('q', '')
    inmates = Inmate.objects.filter(
        assigned_officer=request.user,
        first_name__icontains=query
    ) | Inmate.objects.filter(
        assigned_officer=request.user,
        last_name__icontains=query
    ) | Inmate.objects.filter(
        assigned_officer=request.user,
        inmate_id__icontains=query
    )
    
    inmates_data = [{
        'id': inmate.id,
        'name': inmate.get_full_name(),
        'inmate_id': inmate.inmate_id
    } for inmate in inmates[:10]]
    
    return JsonResponse({'inmates': inmates_data})


@login_required
@require_http_methods(["POST"])
def update_report_status(request, report_id):
    """Update report status via AJAX with role-based permissions"""
    if not check_role_access(request, ['prison_officer']):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    report = get_object_or_404(InmateReport, id=report_id)
    
    # Check if the current user can update this report
    if report.inmate.assigned_officer != request.user:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    action = request.POST.get('action')
    
    if action == 'review':
        report.mark_as_reviewed(request.user)
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid action'})


@login_required
@require_http_methods(["POST"])
def update_program_progress(request, program_id):
    """Update program progress via AJAX with role-based permissions"""
    if not check_role_access(request, ['prison_officer']):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    program = get_object_or_404(InmateProgram, id=program_id)
    
    # Check if the current user can update this program
    if program.inmate.assigned_officer != request.user:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    progress_percentage = request.POST.get('progress_percentage')
    status = request.POST.get('status')
    
    try:
        if progress_percentage:
            program.progress_percentage = int(progress_percentage)
        if status:
            program.status = status
            if status == 'completed':
                program.actual_end_date = date.today()
        
        program.save()
        return JsonResponse({'status': 'success'})
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid progress percentage'})


@login_required
def program_edit(request, program_id):
    """Edit program details with role-based permissions"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('prison:program_list')
    
    program = get_object_or_404(InmateProgram, id=program_id)
    
    # Check if the current user can edit this program
    if program.inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. You do not have permission to edit this program.')
        return redirect('prison:program_detail', program_id=program.id)
    
    if request.method == 'POST':
        try:
            program_name = request.POST.get('program_name')
            program_type = request.POST.get('program_type')
            description = request.POST.get('description')
            start_date = request.POST.get('start_date')
            expected_end_date = request.POST.get('expected_end_date')
            status = request.POST.get('status')
            progress_percentage = request.POST.get('progress_percentage')
            instructor = request.POST.get('instructor')
            notes = request.POST.get('notes')
            
            # Validate required fields
            if not all([program_name, program_type, description, start_date, expected_end_date, status]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('prison:program_edit', program_id=program.id)
            
            # Parse dates
            start_date_parsed = date.fromisoformat(start_date)
            expected_end_date_parsed = date.fromisoformat(expected_end_date)
            
            # Update program
            program.program_name = program_name
            program.program_type = program_type
            program.description = description
            program.start_date = start_date_parsed
            program.expected_end_date = expected_end_date_parsed
            program.status = status
            program.progress_percentage = int(progress_percentage) if progress_percentage else 0
            program.instructor = instructor
            program.notes = notes
            
            # Set actual end date if completed
            if status == 'completed':
                program.actual_end_date = date.today()
            
            program.save()
            
            messages.success(request, f'Program "{program.program_name}" updated successfully.')
            return redirect('prison:program_detail', program_id=program.id)
            
        except Exception as e:
            messages.error(request, f'Error updating program: {str(e)}')
            return redirect('prison:program_edit', program_id=program.id)
    
    context = {
        'program': program,
        'program_types': InmateProgram.PROGRAM_TYPE_CHOICES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/program_edit.html', context)


@login_required
def release_edit(request, release_id):
    """Edit release record with role-based permissions"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('prison:release_list')
    
    # Since we don't have a separate Release model, we'll redirect to inmate release
    # This could be enhanced with a proper Release model in the future
    messages.info(request, 'Release editing is not yet implemented.')
    return redirect('prison:release_list')


@login_required
def release_list(request):
    """List all releases with role-based filtering"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    # Role-based filtering - officers only see releases for their assigned inmates
    inmates = Inmate.objects.filter(
        assigned_officer=request.user,
        status__in=['released', 'active']
    ).order_by('expected_release_date')
    
    context = {
        'inmates': inmates,
        'user_role': request.user.profile.role,
        'total_releases': inmates.filter(status='released').count(),
        'upcoming_releases': inmates.filter(status='active').count(),
    }
    
    return render(request, 'prison/release_list.html', context)


@login_required
def release_create(request):
    """Create a new release record"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            inmate_id = request.POST.get('inmate_id')
            release_date = request.POST.get('release_date')
            release_type = request.POST.get('release_type')
            release_notes = request.POST.get('release_notes')
            authorized_by_id = request.POST.get('authorized_by')
            
            # Validate required fields
            if not all([inmate_id, release_date, release_type, authorized_by_id]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('prison:release_create')
            
            # Get inmate and check assignment
            inmate = get_object_or_404(Inmate, id=inmate_id)
            if inmate.assigned_officer != request.user:
                messages.error(request, 'You can only create releases for inmates assigned to you.')
                return redirect('prison:release_create')
            
            authorized_by = get_object_or_404(User, id=authorized_by_id)
            
            # Parse release date
            release_date_parsed = date.fromisoformat(release_date)
            
            # Update inmate status and release date
            inmate.status = 'released'
            inmate.actual_release_date = release_date_parsed
            inmate.save()
            
            messages.success(request, f'Release processed successfully for {inmate.get_full_name()}.')
            return redirect('prison:release_list')
            
        except Exception as e:
            messages.error(request, f'Error processing release: {str(e)}')
            return redirect('prison:release_create')
    
    # Get inmates assigned to the current officer
    inmates = Inmate.objects.filter(assigned_officer=request.user, status='active').order_by('last_name', 'first_name')
    officers = User.objects.filter(is_staff=True).order_by('first_name', 'last_name')
    
    context = {
        'inmates': inmates,
        'officers': officers,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/release_create.html', context)


@login_required
def release_detail(request, release_id):
    """View release details"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    # Since we don't have a separate Release model, we'll show released inmates
    # This could be enhanced with a proper Release model in the future
    inmates = Inmate.objects.filter(
        assigned_officer=request.user,
        status='released'
    ).order_by('-actual_release_date')
    
    context = {
        'inmates': inmates,
        'show_released_only': True,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/release_list.html', context)


@login_required
def inmate_release(request, inmate_id):
    """Process release for a specific inmate"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    inmate = get_object_or_404(Inmate, id=inmate_id)
    
    # Check if the current user can release this inmate
    if inmate.assigned_officer != request.user:
        messages.error(request, 'Access denied. You do not have permission to release this inmate.')
        return redirect('prison:inmate_detail', inmate_id=inmate.id)
    
    if request.method == 'POST':
        try:
            release_date = request.POST.get('release_date')
            release_type = request.POST.get('release_type')
            release_notes = request.POST.get('release_notes')
            authorized_by_id = request.POST.get('authorized_by')
            
            # Validate required fields
            if not all([release_date, release_type, authorized_by_id]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('prison:inmate_release', inmate_id=inmate.id)
            
            authorized_by = get_object_or_404(User, id=authorized_by_id)
            
            # Parse release date
            release_date_parsed = date.fromisoformat(release_date)
            
            # Update inmate status and release date
            inmate.status = 'released'
            inmate.actual_release_date = release_date_parsed
            inmate.save()
            
            messages.success(request, f'Release processed successfully for {inmate.get_full_name()}.')
            return redirect('prison:inmate_detail', inmate_id=inmate.id)
            
        except Exception as e:
            messages.error(request, f'Error processing release: {str(e)}')
            return redirect('prison:inmate_release', inmate_id=inmate.id)
    
    # Get officers for authorization
    officers = User.objects.filter(is_staff=True).order_by('first_name', 'last_name')
    
    context = {
        'inmate': inmate,
        'officers': officers,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/inmate_release.html', context)


@login_required
def officer_profile(request):
    """View officer profile"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    user = request.user
    
    # Get assigned inmates count
    assigned_inmates_count = Inmate.objects.filter(assigned_officer=user, status='active').count()
    
    # Get recent activity
    recent_reports = InmateReport.objects.filter(submitted_by=user).order_by('-submission_date')[:5]
    recent_visits = VisitorLog.objects.filter(authorized_by=user).order_by('-created_at')[:5]
    
    context = {
        'user': user,
        'assigned_inmates_count': assigned_inmates_count,
        'recent_reports': recent_reports,
        'recent_visits': recent_visits,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/officer_profile.html', context)


@login_required
def officer_profile_edit(request):
    """Edit officer profile"""
    if not check_role_access(request, ['prison_officer']):
        messages.error(request, 'Access denied. Prison Officer role required.')
        return redirect('core:dashboard')
    
    user = request.user
    
    if request.method == 'POST':
        try:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            department = request.POST.get('department')
            badge_number = request.POST.get('badge_number')
            
            # Validate required fields
            if not all([first_name, last_name, email]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('prison:officer_profile_edit')
            
            # Update user profile
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            
            # Update or create user profile (you might want to create a separate Profile model)
            # For now, we'll just update the basic user fields
            user.save()
            
            messages.success(request, 'Profile updated successfully.')
            return redirect('prison:officer_profile')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
            return redirect('prison:officer_profile_edit')
    
    context = {
        'user': user,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'prison/officer_profile_edit.html', context)
