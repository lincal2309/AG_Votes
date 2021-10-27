# -*-coding:Utf-8 -*
'''
# ===================================
#            Test admin views
# ===================================
'''

from django.test import TestCase
from django.shortcuts import reverse
from django.contrib.auth.models import User

from .tools import (
    create_dummy_user,
    create_dummy_company,
    # add_dummy_event,
)

from .models import (
    Company,
    Event,
    Question,
    Choice,
    UserVote,
    EventGroup,
    Result,
    Procuration,
    UserComp,
)

from .forms import (
    UserForm,
    UserBaseForm,
    UserCompForm,
    UploadFileForm,
    GroupDetail,
    EventDetail,
    CompanyForm
)



class TestOptions(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        self.user_staff = create_dummy_user(self.company, "staff", admin=True)
        self.client.force_login(self.user_staff.user)

    def test_access_admin(self):
        # Ensure the user will be redirected if he is not granted as admin for the company
        # Test the use of the decorator for all admin views
        comp = Company.get_company(self.company.comp_slug)
        self.user_lambda = create_dummy_user(self.company, "lambda")
        self.client.force_login(self.user_lambda.user)
        url = reverse("polls:adm_options", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_access_superuser(self):
        # Ensure the superusers will access the views
        # Test the use of the decorator for all admin views
        self.user_su = create_dummy_user(self.company, "superuser", staff=True)
        self.client.force_login(self.user_su.user)
        self.assertEqual(self.user_su.user.is_superuser, True)
        url = reverse("polls:adm_options", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fauvettes")

    def test_adm_options(self):
        url = reverse("polls:adm_options", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fauvettes")
        self.assertEqual(self.company.use_groups, False)

    def test_adm_options_update(self):
        # Load company options page
        url = reverse("polls:adm_options", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0123456789")
        self.assertEqual(self.company.siret, "0123456789")

        # Options update
        self.company.siret = "987654321"
        self.company.street_cplt = "bis"

        # Create a dict with values that are not None to ensure form validation
        # This shall raise an error any way if a mandatory field is missing
        comp_data = {k: v for k, v in self.company.__dict__.items() if v is not None}
        # Remove 'logo' field if no logo is present to avoid unexpected error
        if not self.company.logo:
            del comp_data['logo']

        response = self.client.post(
            reverse("polls:adm_options", args=[self.company.comp_slug]),
            # self.company.__dict__,
            comp_data
        )
        self.company.refresh_from_db()
        # print(self.company.__dict__)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "987654321")
        self.assertNotContains(response, "0123456789")
        self.assertEqual(self.company.siret, "987654321")
        self.assertEqual(self.company.street_cplt, "bis")


class TestAdmUsers(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        self.user_staff = create_dummy_user(self.company, "staff", admin=True)
        self.usr11 = create_dummy_user(self.company, "user11")
        self.usr12 = create_dummy_user(self.company, "user12", admin=True)
        self.usr13 = create_dummy_user(self.company, "user13")
        self.usr14 = create_dummy_user(self.company, "user14")
        self.usr21 = create_dummy_user(self.company, "user21")
        self.usr22 = create_dummy_user(self.company, "user22")

        self.client.force_login(self.user_staff.user)

    def test_adm_users(self):
        url = reverse("polls:adm_users", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['user_list']), 7)
        i = 0
        for usr in response.context['user_list']:
            if usr.is_admin: i += 1
        self.assertEqual(i, 2)


class TestUserProfile(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        self.user_staff = create_dummy_user(self.company, "staff", admin=True)
        self.usr11 = create_dummy_user(self.company, "user11")
        self.usr12 = create_dummy_user(self.company, "user12")
        self.usr21 = create_dummy_user(self.company, "user21")

    def test_userprofile_access(self):
        # Test several combinations to check access rights

        # User creation - admin
        self.client.force_login(self.user_staff.user)
        url = reverse("polls:adm_create_user", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # User creation - lambda
        self.client.force_login(self.usr11.user)
        url = reverse("polls:adm_create_user", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # User profile - admin
        self.client.force_login(self.user_staff.user)
        url = reverse("polls:adm_user_profile", args=[self.company.comp_slug, self.usr12.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user12")

        # User profile - personal
        self.client.force_login(self.usr12.user)
        url = reverse("polls:adm_user_profile", args=[self.company.comp_slug, self.usr12.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user12")

        # User profile - external
        self.client.force_login(self.usr21.user)
        url = reverse("polls:adm_user_profile", args=[self.company.comp_slug, self.usr12.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_userprofile_create(self):
        # User access creation page
        self.client.force_login(self.user_staff.user)
        url = reverse("polls:adm_create_user", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # User creation
        response = self.client.post(
            reverse("polls:adm_create_user", args=[self.company.comp_slug]),
            {"username": "new_user",
            "last_name": "new_name",
            "mail": "new_mail@titi.com"}
        )
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username="new_user")
        self.assertEqual(new_user.last_name, "new_name")

    def test_userprofile_update(self):
        # User access his page
        self.client.force_login(self.usr11.user)
        url = reverse("polls:adm_user_profile", args=[self.company.comp_slug, self.usr11.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user11")
        self.assertContains(response, "user11@toto.com")

        # Profil update
        response = self.client.post(
            reverse("polls:adm_user_profile", args=[self.company.comp_slug, self.usr11.user.id]),
            {"email": "new_mail@titi.com"}
        )
        self.usr11.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user11")
        self.assertNotContains(response, "user11@toto.com")
        self.assertContains(response, "new_mail@titi.com")
        self.assertEqual(self.usr11.user.email, "new_mail@titi.com")


