from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
import json


# ===================== Custom User Model =======================
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Super Admin'),
        ('officer', 'Officer'),
        ('citizen', 'Citizen'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


# ===================== Police Department =======================
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    established_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Suspended'})"


# ===================== Police Officer =======================
class Officer(models.Model):
    RANK_CHOICES = [
        ('ASP', 'Assistant Superintendent of Police'),
        ('DSP', 'Deputy Superintendent of Police'),
        ('SP', 'Superintendent of Police'),
        ('CSP', 'Chief Superintendent of Police'),
        ('ACP', 'Assistant Commissioner of Police'),
        ('DCP', 'Deputy Commissioner of Police'),
        ('CP', 'Commissioner of Police'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rank = models.CharField(max_length=50, choices=RANK_CHOICES)
    badge_number = models.CharField(max_length=30, unique=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='officers')
    profile_picture = models.ImageField(upload_to='officers/', blank=True, null=True)
    on_duty = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.rank}"


# ===================== Crime Report =======================
class CrimeReport(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Investigating', 'Investigating'),
        ('Resolved', 'Resolved'),
        ('Dismissed', 'Dismissed')
    )

    PRIORITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Emergency', 'Emergency')
    )

    INCIDENT_TYPES = [
       
        ('ASSAULT', 'Assault'),
        ('BURGLARY', 'Burglary'),
        ('THEFT', 'Theft'),
        ('ROBBERY', 'Robbery'),
        ('VANDALISM', 'Vandalism'),
        ('FRAUD', 'Fraud'),
        ('CYBERCRIME', 'Cyber Crime'),
        ('DRUG_OFFENSE', 'Drug Offense'),
        ('TRAFFIC_ACCIDENT', 'Traffic Accident'),
        ('DOMESTIC_VIOLENCE', 'Domestic Violence'),
        ('HARASSMENT', 'Harassment'),
        ('OTHER', 'Other'),
    ]

    report_id = models.CharField(max_length=12, unique=True, editable=False)
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    
    # GPS Coordinates
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    
    # Evidence Files
    evidence_image = models.ImageField(upload_to='evidence/images/%Y/%m/%d/', null=True, blank=True)
    evidence_video = models.FileField(upload_to='evidence/videos/%Y/%m/%d/', null=True, blank=True)
    evidence_audio = models.FileField(upload_to='evidence/audio/%Y/%m/%d/', null=True, blank=True)
    
    # Timestamps
    date_reported = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    # ==================== AI-ENHANCED FIELDS ====================
    ai_priority_suggestion = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        null=True, 
        blank=True,
        help_text="AI-suggested priority based on description analysis"
    )
    ai_priority_confidence = models.FloatField(
        default=0.0,
        help_text="Confidence score for AI priority suggestion (0-100)"
    )
    ai_incident_suggestion = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="AI-suggested incident type based on description"
    )
    ai_incident_confidence = models.FloatField(
        default=0.0,
        help_text="Confidence score for AI incident suggestion (0-100)"
    )
    ai_analysis_data = models.TextField(
        null=True, 
        blank=True,
        help_text="JSON field storing detailed AI analysis results"
    )
    ai_analyzed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when AI last analyzed this report"
    )
    ai_matched_keywords = models.TextField(
        null=True, 
        blank=True,
        help_text="JSON field storing keywords that triggered AI suggestions"
    )
    # ============================================================

    def save(self, *args, **kwargs):
        if not self.report_id:
            self.report_id = f"CR-{uuid.uuid4().hex[:8].upper()}"
        
        # Run AI analysis on new reports
        if not self.pk:  # New report
            self.run_ai_analysis()
        
        super().save(*args, **kwargs)

    # ==================== AI METHODS ====================
    def run_ai_analysis(self):
        """Run AI analysis on the report description"""
        from .ai_helper import CrimeAIAnalyzer
        
        if self.description and len(self.description.strip()) > 10:
            # Analyze priority
            priority_result = CrimeAIAnalyzer.analyze_priority(
                self.title, 
                self.description
            )
            self.ai_priority_suggestion = priority_result['suggested_priority']
            self.ai_priority_confidence = priority_result['confidence']
            
            # Analyze incident type
            incident_result = CrimeAIAnalyzer.analyze_incident_type(
                self.description
            )
            self.ai_incident_suggestion = incident_result['suggested_incident']
            self.ai_incident_confidence = incident_result['confidence']
            
            # Store full analysis as JSON
            self.ai_analysis_data = json.dumps({
                'priority': priority_result,
                'incident': incident_result,
                'analyzed_at': timezone.now().isoformat()
            })
            
            # Store matched keywords
            self.ai_matched_keywords = json.dumps({
                'priority_keywords': priority_result.get('matched_keywords', []),
                'incident_keywords': incident_result.get('matched_keywords', [])
            })
            
            self.ai_analyzed_at = timezone.now()
    
    def get_ai_summary(self):
        """Get formatted AI analysis summary"""
        if self.ai_priority_suggestion and self.ai_incident_suggestion:
            return {
                'priority': self.ai_priority_suggestion,
                'priority_conf': f"{self.ai_priority_confidence}%",
                'incident': self.ai_incident_suggestion,
                'incident_conf': f"{self.ai_incident_confidence}%",
                'analyzed': self.ai_analyzed_at.strftime('%Y-%m-%d %H:%M') if self.ai_analyzed_at else 'Not analyzed'
            }
        return None
    
    # ===== NEW HELPER METHODS =====
    def get_priority_keywords(self):
        """Extract priority keywords from stored JSON"""
        if self.ai_matched_keywords:
            try:
                data = json.loads(self.ai_matched_keywords)
                return data.get('priority_keywords', [])
            except:
                return []
        return []

    def get_incident_keywords(self):
        """Extract incident keywords from stored JSON"""
        if self.ai_matched_keywords:
            try:
                data = json.loads(self.ai_matched_keywords)
                return data.get('incident_keywords', [])
            except:
                return []
        return []
    
    def get_ai_priority_color(self):
        """Get color class for AI priority badge"""
        colors = {
            'Emergency': 'text-red-600 bg-red-100',
            'High': 'text-orange-600 bg-orange-100',
            'Medium': 'text-yellow-600 bg-yellow-100',
            'Low': 'text-green-600 bg-green-100',
        }
        return colors.get(self.ai_priority_suggestion, 'text-gray-600 bg-gray-100')
    
    @property
    def has_ai_analysis(self):
        """Check if report has AI analysis"""
        return self.ai_analyzed_at is not None
    # =============================

    def get_google_maps_url(self):
        """Generate Google Maps URL from coordinates"""
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None

    def get_static_map_url(self, size="400x300", zoom=15):
        """Generate static map image URL (requires Google Maps API key in production)"""
        if self.latitude and self.longitude:
            api_key = "YOUR_GOOGLE_MAPS_API_KEY"
            return f"https://maps.googleapis.com/maps/api/staticmap?center={self.latitude},{self.longitude}&zoom={zoom}&size={size}&markers=color:red%7C{self.latitude},{self.longitude}&key={api_key}"
        return None

    def get_status_badge_class(self):
        """Return CSS class for status badge"""
        status_classes = {
            'Pending': 'bg-yellow-100 text-yellow-800',
            'Investigating': 'bg-blue-100 text-blue-800',
            'Resolved': 'bg-green-100 text-green-800',
            'Dismissed': 'bg-red-100 text-red-800',
        }
        return status_classes.get(self.status, 'bg-gray-100 text-gray-800')

    def get_priority_badge_class(self):
        """Return CSS class for priority badge"""
        priority_classes = {
            'Low': 'bg-green-100 text-green-800',
            'Medium': 'bg-yellow-100 text-yellow-800',
            'High': 'bg-orange-100 text-orange-800',
            'Emergency': 'bg-red-100 text-red-800',
        }
        return priority_classes.get(self.priority, 'bg-gray-100 text-gray-800')

    def get_evidence_count(self):
        """Count total evidence files attached"""
        count = 0
        if self.evidence_image:
            count += 1
        if self.evidence_video:
            count += 1
        if self.evidence_audio:
            count += 1
        return count

    def is_owned_by(self, user):
        """Check if user owns this report"""
        return self.reporter == user

    def can_be_accessed_by(self, user):
        """Check if user can access this report"""
        if user.is_superuser or hasattr(user, 'officer'):
            return True
        return self.reporter == user

    @property
    def days_since_reported(self):
        """Calculate days since report was submitted"""
        return (timezone.now() - self.date_reported).days

    def __str__(self):
        return f"{self.title} ({self.report_id})"

    class Meta:
        ordering = ['-date_reported']
        indexes = [
            models.Index(fields=['status', 'date_reported']),
            models.Index(fields=['reporter', 'date_reported']),
            models.Index(fields=['department', 'date_reported']),
            # Index for AI queries
            models.Index(fields=['ai_priority_suggestion', 'date_reported']),
        ]
        verbose_name = "Crime Report"
        verbose_name_plural = "Crime Reports"


# ===================== Notification Models =======================

class Notification(models.Model):
    officer = models.ForeignKey(
        'Officer',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.officer.user.username} - {self.message[:50]}"
    

class CitizenNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('status_update', 'Status Update'),
        ('reminder', 'Reminder'),
        ('general', 'General'),
        ('ai_insight', 'AI Insight'),  # AI notification type
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_report = models.ForeignKey('CrimeReport', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"
    

class ReportReminder(models.Model):
    report = models.ForeignKey('CrimeReport', on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_acknowledged = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reminder for {self.report.title} - {self.created_at}"