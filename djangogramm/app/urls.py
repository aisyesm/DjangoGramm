from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    # ex: /app/
    path('', views.Authentication.as_view(), name='handle_authentication'),
    # ex: /app/5/enter_info
    path('<int:pk>/enter_info', views.UserEnterInfoView.as_view(), name='enter_info'),

    path('activate/<uidb64>/<token>', views.activate, name='activate')
]