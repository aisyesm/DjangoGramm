from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    # ex: /app/
    path('', views.handle_authentication, name='handle_authentication'),
    # ex: /app/5
    # path('<int:pk>/', views.DetailView.as_view(), name='user_page')
    path('<int:user_id>/', views.user_page, name='user_page')
]