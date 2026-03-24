from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.index, name='index'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('my-login/', views.my_login, name='my-login'),
    path('logout/', views.my_logout, name='logout'),
    
    # Admin URLs - FIXED: Added trailing slashes
    path('dashboard/', views.dashboard, name='dashboard'),
    path('officer-list/', views.officer_list, name='officer-list'),  # Fixed trailing slash
    path('department/', views.department_list, name='department'),
    path('reported-crime/', views.reported_crime, name='reported-crime'),
    path('crime-detail/<int:pk>/', views.crime_detail, name='crime-detail'),
    path('update-report-status/<int:pk>/', views.update_report_status, name='update-report-status'),
    path('search-crime/', views.search_crime, name='search-crime'),
    
    # Officer URLs
    path('officer-board/', views.officer_board, name='officer-board'),
    path('add-report/', views.add_report, name='add-report'),
    path('report-detail/<int:pk>/', views.report_detail, name='report-detail'),
    path('update-status/<int:pk>/', views.update_status, name='update-status'),
    path('search-report/', views.search_report, name='search-report'),
    
    # Citizen URLs
    path('user-board/', views.user_board, name='user-board'),
    path('user-report/', views.user_report, name='user-report'),
    path('report-history/', views.report_history, name='report-history'),
    path('c-report-detail/<int:pk>/', views.c_report_detail, name='c-report-detail'),
    path('citizen-notifications/', views.citizen_notifications, name='citizen_notifications'),
    
    # Notification URLs
    path('mark-notification-read/<int:notification_id>/', 
         views.mark_notification_read, 
         name='mark_notification_read'),
    
    path('mark-all-notifications-read/', 
         views.mark_all_notifications_read, 
         name='mark_all_notifications_read'),
    
    # AI URLs
    path('ai-analyze-realtime/', views.ai_analyze_realtime, name='ai-analyze-realtime'),
]