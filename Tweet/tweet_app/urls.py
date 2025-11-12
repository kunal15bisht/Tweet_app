from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path('tweet_home/', views.tweet_list, name='tweet_list'),
    path('create/', views.tweet_create, name='tweet_create'),
    path('<int:tweet_id>/edit', views.tweet_edit, name='tweet_edit'),
    path('<int:tweet_id>/delete', views.tweet_delete, name='tweet_delete'),
    path('search/', views.tweet_search, name='tweet_search'),

    # Authentication
    path('', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]