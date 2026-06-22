from django.urls import path
from . import views

urlpatterns = [
    # The absolute landing page is now strictly bound to the login portal view
    path('', views.employee_login, name='employee_login'),
    
    path('register/', views.employee_register, name='employee_register'),
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    
    # Global Session Termination Route (Fixes the crashing NoReverseMatch template link)
    path('logout/', views.user_logout, name='user_logout'),
    
    # Custom Admin Portal Routes
    path('admin/portal/login/', views.admin_login, name='admin_login'),
    path('admin/portal/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # API Endpoints for Fetch Methods
    path('api/admin/create-user/', views.admin_create_user, name='admin_create_user'),
    path('api/admin/assign-task/', views.admin_assign_task, name='admin_assign_task'),
    path('api/tasks/<int:task_id>/update/', views.update_task_status, name='update_task_status'),
    path('api/tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('forgot-password/', views.reset_password, name='reset_password'),

    path('api/tasks/<int:task_id>/update/', views.admin_update_task, name='admin_update_task'),
]