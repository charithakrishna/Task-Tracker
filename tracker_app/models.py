from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = [
        ('DEVELOPER', 'Developer'),
        ('DESIGNER', 'Designer'),
        ('MANAGER', 'Project Manager'),
        ('ANALYST', 'Business Analyst'),
        ('QA', 'QA Engineer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='DEVELOPER')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Task(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROGRESSING', 'Under Progress'),
        ('COMPLETED', 'Completed'),
    ]

    PRIORITY_CHOICES = [
        ('1_HIGH', 'High'),      
        ('2_MEDIUM', 'Medium'),
        ('3_LOW', 'Low'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='3_LOW')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', '-created_at']

    def __str__(self):
        # Renders: Task Title - Jane Doe (EMP-12345) (High)
        return f"{self.title} - {self.assigned_to.first_name} {self.assigned_to.last_name} ({self.assigned_to.username}) ({self.get_priority_display()})"