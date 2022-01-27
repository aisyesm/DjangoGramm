import re

from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseNotAllowed, Http404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, CreateView, DeleteView, UpdateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse, reverse_lazy
from django.conf import settings
from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response

from .helpers import get_timedelta_for_post
from .models import User, Post, Subscription, Like
from .forms import UserLoginForm, UserFullInfoForm, UserRegisterForm, AddPostForm, UserEditInfoForm, \
    UserAvatarUpdateForm
from .serializers import UserProfilePostSerializer, FeedPostSerializer, SubscriptionSerializer, LikeSerializer
from .permissions import IsAdminOrUserOwnSubscriptions


class Authentication(View):
    form_class = UserLoginForm
    template_name = 'app/login.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            if request.POST['proceed'] == 'login':
                user = authenticate(email=form.cleaned_data['email'],
                                    password=form.cleaned_data['password'])
                if user is not None:
                    login(request, user)
                    if user.first_name and user.last_name:
                        return HttpResponseRedirect(reverse('app:feed'))
                    return HttpResponseRedirect(
                        reverse('app:enter_info', args=[user.id]))
                else:
                    context = {'form': form, 'invalid_credentials': True}
                    return render(request, self.template_name, context=context)

        return render(request, self.template_name, {'form': form})


class Register(View):
    form_class = UserRegisterForm
    template_name = 'app/register.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            if request.POST['proceed'] == 'register':
                try:
                    validate_email(form.cleaned_data['email'])
                except ValidationError:
                    context = {'form': form, 'invalid_email': True}
                    return render(request, self.template_name, context=context)
                else:
                    if form.cleaned_data['password'] != form.cleaned_data['confirm_password']:
                        context = {'form': form, 'passwords_dont_match': True}
                        return render(
                            request, self.template_name, context=context)
                    existing_user = User.objects.filter(
                        email=form.cleaned_data['email']).first()
                    if existing_user:
                        context = {'form': form, 'user_already_exist': True}
                        return render(
                            request, self.template_name, context=context)
                    user = User.objects.create_user(
                        form.cleaned_data['email'], form.cleaned_data['password'])
                    current_site = get_current_site(request)
                    mail_subject = 'Activate your DjangoGramm account.'
                    message = render_to_string('app/acc_active_email.html', {
                        'user': user,
                        'domain': current_site.domain,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': default_token_generator.make_token(user),
                    })
                    to_email = form.cleaned_data.get('email')
                    send_mail(
                        mail_subject,
                        message,
                        settings.EMAIL_HOST_USER,
                        [to_email],
                        fail_silently=False,
                    )
                    return render(request,
                                  "app/activation_link_sent.html",
                                  {'email': form.cleaned_data['email']})

        return render(request, self.template_name, {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return HttpResponseRedirect(reverse('app:enter_info', args=[user.id]))
    else:
        return HttpResponse('Activation link is invalid!')


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('app:handle_authentication'))


class UserEnterInfoView(UserPassesTestMixin, LoginRequiredMixin, FormView):
    form_class = UserFullInfoForm
    template_name = 'app/user_enter_info.html'
    login_url = reverse_lazy('app:handle_authentication')

    def test_func(self):
        pattern = r'app/(\d+)/enter_info'
        url = re.search(pattern, self.request.path)
        user_id = url.group(1)
        return user_id == str(self.request.user.pk)

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        if self.request.user.is_authenticated:
            user = User.objects.get(email=self.request.user.email)
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.bio = form.cleaned_data.get('bio')
            user.avatar = form.files.get('avatar')
            user.save()
            self.success_url = reverse('app:profile', args=[user.id])
        return super().form_valid(form)


class UserEditInfoView(UserPassesTestMixin, LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserEditInfoForm
    template_name = 'app/user_edit_profile.html'
    context_object_name = 'user'
    login_url = reverse_lazy('app:handle_authentication')

    def test_func(self):
        return self.request.user.pk == self.get_object().pk

    def get_success_url(self):
        return reverse("app:profile", args=[self.request.user.id])

    def get_form(self, form_class=None):
        form = super(UserEditInfoView, self).get_form(form_class)
        form.fields['first_name'].required = True
        form.fields['last_name'].required = True
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['auth_user'] = self.request.user
        return context


class UserProfile(LoginRequiredMixin, DetailView):
    model = User
    context_object_name = 'user'
    login_url = reverse_lazy('app:handle_authentication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_user = self.get_object()
        auth_user = self.request.user
        context['auth_user'] = auth_user
        context['can_edit'] = True if auth_user.pk == page_user.id else False
        can_follow = True if auth_user.pk != page_user.id else False
        follow_params = {'can_follow': can_follow}
        if can_follow:
            try:
                auth_user.subscription_followers.get(followee=page_user)
            except Subscription.DoesNotExist:
                is_following = False
            else:
                is_following = True
            follow_params['is_following'] = is_following
        context['follow_params'] = follow_params
        context['followers'] = page_user.followers.all()
        context['following'] = page_user.following.all()
        context['num_posts'] = page_user.post_set.count()
        return context


class UserAvatarUpdateView(UserPassesTestMixin, LoginRequiredMixin, FormView):
    form_class = UserAvatarUpdateForm
    login_url = reverse_lazy('app:handle_authentication')

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        if self.request.user.is_authenticated:
            user = User.objects.get(email=self.request.user.email)
            user.avatar = form.files.get('avatar')
            user.save()
            self.success_url = reverse('app:profile', args=[user.id])
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        delete_avatar = request.POST.get('delete_avatar')
        if delete_avatar and delete_avatar == 'true':
            user = User.objects.get(email=self.request.user.email)
            user.avatar = None
            user.save()
            return HttpResponseRedirect(reverse('app:profile', args=[user.id]))
        return super().post(request, args, kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['GET'])

    def test_func(self):
        pattern = r'app/(\d+)/change_avatar'
        url = re.search(pattern, self.request.path)
        user_id = url.group(1)
        return user_id == str(self.request.user.id)


class AddPostView(UserPassesTestMixin, LoginRequiredMixin, CreateView):
    model = Post
    form_class = AddPostForm
    template_name_suffix = '_create_form'
    login_url = reverse_lazy('app:handle_authentication')

    def test_func(self):
        pattern = r'app/(\d+)/add_post'
        url = re.search(pattern, self.request.path)
        user_id = url.group(1)
        return user_id == str(self.request.user.pk)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("app:profile", args=[self.request.user.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['auth_user'] = self.request.user
        return context


class UserPostList(APIView):
    """
    View class to return posts for UserProfile or Feed views.
    """
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def get(request, format=None):
        # store received query params
        q_params = {
            'offset': request.GET.get('offset'),
            'start': request.GET.get('start'),
            'user_id': request.GET.get('user_id')
        }
        # validate params
        for param, val in q_params.items():
            if val:
                try:
                    q_params[param] = int(val)
                except TypeError:
                    return Response(status=status.HTTP_400_BAD_REQUEST)

        if q_params['user_id']:
            if not q_params['start'] and not q_params['offset']:
                posts = Post.objects.filter(user__id=q_params['user_id'])
            elif not q_params['start'] or not q_params['offset']:
                posts = Post.objects.filter(user__id=q_params['user_id'])[
                        q_params['start']:q_params['offset']]
            elif q_params['offset'] and q_params['start']:
                posts = Post.objects.filter(
                    user__id=q_params['user_id'])[
                        q_params['start']:q_params['start'] +
                                          q_params['offset']]
            serializer = UserProfilePostSerializer(posts, many=True)
        else:
            auth_user = User.objects.get(id=request.user.id)
            if not q_params['start'] and not q_params['offset']:
                posts = Post.objects.filter(user__in=auth_user.following.all())
            elif not q_params['start'] or not q_params['offset']:
                posts = Post.objects.filter(user__in=auth_user.following.all())[
                        q_params['start']:q_params['offset']]
            elif q_params['offset'] and q_params['start']:
                posts = Post.objects.filter(user__in=auth_user.following.all())[
                        q_params['start']:q_params['start'] + q_params['offset']]
            serializer = FeedPostSerializer(posts, many=True)

        return Response(serializer.data)


class PostDetail(LoginRequiredMixin, DetailView):
    model = Post
    context_object_name = 'post'
    login_url = reverse_lazy('app:handle_authentication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pub_date = self.get_object().pub_date
        context['post_timedelta'] = get_timedelta_for_post(pub_date)
        context['can_edit'] = True if self.request.user.pk == self.get_object().user.pk else False
        context['auth_user'] = self.request.user
        return context


class PostDeleteView(UserPassesTestMixin, LoginRequiredMixin, DeleteView):
    model = Post
    context_object_name = 'post'
    login_url = reverse_lazy('app:handle_authentication')

    def test_func(self):
        return self.request.user.pk == self.get_object().user.pk

    def get_success_url(self):
        return reverse_lazy('app:profile', kwargs={'pk': self.object.user.id})

    def get(self, request, *args, **kwargs):
        return HttpResponseNotFound('<h1>Page not found</h1>')


class PostUpdateView(UserPassesTestMixin, LoginRequiredMixin, UpdateView):
    model = Post
    fields = ['caption']
    template_name_suffix = '_update_form'
    context_object_name = 'post'
    login_url = reverse_lazy('app:handle_authentication')

    def test_func(self):
        return self.request.user.pk == self.get_object().user.pk

    def get(self, request, *args, **kwargs):
        return HttpResponseNotFound('<h1>Page not found</h1>')


class Feed(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'app/feed.html'
    login_url = reverse_lazy('app:handle_authentication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_num_posts'] = Post.objects.all().count()
        context['auth_user'] = self.request.user
        return context


class SubscriptionList(APIView):
    """
    List all user subscriptions, or create a new subscription.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrUserOwnSubscriptions]

    def get(self, request, follower_id):
        try:
            User.objects.get(id=follower_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        subscriptions = Subscription.objects.filter(follower=follower_id)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)

    def post(self, request, follower_id):
        # has to provide who to follow
        if not request.data.get('followee_id'):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            followee_id = request.data['followee_id']

        # followee and followee have to exist
        try:
            User.objects.get(id=followee_id)
            User.objects.get(id=follower_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # user cannot follow himself or subscribe twice
        if int(followee_id) == int(follower_id) or \
            Subscription.objects.filter(followee=followee_id, follower=follower_id):
            return Response(status=status.HTTP_409_CONFLICT)

        serializer = SubscriptionSerializer(data={
            'followee': followee_id,
            'follower': follower_id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionDetail(APIView):
    """
    Retrieve or delete a subscription.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrUserOwnSubscriptions]

    def get_object(self, followee_id, follower_id):
        try:
            return Subscription.objects.get(
                followee=followee_id, follower=follower_id)
        except Subscription.DoesNotExist:
            raise Http404

    def get(self, request, follower_id, followee_id):
        subscription = self.get_object(followee_id, follower_id)
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)

    def delete(self, request, follower_id, followee_id):
        subscription = self.get_object(followee_id, follower_id)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LikeList(generics.ListCreateAPIView):
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id')
        queryset = self.get_queryset(post_id=post_id)
        serializer = self.get_serializer_class()(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self, *args, **kwargs):
        post_id = kwargs.get('post_id')
        return Like.objects.filter(post=post_id)

    def create(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id')
        user_id = request.data.get('user_id')

        serializer = self.get_serializer_class()(data={'user': user_id, 'post': post_id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExploreUserListView(ListView):

    model = User
    paginate_by = 15
    ordering = ['last_name']
    queryset = User.objects.filter(is_active=True).exclude(is_admin=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['auth_user'] = self.request.user
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.exclude(id=self.request.user.id)
        return queryset

