from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Case(models.Model):
    """Court case model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('decided', 'Decided'),
        ('closed', 'Closed'),
        ('appealed', 'Appealed'),
    ]
    
    CASE_TYPES = [
        ('criminal', 'Criminal'),
        ('civil', 'Civil'),
        ('family', 'Family'),
        ('commercial', 'Commercial'),
        ('administrative', 'Administrative'),
    ]
    
    case_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    case_type = models.CharField(max_length=20, choices=CASE_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Case participants
    plaintiff = models.CharField(max_length=200)
    defendant = models.CharField(max_length=200)
    plaintiff_lawyer = models.CharField(max_length=200, blank=True, null=True)
    defendant_lawyer = models.CharField(max_length=200, blank=True, null=True)
    
    # Case management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_cases')
    assigned_judge = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    
    # Important dates
    filing_date = models.DateTimeField(auto_now_add=True)
    hearing_date = models.DateTimeField(null=True, blank=True)
    decision_date = models.DateTimeField(null=True, blank=True)
    
    # Case outcome
    verdict = models.TextField(blank=True, null=True)
    sentence = models.TextField(blank=True, null=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Metadata
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    SENTENCE_TYPE_CHOICES = [
        ('imprisonment', 'Imprisonment'),
        ('probation', 'Probation'),
        ('community_service', 'Community Service'),
        ('fine', 'Fine'),
        ('suspended', 'Suspended Sentence'),
        ('dismissed', 'Dismissed'),
    ]
    
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for enhanced workflow
    plaintiff_name = models.CharField(max_length=200, blank=True, null=True)
    defendant_name = models.CharField(max_length=200, blank=True, null=True)
    assigned_date = models.DateField(null=True, blank=True)
    assignment_notes = models.TextField(blank=True, null=True)
    sentence_type = models.CharField(max_length=20, choices=SENTENCE_TYPE_CHOICES, blank=True, null=True)
    sentence_duration = models.CharField(max_length=100, blank=True, null=True)
    sentence_notes = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.case_number} - {self.title}"
    
    class Meta:
        verbose_name = "Case"
        verbose_name_plural = "Cases"
        ordering = ['-filing_date']


class Evidence(models.Model):
    """Evidence attached to cases"""
    
    EVIDENCE_TYPES = [
        ('document', 'Document'),
        ('photo', 'Photo'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('physical', 'Physical Evidence'),
        ('witness', 'Witness Statement'),
        ('expert', 'Expert Report'),
    ]
    
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='evidence')
    evidence_type = models.CharField(max_length=20, choices=EVIDENCE_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    file_path = models.FileField(upload_to='evidence/', null=True, blank=True)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_evidence')
    submitted_by_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evidence_submitted', null=True, blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    is_admissible = models.BooleanField(default=True)
    
    # Additional fields for evidence review workflow
    is_approved = models.BooleanField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_evidence')
    reviewed_date = models.DateField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.case.case_number} - {self.title}"
    
    class Meta:
        verbose_name = "Evidence"
        verbose_name_plural = "Evidence"
        ordering = ['-submission_date']


class CaseReport(models.Model):
    """Final case reports submitted by judges"""
    
    REPORT_TYPES = [
        ('final', 'Final Report'),
        ('interim', 'Interim Report'),
        ('appeal', 'Appeal Report'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='final')
    title = models.CharField(max_length=200)
    content = models.TextField()
    recommendations = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Report metadata
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports')
    submission_date = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reports')
    approval_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.case.case_number} - {self.title}"
    
    class Meta:
        verbose_name = "Case Report"
        verbose_name_plural = "Case Reports"
        ordering = ['-submission_date']


class Hearing(models.Model):
    """Court hearing sessions"""
    
    HEARING_TYPES = [
        ('preliminary', 'Preliminary Hearing'),
        ('trial', 'Trial'),
        ('sentencing', 'Sentencing'),
        ('appeal', 'Appeal Hearing'),
        ('review', 'Review Hearing'),
    ]
    
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='hearings')
    hearing_type = models.CharField(max_length=20, choices=HEARING_TYPES)
    scheduled_date = models.DateTimeField()
    actual_date = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    courtroom = models.CharField(max_length=100, blank=True, null=True)
    
    # Participants
    judge = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hearings')
    clerk = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clerk_hearings', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_hearings', null=True, blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_hearings')
    
    # Hearing details
    location = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)
    outcome = models.TextField(blank=True, null=True)
    next_hearing_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_completed = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.case.case_number} - {self.hearing_type} - {self.scheduled_date.strftime('%Y-%m-%d')}"
    
    class Meta:
        verbose_name = "Hearing"
        verbose_name_plural = "Hearings"
        ordering = ['-scheduled_date']
