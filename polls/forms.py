# Forms used by polls app

from django import forms
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

from .models import (
    Question,
    UserComp,
    UserGroup,
    Company,
    Event,
    Choice
)


# Admin create user form
class CreateUserForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=30)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    company=forms.ModelChoiceField(label="Société",
        queryset=Company.objects.all())


# Login view
class UserForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=30)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)


# User management
class UserBaseForm(forms.ModelForm):
    # Create user
    class Meta:
        model = User
        fields = ['username', 'last_name', 'first_name', 'email']

class UserCompForm(forms.ModelForm):
    class Meta:
        model = UserComp
        fields = ['phone_num', 'is_admin']


# Form to upload an excel file to create many users at once
class UploadFileForm(forms.Form):
    file = forms.FileField(label="Fichier", validators=[FileExtensionValidator(['xls', 'xlsx'], message=("Seuls les fichiers *.xls et *.xlsx sont pris en charge"))])
    sheet = forms.CharField(label="Onglet", max_length=30, initial="Feuil1")
    use_groups = forms.BooleanField(label="Utiliser les groupes", initial=False)


# Company management
class CompanyForm(forms.ModelForm):
    # rule = forms.Select(label="mode de scrutin")
    class Meta:
        model = Company
        exclude = []

    def __init__(self, *args, **kwags):
        # Disable two mandatory fields to avoid updating them in the form and allo form validation
        super().__init__(*args, **kwags)
        self.fields['company_name'].disabled = True
        self.fields['comp_slug'].disabled = True


# Event management
class EventDetail(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        label = "Liste des groupes",
        queryset = None,
        widget = forms.CheckboxSelectMultiple,
        required = False
        )

    class Meta:
        model = Event
        fields = ['event_name', 'event_start_date', "event_end_date", 'quorum', 'rule']


# Group management
class GroupDetail(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        label="Dans le groupe",
        queryset=None,
        widget=forms.SelectMultiple,
        required=False
        )
    all_users = forms.ModelMultipleChoiceField(
        label="Utilisateurs",
        queryset=None,
        widget=forms.SelectMultiple,
        required=False
        )
    users_in_group = forms.CharField(max_length=500, required=False)
    
    class Meta:
        model = UserGroup
        fields = ['group_name', 'weight', 'users', 'all_users', 'users_in_group']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance is not None:
            # Users to be selected : all users except the ones already in group
            self.fields['all_users'].queryset= UserComp.objects.\
                                                        filter(company=instance.company).\
                                                        exclude(usergroup=instance).\
                                                        order_by('user__last_name', 'user__first_name')
            # Current users in group
            self.fields['users'].queryset = instance.users.all().\
                                                     order_by('user__last_name', 'user__first_name')
            # Group's users list in string format
            self.fields['users_in_group'].initial = "-".join([str(elt.id) for elt in instance.users.all()])
        else:
            self.fields['all_users'].queryset = UserComp.objects.none()
            self.fields['users'].queryset = UserComp.objects.none()
            self.fields['users_in_group'].initial = ""
            self.fields['weight'].initial = 100

class QuestionDetail(forms.ModelForm):
    question_no = forms.IntegerField(label="Numéro", min_value=1, required=False)
    class Meta:
        model = Question
        fields = ["question_no", "question_text"]

class ChoiceDetail(forms.ModelForm):
    choice_no = forms.IntegerField(label="Numéro", min_value=1, required=False)
    class Meta:
        model = Choice
        fields = ["choice_no", "choice_text"]
