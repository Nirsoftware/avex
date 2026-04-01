"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from rest_framework.authtoken.views import obtain_auth_token
from profiles.views import signup_view, login_view, profile_view, feeds_view, SignupView, LoginView
from feed.views import public_post_page

urlpatterns = [
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    path('admin/', admin.site.urls),

    # UI routes
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('profile/', profile_view, name='profile'),
    path('feeds/', feeds_view, name='feeds'),
    path('feeds', feeds_view),
    path('post/<int:post_id>/', public_post_page, name='public-post'),

    # API routes
    path('api/auth/token/', obtain_auth_token),
    path('api/signup/', SignupView.as_view()),
    path('api/login/', LoginView.as_view()),
    path('api/profile/', include('profiles.urls')),
    path('api/profiles/', include('profiles.urls')),
    path('api/', include('feed.urls')),
    path('', include('jobs.urls')),     # HTML jobs page handles /jobs/
    path('api/', include(('jobs.urls', 'jobs'), namespace='jobs-api')), # REST API within /api/
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
