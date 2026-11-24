from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from django.utils.html import strip_tags
from django.core.validators import RegexValidator
# gettext_lazy: атрибуты класса создаются при запуске сервера, а переводить надо в момент показа
from django.utils.translation import gettext_lazy as _


User = get_user_model()

# Один формат телефона для профиля и для оформления заказа
phone_validator = RegexValidator(r'^\+?1?\d{9,15}$', _("Enter a valid phone number."))


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=254, widget=forms.EmailInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('EMAIL')}))
    first_name = forms.CharField(required=True, max_length=50, widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('FIRST NAME')}))
    last_name = forms.CharField(required=True, max_length=50, widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('LAST NAME')}))
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('PASSWORD')})
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('CONFIRM PASSWORD')})
    )


    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # iexact: Ivan@mail.ru и ivan@mail.ru — один адрес, второй аккаунт на него заводить нельзя
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('This email is already in use.'))
        return email
    

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class CustomUserLoginForm(AuthenticationForm):
    username = forms.CharField(label=_("Email"), widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('EMAIL')}))
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('PASSWORD')})
    )


    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if email and password:
            self.user_cache = authenticate(self.request, email = email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(_('Invalid email or password.'))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_('This account is inactive.'))
            return self.cleaned_data


class CustomUserUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        empty_value=None,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('PHONE NUMBER')})
    )
    first_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('FIRST NAME')})
    )
    last_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('LAST NAME')})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('EMAIL')})
    )

    


    class Meta:
        model = User
        fields= ('first_name', 'last_name', 'email', 'company' , 'address1',
                    'address2', 'city', 'country', 'province', 'postal_code', 'phone')

        widgets = {
            'company': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('COMPANY')}),
            'address1': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('ADDRESS LINE 1')}),
            'address2': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('ADDRESS LINE 2')}),
            'city': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('CITY')}),
            'country': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('COUNTRY')}),
            'province': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('PROVINCE')}),
            'postal_code': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _('POSTAL CODE')}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exclude(id = self.instance.id).exists():
            raise forms.ValidationError(_('This email is already in use.'))
        return email


    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('email'):
            cleaned_data['email'] = self.instance.email
        for field in ['company', 'address1', 'address2', 'city', 'country',
                      'province', 'postal_code', 'phone']:
            if cleaned_data.get(field):
                cleaned_data[field] = strip_tags(cleaned_data[field])
        return cleaned_data
            






