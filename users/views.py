from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User
from bookings.models import Booking


def register_view(request):
    """
    Handle user registration with email, name, phone, and password.
    Uses CustomUserManager.create_user() to hash password automatically.
    """
    # Redirect authenticated users to home
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        # Get form data from POST request
        email = request.POST.get('email', '').strip().lower()
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validation flags
        has_error = False
        
        # Validate email
        if not email:
            messages.error(request, 'Email address is required.')
            has_error = True
        
        # Validate name
        if not name:
            messages.error(request, 'Full name is required.')
            has_error = True
        
        # Validate password
        if not password:
            messages.error(request, 'Password is required.')
            has_error = True
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            has_error = True
        
        # Validate password confirmation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            has_error = True
        
        # Check if email already exists
        if email and User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            has_error = True
        
        # If no errors, create the user
        if not has_error:
            try:
                # Use the custom manager to create user (password gets hashed automatically)
                user = User.objects.create_user(
                    email=email,
                    name=name,
                    password=password,
                    phone=phone if phone else ''
                )
                
                messages.success(
                    request, 
                    f'Account created successfully! Welcome {user.name}. You can now login.'
                )
                return redirect('login')
                
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
        
        # If there were errors, re-render the form with the submitted data
        # Store submitted data in context to repopulate form
        context = {
            'form_data': {
                'email': email,
                'name': name,
                'phone': phone,
            }
        }
        return render(request, 'users/register.html', context)
    
    # GET request - show empty registration form
    return render(request, 'users/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, 'Both email and password are required.')
            return render(request, 'users/login.html', {'email': email})
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.name}!')
                
                # Check if user is admin/staff - redirect to admin dashboard
                if user.is_staff or user.is_superuser:
                    return redirect('admin_dashboard')
                
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'This account has been deactivated.')
        else:
            messages.error(request, 'Invalid email or password.')
            
        return render(request, 'users/login.html', {'email': email})
    
    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    """
    Handle user logout.
    Requires user to be logged in.
    """
    if request.method == 'POST' or request.method == 'GET':
        # Store name for farewell message before logging out
        user_name = request.user.name
        
        # Logout the user
        logout(request)
        
        # Show farewell message
        messages.success(request, f'Goodbye, {user_name}! You have been logged out successfully.')
        
        return redirect('login')


# ==================== PROFILE VIEW ====================
@login_required
def profile(request):
    user = request.user
    bookings = Booking.objects.filter(user=user).order_by('-created_at')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        if name:
            user.name = name
        if phone:
            user.phone = phone
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    context = {
        'user': user,
        'bookings': bookings,
    }
    return render(request, 'users/profile.html', context)