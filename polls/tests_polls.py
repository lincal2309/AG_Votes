# -*-coding:Utf-8 -*

from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify
from django.shortcuts import reverse, get_list_or_404, get_object_or_404
from django.contrib.auth.models import User
# from django.core import mail
# from django.core.files import File
# from django.conf import settings
# from django.db.models import Sum

# from unittest import mock

# import os
import datetime

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

from .forms import (
    UserForm,
    UserBaseForm,
    UserCompForm,
    UploadFileForm,
    GroupDetail,
    EventDetail,
    CompanyForm
)

# from .tools import set_chart_data, init_event
# from .pollsmail import PollsMail


# ===================================
#            Test views
# ===================================

class TestLoginUser(TestCase):
    def test_login(self):
        self.company = create_dummy_company("Société de test")
        create_dummy_user(self.company, "toto")
        response = self.client.post(
            reverse("polls:login"), {"username": "toto", "password": "toto"}
        )
        logged_user = User.objects.get(username="toto")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(logged_user.is_authenticated, True)

    def test_login_unknown_user(self):
        response = self.client.post(
            reverse("polls:login"), {"username": "toto", "password": "toto"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["error"], True)
        self.assertContains(response, "Utilisateur inconnu")

    def test_already_logged_in(self):
        self.company = create_dummy_company("Société de test")
        user = create_dummy_user(self.company, "toto")
        self.client.force_login(user.user)
        response = self.client.get(reverse("polls:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vous êtes déjà connecté")
        self.assertContains(response, user.user.username)


class TestIndex(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = create_dummy_company("Société de test")
        cls.company2 = create_dummy_company("Une autre société de test")
        passed_date = timezone.now() - datetime.timedelta(days=1)
        future_date = timezone.now() + datetime.timedelta(days=1)
        Event.objects.create(
            event_name="Evénement passé",
            event_date=passed_date,
            slug=slugify("Evénement passé" + str(passed_date)),
            company=cls.company,
        )
        Event.objects.create(
            event_name="Evénement futur",
            event_date=future_date,
            slug=slugify("Evénement futur" + str(future_date)),
            company=cls.company,
        )

    def test_display_home_no_login_user(self):
        # Displays dedicated home page
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        # TO DO : Change next tests according to finalize home page
        # self.assertIn("login", response.url)

    def test_display_home(self):
        # Display only future events
        user = create_dummy_user(self.company, "toto")
        self.client.force_login(user.user)

        # Test with follow=True arg to be able to test html content
        # Thus, status code will be 200 instead of 302 for a redirection
        response = self.client.get(reverse("polls:index"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prochain")
        self.assertContains(response, "Prévu le")
        self.assertNotContains(response, "Aucun")

    def test_display_home_superuser(self):
        # Display list of companies
        self.user_su = create_dummy_user(self.company, "superuser", staff=True)
        self.client.force_login(self.user_su.user)

        response = self.client.get(reverse("polls:index"))
        self.assertEqual(self.user_su.user.is_superuser, True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Prochain")
        self.assertNotContains(response, "Prévu le")
        self.assertContains(response, "Administration générale")
        self.assertContains(response, "Création")
        self.assertContains(response, "entreprises")
        self.assertContains(response, "Société")


class TestEvent(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        self.user_staff = create_dummy_user(self.company, "staff", admin=True)
        self.user_lambda = create_dummy_user(self.company, "lambda")
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            company=self.company,
        )
        self.question1 = Question.objects.create(
            question_text="Question 1", question_no=1, event=self.event
        )
        self.question2 = Question.objects.create(
            question_text="Question 2", question_no=2, event=self.event
        )

    def test_user_staff_event_not_started(self):
        self.client.force_login(self.user_staff.user)
        url = reverse("polls:event", args=(self.company.comp_slug, self.event.slug))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nb_questions"], 2)
        self.assertContains(response, "Lancer l'événement")
        self.assertNotContains(response, "Accéder à l'événement")

    def test_user_staff_event_started(self):
        self.client.force_login(self.user_staff.user)
        self.event.current = True
        self.event.save()
        url = reverse("polls:event", args=(self.company.comp_slug, self.event.slug))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nb_questions"], 2)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertContains(response, "Accéder à l'événement")

    def test_user_lambda_event_not_started(self):
        self.group = UserGroup.objects.create(group_name="Groupe 1", weight=70)
        self.event.groups.add(self.group)
        self.group.users.add(self.user_lambda)
        self.client.force_login(self.user_lambda.user)
        url = reverse("polls:event", args=(self.company.comp_slug, self.event.slug))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nb_questions"], 2)
        self.assertEqual(response.context["user_can_vote"], True)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertNotContains(response, "Accéder à l'événement")

    def test_user_lambda_event_started(self):
        self.group = UserGroup.objects.create(group_name="Groupe 1", weight=70)
        self.event.groups.add(self.group)
        self.group.users.add(self.user_lambda)
        self.client.force_login(self.user_lambda.user)
        self.event.current = True
        self.event.save()
        url = reverse("polls:event", args=(self.company.comp_slug, self.event.slug))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nb_questions"], 2)
        self.assertEqual(response.context["user_can_vote"], True)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertContains(response, "Accéder à l'événement")

    def test_user_lambda_not_in_event_list(self):
        self.client.force_login(self.user_lambda.user)
        self.event.current = True
        self.event.save()
        url = reverse("polls:event", args=(self.company.comp_slug, self.event.slug))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nb_questions"], 2)
        self.assertEqual(response.context["user_can_vote"], False)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertNotContains(response, "Accéder à l'événement")


class TestQuestion(TestCase):
    def setUp(self):
        self.company = create_dummy_company("Société de test")
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            event_name="Evénement de test",
            event_date=event_date,
            slug=slugify("Evénement de test" + str(event_date)),
            company=self.company,
        )
        self.group = UserGroup.objects.create(group_name="Groupe 1", weight=70)
        self.event.groups.add(self.group)
        self.user_staff = create_dummy_user(self.company, "staff", group=self.group, admin=True)
        self.user_lambda = create_dummy_user(self.company, "lambda", group=self.group)
        self.question1 = Question.objects.create(
            question_text="Question 1", question_no=1, event=self.event
        )
        self.question2 = Question.objects.create(
            question_text="Question 2", question_no=2, event=self.event
        )

    def test_launch_event_total_weight_not_100(self):
        # Launching event not possible until total groups' weight == 100
        self.client.force_login(self.user_staff.user)
        url = reverse("polls:question", args=(self.company.comp_slug, self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_launch_event(self):
        # Add a group to have a total weight of 100
        group2 = UserGroup.objects.create(group_name="Groupe 2", weight=30)
        self.event.groups.add(group2)
        self.client.force_login(self.user_staff.user)
        url = reverse("polls:question", args=(self.company.comp_slug, self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        my_event = get_object_or_404(Event, id=self.event.id)
        self.assertEqual(my_event.current, True)
        user_list = get_list_or_404(UserVote)
        self.assertEqual(len(user_list), 4)
        self.assertEqual(response.context["question_no"], 1)
        self.assertEqual(response.context["event"].current, True)
        self.assertContains(response, "Question 1")
        self.assertContains(response, "Résolution suivante")

    def test_user_display_first_question(self):
        UserVote.objects.create(
            event=self.event,
            user=self.user_lambda,
            question=self.question1,
            has_voted=False,
            nb_user_votes=1,
        )
        self.event.current = True
        self.event.save()
        self.client.force_login(self.user_lambda.user)
        url = reverse("polls:question", args=(self.company.comp_slug, self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["question_no"], 1)
        self.assertEqual(response.context["last_question"], False)
        self.assertEqual(response.context["user_vote"].has_voted, False)
        self.assertContains(response, "Question 1")
        self.assertContains(response, "Voter")
        self.assertContains(response, "Résolution suivante")

    def test_user_display_question_user_has_voted(self):
        UserVote.objects.create(
            event=self.event,
            user=self.user_lambda,
            question=self.question1,
            has_voted=True,
            nb_user_votes=0,
        )
        self.event.current = True
        self.event.save()
        self.client.force_login(self.user_lambda.user)
        url = reverse("polls:question", args=(self.company.comp_slug, self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["question_no"], 1)
        self.assertEqual(response.context["event"].current, True)
        self.assertEqual(response.context["last_question"], False)
        self.assertEqual(response.context["user_vote"].has_voted, True)

    def test_user_display_last_question(self):
        UserVote.objects.create(
            event=self.event,
            user=self.user_lambda,
            question=self.question2,
            has_voted=False,
            nb_user_votes=1,
        )
        self.event.current = True
        self.event.save()
        self.client.force_login(self.user_lambda.user)
        url = reverse("polls:question", args=(self.company.comp_slug, self.event.slug, 2))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["question_no"], 2)
        self.assertEqual(response.context["last_question"], True)
        self.assertContains(response, "Question 2")
        self.assertContains(response, "Voter")
        self.assertNotContains(response, "Résolution suivante")
