from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROGRESSING', 'Under Progress'),
        ('COMPLETED', 'Completed'),
    ]

    # Prefixes like '1_', '2_', '3_' ensure the database orders them perfectly by default
    PRIORITY_CHOICES = [
        ('1_HIGH', 'High'),      
        ('2_MEDIUM', 'Medium'),
        ('3_LOW', 'Low'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Links task to a user. If a user is deleted, their tasks are deleted too.
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='3_LOW')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Guarantees tasks always display by priority order first, then newest first
        ordering = ['priority', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.assigned_to.username} ({self.get_priority_display()})"