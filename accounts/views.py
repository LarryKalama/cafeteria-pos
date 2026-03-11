from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import User
from .forms import LoginForm, UserCreateForm, UserUpdateForm
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login
from django.contrib import messages
User = get_user_model()

def first_time_setup(request):
    """
    First-time setup view: only shown if no superuser exists.
    Creates the initial Super Admin account and auto-logs in.
    """
    # If any superuser already exists → redirect to login (setup is done)
    if User.objects.filter(is_superuser=True).exists():
        messages.info(request, "System is already set up. Please log in.")
        return redirect('accounts:login')  # or 'login' if that's your URL name

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Basic validation
        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect('setup')

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('setup')

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('setup')

        try:
            # Create the superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            # Optional: set additional fields if your User model has them
            # user.role = 'SUPERADMIN'
            # user.is_staff = True
            user.save()

            # Auto-login the new admin
            login(request, user)

            messages.success(
                request,
                "Super Admin account created successfully! Welcome to Cafeteria POS."
            )
            return redirect('home')  # Change to your actual dashboard URL name

        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return redirect('setup')

    # GET request: show the setup form
    return render(request, 'accounts/first_time_setup.html')


def is_superadmin(user):
    """Check if user is superadmin"""
    return user.is_authenticated and user.role == 'SUPERADMIN'


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Custom login page with form validation and redirect after success."""
    # Redirect already logged-in users
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = LoginForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name() or username}!')
                    # Force redirect - this is the critical line
                    return redirect('dashboard:home')
                else:
                    messages.error(request, 'Your account has been disabled. Contact support.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')

    # GET or invalid POST → show form with errors
    return render(request, 'accounts/login.html', {'form': form})
@login_required
def logout_view(request):
    """Logout user"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
@user_passes_test(is_superadmin)
def user_list(request):
    """List all users - Superadmin only"""
    users = User.objects.all()
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@user_passes_test(is_superadmin)
def user_create(request):
    """Create new user - Superadmin only"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('accounts:user_list')
    else:
        form = UserCreateForm()
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Create New User'
    })


@login_required
@user_passes_test(is_superadmin)
def user_update(request, pk):
    """Update user - Superadmin only"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('accounts:user_list')
    else:
        form = UserUpdateForm(instance=user)
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': f'Update User: {user.username}'
    })


@login_required
@user_passes_test(is_superadmin)
def user_delete(request, pk):
    """Delete user - Superadmin only"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('accounts:user_list')
    
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})


@login_required
def profile_view(request):
    """User profile"""
    return render(request, 'accounts/profile.html')