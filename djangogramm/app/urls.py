from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    path('', views.Authentication.as_view(), name='handle_authentication'),
    path('logout', views.logout_view, name='logout'),
    path('<int:pk>/enter_info', views.UserEnterInfoView.as_view(), name='enter_info'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('<int:pk>/profile', views.UserProfile.as_view(), name='profile')
]