# -*-coding:Utf-8 -*

from django.test import TestCase, Client
from django.contrib.auth import authenticate, login
# from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.shortcuts import render, redirect, reverse, get_list_or_404, get_object_or_404
from django.db.models import Count
from django.contrib.auth.models import User

import datetime

from .models import Company, Event, Question, Choice, UserVote, EventGroup


def create_user(username, staff=False):
    return User.objects.create_user(username, password=username, is_staff=staff)

def create_company():
    return Company.objects.create(company_name='Société de test', logo="logo.png")



class TestLoginUser(TestCase):
    def test_login(self):
        create_user('toto')
        response = self.client.post(reverse('polls:login'), 
            {'username': 'toto', 'password': 'toto'})
        logged_user = User.objects.get(username='toto')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(logged_user.is_authenticated, True)

    def test_login_unknown_user(self):
        response = self.client.post(reverse('polls:login'), 
            {'username': 'toto', 'password': 'toto'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], True)
        self.assertContains(response, "Utilisateur inconnu")
 
    def test_already_logged_in(self):
        user = create_user('toto')
        self.client.force_login(user)
        response = self.client.get(reverse('polls:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vous êtes déjà connecté")
        self.assertContains(response, user.username)


class TestIndex(TestCase):
    @classmethod
    def setUpTestData(cls):
        company = create_company()
        passed_date = timezone.now() - datetime.timedelta(days=1)
        future_date = timezone.now() + datetime.timedelta(days=1)
        Event.objects.create(event_name="Evénement passé", event_date=passed_date, 
            slug=slugify("Evénement passé" + str(passed_date)), company=company)
        Event.objects.create(event_name="Evénement futur", event_date=future_date, 
            slug=slugify("Evénement futur" + str(future_date)), company=company)

    def test_display_home_no_login_user(self):
        # Redirect to login page if no user logged in
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_display_home(self):
        # Display only future events
        user = create_user('toto', False)
        self.client.force_login(user)

        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "futur")
        self.assertNotContains(response, "passé")

class TestEvent(TestCase):
    def setUp(self):
        self.user_staff = create_user('staff', True)
        self.user_lambda = create_user('lambda', False)
        self.company = create_company()
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), company=self.company)
        self.question1 = Question.objects.create(question_text="Question 1", event=self.event)
        self.question2 = Question.objects.create(question_text="Question 2", event=self.event)
    
    def test_user_staff_event_not_started(self):
        self.client.force_login(self.user_staff)
        url = reverse('polls:event', args=(self.event.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nb_questions'], 2)
        self.assertContains(response, "Lancer l'événement")
        self.assertNotContains(response, "Accéder à l'événement")

    def test_user_staff_event_started(self):
        self.client.force_login(self.user_staff)
        self.event.current = True
        self.event.save()
        url = reverse('polls:event', args=(self.event.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nb_questions'], 2)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertContains(response, "Accéder à l'événement")

    def test_user_lambda_event_not_started(self):
        EventGroup.objects.create(event=self.event, user=self.user_lambda)
        self.client.force_login(self.user_lambda)
        url = reverse('polls:event', args=(self.event.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nb_questions'], 2)
        self.assertEqual(response.context['user_can_vote'], True)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertNotContains(response, "Accéder à l'événement")

    def test_user_lambda_event_started(self):
        EventGroup.objects.create(event=self.event, user=self.user_lambda)
        self.client.force_login(self.user_lambda)
        self.event.current = True
        self.event.save()
        url = reverse('polls:event', args=(self.event.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nb_questions'], 2)
        self.assertEqual(response.context['user_can_vote'], True)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertContains(response, "Accéder à l'événement")

    def test_user_lambda_not_in_event_list(self):
        self.client.force_login(self.user_lambda)
        self.event.current = True
        self.event.save()
        url = reverse('polls:event', args=(self.event.slug,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nb_questions'], 2)
        self.assertEqual(response.context['user_can_vote'], False)
        self.assertNotContains(response, "Lancer l'événement")
        self.assertNotContains(response, "Accéder à l'événement")

class TestQuestion(TestCase):
    # Lancement événement (staff only)
    # Première question, utilisateur n'a pas voté
    # Première question l'utilisateur a voté
    # Dernière question
    def setUp(self):
        self.user_staff = create_user('staff', True)
        self.user_lambda = create_user('lambda', False)
        self.company = create_company()
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), company=self.company)
        self.question1 = Question.objects.create(question_text="Question 1", event=self.event)
        self.question2 = Question.objects.create(question_text="Question 2", event=self.event)
        EventGroup.objects.create(event=self.event, user=self.user_lambda)
        Choice.objects.create(choice_text="Oui", question=self.question1)
        Choice.objects.create(choice_text="Non", question=self.question1)
        Choice.objects.create(choice_text="NSP", question=self.question1)
        Choice.objects.create(choice_text="Oui", question=self.question2)
        Choice.objects.create(choice_text="Non", question=self.question2)
        Choice.objects.create(choice_text="NSP", question=self.question2)

    def test_launch_event(self):
        self.client.force_login(self.user_staff)
        url = reverse('polls:question', args=(self.event.slug, 0))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        my_event = get_object_or_404(Event, id=self.event.id)
        self.assertEqual(my_event.current, True)
        user_list = get_list_or_404(UserVote)
        self.assertEqual(len(user_list), 2)
        self.assertEqual(response.context['question_no'], 1)
        self.assertContains(response, "Question 1")
        self.assertContains(response, "Oui : 0,00 %")
        self.assertContains(response, "Résolution suivante")

    def test_user_display_first_question(self):
        self.client.force_login(self.user_lambda)
        url = reverse('polls:question', args=(self.event.slug, 0))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['question_no'], 1)
        self.assertContains(response, "Question 1")
        self.assertContains(response, "Oui")
        self.assertNotContains(response, "Oui : 0,00 %")
        self.assertContains(response, "Voter")
        self.assertContains(response, "Résolution suivante")

    def test_user_vote_first_question(self):
        self.client.force_login(self.user_lambda)
        url = reverse('polls:question', args=(self.event.slug, 1))
        response = self.client.post(url, {'choice': 1})
        self.assertEqual(response.status_code, 200)
        my_vote = get_object_or_404(UserVote, user=self.user_lambda, question=self.question1)
        self.assertEqual(my_vote.as_voted, True)
        my_choice = get_object_or_404(Choice, choice_text="Oui", question=self.question1)
        self.assertEqual(my_choice.votes, 1)
        self.assertEqual(response.context['question_no'], 1)
        self.assertContains(response, "Question 1")
        self.assertContains(response, "Oui")
        self.assertNotContains(response, "Oui : 0,00 %")
        self.assertContains(response, "Voter")
        self.assertContains(response, "Résolution suivante")
        
    def test_user_display_last_question(self):
        self.client.force_login(self.user_lambda)
        url = reverse('polls:question', args=(self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['question_no'], 2)
        self.assertContains(response, "Question 2")
        self.assertContains(response, "Oui")
        self.assertNotContains(response, "Oui : 0,00 %")
        self.assertContains(response, "Voter")
        self.assertNotContains(response, "Résolution suivante")

    def test_results_last_question(self):
        self.client.force_login(self.user_staff)
        choice = get_object_or_404(Choice, choice_text="Oui", question=self.question2)
        choice.votes = 3
        choice.save()
        choice = get_object_or_404(Choice, choice_text="Non", question=self.question2)
        choice.votes = 1
        choice.save()
        url = reverse('polls:question', args=(self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Oui : 75,00 %")
        self.assertContains(response, "Non : 25,00 %")
        self.assertNotContains(response, "Résolution suivante")


class TestResults(TestCase):
    pass

