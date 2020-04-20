# Forms used by polls app

from django import forms
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

from .models import (
    UserComp,
)


# Form used for login view
class UserForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=30)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)


# Forms for user management
class UserBaseForm(forms.ModelForm):
    # Create user form
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'username', 'email']

class UserCompForm(forms.ModelForm):
    class Meta:
        model = UserComp
        fields = ['phone_num', 'is_admin']

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Fichier", validators=[FileExtensionValidator(['xls', 'xlsx'], message=("Seuls les fichiers *.xls et *.xlsx sont pris en charge"))])
    sheet = forms.CharField(label="Onglet", max_length=30, initial="Feuil1")
    use_groups = forms.BooleanField(label="Utiliser les groupes", initial=True)
