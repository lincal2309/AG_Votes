# Forms used by polls app

from django import forms

# Form used for user creation view
# class UserCreateForm(forms.Form):
#     username = forms.CharField(label="Nom d'utilisateur", max_length=30)
#     first_name = forms.CharField(label="Prénom", max_length=30)
#     email = forms.EmailField(label="Adresse de messagerie", required=False)
#     password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)

# Form used for login view
class UserForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=30)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)