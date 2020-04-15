# Forms used by polls app

from django.forms import Form, ModelForm, CharField, PasswordInput
from django.contrib.auth.models import User
# from django.contrib.auth.forms import UserCreationForm
# from bootstrap_modal_forms.forms import BSModalForm

from .models import (
    UserComp
)


# Form used for login view
class UserForm(Form):
    username = CharField(label="Nom d'utilisateur", max_length=30)
    password = CharField(label="Mot de passe", widget=PasswordInput)


# Forms for user management
class UserBaseForm(ModelForm):
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'username', 'password', 'email']
        widgets = {
            'password': PasswordInput,
        }

class UserCompForm(ModelForm):
    class Meta:
        model = UserComp
        fields = ['is_admin']
