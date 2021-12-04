from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import generic, View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions


from .models import User, Post
from .forms import UserLoginForm, UserFullInfoForm, UserEditInfoForm
from .serializers import PostSerializer


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
                        return HttpResponseRedirect(reverse('app:profile', args=[user.id]))
                    return HttpResponseRedirect(reverse('app:enter_info', args=[user.id]))
                else:
                    context = {'form': form, 'invalid_credentials': True}
                    return render(request, self.template_name, context=context)

            # user pressed register button
            elif request.POST['proceed'] == 'register':
                try:
                    validate_email(form.cleaned_data['email'])
                except ValidationError:
                    context = {'form': form, 'invalid_email': True}
                    return render(request, self.template_name, context=context)
                else:
                    user = User.objects.create_user(form.cleaned_data['email'],
                                                    form.cleaned_data['password'])
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
                    return HttpResponse('Account activation link sent to your email')

        return render(request, self.template_name, {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
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


class UserEnterInfoView(generic.edit.FormView):
    form_class = UserFullInfoForm
    template_name = 'app/user_enter_info.html'

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


class UserEditInfoView(generic.edit.FormView):
    form_class = UserEditInfoForm
    template_name = 'app/user_edit_profile.html'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        if self.request.user.is_authenticated:
            user = User.objects.get(email=self.request.user.email)
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.bio = form.cleaned_data.get('bio')
            # user.avatar = form.files.get('avatar')
            user.save()
            self.success_url = reverse('app:profile', args=[user.id])
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(UserEditInfoView, self).get_form_kwargs()
        kwargs['initial_values'] = {'first_name': self.request.user.first_name,
                                    'last_name': self.request.user.last_name,
                                    'bio': self.request.user.bio}
        return kwargs


class UserProfile(generic.detail.DetailView):
    model = User
    context_object_name = 'user'


class AddPostView(generic.edit.CreateView, LoginRequiredMixin):
    model = Post
    fields = ['image', 'caption']
    template_name_suffix = '_create_form'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("app:profile", args=[self.request.user.id])


class UserPostList(APIView):
    """
    Get posts for the currently authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, amount=None, format=None):
        amount = request.GET.get('amount', '')
        start = request.GET.get('start', '')
        try:
            amount = int(amount)
            start = int(start)
        except Exception as e:
            print(f'Caught exception while getting posts {e}')
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not start and not amount:
            posts = Post.objects.filter(user__id=request.user.id)
        elif isinstance(start, int) and not amount:
            posts = Post.objects.filter(user__id=request.user.id)[start:]
        elif isinstance(amount, int) and not start:
            posts = Post.objects.filter(user__id=request.user.id)[:amount]
        elif isinstance(amount, int) and isinstance(start, int):
            posts = Post.objects.filter(user__id=request.user.id)[start:start + amount]
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)





