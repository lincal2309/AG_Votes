# -*-coding:Utf-8 -*
'''
# ===================================
#            Test admin views
# ===================================
'''

from django.test import TestCase
from django.shortcuts import reverse
from django.contrib.auth.models import User

from .tools_tests import (
    create_dummy_user,
    create_dummy_company,
    add_dummy_event,
)

from .models import (
    Company,
    Event,
    Question,
    Choice,
    UserVote,
    UserGroup,
    Result,
    Procuration,
    UserComp,
)

# from .forms import (
#     UserForm,
#     UserBaseForm,
#     UserCompForm,
#     UploadFileForm,
#     GroupDetail,
#     EventDetail,
#     CompanyForm
# )


class TestOptions(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        self.user_staff = create_dummy_user(self.company, "staff", admin=True)
        self.client.force_login(self.user_staff.user)

    def test_access_admin(self):
        # Ensure the user will be redirected if he is not granted as admin for the company
        # Test the use of the decorator for all admin views
        # comp = Company.get_company(self.company.comp_slug)
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

    def test_adm_delete_user(self):
        test_usercomp_id = self.usr13.id
        usrcomp = UserComp.objects.get(user__username="user13")
        self.assertEqual(usrcomp.id, test_usercomp_id)

        url = reverse("polls:adm_delete_user", args=[self.company.comp_slug, test_usercomp_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=test_usercomp_id)
        with self.assertRaises(UserComp.DoesNotExist):
            UserComp.objects.get(id=test_usercomp_id)


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

        # Profile update by admin user
        self.client.force_login(self.user_staff.user)
        response = self.client.post(
            reverse("polls:adm_user_profile", args=[self.company.comp_slug, self.usr11.user.id]),
            {"email": "new_mail@titi.com"}
        )
        self.usr11.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.usr11.user.email, "new_mail@titi.com")


class TestAdmGroups(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")

        self.user_staff = create_dummy_user(self.company, "staff", admin=True)
        self.usr11 = create_dummy_user(self.company, "user11")
        self.usr12 = create_dummy_user(self.company, "user12", admin=True)
        self.usr13 = create_dummy_user(self.company, "user13")
        self.usr14 = create_dummy_user(self.company, "user14")
        self.usr21 = create_dummy_user(self.company, "user21")
        self.usr22 = create_dummy_user(self.company, "user22")

        user_list = [self.usr11.id, self.usr12.id, self.usr13.id, self.usr14.id]
        users = UserComp.objects.filter(id__in=user_list)
        self.group1 = UserGroup.create_group({
            "company": self.company,
            "group_name": "Groupe 1",
            "weight": 40,
            },
            user_list=users)

        user_list = [self.usr21.id, self.usr22.id]
        users = UserComp.objects.filter(id__in=user_list)
        self.group2 = UserGroup.create_group({
            "company": self.company,
            "group_name": "Groupe 2",
            "weight": 60,
            },
            user_list=users)

    def test_adm_groups(self):
        # Test access with no connection
        url = reverse("polls:adm_groups", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Test access for a dummy user
        self.client.force_login(self.usr11.user)
        url = reverse("polls:adm_groups", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Test access for a staff user
        self.client.force_login(self.user_staff.user)
        url = reverse("polls:adm_groups", args=[self.company.comp_slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['group_list']), 2)

    def test_adm_create_group(self):
        self.client.force_login(self.user_staff.user)

        user_list = [self.usr11.id, self.usr21.id]
        users = "-".join([str(x) for x in user_list])
        group_form = {}
        group_form["all_users"] = UserComp.objects.all()
        group_form["users"] = UserComp.objects.filter(id__in=user_list)

        response = self.client.post(
            reverse("polls:adm_create_group", args=[self.company.comp_slug]),
            {"company": self.company,
            "group_name": "Nouveau Groupe",
            "weight": 12,
            "group_form": group_form,
            "users_in_group": users}
        )
        self.assertEqual(response.status_code, 200)
        new_group = UserGroup.objects.get(group_name="Nouveau Groupe")
        self.assertEqual(new_group.id, 4)
        group_users = UserComp.objects.filter(usergroup__id=new_group.id)
        self.assertEqual(len(group_users), 2)
        self.assertIn(self.usr11, group_users)
        self.assertEqual(group_users[0].id, self.usr11.id)

        # Create group without any user
        response = self.client.post(
            reverse("polls:adm_create_group", args=[self.company.comp_slug]),
            {"company": self.company,
            "group_name": "Groupe Vide",
            "weight": 33,
            "group_form": group_form,
            "users_in_group": []}
        )
        self.assertEqual(response.status_code, 200)
        new_group = UserGroup.objects.get(group_name="Groupe Vide")
        group_users = UserComp.objects.filter(usergroup__id=new_group.id)
        self.assertEqual(len(group_users), 0)


    def test_adm_update_group(self):
        self.client.force_login(self.user_staff.user)
        group_users = self.group1.users.all()
        self.assertIn(self.usr11, group_users)
        self.assertIn(self.usr14, group_users)
        self.assertNotIn(self.usr21, group_users)

        user_list = [self.usr11.id, self.usr21.id]
        users = "-".join([str(x) for x in user_list])
        group_form = {}
        group_form["all_users"] = UserComp.objects.all()
        group_form["users"] = UserComp.objects.filter(id__in=user_list)

        response = self.client.post(
            reverse("polls:adm_group_detail", args=[self.company.comp_slug, self.group1.id]),
            {"company": self.company,
            "group_name": "Groupe 1",
            "weight": 33,
            "group_form": group_form,
            "users_in_group": users}
        )

        self.assertEqual(response.status_code, 200)
        self.group1.refresh_from_db()
        self.assertEqual(self.group1.weight, 33)
        group_users = response.context["group_form"].fields["users"].queryset
        self.assertIn(self.usr11, group_users)
        self.assertNotIn(self.usr14, group_users)
        self.assertIn(self.usr21, group_users)


    def test_adm_delete_group(self):
        test_group_id = self.group1.id
        grp = UserGroup.objects.get(group_name="Groupe 1")
        self.assertEqual(grp.id, test_group_id)

        url = reverse("polls:adm_delete_group", args=[self.company.comp_slug, test_group_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(UserGroup.DoesNotExist):
            UserGroup.objects.get(id=test_group_id)
