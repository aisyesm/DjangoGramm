from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns


from . import views

app_name = 'app'
urlpatterns = [
    path('', views.Authentication.as_view(), name='handle_authentication'),
    path('register', views.Register.as_view(), name='register'),
    path('logout', views.logout_view, name='logout'),
    path('<int:pk>/enter_info', views.UserEnterInfoView.as_view(), name='enter_info'),
    path('<int:pk>/edit_profile', views.UserEditInfoView.as_view(), name='edit_profile'),
    path('<int:pk>/add_post', views.AddPostView.as_view(), name='add_post'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('<int:pk>/profile', views.UserProfile.as_view(), name='profile'),
    path('p/<int:pk>', views.PostDetail.as_view(), name='post_detail'),
    path('p/<int:pk>/delete', views.PostDeleteView.as_view(), name='post_delete'),
    path('p/<int:pk>/update', views.PostUpdateView.as_view(), name='post_update'),
    path('feed', views.Feed.as_view(), name='feed'),
    path('api-auth/', include('rest_framework.urls')),
]

urlpatterns += format_suffix_patterns([path('posts/', views.UserPostList.as_view()),])