from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import generic
from django.contrib.auth import authenticate, login
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings


from .models import User
from .forms import UserForm


def handle_authentication(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # user pressed login button
            if request.POST['proceed'] == 'login':
                user = authenticate(email=form.cleaned_data['email'],
                                    password=form.cleaned_data['password'])
                if user is not None:
                    login(request, user)
                    return HttpResponseRedirect(reverse('app:user_page', args=[user.id]))
                else:
                    return render_initial_page(request, UserForm(), invalid_credentials=True)

            # user pressed register button
            elif request.POST['proceed'] == 'register':
                try:
                    validate_email(form.cleaned_data['email'])
                except ValidationError:
                    return render_initial_page(request, UserForm(), invalid_email=True)
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

    # if a GET (or any other method) we'll create a blank form
    else:
        return render_initial_page(request, UserForm())


def render_initial_page(request, form, invalid_credentials=False, invalid_email=False):
    context = {
        'form': form,
        'invalid_credentials': invalid_credentials,
        'invalid_email': invalid_email
    }
    return render(request, 'app/login.html', context)


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
        return HttpResponseRedirect(reverse('app:user_page', args=[user.id]))
    else:
        return HttpResponse('Activation link is invalid!')


class UserDetailView(generic.DetailView):
    model = User


# def user_page(request, user_id):
#     user = get_object_or_404(User, pk=user_id)
#     context = {
#         'user': user,
#     }
#     return render(request, 'app/user_detail.html', context=context)
