from django.contrib.auth.views import LogoutView
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('tweet_home/', views.tweet_list, name='tweet_list'),
    path('<int:tweet_id>/', views.tweet_detail, name='tweet_detail'),
    path('create/', views.tweet_create, name='tweet_create'),
    path('<int:tweet_id>/edit', views.tweet_edit, name='tweet_edit'),
    path('<int:tweet_id>/delete', views.tweet_delete, name='tweet_delete'),
    path('search/', views.tweet_search, name='tweet_search'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('tweet_like/<int:tweet_id>', views.tweet_like, name='tweet_like'),
    # Authentication
    path('', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    #password reset
    path('reset_password/',auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"),name='password_reset'),
    path('reset_password/sent/',auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),name='password_reset_confirm'),
    path('reset_password/complete/',auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),name='password_reset_complete'),
]