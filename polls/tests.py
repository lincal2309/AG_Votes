# -*-coding:Utf-8 -*

from django.test import TestCase, Client
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.utils.text import slugify
from django.shortcuts import reverse, get_list_or_404, get_object_or_404
from django.db.models import Count
from django.contrib.auth.models import User

from unittest import mock

import datetime
import json

from .models import Company, Event, Question, Choice, UserVote, EventGroup


# ===================================
#  Global functions used for testing
# ===================================

def create_user(username, staff=False):
    return User.objects.create_user(username, password=username, is_staff=staff)

def create_company(name):
    return Company.objects.create(company_name=name, logo="logo.png")


# ===================================
#          Mock functions
# Predefined mock for models' methods
# ===================================

def mock_get_company(id):
    return Company(id=1, company_name='Société de test', logo="logo.png")

def mock_get_next_events(company):
    future_date = timezone.now() + datetime.timedelta(days=1)
    return Event(id=2, event_name="Evénement futur", event_date=future_date, 
        slug=slugify("Evénement futur" + str(future_date)), company=company)


def mock_get_event_user_list(event_slug):
    user1 = create_user('user1', False)
    user2 = create_user('user2', False)
    company = create_company('Une société de test')
    event_date = datetime.date(2150, 5, 12)
    event = Event.objects.create(event_name="Un événement de test", event_date=event_date, 
            slug=slugify('dummy-event-slug'), company=company)
    user_vote1 = EventGroup.objects.create(event=event, user=user1)
    user_vote2 = EventGroup.objects.create(event=event, user=user2)
    event_user_list = (user_vote1, user_vote2)
    return event_user_list

def mock_get_question_list(event_slug):
    company = create_company('Une société de test')
    event_date = datetime.date(2150, 5, 12)
    event, created = Event.objects.get_or_create(event_name="Un événement de test", event_date=event_date, 
            slug=slugify('dummy-event-slug'), company=company)
    question1 = Question.objects.create(question_text="Dummy question 1", question_no=1, event=event)
    question2 = Question.objects.create(question_text="Dummy question 2", question_no=2, event=event)
    question_list = (question1, question2)
    return question_list


# ===================================
#        Test models' methods
# ===================================

class TestModelCompany(TestCase):
    def test_get_company(self):
        comp = create_company('Société de test')
        company = Company.get_company(1)
        self.assertEqual(comp.id, company.id)

class TestModelEvent(TestCase):
    def test_get_event(self):
        self.company = create_company('Société de test')
        event_date = datetime.date(2150, 5, 12)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), company=self.company)
        my_event = Event.get_event("evenement-de-test2150-05-12")
        self.assertEqual(self.event, my_event)
    
    def test_get_next_events(self):
        company = create_company('Société de test')
        passed_date = timezone.now() - datetime.timedelta(days=1)
        future_date = timezone.now() + datetime.timedelta(days=1)
        Event.objects.create(event_name="Evénement passé", event_date=passed_date, 
            slug=slugify("Evénement passé" + str(passed_date)), company=company)
        Event.objects.create(event_name="Evénement futur", event_date=future_date, 
            slug=slugify("Evénement futur" + str(future_date)), company=company)
        
        next_events = Event.get_next_events(company)
        self.assertEqual(len(next_events), 1)
        self.assertEqual(next_events[0].event_name, "Evénement futur")
    
    def test_set_current(self):
        self.company = create_company('Société de test')
        event_date = datetime.date(2150, 5, 12)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), company=self.company)

        self.assertEqual(self.event.current, False)
        self.event.set_current()
        self.assertEqual(self.event.current, True)

class TestModelQuestion(TestCase):
    def setUp(self):
        self.company = create_company('Société de test')
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), company=self.company)
        self.question1 = Question.objects.create(question_text="Question 1", question_no=1, event=self.event)
        self.question2 = Question.objects.create(question_text="Question 2", question_no=2, event=self.event)

    def test_get_question_list(self):
        question_list = Question.get_question_list(self.event.slug)
        self.assertEqual(len(question_list), 2)
        self.assertEqual(question_list[0].question_text, "Question 1")
        self.assertEqual(question_list[1].question_text, "Question 2")

    def test_get_question(self):
        my_question = Question.get_question(self.event.slug, 1)
        self.assertEqual(my_question, self.question1)

class TestModelChoice(TestCase):
    def setUp(self):
        self.user_lambda = create_user('lambda', False)
        self.company = create_company('Société de test')
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), company=self.company)
        self.question1 = Question.objects.create(question_text="Question 1", question_no=1, event=self.event)
        self.question2 = Question.objects.create(question_text="Question 2", question_no=2, event=self.event)
        EventGroup.objects.create(event=self.event, user=self.user_lambda)
        self.c1 = Choice.objects.create(choice_text="Oui", question=self.question1)
        self.c2 = Choice.objects.create(choice_text="Non", question=self.question1, votes=3)
        self.c3 = Choice.objects.create(choice_text="NSP", question=self.question1)
        Choice.objects.create(choice_text="Oui", question=self.question2)
        Choice.objects.create(choice_text="Non", question=self.question2)
        Choice.objects.create(choice_text="NSP", question=self.question2)

    def test_get_choice_list(self):
        choice_list = Choice.get_choice_list(self.event.slug, 1)
        self.assertEqual(len(choice_list), 3)
        self.assertEqual(choice_list[0].choice_text, "Oui")

    def test_add_vote(self):
        self.assertEqual(self.c1.votes, 0)
        self.assertEqual(self.c2.votes, 3)
        Choice.add_vote(1)
        self.c1.refresh_from_db()  # Need to fetch database after it's been updated
        self.assertEqual(self.c1.votes, 1)
        Choice.add_vote(2)
        self.c2.refresh_from_db()
        self.assertEqual(self.c2.votes, 4)

class TestModelEventGroup(TestCase):
    def setUp(self):
        self.user_lambda = create_user('lambda', False)
        self.user_alpha = create_user('alpha', False)
        self.company = create_company('Société de test')
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), current=True, company=self.company)
        self.question1 = Question.objects.create(question_text="Question 1", question_no=1, event=self.event)
        self.question2 = Question.objects.create(question_text="Question 2", question_no=2, event=self.event)
        EventGroup.objects.create(event=self.event, user=self.user_lambda)
        Choice.objects.create(choice_text="Oui", question=self.question1, votes=1)
        Choice.objects.create(choice_text="Non", question=self.question1, votes=2)
        Choice.objects.create(choice_text="NSP", question=self.question1)

    def test_get_user_list(self):
        user_list = EventGroup.get_user_list(self.event.slug)
        self.assertEqual(len(user_list), 1)
        self.assertEqual(user_list[0].user.username, "lambda")

    def test_count_total_votes(self):
        nb_votes = EventGroup.count_total_votes(self.event.slug)
        self.assertEqual(nb_votes, 1)

    def test_user_in_event_group(self):
        user_in_group = EventGroup.user_in_event_group(self.event.slug, self.user_lambda)
        self.assertEqual(user_in_group, True)
        user_in_group = EventGroup.user_in_event_group(self.event.slug, self.user_alpha)
        self.assertEqual(user_in_group, False)

class TestModelUserVote(TestCase):
    def setUp(self):
        self.user_lambda = create_user('lambda', False)
        self.user_alpha = create_user('alpha', False)
        self.company = create_company('Société de test')
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), current=True, company=self.company)
        self.question1 = Question.objects.create(question_text="Question 1", question_no=1, event=self.event)
        self.question2 = Question.objects.create(question_text="Question 2", question_no=2, event=self.event)
        EventGroup.objects.create(event=self.event, user=self.user_lambda)
        self.c1 = Choice.objects.create(choice_text="Oui", question=self.question1, votes=1)
        self.c2 = Choice.objects.create(choice_text="Non", question=self.question1, votes=2)
        self.c3 = Choice.objects.create(choice_text="NSP", question=self.question1)

    def test_get_user_vote(self):
        UserVote.objects.create(user=self.user_lambda, question=self.question1, has_voted=False)
        UserVote.objects.create(user=self.user_alpha, question=self.question1, has_voted=True)
        user_vote = UserVote.get_user_vote(self.user_lambda, 1)
        self.assertEqual(user_vote.has_voted, False)
        user_vote = UserVote.get_user_vote(self.user_alpha, 1)
        self.assertEqual(user_vote.has_voted, True)
        
    @mock.patch('polls.models.Question.get_question_list')
    @mock.patch('polls.models.EventGroup.get_user_list')
    def test_init_uservotes(self, mock_user_list, mock_question_list):
        mock_user_list.return_value = mock_get_event_user_list('dummy-event-slug')
        mock_question_list.return_value = mock_get_question_list('dummy-event-slug')
        UserVote.init_uservotes('dummy-event-slug')
        new_user_list = UserVote.objects.filter(question__event__slug='dummy-event-slug')
        self.assertEqual(len(new_user_list), 4)
        self.assertEqual(new_user_list[0].user.username, 'user1')
        self.assertEqual(new_user_list[0].question.question_text, 'Dummy question 1')
        self.assertEqual(new_user_list[3].user.username, 'user2')

    def test_set_vote(self):
        UserVote.objects.create(user=self.user_lambda, question=self.question1, has_voted=False)
        user_vote = UserVote.set_vote(self.user_lambda, 1)
        self.assertEqual(user_vote.has_voted, True)


# ===================================
#            Test views
# ===================================

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
        company = create_company('Société de test')
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

    # @mock.patch('polls.models.Event.get_next_events')
    # @mock.patch('polls.models.Company.get_company')
    # def test_display_home(self, mock_company, mock_next_events):
    def test_display_home(self):
        # Display only future events
        user = create_user('toto', False)
        self.client.force_login(user)

        # mock_company.return_value = mock_get_company(1)
        # mock_next_events.return_value = mock_get_next_events(mock_company.return_value)

        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "futur")
        self.assertNotContains(response, "passé")

class TestEvent(TestCase):
    def setUp(self):
        self.user_staff = create_user('staff', True)
        self.user_lambda = create_user('lambda', False)
        self.company = create_company('Société de test')
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), company=self.company)
        self.question1 = Question.objects.create(question_text="Question 1", question_no=1, event=self.event)
        self.question2 = Question.objects.create(question_text="Question 2", question_no=2, event=self.event)
    
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
    def setUp(self):
        self.user_staff = create_user('staff', True)
        self.user_lambda = create_user('lambda', False)
        self.company = create_company('Société de test')
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), company=self.company)
        self.question1 = Question.objects.create(question_text="Question 1", question_no=1, event=self.event)
        self.question2 = Question.objects.create(question_text="Question 2", question_no=2, event=self.event)
        EventGroup.objects.create(event=self.event, user=self.user_lambda)
        Choice.objects.create(choice_text="Oui", question=self.question1)
        Choice.objects.create(choice_text="Non", question=self.question1)
        Choice.objects.create(choice_text="NSP", question=self.question1)
        Choice.objects.create(choice_text="Oui", question=self.question2)
        Choice.objects.create(choice_text="Non", question=self.question2)
        Choice.objects.create(choice_text="NSP", question=self.question2)

    def test_launch_event(self):
        self.client.force_login(self.user_staff)
        url = reverse('polls:question', args=(self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        my_event = get_object_or_404(Event, id=self.event.id)
        self.assertEqual(my_event.current, True)
        user_list = get_list_or_404(UserVote)
        self.assertEqual(len(user_list), 2)
        self.assertEqual(response.context['question_no'], 1)
        self.assertEqual(response.context['event'].current, True)
        self.assertContains(response, "Question 1")
        self.assertContains(response, "Résolution suivante")

    def test_user_display_first_question(self):
        UserVote.objects.create(user=self.user_lambda, question=self.question1, has_voted=False)
        self.event.current = True
        self.event.save()
        self.client.force_login(self.user_lambda)
        url = reverse('polls:question', args=(self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['question_no'], 1)
        self.assertEqual(response.context['last_question'], False)
        self.assertEqual(response.context['user_vote'].has_voted, False)
        self.assertContains(response, "Question 1")
        self.assertContains(response, "Oui")
        self.assertContains(response, "Voter")
        self.assertContains(response, "Résolution suivante")

    def test_user_display_question_user_has_voted(self):
        UserVote.objects.create(user=self.user_lambda, question=self.question1, has_voted=True)
        self.event.current = True
        self.event.save()
        self.client.force_login(self.user_lambda)
        url = reverse('polls:question', args=(self.event.slug, 1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['question_no'], 1)
        self.assertEqual(response.context['event'].current, True)
        self.assertEqual(response.context['last_question'], False)
        self.assertEqual(response.context['user_vote'].has_voted, True)

    def test_user_display_last_question(self):
        UserVote.objects.create(user=self.user_lambda, question=self.question2, has_voted=False)
        self.event.current = True
        self.event.save()
        self.client.force_login(self.user_lambda)
        url = reverse('polls:question', args=(self.event.slug, 2))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['question_no'], 2)
        self.assertEqual(response.context['last_question'], True)
        self.assertContains(response, "Question 2")
        self.assertContains(response, "Oui")
        self.assertContains(response, "Voter")
        self.assertNotContains(response, "Résolution suivante")


class TestGetChartData(TestCase):
    def setUp(self):
        self.user_lambda = create_user('lambda', False)
        self.company = create_company('Société de test')
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), current=True, company=self.company)
        self.question1 = Question.objects.create(question_text="Question 1", question_no=1, event=self.event)
        self.question2 = Question.objects.create(question_text="Question 2", question_no=2, event=self.event)
        EventGroup.objects.create(event=self.event, user=self.user_lambda)
        Choice.objects.create(choice_text="Oui", question=self.question1, votes=3)
        Choice.objects.create(choice_text="Non", question=self.question1, votes=1)
        Choice.objects.create(choice_text="NSP", question=self.question1)

    def test_chart_first_question(self):
        url = reverse('polls:chart_data')
        response = self.client.get(url, {'event_slug': self.event.slug, 'question_no': 1})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['labels'], ['Oui', 'Non', 'NSP'])
        self.assertEqual(result['values'], [3, 1, 0])
        self.assertEqual(result['nb_votes'], 4)
        self.assertEqual(result['total_votes'], 1)
        bg_colors = [
            'rgba(124, 252, 0, 0.2)',
            'rgba(255, 99, 132, 0.2)',
            'rgba(255, 159, 64, 0.2)',
            'rgba(54, 162, 235, 0.2)',
            'rgba(75, 192, 192, 0.2)',
            'rgba(153, 102, 255, 0.2)',
            'rgba(128, 128, 128, 0.2)',
            'rgba(255, 206, 86, 0.2)',
            'rgba(222, 184, 135, 0.2)',
            'rgba(127, 255, 212, 0.2)'
        ]
        self.assertEqual(result['backgroundColor'], bg_colors)

class TestVote(TestCase):
    def setUp(self):
        self.user_lambda = create_user('lambda', False)
        self.company = create_company('Société de test')
        event_date = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(event_name="Evénement de test", event_date=event_date, 
            slug=slugify("Evénement de test" + str(event_date)), current=True, company=self.company)
        self.question1 = Question.objects.create(question_text="Question 1", question_no=1, event=self.event)
        self.question2 = Question.objects.create(question_text="Question 2", question_no=2, event=self.event)
        EventGroup.objects.create(event=self.event, user=self.user_lambda)
        Choice.objects.create(choice_text="Oui", question=self.question1)
        Choice.objects.create(choice_text="Non", question=self.question1)
        Choice.objects.create(choice_text="NSP", question=self.question1)
        UserVote.objects.create(user=self.user_lambda, question=self.question1, has_voted=False)

    def test_user_vote_first_question(self):
        self.client.force_login(self.user_lambda)
        url = reverse('polls:vote', args=(self.event.slug, 1))
        response = self.client.post(url, {'choice': 1})
        result = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        my_vote = get_object_or_404(UserVote, user=self.user_lambda, question=self.question1)
        self.assertEqual(my_vote.has_voted, True)
        my_choice = get_object_or_404(Choice, choice_text="Oui", question=self.question1)
        self.assertEqual(my_choice.votes, 1)
        data = {'success': 'OK', 'voted': True}
        self.assertEqual(result, data)


class TestResults(TestCase):
    pass

