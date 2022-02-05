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
    path('<int:pk>/change_avatar', views.UserAvatarUpdateView.as_view(), name='change_avatar'),
    path('<int:pk>/add_post', views.AddPostView.as_view(), name='add_post'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('<int:pk>/profile', views.UserProfile.as_view(), name='profile'),
    path('p/<int:pk>', views.PostDetail.as_view(), name='post_detail'),
    path('p/<int:pk>/delete', views.PostDeleteView.as_view(), name='post_delete'),
    path('p/<int:pk>/update', views.PostUpdateView.as_view(), name='post_update'),
    path('feed', views.Feed.as_view(), name='feed'),
    path('subscriptions/<int:follower_id>', views.SubscriptionList.as_view(), name='subscription_list'),
    path('subscriptions/<int:follower_id>/<int:followee_id>', views.SubscriptionDetail.as_view(), name='subscription'),
    path('explore', views.ExploreUserListView.as_view(), name='user-list'),
    path('likes/<int:post_id>', views.LikeList.as_view(), name='likes'),
    path('likes/<int:post_id>/<int:user_id>', views.LikeDetail.as_view(), name='like'),
    path('user/<int:pk>/fullname', views.UserInfoAPI.as_view(), name='user_fullname'),
    path('<int:pk>/cloudinary', views.Upload.as_view(), name='upload_cloudinary'),
    path('api-auth/', include('rest_framework.urls')),
]

urlpatterns += format_suffix_patterns([path('posts/', views.UserPostList.as_view(), name='posts')])
