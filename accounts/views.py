from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Log the user in immediately after signup
        login(request, user)

        return redirect('my-profile')  # go to profile page

    return render(request, 'accounts/signup.html')


import json
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = None
        password = None

        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
                username = data.get('username')
                password = data.get('password')
            except (ValueError, TypeError):
                messages.error(request, "Invalid request format")
                return redirect('login')
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Username and password are required")
            return redirect('login')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('my-profile')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('login')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')