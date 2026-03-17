from django.utils import timezone
from . models import *

def notify_department_officers(department, message):
    """
    Sends a notification to all officers in a department.
    """
    if department:
        for officer in department.officers.all():
            Notification.objects.create(officer=officer, message=message, created_at=timezone.now())
