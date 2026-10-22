from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)

    class Meta:
        model = User
        fields = ("username", "first_name", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=25)
    address = forms.CharField(max_length=250, widget=forms.TextInput)
    city = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields["full_name"].initial = user.get_full_name() or user.username
            self.fields["email"].initial = user.email
