from django.contrib import admin
from django.utils.html import format_html
from .models import *

# ==================== Custom Admin Configurations ====================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'get_full_name', 'email', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('username', 'password', 'email', 'role')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone', 'address')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'last_name'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'contact_number', 'officer_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'location', 'contact_number']
    ordering = ['name']
    
    def officer_count(self, obj):
        count = obj.officers.count()
        url = f"/admin/crime_app/officer/?department__id__exact={obj.id}"
        return format_html('<a href="{}">{} Officer{}</a>', url, count, 's' if count != 1 else '')
    officer_count.short_description = 'Officers'


@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ['badge_number', 'get_name', 'rank', 'department', 'on_duty', 'get_contact']
    list_filter = ['rank', 'department', 'on_duty']
    search_fields = ['badge_number', 'user__first_name', 'user__last_name', 'user__email']
    raw_id_fields = ['user', 'department']
    
    fieldsets = (
        ('Officer Information', {
            'fields': ('user', 'rank', 'badge_number', 'department')
        }),
        ('Status', {
            'fields': ('on_duty', 'profile_picture')
        }),
    )
    
    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_name.short_description = 'Name'
    get_name.admin_order_field = 'user__last_name'
    
    def get_contact(self, obj):
        return obj.user.email or obj.user.phone or '-'
    get_contact.short_description = 'Contact'


@admin.register(CrimeReport)
class CrimeReportAdmin(admin.ModelAdmin):
    list_display = ['report_id', 'title', 'incident_type_colored', 'priority_colored', 
                    'status_colored', 'department', 'date_reported_short', 
                    'ai_priority_badge', 'get_evidence_badge']
    
    list_filter = ['status', 'priority', 'incident_type', 'department', 
                   'date_reported', 'ai_priority_suggestion']  # Added AI filter
    
    search_fields = ['report_id', 'title', 'description', 'location']
    readonly_fields = ['report_id', 'date_reported', 'date_updated', 
                       'ai_analysis_display', 'ai_keywords_display']  # Added AI read-only fields
    raw_id_fields = ['reporter', 'department']
    
    fieldsets = (
        ('Report Identification', {
            'fields': ('report_id', 'title', 'description')
        }),
        ('Classification', {
            'fields': ('incident_type', 'priority', 'status')
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Assignment', {
            'fields': ('reporter', 'department')
        }),
        ('Evidence', {
            'fields': ('evidence_image', 'evidence_video', 'evidence_audio'),
            'classes': ('wide',)
        }),
        ('AI Analysis', {  # NEW: AI section
            'fields': ('ai_priority_suggestion', 'ai_priority_confidence', 
                      'ai_incident_suggestion', 'ai_incident_confidence',
                      'ai_analyzed_at', 'ai_analysis_display', 'ai_keywords_display'),
            'classes': ('wide', 'collapse'),
        }),
        ('Timestamps', {
            'fields': ('date_reported', 'date_updated')
        }),
    )
    
    # ==================== Custom Display Methods ====================
    
    def incident_type_colored(self, obj):
        colors = {
            'ROBBERY': 'red',
            'ASSAULT': 'orange',
            'THEFT': 'yellow',
            'BURGLARY': 'purple',
            'FRAUD': 'pink',
            'CYBERCRIME': 'blue',
        }
        color = colors.get(obj.incident_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em;">{}</span>',
            color, obj.incident_type
        )
    incident_type_colored.short_description = 'Incident Type'
    
    def priority_colored(self, obj):
        colors = {
            'Emergency': '#dc2626',  # red-600
            'High': '#f97316',        # orange-500
            'Medium': '#eab308',      # yellow-500
            'Low': '#16a34a',         # green-600
        }
        color = colors.get(obj.priority, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em;">{}</span>',
            color, obj.priority
        )
    priority_colored.short_description = 'Priority'
    
    def status_colored(self, obj):
        colors = {
            'Pending': '#eab308',      # yellow-500
            'Investigating': '#3b82f6', # blue-500
            'Resolved': '#22c55e',      # green-500
            'Dismissed': '#6b7280',     # gray-500
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em;">{}</span>',
            color, obj.status
        )
    status_colored.short_description = 'Status'
    
    def date_reported_short(self, obj):
        return obj.date_reported.strftime('%Y-%m-%d %H:%M')
    date_reported_short.short_description = 'Reported'
    date_reported_short.admin_order_field = 'date_reported'
    
    def get_evidence_badge(self, obj):
        count = obj.get_evidence_count()
        if count == 0:
            return '📁 None'
        elif count == 1:
            return '📁 1 file'
        else:
            return f'📁 {count} files'
    get_evidence_badge.short_description = 'Evidence'
    
    # ==================== NEW AI Display Methods ====================
    
    def ai_priority_badge(self, obj):
        if obj.ai_priority_suggestion:
            colors = {
                'Emergency': '#dc2626',
                'High': '#f97316',
                'Medium': '#eab308',
                'Low': '#16a34a',
            }
            color = colors.get(obj.ai_priority_suggestion, '#6b7280')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.7em;">{} ({:.0f}%)</span>',
                color, obj.ai_priority_suggestion, obj.ai_priority_confidence
            )
        return '-'
    ai_priority_badge.short_description = 'AI Priority'
    ai_priority_badge.admin_order_field = 'ai_priority_suggestion'
    
    def ai_analysis_display(self, obj):
        if obj.ai_analysis_data:
            try:
                import json
                data = json.loads(obj.ai_analysis_data)
                priority = data.get('priority', {})
                incident = data.get('incident', {})
                
                html = '<div style="background: #f3f4f6; padding: 10px; border-radius: 5px;">'
                html += '<h4 style="margin: 0 0 5px 0; color: #1f2937;">📊 AI Analysis Results</h4>'
                
                # Priority details
                html += '<div style="margin-bottom: 8px;">'
                html += f'<strong>Priority:</strong> {priority.get("suggested_priority", "N/A")} '
                html += f'({priority.get("confidence", 0):.1f}% confidence)<br>'
                html += f'<small>Keywords: {", ".join(priority.get("matched_keywords", ["none"]))}</small>'
                html += '</div>'
                
                # Incident details
                html += '<div>'
                html += f'<strong>Incident:</strong> {incident.get("suggested_incident", "N/A")} '
                html += f'({incident.get("confidence", 0):.1f}% confidence)<br>'
                html += f'<small>Keywords: {", ".join(incident.get("matched_keywords", ["none"]))}</small>'
                html += '</div>'
                
                html += '</div>'
                return format_html(html)
            except:
                return obj.ai_analysis_data
        return '-'
    ai_analysis_display.short_description = 'AI Analysis Details'
    
    def ai_keywords_display(self, obj):
        if obj.ai_matched_keywords:
            try:
                import json
                keywords = json.loads(obj.ai_matched_keywords)
                priority_kw = keywords.get('priority_keywords', [])
                incident_kw = keywords.get('incident_keywords', [])
                
                html = '<div style="display: flex; gap: 20px;">'
                
                if priority_kw:
                    html += '<div><strong>Priority:</strong> '
                    html += ', '.join([f'<span style="background: #dbeafe; padding: 2px 5px; border-radius: 3px; margin: 2px; display: inline-block;">{k}</span>' for k in priority_kw])
                    html += '</div>'
                
                if incident_kw:
                    html += '<div><strong>Incident:</strong> '
                    html += ', '.join([f'<span style="background: #f3e8ff; padding: 2px 5px; border-radius: 3px; margin: 2px; display: inline-block;">{k}</span>' for k in incident_kw])
                    html += '</div>'
                
                html += '</div>'
                return format_html(html)
            except:
                return obj.ai_matched_keywords
        return '-'
    ai_keywords_display.short_description = 'Matched Keywords'
    
    # ==================== Actions ====================
    
    actions = ['mark_as_resolved', 'mark_as_investigating', 'run_ai_analysis']
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='Resolved')
    mark_as_resolved.short_description = "Mark selected reports as Resolved"
    
    def mark_as_investigating(self, request, queryset):
        queryset.update(status='Investigating')
    mark_as_investigating.short_description = "Mark selected reports as Investigating"
    
    def run_ai_analysis(self, request, queryset):
        for report in queryset:
            report.run_ai_analysis()
            report.save()
        self.message_user(request, f"AI analysis completed for {queryset.count()} reports.")
    run_ai_analysis.short_description = "Run AI analysis on selected reports"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['officer', 'message_short', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['officer__user__username', 'message']
    readonly_fields = ['created_at']
    
    def message_short(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Message'


@admin.register(CitizenNotification)
class CitizenNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    raw_id_fields = ['user', 'related_report']


@admin.register(ReportReminder)
class ReportReminderAdmin(admin.ModelAdmin):
    list_display = ['report', 'user', 'message_short', 'is_acknowledged', 'created_at']
    list_filter = ['is_acknowledged', 'created_at']
    search_fields = ['report__title', 'user__username', 'message']
    raw_id_fields = ['report', 'user']
    
    def message_short(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Message'


# ==================== Custom Admin Site Configuration ====================

admin.site.site_header = "QuickReport Nigeria Administration"
admin.site.site_title = "QuickReport Admin"
admin.site.index_title = "Crime Reporting System Dashboard"