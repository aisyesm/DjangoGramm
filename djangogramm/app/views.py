from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.contrib.auth import authenticate
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import logging

from .models import User
from .forms import UserForm

logger = logging.getLogger('django.request')


def handle_authentication(request):
    logger.info(request)
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # user pressed login button
            if request.POST['proceed'] == 'login':
                user = authenticate(email=form.cleaned_data['email'],
                                    password=form.cleaned_data['password'])
                if user is not None:
                    return HttpResponseRedirect(reverse('app:user_page', args=[user.id]))
                else:
                    return render_initial_page(request, UserForm(), no_such_user=True)

            # user pressed register button
            elif request.POST['proceed'] == 'register':
                try:
                    validate_email(form.cleaned_data['email'])
                except ValidationError:
                    return render_initial_page(request, UserForm(), invalid_email=True)
                else:
                    user = User.objects.create_user(form.cleaned_data['email'],
                                                    form.cleaned_data['password'])
                    return HttpResponseRedirect(reverse('app:user_page', args=[user.id]))

    # if a GET (or any other method) we'll create a blank form
    else:
        return render_initial_page(request, UserForm())


def render_initial_page(request, form, no_such_user=False, invalid_email=False):
    context = {
        'form': form,
        'no_such_user': no_such_user,
        'invalid_email': invalid_email
    }
    return render(request, 'app/login.html', context)


class DetailView(generic.DetailView):
    model = User
    template_name = 'app/user_page.html'


def user_page(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    context = {
        'user': user,
    }
    return render(request, 'app/user_page.html', context=context)
