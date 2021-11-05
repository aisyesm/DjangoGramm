from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import generic, View
from django.contrib.auth import authenticate, login
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.views.generic.edit import FormView


from .models import User
from .forms import UserLoginForm, UserFullInfoForm


class Authentication(View):
    form_class = UserLoginForm
    template_name = 'app/login.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # user pressed login button
            print(type(request.POST))

            if request.POST['proceed'] == 'login':
                user = authenticate(email=form.cleaned_data['email'],
                                    password=form.cleaned_data['password'])
                if user is not None:
                    login(request, user)
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


class UserEnterInfoView(FormView):
    model = User
    form_class = UserFullInfoForm
    template_name = 'app/user_enter_info.html'

