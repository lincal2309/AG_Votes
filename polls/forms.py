# Forms used by polls app

from django import forms
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

from .models import (
    UserComp,
    EventGroup,
    Company,
    Event
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
    # Form to upload an excel file to create many users at once
    file = forms.FileField(label="Fichier", validators=[FileExtensionValidator(['xls', 'xlsx'], message=("Seuls les fichiers *.xls et *.xlsx sont pris en charge"))])
    sheet = forms.CharField(label="Onglet", max_length=30, initial="Feuil1")
    use_groups = forms.BooleanField(label="Utiliser les groupes", initial=True)




# Form for event management
class EventDetail(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        label = "Liste des groupes",
        queryset = EventGroup.objects.none(),
        widget = forms.CheckboxSelectMultiple,
        # label_from_instance = lambda grp: "%s (poids : %s \%)" % (grp.group_name, grp.weight),
        required = False
        )

    class Meta:
        model = Event
        fields = ['event_name', 'event_date', 'quorum', 'rule', 'groups']


    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     instance = kwargs.get('instance', None)
    #     if instance is not None:
    #         self.fields['groups'].queryset= EventGroup.objects.\
    #                                                     filter(company=instance.company).\
    #                                                     order_by('group_name')
    #     else:
    #         self.fields['groups'].queryset = EventGroup.objects.none()



# Form for group management
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
    group_list = forms.CharField(max_length=500)
    
    class Meta:
        model = EventGroup
        fields = ['group_name', 'weight', 'users', 'all_users', 'group_list']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance is not None:
            # Users to be selected : all users except the ones already in group
            self.fields['all_users'].queryset= UserComp.objects.\
                                                        filter(company=instance.company).\
                                                        exclude(eventgroup=instance).\
                                                        order_by('user__last_name', 'user__first_name')
            # Current users in group
            self.fields['users'].queryset = instance.users.all().\
                                                     order_by('user__last_name', 'user__first_name')
            # Group's users list in string format
            self.fields['group_list'].initial = "-".join([str(elt.id) for elt in instance.users.all()])
        else:
            self.fields['all_users'].queryset = UserComp.objects.none()
            self.fields['users'].queryset = UserComp.objects.none()
            self.fields['group_list'].initial = ""
            self.fields['weight'].initial = 100
