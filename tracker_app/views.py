import json  # <-- Missing built-in dependency for parsing incoming API requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Task  # <-- Missing Model Import that broke both dashboards!

# --- EMPLOYEE AUTHENTICATION ---

def employee_register(request):
    if request.method == 'POST':
        # Handles both normal form submissions and AJAX fetch requests
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
        else:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')

        # Simple validation check
        if not username or not email or not password:
            if request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'error': 'All fields are required.'}, status=400)
            messages.error(request, 'All fields are required.')
            return render(request, 'employee/register.html')

        try:
            # Check if the user handle or email already exists in SQLite
            if User.objects.filter(username=username).exists():
                raise ValueError('That username is already taken.')
            if User.objects.filter(email=email).exists():
                raise ValueError('An account with that email already exists.')

            # Create user instance and safely encrypt/hash the password
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            if request.content_type == 'application/json':
                return JsonResponse({'status': 'success', 'redirect_url': '/'})
            
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('employee_login')

        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'error': str(e)}, status=400)
            messages.error(request, str(e))
            return render(request, 'employee/register.html')

    # Default GET logic to load the clean template state
    return render(request, 'employee/register.html')


def employee_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('employee_dashboard')

    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('employee_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'employee/login.html')

    return render(request, 'employee/login.html')


def employee_dashboard(request):
    if not request.user.is_authenticated or request.user.is_staff:
        return redirect('employee_login')
    
    # Active workspace task items (Excludes Completed)
    active_tasks = Task.objects.filter(assigned_to=request.user).exclude(status='COMPLETED')
    
    # Modification 3 Context Data: Complete history array trace
    absolute_history = Task.objects.filter(assigned_to=request.user)
    
    pending_count = absolute_history.filter(status='PENDING').count()
    progress_count = absolute_history.filter(status='PROGRESSING').count()
    completed_count = absolute_history.filter(status='COMPLETED').count()
    
    context = {
        'tasks': active_tasks,
        'absolute_history': absolute_history, # Passed directly into the template
        'stats': {
            'pending': pending_count,
            'progressing': progress_count,
            'completed': completed_count,
        }
    }
    return render(request, 'employee/dashboard.html', context)


def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('employee_login')


# --- CUSTOM ADMIN PORTAL VIEWS ---

def admin_login(request):
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Access Denied: Invalid Administrative Credentials.")
            return render(request, 'admin_portal/login.html')
            
    return render(request, 'admin_portal/login.html')

# Update the admin_dashboard to extract data records from Dataverse
def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
        
    # Fetch all users who are NOT administrative staff (your employees)
    employees = User.objects.filter(is_staff=False)
    # Fetch all tasks order tracked across the infrastructure
    all_tasks = Task.objects.all()
    
    return render(request, 'admin_portal/dashboard.html', {
        'employees': employees,
        'all_tasks': all_tasks
    })

# --- NEW ADMIN API ENDPOINTS FOR CREATION / ASSIGNMENTS ---

def admin_create_user(request):
    if request.method == 'POST' and request.user.is_staff:
        data = json.loads(request.body)
        try:
            user = User.objects.create_user(
                username=data.get('username'),
                email=data.get('email'),
                password=data.get('password')
            )
            user.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Unauthorized view constraint'}, status=403)

def admin_assign_task(request):
    if request.method == 'POST' and request.user.is_staff:
        data = json.loads(request.body)
        try:
            employee = User.objects.get(id=data.get('user_id'))
            task = Task.objects.create(
                title=data.get('title'),
                description=data.get('description'),
                assigned_to=employee,
                priority=data.get('priority'),
                status='PENDING'
            )
            task.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Unauthorized view constraint'}, status=403)


# --- API ENDPOINTS FOR FETCH REQUESTS ---

def update_task_status(request, task_id):
    if request.method == 'POST':
        try:
            # Parse incoming body parameters
            data = json.loads(request.body)
            new_status = data.get('status')
            
            task = Task.objects.get(id=task_id)
            
            # Authorization check: make sure workers can only modify their own data bounds
            if task.assigned_to == request.user or request.user.is_staff:
                task.status = new_status
                task.save()
                return JsonResponse({'status': 'success'})
            return JsonResponse({'error': 'Unauthorized'}, status=403)
            
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Invalid method'}, status=400)

# Update the delete task method to actively handle administrative clear actions
def delete_task(request, task_id):
    if request.method == 'DELETE' and request.user.is_staff:
        try:
            task = Task.objects.get(id=task_id)
            task.delete()
            return JsonResponse({'status': 'success'})
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task matching index target not found'}, status=404)
    return JsonResponse({'error': 'Invalid access authorization context'}, status=403)