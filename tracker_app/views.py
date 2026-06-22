import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Task, Profile

# --- EMPLOYEE AUTHENTICATION ---

def employee_register(request):
    if request.method == 'POST':
        # Handles both normal form submissions and AJAX fetch requests
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            employee_id = data.get('employee_id')  # Maps directly to User.username
            role = data.get('role')
            email = data.get('email')
            phone_number = data.get('phone_number')
            password = data.get('password')
        else:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            employee_id = request.POST.get('employee_id')
            role = request.POST.get('role')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            password = request.POST.get('password')

        # Simple verification check for all required data fields
        if not all([first_name, last_name, employee_id, role, email, phone_number, password]):
            error_msg = 'All fields are strictly required.'
            if request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'error': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'employee/register.html')

        # Explicit database constraints check matching requirements
        if User.objects.filter(username=employee_id).exists():
            msg = "User with the same employee id exists"
            if request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'error': msg}, status=400)
            messages.error(request, msg)
            return render(request, 'employee/register.html')

        if User.objects.filter(email=email).exists():
            msg = "User with the same email exists"
            if request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'error': msg}, status=400)
            messages.error(request, msg)
            return render(request, 'employee/register.html')

        if Profile.objects.filter(phone_number=phone_number).exists():
            msg = "User with the same phone number exists"
            if request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'error': msg}, status=400)
            messages.error(request, msg)
            return render(request, 'employee/register.html')

        try:
            # Create user instance and safely encrypt/hash the password
            user = User.objects.create_user(
                username=employee_id,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.save()

            # Create corresponding model profile link details
            profile = Profile.objects.create(
                user=user,
                phone_number=phone_number,
                role=role
            )
            profile.save()

            if request.content_type == 'application/json':
                return JsonResponse({'status': 'success', 'redirect_url': '/'})
            
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('employee_login')

        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'error': str(e)}, status=400)
            messages.error(request, str(e))
            return render(request, 'employee/register.html')

    # Default GET logic to load clean template state
    return render(request, 'employee/register.html')


def employee_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('employee_dashboard')

    if request.method == 'POST':
        login_method = request.POST.get('login_method')  # 'emp_id' or 'email'
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')
        
        target_username = identifier

        # Dual-Route Verification Strategy
        if login_method == 'email':
            matched_user = User.objects.filter(email=identifier).first()
            if matched_user:
                target_username = matched_user.username
            else:
                messages.error(request, "Invalid email or password.")
                return render(request, 'employee/login.html')

        user = authenticate(request, username=target_username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('employee_dashboard')
        else:
            messages.error(request, f"Invalid {'employee id' if login_method == 'emp_id' else 'email'} or password.")
            return render(request, 'employee/login.html')

    return render(request, 'employee/login.html')


def employee_dashboard(request):
    if not request.user.is_authenticated or request.user.is_staff:
        return redirect('employee_login')
    
    # Active workspace task items (Excludes Completed)
    active_tasks = Task.objects.filter(assigned_to=request.user).exclude(status='COMPLETED')
    
    # Complete history array trace
    absolute_history = Task.objects.filter(assigned_to=request.user)
    
    pending_count = absolute_history.filter(status='PENDING').count()
    progress_count = absolute_history.filter(status='PROGRESSING').count()
    completed_count = absolute_history.filter(status='COMPLETED').count()
    
    context = {
        'tasks': active_tasks,
        'absolute_history': absolute_history,
        'stats': {
            'pending': pending_count,
            'progressing': progress_count,
            'completed': completed_count,
        }
    }
    return render(request, 'employee/dashboard.html', context)


def reset_password(request):
    if request.method == 'GET':
        return render(request, 'reset_password.html')

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            # --- PHASE 1: VERIFY IDENTITY ---
            if action == 'verify':
                lookup_value = data.get('lookup_value', '').strip()
                phone_number = data.get('phone_number', '').strip()
                
                if not lookup_value or not phone_number:
                    return JsonResponse({'error': 'All fields are required.'}, status=400)
                
                # Fetch user from auth_user
                user = User.objects.filter(username=lookup_value).first() or User.objects.filter(email=lookup_value).first()
                
                if not user:
                    return JsonResponse({'error': 'No profile matches the provided credential.'}, status=404)
                
                # FIX: Access the related profile from tracker_app_profile
                user_profile = getattr(user, 'profile', None)
                
                if not user_profile:
                    return JsonResponse({'error': 'No linked profile structure found for this user.'}, status=400)
                
                # Extract phone_number field from the profile object
                db_phone = getattr(user_profile, 'phone_number', '')
                
                if not db_phone or phone_number.replace(" ", "") not in db_phone.replace(" ", ""):
                    return JsonResponse({'error': 'Verification failed. Phone number mismatch.'}, status=400)
                    
                return JsonResponse({'status': 'verified', 'user_id': user.id})
                
            # --- PHASE 2: UPDATE PASSWORD ---
            elif action == 'update':
                user_id = data.get('user_id')
                new_password = data.get('password')
                
                if not user_id or not new_password:
                    return JsonResponse({'error': 'Missing verification parameters.'}, status=400)
                    
                user = User.objects.filter(id=user_id).first()
                if not user:
                    return JsonResponse({'error': 'User target signature missing.'}, status=404)
                    
                user.set_password(new_password)
                user.save()
                return JsonResponse({'status': 'success'})
                
            else:
                return JsonResponse({'error': 'Invalid functional flow action.'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


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


def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
        
    # Modified to include all workers. Since the create form marks created accounts as staff/managers, 
    # we filter out superusers only so that employee lists render correctly.
    employees = User.objects.filter(is_superuser=False)
    all_tasks = Task.objects.all()
    
    return render(request, 'admin_portal/dashboard.html', {
        'employees': employees,
        'all_tasks': all_tasks
    })


# --- NEW ADMIN API ENDPOINTS FOR CREATION / ASSIGNMENTS ---

def admin_create_user(request):
    if request.method == 'POST' and request.user.is_staff:
        try:
            data = json.loads(request.body)
            
            # 1. Grab values from payload, map fallback string defaults
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            phone_number = data.get('phone_number', '').strip()
            role = data.get('role', '').strip() # Extracted role field matching employee_register
            is_staff_member = data.get('is_staff', False) 
            
            # Verification check including the new role field
            if not all([username, email, password, first_name, last_name, phone_number, role]):
                return JsonResponse({'error': 'All fields (including role) are strictly required.'}, status=400)

            # Check database duplicate constraints
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'User with this employee ID already exists.'}, status=400)
            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'User with this email already exists.'}, status=400)
            if phone_number and Profile.objects.filter(phone_number=phone_number).exists():
                return JsonResponse({'error': 'User with this phone number already exists.'}, status=400)
            
            # 2. Instantiate user object
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.is_staff = is_staff_member
            user.save()
            
            # 3. Save profile using the dynamically assigned role field
            profile = Profile.objects.create(
                user=user,
                phone_number=phone_number,
                role=role # Directly mapping the selected/entered role
            )
            profile.save()
            
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

def admin_update_task(request, task_id):
    if request.method == 'POST' and request.user.is_staff:
        try:
            task = Task.objects.get(id=task_id)
            
            # Since the frontend sends URLSearchParams, fields are inside request.POST
            task.title = request.POST.get('title')
            task.description = request.POST.get('description')
            task.priority = request.POST.get('priority')
            task.status = request.POST.get('status')
            
            # Update the worker assignment profile links
            assigned_user_id = request.POST.get('assigned_to') or request.POST.get('user_id')
            if assigned_user_id:
                task.assigned_to = User.objects.get(id=assigned_user_id)
                
            task.save()
            return JsonResponse({'status': 'success'})
            
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Assigned employee profile not found'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Unauthorized view constraint'}, status=403)

# --- API ENDPOINTS FOR FETCH REQUESTS ---

def update_task_status(request, task_id):
    if request.method == 'POST':
        try:
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


def delete_task(request, task_id):
    if request.method == 'DELETE' and request.user.is_staff:
        try:
            task = Task.objects.get(id=task_id)
            task.delete()
            return JsonResponse({'status': 'success'})
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task matching index target not found'}, status=404)
    return JsonResponse({'error': 'Invalid access authorization context'}, status=403)