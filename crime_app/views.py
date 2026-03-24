from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.db.models import Count, Q, F, Avg
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import json
from collections import Counter

from .models import *
from .forms import *

User = get_user_model()

# =============================================================================
# HOME PAGE
# =============================================================================
def index(request):
    """Home page view"""
    return render(request, 'crime_app/homePage/index.html')


# =============================================================================
# AUTHENTICATION
# =============================================================================
def my_login(request):
    """User login view"""
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            if user.is_superuser or getattr(user, 'role', None) == 'admin':
                return redirect('dashboard')
            elif getattr(user, 'role', None) == 'officer':
                return redirect('officer-board')
            else:
                return redirect('user-board')
        else:
            form.add_error(None, 'Invalid email or password')

    return render(request, 'crime_app/homePage/my-login.html', {'form': form})


def register(request):
    """User registration view"""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please login to continue.')
            return redirect('my-login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'crime_app/homePage/register.html', {'form': form})


def my_logout(request):
    """User logout view"""
    logout(request)
    return redirect('my-login')


# =============================================================================
# ADMIN DASHBOARD
# =============================================================================
def dashboard(request):
    """Admin dashboard with AI metrics"""
    # Check if user is admin
    if not request.user.is_authenticated or (not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin'):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('my-login')
    
    # Basic stats
    total_reports = CrimeReport.objects.count()
    resolved_cases = CrimeReport.objects.filter(status='Resolved').count()
    pending_reports = CrimeReport.objects.filter(status='Pending').count()
    total_departments = Department.objects.count()
    recent_reports = CrimeReport.objects.select_related('reporter').order_by('-date_reported')[:5]
    
    # ===== AI METRICS =====
    ai_analyzed = CrimeReport.objects.exclude(ai_analyzed_at__isnull=True).count()
    ai_coverage = round((ai_analyzed / total_reports * 100), 1) if total_reports > 0 else 0
    
    analyzed = CrimeReport.objects.exclude(ai_analyzed_at__isnull=True)
    if analyzed.exists():
        matches = analyzed.filter(priority=F('ai_priority_suggestion')).count()
        ai_accuracy = round((matches / analyzed.count()) * 100, 1)
    else:
        ai_accuracy = 0
    
    priority_dist = {
        'Emergency': CrimeReport.objects.filter(ai_priority_suggestion='Emergency').count(),
        'High': CrimeReport.objects.filter(ai_priority_suggestion='High').count(),
        'Medium': CrimeReport.objects.filter(ai_priority_suggestion='Medium').count(),
        'Low': CrimeReport.objects.filter(ai_priority_suggestion='Low').count(),
    }
    
    high_conf = CrimeReport.objects.filter(ai_priority_confidence__gte=80).count()
    medium_conf = CrimeReport.objects.filter(ai_priority_confidence__gte=50, ai_priority_confidence__lt=80).count()
    low_conf = CrimeReport.objects.filter(ai_priority_confidence__lt=50).exclude(ai_priority_confidence=0).count()
    
    avg_confidence = CrimeReport.objects.aggregate(avg_conf=Avg('ai_priority_confidence'))['avg_conf'] or 0
    
    dept_ai_counts = Department.objects.annotate(
        ai_count=Count('crimereport', filter=Q(crimereport__ai_analyzed_at__isnull=False))
    ).values('name', 'ai_count').order_by('-ai_count')[:5]
    
    ai_conflicts = CrimeReport.objects.exclude(
        priority=F('ai_priority_suggestion')
    ).exclude(ai_priority_suggestion__isnull=True).count()
    
    # Monthly trend
    today = timezone.now().date()
    monthly_ai_data = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year+1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_date.replace(month=month_date.month+1, day=1) - timedelta(days=1)
        
        month_count = CrimeReport.objects.filter(
            ai_analyzed_at__date__gte=month_start,
            ai_analyzed_at__date__lte=month_end
        ).count()
        
        monthly_ai_data.append({'month': month_date.strftime('%b'), 'count': month_count})
    
    # Top keywords
    all_keywords = []
    for report in CrimeReport.objects.exclude(ai_matched_keywords__isnull=True).exclude(ai_matched_keywords='')[:100]:
        try:
            data = json.loads(report.ai_matched_keywords)
            all_keywords.extend(data.get('priority_keywords', []))
            all_keywords.extend(data.get('incident_keywords', []))
        except:
            pass
    
    keyword_counts = Counter(all_keywords)
    top_keywords = []
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink', 'indigo']
    
    for i, (word, count) in enumerate(keyword_counts.most_common(10)):
        top_keywords.append({'word': word, 'count': count, 'color': colors[i % len(colors)]})
    
    context = {
        # Basic stats
        'total_reports': total_reports,
        'resolved_cases': resolved_cases,
        'pending_reports': pending_reports,
        'total_departments': total_departments,
        'recent_reports': recent_reports,
        
        # AI METRICS
        'ai_analyzed': ai_analyzed,
        'ai_coverage': ai_coverage,
        'ai_accuracy': ai_accuracy,
        'priority_dist': priority_dist,
        'high_conf': high_conf,
        'medium_conf': medium_conf,
        'low_conf': low_conf,
        'avg_confidence': round(avg_confidence, 1),
        'dept_ai_counts': dept_ai_counts,
        'ai_conflicts': ai_conflicts,
        'monthly_ai_data': monthly_ai_data,
        'top_keywords': top_keywords,
    }
    
    return render(request, 'crime_app/adminPage/dashboard.html', context)


def officer_list(request):
    """Admin view for managing officers"""
    if not request.user.is_authenticated or (not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin'):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('my-login')
        
    if request.method == 'POST':
        form = OfficerForm(request.POST, request.FILES)
        if form.is_valid():
            officer = form.save()
            messages.success(request, f"Officer {officer.user.get_full_name()} added successfully!")
            return redirect('officer-list')
    else:
        form = OfficerForm()

    officers = Officer.objects.all()
    departments = Department.objects.all()  # ADD THIS LINE
    
    return render(request, 'crime_app/adminPage/officer-list.html', {
        'form': form, 
        'officers': officers,
        'departments': departments  # ADD THIS LINE
    })

def department_list(request):
    """Admin view for managing departments"""
    if not request.user.is_authenticated or (not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin'):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('my-login')
        
    departments = Department.objects.annotate(officer_count=Count('officers'))
    form = DepartmentForm()

    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created successfully!")
            return redirect('department')

    return render(request, 'crime_app/adminPage/department.html', {
        'departments': departments,
        'form': form,
    })


def reported_crime(request):
    """Admin view for all crime reports"""
    if not request.user.is_authenticated or (not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin'):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('my-login')
        
    reports = CrimeReport.objects.all().order_by('status')
    return render(request, 'crime_app/adminPage/reported-crime.html', {'reports': reports})


def crime_detail(request, pk):
    """Admin view for single crime report"""
    if not request.user.is_authenticated or (not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin'):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('my-login')
        
    report = get_object_or_404(CrimeReport, id=pk)
    departments = Department.objects.all()
    return render(request, 'crime_app/adminPage/crime-detail.html', {
        'report': report,
        'departments': departments
    })


def update_report_status(request, pk):
    """Admin view for updating report status"""
    if not request.user.is_authenticated or (not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin'):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('my-login')
        
    report = get_object_or_404(CrimeReport, id=pk)
    if request.method == 'POST':
        old_status = report.status
        old_dept = report.department
        new_status = request.POST.get('status')
        dept_id = request.POST.get('department')

        if dept_id:
            report.department_id = dept_id

        report.status = new_status
        report.save()

        # Citizen notifications
        if old_status != new_status:
            CitizenNotification.objects.create(
                user=report.reporter,
                notification_type='status_update',
                title='Report Status Updated',
                message=f'Your report "{report.title}" status has been changed from {old_status} to {new_status} by Administrator.',
                related_report=report
            )

        if dept_id and old_dept and str(old_dept.id) != str(dept_id):
            new_department = Department.objects.get(id=dept_id)
            CitizenNotification.objects.create(
                user=report.reporter,
                notification_type='assignment',
                title='Report Reassigned',
                message=f'Your report "{report.title}" has been reassigned from {old_dept.name} to {new_department.name}.',
                related_report=report
            )

            # Notify new department officers
            for officer in Officer.objects.filter(department_id=dept_id):
                Notification.objects.create(
                    officer=officer,
                    message=f"📢 New case '{report.title}' has been assigned to your department."
                )

        messages.success(request, "Report updated successfully!")
        return redirect('crime-detail', pk=report.id)


def search_crime(request):
    """Admin search for crime reports"""
    if not request.user.is_authenticated or (not request.user.is_superuser and getattr(request.user, 'role', None) != 'admin'):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('my-login')
        
    query = request.GET.get('q', '')
    results = CrimeReport.objects.filter(
        Q(pk__icontains=query) | Q(location__icontains=query) | 
        Q(status__icontains=query) | Q(incident_type__icontains=query)
    ) if query else []

    return render(request, 'crime_app/adminPage/search-crime.html', {
        'results': results,
        'query': query
    })


# =============================================================================
# OFFICER DASHBOARD
# =============================================================================
def officer_board(request):
    """Officer dashboard with AI insights"""
    if not hasattr(request.user, 'officer'):
        messages.error(request, "Only officers can access this page.")
        return redirect('my-login')

    officer = request.user.officer
    officer_dept = officer.department   
    reports = CrimeReport.objects.filter(department=officer_dept)
    
    # Basic stats
    total_reports = reports.count()
    resolved_cases = reports.filter(status='Resolved').count()
    pending_cases = reports.filter(status='Pending').count()
    dismissed_cases = reports.filter(status='Dismissed').count()
    investigating_cases = reports.filter(status='Investigating').count()
    
    # AI Stats
    ai_emergency_count = reports.filter(ai_priority_suggestion='Emergency').count()
    ai_high_count = reports.filter(ai_priority_suggestion='High').count()
    ai_medium_count = reports.filter(ai_priority_suggestion='Medium').count()
    ai_low_count = reports.filter(ai_priority_suggestion='Low').count()
    
    analyzed_reports = reports.exclude(ai_analyzed_at__isnull=True)
    ai_analyzed = analyzed_reports.count()
    
    if ai_analyzed > 0:
        matches = analyzed_reports.filter(priority=F('ai_priority_suggestion')).count()
        ai_accuracy = round((matches / ai_analyzed) * 100, 1)
    else:
        ai_accuracy = 0
    
    high_confidence_count = analyzed_reports.filter(ai_priority_confidence__gte=80).count()
    
    # Keywords
    all_keywords = []
    for report in reports.exclude(ai_matched_keywords__isnull=True).exclude(ai_matched_keywords='')[:50]:
        try:
            data = json.loads(report.ai_matched_keywords)
            all_keywords.extend(data.get('priority_keywords', []))
            all_keywords.extend(data.get('incident_keywords', []))
        except:
            pass
    
    keyword_counts = Counter(all_keywords)
    top_keywords = []
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink', 'indigo']
    
    for i, (word, count) in enumerate(keyword_counts.most_common(8)):
        top_keywords.append({'word': word, 'count': count, 'color': colors[i % len(colors)]})
    
    ai_pending_high = reports.filter(status='Pending', ai_priority_suggestion__in=['Emergency', 'High']).count()
    
    investigating = reports.filter(status='Investigating')
    investigating_confidence = round(investigating.aggregate(avg_conf=Avg('ai_priority_confidence'))['avg_conf'] or 0, 1) if investigating.exists() else 0
    
    # Chart data
    today = timezone.now().date()
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    cases_by_day = []
    
    for i in range(6, -1, -1):
        day_date = today - timedelta(days=i)
        day_count = reports.filter(date_reported__date=day_date).count()
        cases_by_day.append({
            'day': days_of_week[day_date.weekday()],
            'count': day_count,
            'date': day_date
        })
    
    week_start = today - timedelta(days=today.weekday())
    this_week_count = reports.filter(date_reported__date__gte=week_start).count()
    
    recent_reports = reports.order_by('-date_reported')[:10]
    new_reports = reports.order_by('-date_reported')[:5]
    
    context = {
        # Basic counts
        'total_reports': total_reports,
        'resolved_cases': resolved_cases,
        'pending_cases': pending_cases,
        'dismissed_cases': dismissed_cases,
        'investigating_cases': investigating_cases,
        
        # AI STATS
        'ai_emergency_count': ai_emergency_count,
        'ai_high_count': ai_high_count,
        'ai_medium_count': ai_medium_count,
        'ai_low_count': ai_low_count,
        'ai_accuracy': ai_accuracy,
        'ai_analyzed': ai_analyzed,
        'high_confidence_count': high_confidence_count,
        'top_keywords': top_keywords,
        'ai_pending_high': ai_pending_high,
        'investigating_confidence': investigating_confidence,
        'emergency_response_time': 12,
        
        # Chart data
        'cases_by_day': cases_by_day,
        'total_this_week': this_week_count,
        
        # Reports
        'recent_reports': recent_reports,
        'new_reports': new_reports,
    }
    
    return render(request, 'crime_app/officerPage/officer-board.html', context)


def add_report(request):
    """Officer view for adding crime reports"""
    if not hasattr(request.user, 'officer'):
        messages.error(request, "Only officers can access this page.")
        return redirect('my-login')

    if request.method == 'POST':
        form = CrimeReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.evidence_image = request.FILES.get('photo_file') or request.FILES.get('evidence_image')
            report.evidence_audio = request.FILES.get('audio_file') or request.FILES.get('evidence_audio')
            report.evidence_video = request.FILES.get('video_file') or request.FILES.get('evidence_video')
            report.reporter = request.user
            report.department = request.user.officer.department
            report.save()

            # Notify officers
            if report.department:
                for officer in Officer.objects.filter(department=report.department):
                    Notification.objects.create(
                        officer=officer,
                        message=f"🚨 New crime reported in your department: {report.title}"
                    )

            messages.success(request, "Crime report submitted successfully!")
            return redirect('officer-board')
    else:
        form = CrimeReportForm()

    reports = CrimeReport.objects.filter(department=request.user.officer.department).order_by('-date_reported')
    return render(request, 'crime_app/officerPage/add-report.html', {'form': form, 'reports': reports})


def report_detail(request, pk):
    """Officer view for single report details"""
    if not hasattr(request.user, 'officer'):
        messages.error(request, "Only officers can access this page.")
        return redirect('my-login')

    crime = get_object_or_404(CrimeReport, id=pk)
    
    if crime.department != request.user.officer.department:
        messages.error(request, "You can only access reports from your department.")
        return redirect('officer-board')
        
    return render(request, 'crime_app/officerPage/report-detail.html', {'crime': crime})


def update_status(request, pk):
    """Officer view for updating report status"""
    if not hasattr(request.user, 'officer'):
        messages.error(request, "Only officers can access this page.")
        return redirect('my-login')

    report = get_object_or_404(CrimeReport, id=pk)
    officer = request.user.officer

    if report.department != officer.department:
        messages.error(request, "You can only update reports within your department.")
        return redirect('report-detail', pk=report.id)

    if request.method == 'POST':
        old_status = report.status
        new_status = request.POST.get('status')
        
        if new_status:
            report.status = new_status
            report.save()
            
            if old_status != new_status:
                CitizenNotification.objects.create(
                    user=report.reporter,
                    notification_type='status_update',
                    title='Report Status Updated',
                    message=f'Your report "{report.title}" status has been updated from {old_status} to {new_status} by Officer {request.user.get_full_name()}.',
                    related_report=report
                )
            
            # Notify other officers
            for o in Officer.objects.filter(department=report.department).exclude(id=officer.id):
                Notification.objects.create(
                    officer=o,
                    message=f"⚙️ Status of case '{report.title}' updated to {new_status} by {request.user.get_full_name()}."
                )
            
            messages.success(request, f"Report status updated to {new_status}.")
        else:
            messages.error(request, "Please select a valid status.")

    return redirect('report-detail', pk=report.id)


def search_report(request):
    """Officer search for reports"""
    if not hasattr(request.user, 'officer'):
        messages.error(request, "Only officers can access this page.")
        return redirect('my-login')

    officer = request.user.officer
    query = request.GET.get('q', '')
    
    results = CrimeReport.objects.filter(
        Q(department=officer.department) & (
            Q(report_id__icontains=query) | Q(location__icontains=query) |
            Q(status__icontains=query) | Q(incident_type__icontains=query)
        )
    ) if query else CrimeReport.objects.filter(department=officer.department)

    return render(request, 'crime_app/officerPage/search-report.html', {
        'results': results,
        'query': query
    })


# =============================================================================
# CITIZEN DASHBOARD
# =============================================================================
def user_board(request):
    """Citizen dashboard view"""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to access your dashboard.")
        return redirect('my-login')
    
    if hasattr(request.user, 'officer') or (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
        messages.error(request, "This page is for citizens only.")
        return redirect('dashboard' if request.user.is_superuser or getattr(request.user, 'role', None) == 'admin' else 'officer-board')
    
    user_reports = CrimeReport.objects.filter(reporter=request.user).order_by('-date_reported')
    
    context = {
        'total_reports': user_reports.count(),
        'resolved_reports': user_reports.filter(status='Resolved').count(),
        'pending_reports': user_reports.filter(status='Pending').count(),
        'recent_reports': user_reports[:4],
        'unread_count': CitizenNotification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'crime_app/citizenPage/user-board.html', context)


def user_report(request):
    """Citizen view for submitting crime reports"""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to report a crime.")
        return redirect('my-login')
    
    if hasattr(request.user, 'officer') or (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
        messages.error(request, "Officers and admins cannot submit citizen reports.")
        return redirect('dashboard' if request.user.is_superuser or getattr(request.user, 'role', None) == 'admin' else 'officer-board')
    
    if request.method == 'POST':
        form = CrimeReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            
            # GPS
            if request.POST.get('latitude') and request.POST.get('longitude'):
                report.latitude = request.POST.get('latitude')
                report.longitude = request.POST.get('longitude')
            
            # Evidence
            report.evidence_image = request.FILES.get('photo_file') or request.FILES.get('evidence_image')
            report.evidence_video = request.FILES.get('video_file') or request.FILES.get('evidence_video')
            report.evidence_audio = request.FILES.get('audio_file') or request.FILES.get('evidence_audio')
            
            report.save()
            
            # Notify officers
            if report.department:
                for officer in Officer.objects.filter(department=report.department):
                    Notification.objects.create(
                        officer=officer,
                        message=f"🚨 New crime reported: {report.title} (ID: {report.id})"
                    )
            
            messages.success(request, "Crime report submitted successfully!")
            return redirect('user-board')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CrimeReportForm()

    return render(request, 'crime_app/citizenPage/user-report.html', {'form': form})


def report_history(request):
    """Citizen view for report history"""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view your report history.")
        return redirect('my-login')
    
    if hasattr(request.user, 'officer') or (request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'):
        messages.error(request, "This page is for citizens only.")
        return redirect('dashboard' if request.user.is_superuser or getattr(request.user, 'role', None) == 'admin' else 'officer-board')
    
    user_reports = CrimeReport.objects.filter(reporter=request.user).order_by('-date_reported')
    
    context = {
        'reports': user_reports,
        'total_reports': user_reports.count(),
        'pending_reports': user_reports.filter(status='Pending').count(),
        'resolved_reports': user_reports.filter(status='Resolved').count(),
        'dismissed_reports': user_reports.filter(status='Dismissed').count(),
    }
    return render(request, 'crime_app/citizenPage/report-history.html', context)


def c_report_detail(request, pk):
    """Citizen view for single report details"""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view report details.")
        return redirect('my-login')
    
    try:
        report = CrimeReport.objects.get(id=pk)
        if report.reporter != request.user and not (hasattr(request.user, 'officer') or request.user.is_superuser):
            messages.error(request, "You don't have permission to view this report.")
            return redirect('user-board')
    except CrimeReport.DoesNotExist:
        messages.error(request, "Report not found.")
        return redirect('user-board')
    
    return render(request, 'crime_app/citizenPage/c-report-detail.html', {'report': report})


# =============================================================================
# NOTIFICATIONS
# =============================================================================
def citizen_notifications(request):
    """Citizen notifications view"""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to view notifications.")
        return redirect('my-login')
    
    notifications = CitizenNotification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'crime_app/citizenPage/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@csrf_exempt
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    if request.method == "POST" and request.user.is_authenticated:
        try:
            notification = CitizenNotification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'success'})
        except CitizenNotification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notification not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@csrf_exempt
def mark_all_notifications_read(request):
    """Mark all citizen notifications as read"""
    if request.method == "POST" and request.user.is_authenticated:
        count = CitizenNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success', 'count': count})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@csrf_exempt
def mark_notifications_read(request):
    """Mark all officer notifications as read"""
    if request.method == "POST":
        if hasattr(request.user, "officer"):
            count = Notification.objects.filter(officer=request.user.officer, is_read=False).update(is_read=True)
            return JsonResponse({"status": "success", "count": count})
        else:
            return JsonResponse({"status": "error", "message": "User is not an officer"}, status=403)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


# =============================================================================
# AI
# =============================================================================
def ai_analyze_realtime(request):
    """AJAX endpoint for real-time AI analysis during report submission"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            title = data.get('title', '')
            description = data.get('description', '')
            
            if not description or len(description.strip()) < 10:
                return JsonResponse({'success': False, 'error': 'Description too short'})
            
            from .ai_helper import CrimeAIAnalyzer
            priority_result = CrimeAIAnalyzer.analyze_priority(title, description)
            incident_result = CrimeAIAnalyzer.analyze_incident_type(description)
            
            return JsonResponse({
                'success': True,
                'priority': priority_result,
                'incident': incident_result
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})