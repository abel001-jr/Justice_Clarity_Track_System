from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta, datetime

from .models import Case, Evidence, CaseReport, Hearing


def check_role_access(request, required_roles):
    """Helper function to check if user has required role access"""
    if not hasattr(request.user, 'profile'):
        return False
    return request.user.profile.role in required_roles


@login_required
def case_list(request):
    """List all cases with role-based filtering"""
    if not check_role_access(request, ['judge', 'clerk']):
        messages.error(request, 'Access denied. Judge or Clerk role required.')
        return redirect('core:dashboard')
    
    # Role-based filtering
    if request.user.profile.role == 'judge':
        cases = Case.objects.filter(assigned_judge=request.user).order_by('-filing_date')
    else:  # clerk
        cases = Case.objects.all().order_by('-filing_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        cases = cases.filter(status=status_filter)
    
    # Filter by priority if provided
    priority_filter = request.GET.get('priority')
    if priority_filter:
        cases = cases.filter(priority=priority_filter)
    
    context = {
        'cases': cases,
        'user_role': request.user.profile.role,
        'status_choices': Case.STATUS_CHOICES,
        'priority_choices': Case.PRIORITY_CHOICES,
        'total_cases': cases.count(),
        'pending_cases': cases.filter(status='pending').count(),
        'in_progress_cases': cases.filter(status='in_progress').count(),
        'completed_cases': cases.filter(status='decided').count(),
    }
    
    return render(request, 'court/case_list.html', context)


@login_required
def case_create(request):
    """Create a new case with enhanced validation and workflow"""
    if not check_role_access(request, ['clerk']):
        messages.error(request, 'Access denied. Clerk role required.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            # Extract form data
            case_number = request.POST.get('case_number')
            title = request.POST.get('title')
            description = request.POST.get('description')
            case_type = request.POST.get('case_type')
            priority = request.POST.get('priority')
            filing_date = request.POST.get('filing_date')
            plaintiff_name = request.POST.get('plaintiff_name')
            defendant_name = request.POST.get('defendant_name')
            assigned_judge_id = request.POST.get('assigned_judge')
            
            # Validate required fields
            if not all([case_number, title, case_type, priority, filing_date]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('court:case_create')
            
            # Check if case number already exists
            if Case.objects.filter(case_number=case_number).exists():
                messages.error(request, 'Case number already exists.')
                return redirect('court:case_create')
            
            # Parse filing date
            try:
                filing_date_parsed = date.fromisoformat(filing_date)
            except ValueError:
                messages.error(request, 'Invalid filing date format.')
                return redirect('court:case_create')
            
            # Convert date to datetime for the model
            from django.utils import timezone
            filing_datetime = timezone.make_aware(
                datetime.combine(filing_date_parsed, datetime.min.time())
            )
            
            # Get assigned judge if provided
            assigned_judge = None
            if assigned_judge_id:
                try:
                    assigned_judge = User.objects.get(id=assigned_judge_id, profile__role='judge')
                except User.DoesNotExist:
                    messages.error(request, 'Selected judge not found.')
                    return redirect('court:case_create')
            
            # Create the case
            case = Case.objects.create(
                case_number=case_number,
                title=title,
                description=description,
                case_type=case_type,
                priority=priority,
                filing_date=filing_datetime,
                plaintiff_name=plaintiff_name,
                defendant_name=defendant_name,
                assigned_judge=assigned_judge,
                status='pending' if not assigned_judge else 'assigned',
                created_by=request.user
            )
            
            messages.success(request, f'Case "{case.title}" created successfully!')
            return redirect('court:case_detail', case_id=case.id)
            
        except Exception as e:
            messages.error(request, f'Error creating case: {str(e)}')
            return redirect('court:case_create')
    
    # Get judges for assignment
    judges = User.objects.filter(profile__role='judge').order_by('first_name', 'last_name')
    
    context = {
        'judges': judges,
        'case_types': Case.CASE_TYPES,
        'priority_choices': Case.PRIORITY_CHOICES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'court/case_create.html', context)


@login_required
def case_templates(request):
    """Display case templates for quick case creation"""
    if not check_role_access(request, ['clerk']):
        messages.error(request, 'Access denied. Clerk role required.')
        return redirect('core:dashboard')
    
    # Define case templates
    case_templates = [
        {
            'id': 'criminal_general',
            'name': 'Criminal Case - General',
            'type': 'criminal',
            'description': 'Standard criminal case template with common fields',
            'icon': 'bi-shield-exclamation',
            'color': 'danger',
            'fields': {
                'case_type': 'criminal',
                'priority': 'high',
                'plaintiff_name': 'State',
                'defendant_name': '',
                'description': 'Criminal case involving violation of state laws.'
            }
        },
        {
            'id': 'civil_contract',
            'name': 'Civil Case - Contract Dispute',
            'type': 'civil',
            'description': 'Template for contract-related civil cases',
            'icon': 'bi-file-earmark-text',
            'color': 'primary',
            'fields': {
                'case_type': 'civil',
                'priority': 'medium',
                'plaintiff_name': '',
                'defendant_name': '',
                'description': 'Civil case involving contract dispute between parties.'
            }
        },
        {
            'id': 'family_divorce',
            'name': 'Family Case - Divorce',
            'type': 'family',
            'description': 'Template for divorce and family law cases',
            'icon': 'bi-heart',
            'color': 'warning',
            'fields': {
                'case_type': 'family',
                'priority': 'medium',
                'plaintiff_name': '',
                'defendant_name': '',
                'description': 'Family law case involving divorce proceedings.'
            }
        },
        {
            'id': 'commercial_business',
            'name': 'Commercial Case - Business Dispute',
            'type': 'commercial',
            'description': 'Template for business and commercial disputes',
            'icon': 'bi-building',
            'color': 'info',
            'fields': {
                'case_type': 'civil',
                'priority': 'medium',
                'plaintiff_name': '',
                'defendant_name': '',
                'description': 'Commercial case involving business dispute.'
            }
        },
        {
            'id': 'administrative_appeal',
            'name': 'Administrative Case - Appeal',
            'type': 'administrative',
            'description': 'Template for administrative appeals',
            'icon': 'bi-clipboard-data',
            'color': 'secondary',
            'fields': {
                'case_type': 'administrative',
                'priority': 'low',
                'plaintiff_name': '',
                'defendant_name': '',
                'description': 'Administrative case involving appeal of government decision.'
            }
        },
        {
            'id': 'criminal_traffic',
            'name': 'Criminal Case - Traffic Violation',
            'type': 'criminal',
            'description': 'Template for traffic-related criminal cases',
            'icon': 'bi-car-front',
            'color': 'danger',
            'fields': {
                'case_type': 'criminal',
                'priority': 'low',
                'plaintiff_name': 'State',
                'defendant_name': '',
                'description': 'Criminal case involving traffic law violations.'
            }
        }
    ]
    
    context = {
        'case_templates': case_templates,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'court/case_templates.html', context)


@login_required
def case_detail(request, case_id):
    """View case details with role-based access and enhanced information"""
    if not check_role_access(request, ['judge', 'clerk']):
        messages.error(request, 'Access denied. Judge or Clerk role required.')
        return redirect('core:dashboard')
    
    case = get_object_or_404(Case, id=case_id)
    
    # Role-based access control
    if request.user.profile.role == 'judge' and case.assigned_judge != request.user:
        messages.error(request, 'Access denied. This case is not assigned to you.')
        return redirect('court:case_list')
    
    # Get related data
    evidence = case.evidence.all().order_by('-submission_date')
    hearings = case.hearings.all().order_by('-scheduled_date')
    reports = case.reports.all().order_by('-submission_date')
    
    # Calculate case statistics
    case_stats = {
        'total_evidence': evidence.count(),
        'pending_evidence': evidence.filter(is_approved__isnull=True).count(),
        'total_hearings': hearings.count(),
        'completed_hearings': hearings.filter(is_completed=True).count(),
        'upcoming_hearings': hearings.filter(is_completed=False, is_cancelled=False).count(),
        'total_reports': reports.count(),
        'days_since_filing': (date.today() - case.filing_date).days,
    }
    
    context = {
        'case': case,
        'evidence': evidence,
        'hearings': hearings,
        'reports': reports,
        'case_stats': case_stats,
        'user_role': request.user.profile.role,
        'can_edit': request.user.profile.role == 'clerk' or (request.user.profile.role == 'judge' and case.assigned_judge == request.user),
    }
    
    return render(request, 'court/case_detail.html', context)


@login_required
def case_edit(request, case_id):
    """Edit case details with role-based permissions"""
    case = get_object_or_404(Case, id=case_id)
    
    # Check permissions
    if not (request.user.profile.role == 'clerk' or 
            (request.user.profile.role == 'judge' and case.assigned_judge == request.user)):
        messages.error(request, 'Access denied. You do not have permission to edit this case.')
        return redirect('court:case_detail', case_id=case.id)
    
    if request.method == 'POST':
        try:
            # Update case fields
            case.title = request.POST.get('title', case.title)
            case.description = request.POST.get('description', case.description)
            case.case_type = request.POST.get('case_type', case.case_type)
            case.priority = request.POST.get('priority', case.priority)
            case.plaintiff_name = request.POST.get('plaintiff_name', case.plaintiff_name)
            case.defendant_name = request.POST.get('defendant_name', case.defendant_name)
            
            # Handle judge assignment (only clerks can change judge assignment)
            if request.user.profile.role == 'clerk':
                assigned_judge_id = request.POST.get('assigned_judge')
                if assigned_judge_id:
                    try:
                        assigned_judge = User.objects.get(id=assigned_judge_id, profile__role='judge')
                        case.assigned_judge = assigned_judge
                        case.status = 'assigned'
                    except User.DoesNotExist:
                        messages.error(request, 'Selected judge not found.')
                        return redirect('court:case_edit', case_id=case.id)
            
            case.save()
            messages.success(request, 'Case updated successfully!')
            return redirect('court:case_detail', case_id=case.id)
            
        except Exception as e:
            messages.error(request, f'Error updating case: {str(e)}')
            return redirect('court:case_edit', case_id=case.id)
    
    # Get judges for assignment
    judges = User.objects.filter(profile__role='judge').order_by('first_name', 'last_name')
    
    context = {
        'case': case,
        'judges': judges,
        'case_types': Case.CASE_TYPES,
        'priority_choices': Case.PRIORITY_CHOICES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'court/case_edit.html', context)


@login_required
def case_assign(request, case_id):
    """Assign judge to case with enhanced workflow"""
    if not check_role_access(request, ['clerk']):
        messages.error(request, 'Access denied. Clerk role required.')
        return redirect('core:dashboard')
    
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        try:
            assigned_judge_id = request.POST.get('assigned_judge')
            assignment_notes = request.POST.get('assignment_notes')
            
            if not assigned_judge_id:
                messages.error(request, 'Please select a judge to assign.')
                return redirect('court:case_assign', case_id=case.id)
            
            # Get the judge
            try:
                assigned_judge = User.objects.get(id=assigned_judge_id, profile__role='judge')
            except User.DoesNotExist:
                messages.error(request, 'Selected judge not found.')
                return redirect('court:case_assign', case_id=case.id)
            
            # Update case assignment
            case.assigned_judge = assigned_judge
            case.status = 'assigned'
            case.assignment_date = date.today()
            case.assignment_notes = assignment_notes
            case.save()
            
            messages.success(request, f'Case assigned to Judge {assigned_judge.get_full_name()} successfully!')
            return redirect('court:case_detail', case_id=case.id)
            
        except Exception as e:
            messages.error(request, f'Error assigning case: {str(e)}')
            return redirect('court:case_assign', case_id=case.id)
    
    # Get available judges
    judges = User.objects.filter(profile__role='judge').order_by('first_name', 'last_name')
    
    context = {
        'case': case,
        'judges': judges,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'court/case_assign.html', context)


@login_required
def case_sentence(request, case_id):
    """Pass sentence for case with enhanced workflow"""
    if not check_role_access(request, ['judge']):
        messages.error(request, 'Access denied. Judge role required.')
        return redirect('core:dashboard')
    
    case = get_object_or_404(Case, id=case_id)
    
    # Check if case is assigned to the current judge
    if case.assigned_judge != request.user:
        messages.error(request, 'Access denied. This case is not assigned to you.')
        return redirect('court:case_detail', case_id=case.id)
    
    if request.method == 'POST':
        try:
            sentence_type = request.POST.get('sentence_type')
            sentence_duration = request.POST.get('sentence_duration')
            fine_amount = request.POST.get('fine_amount')
            sentence_notes = request.POST.get('sentence_notes')
            decision_date = request.POST.get('decision_date')
            
            # Validate required fields
            if not sentence_type:
                messages.error(request, 'Please specify the sentence type.')
                return redirect('court:case_sentence', case_id=case.id)
            
            # Parse decision date
            try:
                decision_date_parsed = date.fromisoformat(decision_date) if decision_date else date.today()
            except ValueError:
                messages.error(request, 'Invalid decision date format.')
                return redirect('court:case_sentence', case_id=case.id)
            
            # Update case with sentence
            case.status = 'decided'
            case.decision_date = decision_date_parsed
            case.sentence_type = sentence_type
            case.sentence_duration = sentence_duration
            case.fine_amount = fine_amount if fine_amount else None
            case.sentence_notes = sentence_notes
            case.save()
            
            messages.success(request, 'Sentence passed successfully!')
            return redirect('court:case_detail', case_id=case.id)
            
        except Exception as e:
            messages.error(request, f'Error passing sentence: {str(e)}')
            return redirect('court:case_sentence', case_id=case.id)
    
    context = {
        'case': case,
        'sentence_types': Case.SENTENCE_TYPE_CHOICES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'court/case_sentence.html', context)


@login_required
def evidence_list(request, case_id):
    """List evidence for a case with role-based access"""
    case = get_object_or_404(Case, id=case_id)
    
    # Check access permissions
    if request.user.profile.role == 'judge' and case.assigned_judge != request.user:
        messages.error(request, 'Access denied. This case is not assigned to you.')
        return redirect('court:case_list')
    
    evidence = case.evidence.all().order_by('-submission_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'pending':
            evidence = evidence.filter(is_approved__isnull=True)
        elif status_filter == 'approved':
            evidence = evidence.filter(is_approved=True)
        elif status_filter == 'rejected':
            evidence = evidence.filter(is_approved=False)
    
    context = {
        'case': case,
        'evidence': evidence,
        'user_role': request.user.profile.role,
        'can_review': request.user.profile.role == 'judge' and case.assigned_judge == request.user,
        'total_evidence': evidence.count(),
        'pending_evidence': evidence.filter(is_approved__isnull=True).count(),
        'approved_evidence': evidence.filter(is_approved=True).count(),
        'rejected_evidence': evidence.filter(is_approved=False).count(),
    }
    
    return render(request, 'court/evidence_list.html', context)


@login_required
def evidence_add(request, case_id):
    """Add evidence to case with enhanced validation"""
    case = get_object_or_404(Case, id=case_id)
    
    # Check access permissions
    if request.user.profile.role == 'judge' and case.assigned_judge != request.user:
        messages.error(request, 'Access denied. This case is not assigned to you.')
        return redirect('court:case_detail', case_id=case.id)
    
    if request.method == 'POST':
        try:
            evidence_type = request.POST.get('evidence_type')
            description = request.POST.get('description')
            submission_date = request.POST.get('submission_date')
            submitted_by = request.POST.get('submitted_by')
            notes = request.POST.get('notes')
            
            # Validate required fields
            if not all([evidence_type, description, submission_date]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('court:evidence_add', case_id=case.id)
            
            # Parse submission date
            try:
                submission_date_parsed = date.fromisoformat(submission_date)
            except ValueError:
                messages.error(request, 'Invalid submission date format.')
                return redirect('court:evidence_add', case_id=case.id)
            
            # Create evidence
            evidence = Evidence.objects.create(
                case=case,
                evidence_type=evidence_type,
                description=description,
                submission_date=submission_date_parsed,
                submitted_by=submitted_by,
                notes=notes,
                submitted_by_user=request.user
            )
            
            messages.success(request, 'Evidence added successfully!')
            return redirect('court:evidence_list', case_id=case.id)
            
        except Exception as e:
            messages.error(request, f'Error adding evidence: {str(e)}')
            return redirect('court:evidence_add', case_id=case.id)
    
    context = {
        'case': case,
        'evidence_types': Evidence.EVIDENCE_TYPE_CHOICES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'court/evidence_add.html', context)


@login_required
def evidence_detail(request, evidence_id):
    """View evidence details with role-based access"""
    evidence = get_object_or_404(Evidence, id=evidence_id)
    case = evidence.case
    
    # Check access permissions
    if request.user.profile.role == 'judge' and case.assigned_judge != request.user:
        messages.error(request, 'Access denied. This case is not assigned to you.')
        return redirect('court:case_list')
    
    context = {
        'evidence': evidence,
        'case': case,
        'user_role': request.user.profile.role,
        'can_review': request.user.profile.role == 'judge' and case.assigned_judge == request.user,
    }
    
    return render(request, 'court/evidence_detail.html', context)


@login_required
def hearing_list(request):
    """List all hearings with role-based filtering"""
    if not check_role_access(request, ['judge', 'clerk']):
        messages.error(request, 'Access denied. Judge or Clerk role required.')
        return redirect('core:dashboard')
    
    # Role-based filtering
    if request.user.profile.role == 'judge':
        hearings = Hearing.objects.filter(judge=request.user).order_by('-scheduled_date')
    else:  # clerk
        hearings = Hearing.objects.all().order_by('-scheduled_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        if status_filter == 'upcoming':
            hearings = hearings.filter(scheduled_date__gte=date.today(), is_completed=False, is_cancelled=False)
        elif status_filter == 'completed':
            hearings = hearings.filter(is_completed=True)
        elif status_filter == 'cancelled':
            hearings = hearings.filter(is_cancelled=True)
    
    context = {
        'hearings': hearings,
        'user_role': request.user.profile.role,
        'total_hearings': hearings.count(),
        'upcoming_hearings': hearings.filter(scheduled_date__gte=date.today(), is_completed=False, is_cancelled=False).count(),
        'completed_hearings': hearings.filter(is_completed=True).count(),
        'cancelled_hearings': hearings.filter(is_cancelled=True).count(),
    }
    
    return render(request, 'court/hearing_list.html', context)


@login_required
def hearing_create(request):
    """Create a new hearing with enhanced workflow"""
    if not check_role_access(request, ['clerk', 'judge']):
        messages.error(request, 'Access denied. Clerk or Judge role required.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            case_id = request.POST.get('case')
            hearing_type = request.POST.get('hearing_type')
            scheduled_date = request.POST.get('scheduled_date')
            scheduled_time = request.POST.get('scheduled_time')
            courtroom = request.POST.get('courtroom')
            judge_id = request.POST.get('judge')
            notes = request.POST.get('notes')
            
            # Validate required fields
            if not all([case_id, hearing_type, scheduled_date, scheduled_time, courtroom]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('court:hearing_create')
            
            # Get case
            case = get_object_or_404(Case, id=case_id)
            
            # Check if judge is assigned to case (for judges creating hearings)
            if request.user.profile.role == 'judge' and case.assigned_judge != request.user:
                messages.error(request, 'You can only create hearings for cases assigned to you.')
                return redirect('court:hearing_create')
            
            # Get judge
            if judge_id:
                judge = get_object_or_404(User, id=judge_id, profile__role='judge')
            else:
                judge = case.assigned_judge
            
            # Parse date and time
            try:
                scheduled_datetime = timezone.make_aware(
                    timezone.datetime.combine(
                        date.fromisoformat(scheduled_date),
                        timezone.datetime.strptime(scheduled_time, '%H:%M').time()
                    )
                )
            except ValueError:
                messages.error(request, 'Invalid date or time format.')
                return redirect('court:hearing_create')
            
            # Create hearing
            hearing = Hearing.objects.create(
                case=case,
                hearing_type=hearing_type,
                scheduled_date=scheduled_datetime,
                courtroom=courtroom,
                judge=judge,
                notes=notes,
                created_by=request.user
            )
            
            messages.success(request, 'Hearing scheduled successfully!')
            return redirect('court:hearing_detail', hearing_id=hearing.id)
            
        except Exception as e:
            messages.error(request, f'Error creating hearing: {str(e)}')
            return redirect('court:hearing_create')
    
    # Get cases and judges
    if request.user.profile.role == 'judge':
        cases = Case.objects.filter(assigned_judge=request.user, status__in=['assigned', 'in_progress'])
    else:  # clerk
        cases = Case.objects.filter(status__in=['assigned', 'in_progress'])
    
    judges = User.objects.filter(profile__role='judge').order_by('first_name', 'last_name')
    
    context = {
        'cases': cases,
        'judges': judges,
        'hearing_types': Hearing.HEARING_TYPES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'court/hearing_create.html', context)


@login_required
def hearing_detail(request, hearing_id):
    """View hearing details with role-based access"""
    hearing = get_object_or_404(Hearing, id=hearing_id)
    
    # Check access permissions
    if request.user.profile.role == 'judge' and hearing.judge != request.user:
        messages.error(request, 'Access denied. This hearing is not assigned to you.')
        return redirect('court:hearing_list')
    
    context = {
        'hearing': hearing,
        'user_role': request.user.profile.role,
        'can_edit': request.user.profile.role == 'clerk' or (request.user.profile.role == 'judge' and hearing.judge == request.user),
    }
    
    return render(request, 'court/hearing_detail.html', context)


@login_required
def hearing_edit(request, hearing_id):
    """Edit hearing details with role-based permissions"""
    hearing = get_object_or_404(Hearing, id=hearing_id)
    
    # Check permissions
    if not (request.user.profile.role == 'clerk' or 
            (request.user.profile.role == 'judge' and hearing.judge == request.user)):
        messages.error(request, 'Access denied. You do not have permission to edit this hearing.')
        return redirect('court:hearing_detail', hearing_id=hearing.id)
    
    if request.method == 'POST':
        try:
            # Update hearing fields
            hearing.hearing_type = request.POST.get('hearing_type', hearing.hearing_type)
            hearing.courtroom = request.POST.get('courtroom', hearing.courtroom)
            hearing.notes = request.POST.get('notes', hearing.notes)
            
            # Handle date and time updates
            scheduled_date = request.POST.get('scheduled_date')
            scheduled_time = request.POST.get('scheduled_time')
            
            if scheduled_date and scheduled_time:
                try:
                    scheduled_datetime = timezone.make_aware(
                        timezone.datetime.combine(
                            date.fromisoformat(scheduled_date),
                            timezone.datetime.strptime(scheduled_time, '%H:%M').time()
                        )
                    )
                    hearing.scheduled_date = scheduled_datetime
                except ValueError:
                    messages.error(request, 'Invalid date or time format.')
                    return redirect('court:hearing_edit', hearing_id=hearing.id)
            
            # Handle judge assignment (only clerks can change judge)
            if request.user.profile.role == 'clerk':
                judge_id = request.POST.get('judge')
                if judge_id:
                    judge = get_object_or_404(User, id=judge_id, profile__role='judge')
                    hearing.judge = judge
            
            hearing.save()
            messages.success(request, 'Hearing updated successfully!')
            return redirect('court:hearing_detail', hearing_id=hearing.id)
            
        except Exception as e:
            messages.error(request, f'Error updating hearing: {str(e)}')
            return redirect('court:hearing_edit', hearing_id=hearing.id)
    
    # Get judges for assignment
    judges = User.objects.filter(profile__role='judge').order_by('first_name', 'last_name')
    
    context = {
        'hearing': hearing,
        'judges': judges,
        'hearing_types': Hearing.HEARING_TYPES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'court/hearing_edit.html', context)


@login_required
def report_list(request):
    """List all case reports with role-based filtering"""
    if not check_role_access(request, ['judge', 'clerk']):
        messages.error(request, 'Access denied. Judge or Clerk role required.')
        return redirect('core:dashboard')
    
    # Role-based filtering
    if request.user.profile.role == 'judge':
        reports = CaseReport.objects.filter(submitted_by=request.user).order_by('-submission_date')
    else:  # clerk
        reports = CaseReport.objects.all().order_by('-submission_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    context = {
        'reports': reports,
        'user_role': request.user.profile.role,
        'total_reports': reports.count(),
        'pending_reports': reports.filter(is_approved__isnull=True).count(),
        'approved_reports': reports.filter(is_approved=True).count(),
        'rejected_reports': reports.filter(is_approved=False).count(),
    }
    
    return render(request, 'court/report_list.html', context)


@login_required
def report_create(request):
    """Create a new case report with enhanced workflow"""
    if not check_role_access(request, ['judge', 'clerk']):
        messages.error(request, 'Access denied. Judge or Clerk role required.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        try:
            case_id = request.POST.get('case')
            report_type = request.POST.get('report_type')
            title = request.POST.get('title')
            content = request.POST.get('content')
            priority = request.POST.get('priority')
            recommendations = request.POST.get('recommendations')
            
            # Validate required fields
            if not all([case_id, report_type, title, content]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('court:report_create')
            
            # Get case
            case = get_object_or_404(Case, id=case_id)
            
            # Check if judge can create report for this case
            if request.user.profile.role == 'judge' and case.assigned_judge != request.user:
                messages.error(request, 'You can only create reports for cases assigned to you.')
                return redirect('court:report_create')
            
            # Create report
            report = CaseReport.objects.create(
                case=case,
                report_type=report_type,
                title=title,
                content=content,
                priority=priority,
                recommendations=recommendations,
                submitted_by=request.user
            )
            
            messages.success(request, 'Report submitted successfully!')
            return redirect('court:report_detail', report_id=report.id)
            
        except Exception as e:
            messages.error(request, f'Error creating report: {str(e)}')
            return redirect('court:report_create')
    
    # Get cases
    if request.user.profile.role == 'judge':
        cases = Case.objects.filter(assigned_judge=request.user)
    else:  # clerk
        cases = Case.objects.all()
    
    context = {
        'cases': cases,
        'report_types': CaseReport.REPORT_TYPES,
        'priority_choices': CaseReport.PRIORITY_CHOICES,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'court/report_create.html', context)


@login_required
def report_detail(request, report_id):
    """View report details with role-based access"""
    report = get_object_or_404(CaseReport, id=report_id)
    
    # Check access permissions
    if request.user.profile.role == 'judge' and report.submitted_by != request.user:
        messages.error(request, 'Access denied. You can only view your own reports.')
        return redirect('court:report_list')
    
    context = {
        'report': report,
        'user_role': request.user.profile.role,
        'can_edit': report.submitted_by == request.user,
    }
    
    return render(request, 'court/report_detail.html', context)


@login_required
def get_judges(request):
    """Get list of judges via AJAX with enhanced filtering"""
    if not check_role_access(request, ['clerk', 'judge']):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    judges = User.objects.filter(profile__role='judge').order_by('first_name', 'last_name')
    judges_data = [{'id': judge.id, 'name': judge.get_full_name()} for judge in judges]
    return JsonResponse({'judges': judges_data})


@login_required
@require_http_methods(["POST"])
def update_case_status(request, case_id):
    """Update case status via AJAX with role-based permissions"""
    case = get_object_or_404(Case, id=case_id)
    
    # Check permissions
    if not (request.user.profile.role == 'clerk' or 
            (request.user.profile.role == 'judge' and case.assigned_judge == request.user)):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    new_status = request.POST.get('status')
    if new_status in dict(Case.STATUS_CHOICES):
        case.status = new_status
        case.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid status'})


@login_required
@require_http_methods(["POST"])
def review_evidence(request, evidence_id):
    """Review evidence via AJAX with judge permissions"""
    if not check_role_access(request, ['judge']):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    evidence = get_object_or_404(Evidence, id=evidence_id)
    
    # Check if judge is assigned to the case
    if evidence.case.assigned_judge != request.user:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    action = request.POST.get('action')
    review_notes = request.POST.get('review_notes', '')
    
    if action == 'approve':
        evidence.is_approved = True
        evidence.reviewed_by = request.user
        evidence.reviewed_date = date.today()
        evidence.review_notes = review_notes
        evidence.save()
        return JsonResponse({'status': 'success', 'message': 'Evidence approved'})
    elif action == 'reject':
        evidence.is_approved = False
        evidence.reviewed_by = request.user
        evidence.reviewed_date = date.today()
        evidence.review_notes = review_notes
        evidence.save()
        return JsonResponse({'status': 'success', 'message': 'Evidence rejected'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid action'})


@login_required
@require_http_methods(["POST"])
def complete_hearing(request, hearing_id):
    """Mark hearing as completed via AJAX"""
    if not check_role_access(request, ['judge', 'clerk']):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    hearing = get_object_or_404(Hearing, id=hearing_id)
    
    # Check permissions
    if not (request.user.profile.role == 'clerk' or 
            (request.user.profile.role == 'judge' and hearing.judge == request.user)):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    hearing.is_completed = True
    hearing.completed_date = timezone.now()
    hearing.completed_by = request.user
    hearing.save()
    
    return JsonResponse({'status': 'success', 'message': 'Hearing marked as completed'})
