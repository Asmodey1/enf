from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from .forms import CustomUserCreationForm, CustomUserLoginForm, \
    CustomUserUpdateForm
from cart.models import Cart
from main.models import Product
from django.utils.http import url_has_allowed_host_and_scheme


def login_user(request, user):
    # login() меняет ключ сессии, а корзина привязана к нему — переносим её, чтобы товары не пропали
    old_session_key = request.session.session_key
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    if old_session_key:
        Cart.objects.filter(session_key=old_session_key).update(session_key=request.session.session_key)


def redirect_after_login(request):
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                                    require_https=request.is_secure()):
        return redirect(next_url)
    return redirect('main:index')


def register(request):
    if request.method =='POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login_user(request, user)
            return redirect_after_login(request)
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form':form})

def login_view(request):
    if request.method =='POST':
        form = CustomUserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login_user(request, user)
            return redirect_after_login(request)
    else:
        form = CustomUserLoginForm()
    return render(request, 'users/login.html', {'form': form})


@login_required
def profile_view(request):
    # Страница только показывает данные: правка идёт через update_account_details.
    # Заказы с позициями грузим одним запросом, а не отдельным на каждый заказ
    orders = request.user.orders.prefetch_related('items__product').order_by('-created_at')
    recommended_products = Product.objects.all().order_by('id')[:3]

    return TemplateResponse(request, 'users/profile.html', {
        'user': request.user,
        'orders': orders,
        'recommended_products': recommended_products
    })



@login_required
def account_details(request):
    return TemplateResponse(request, 'users/partials/account_details.html', {'user': request.user})



@login_required
def edit_account_details(request):
    form = CustomUserUpdateForm(instance=request.user)
    return TemplateResponse(request, 'users/partials/edit_account_details.html',
                            {'user':request.user, 'form':form})



@login_required
def update_account_details(request):
    if request.method !='POST':
        if request.headers.get('HX-Request'):
            return HttpResponse(headers={'HX-Redirect': reverse('users:profile')})
        return redirect('users:profile')

    form = CustomUserUpdateForm(request.POST, instance=request.user)
    if not form.is_valid():
        return TemplateResponse(request, 'users/partials/edit_account_details.html', {'user': request.user, 'form': form})

    user = form.save(commit=False)
    user.clean()
    user.save()
    return TemplateResponse(request, 'users/partials/account_details.html', {'user': user})


# Только POST: выход по обычной ссылке (GET) позволял разлогинить человека чужой ссылкой или картинкой
@require_POST
def logout_view(request):
    logout(request)
    if request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect':reverse('main:index')})
    return redirect('main:index')
