from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Inmate(models.Model):
    """Inmate model for prison management"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('released', 'Released'),
        ('transferred', 'Transferred'),
        ('deceased', 'Deceased'),
        ('escaped', 'Escaped'),
    ]
    
    SENTENCE_TYPE_CHOICES = [
        ('prison', 'Prison Sentence'),
        ('probation', 'Probation'),
        ('fine', 'Fine Only'),
        ('community_service', 'Community Service'),
        ('life', 'Life Sentence'),
        ('death', 'Death Penalty'),
    ]
    
    # Personal Information
    inmate_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    nationality = models.CharField(max_length=100)
    identification_number = models.CharField(max_length=50, unique=True)
    
    # Contact Information
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)
    
    # Case Information
    case_number = models.CharField(max_length=50)
    conviction_date = models.DateField()
    crime_description = models.TextField()
    sentence_type = models.CharField(max_length=20, choices=SENTENCE_TYPE_CHOICES)
    sentence_duration_years = models.IntegerField(null=True, blank=True)
    sentence_duration_months = models.IntegerField(null=True, blank=True)
    sentence_duration_days = models.IntegerField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Prison Information
    admission_date = models.DateField()
    expected_release_date = models.DateField(null=True, blank=True)
    actual_release_date = models.DateField(null=True, blank=True)
    cell_number = models.CharField(max_length=20, blank=True, null=True)
    block = models.CharField(max_length=50, blank=True, null=True)
    
    # Management
    assigned_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_inmates')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    assignment_date = models.DateField(null=True, blank=True)
    assignment_reason = models.TextField(blank=True, null=True)
    assignment_type = models.CharField(max_length=50, blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)
    
    # Behavior and Health
    BEHAVIOR_RATING_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    behavior_rating = models.CharField(max_length=10, choices=BEHAVIOR_RATING_CHOICES, default='good')
    medical_conditions = models.TextField(blank=True, null=True)
    special_needs = models.TextField(blank=True, null=True)
    medical_attention_required = models.BooleanField(default=False)
    disciplinary_issues = models.BooleanField(default=False)
    protective_custody = models.BooleanField(default=False)
    last_health_check = models.DateField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def days_until_release(self):
        if self.expected_release_date:
            delta = self.expected_release_date - timezone.now().date()
            return delta.days if delta.days > 0 else 0
        return None
    
    def is_release_approaching(self, days=7):
        """Check if release date is within specified days"""
        if self.expected_release_date:
            return self.days_until_release() <= days
        return False
    
    def __str__(self):
        return f"{self.inmate_id} - {self.get_full_name()}"
    
    class Meta:
        verbose_name = "Inmate"
        verbose_name_plural = "Inmates"
        ordering = ['last_name', 'first_name']


class InmateReport(models.Model):
    """Reports submitted by prison officers about inmates"""
    
    REPORT_TYPE_CHOICES = [
        ('regular', 'Regular Report'),
        ('urgent', 'Urgent Report'),
        ('disciplinary', 'Disciplinary Report'),
        ('medical', 'Medical Report'),
        ('behavioral', 'Behavioral Report'),
        ('incident', 'Incident Report'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    inmate = models.ForeignKey(Inmate, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    recommendations = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Report metadata
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inmate_reports')
    submission_date = models.DateTimeField(auto_now_add=True)
    incident_date = models.DateTimeField(null=True, blank=True)
    
    # Review status
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_inmate_reports')
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Actions taken
    action_required = models.BooleanField(default=False)
    action_taken = models.TextField(blank=True, null=True)
    action_date = models.DateTimeField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    
    def mark_as_reviewed(self, reviewer, notes=""):
        """Mark report as reviewed"""
        self.is_reviewed = True
        self.reviewed_by = reviewer
        self.review_date = timezone.now()
        self.review_notes = notes
        self.save()
    
    def __str__(self):
        return f"{self.inmate.inmate_id} - {self.title}"
    
    class Meta:
        verbose_name = "Inmate Report"
        verbose_name_plural = "Inmate Reports"
        ordering = ['-submission_date']


class VisitorLog(models.Model):
    """Log of inmate visitors"""
    
    VISIT_TYPE_CHOICES = [
        ('family', 'Family Visit'),
        ('legal', 'Legal Visit'),
        ('official', 'Official Visit'),
        ('medical', 'Medical Visit'),
        ('religious', 'Religious Visit'),
    ]
    
    RELATIONSHIP_CHOICES = [
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
        ('friend', 'Friend'),
        ('lawyer', 'Lawyer'),
        ('doctor', 'Doctor'),
        ('clergy', 'Clergy'),
        ('other', 'Other'),
    ]
    
    inmate = models.ForeignKey(Inmate, on_delete=models.CASCADE, related_name='visitor_logs')
    visitor_name = models.CharField(max_length=200)
    visitor_id_number = models.CharField(max_length=50, blank=True, null=True)
    visitor_phone = models.CharField(max_length=20, blank=True, null=True)
    relationship = models.CharField(max_length=100, choices=RELATIONSHIP_CHOICES)
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPE_CHOICES)
    
    # Visit details
    visit_date = models.DateTimeField()
    visit_duration_minutes = models.IntegerField()
    purpose = models.TextField()
    notes = models.TextField(blank=True, null=True)
    
    # Authorization
    authorized_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authorized_visits')
    is_approved = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.inmate.inmate_id} - {self.visitor_name} - {self.visit_date.strftime('%Y-%m-%d')}"
    
    class Meta:
        verbose_name = "Visitor Log"
        verbose_name_plural = "Visitor Logs"
        ordering = ['-visit_date']


class InmateProgram(models.Model):
    """Rehabilitation and education programs for inmates"""
    
    PROGRAM_TYPE_CHOICES = [
        ('education', 'Education'),
        ('vocational', 'Vocational Training'),
        ('counseling', 'Counseling'),
        ('therapy', 'Therapy'),
        ('work', 'Work Program'),
        ('religious', 'Religious Program'),
        ('recreation', 'Recreation'),
    ]
    
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('suspended', 'Suspended'),
    ]
    
    inmate = models.ForeignKey(Inmate, on_delete=models.CASCADE, related_name='programs')
    program_name = models.CharField(max_length=200)
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPE_CHOICES)
    description = models.TextField()
    
    # Program timeline
    start_date = models.DateField()
    expected_end_date = models.DateField()
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Progress tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    progress_percentage = models.IntegerField(default=0)
    instructor = models.CharField(max_length=200, blank=True, null=True)
    
    # Outcomes
    grade_or_score = models.CharField(max_length=10, blank=True, null=True)
    certificate_earned = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.inmate.inmate_id} - {self.program_name}"
    
    class Meta:
        verbose_name = "Inmate Program"
        verbose_name_plural = "Inmate Programs"
        ordering = ['-start_date']
