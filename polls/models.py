# -*-coding:Utf-8 -*

from django.db import models
from django.contrib.auth.models import User, Group


class Company(models.Model):
    company_name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to="img/", null=True)

    class Meta:
        verbose_name = "Société"

    def __str__(self):
        return self.company_name


class Event(models.Model):
    event_name = models.CharField(max_length=200)
    event_date = models.DateField()
    slug = models.SlugField()
    current = models.BooleanField(default=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Evénement"

    def __str__(self):
        return self.event_name


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Question"

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Choix"
        verbose_name_plural = "Choix"

    def __str__(self):
        return self.choice_text


class EventGroup(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    # group = models.ForeignKey(Group, on_delete=models.CASCADE)   # - Prévoir relation  ManyToMany
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Evénements : groupes d'utilisateurs"
        verbose_name_plural = "Evénements : groupes d'utilisateurs"

    def __str__(self):
        return "Groupes associés à l'événement " + self.event.event_name


class UserVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    proxy_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='proxy')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    has_voted = models.BooleanField(default=False)
    date_vote = models.DateTimeField(null=True)

    class Meta:
        verbose_name = "Vote utilisateurs et pouvoirs"
        verbose_name_plural = "Votes utilisateurs et pouvoirs"

    def __str__(self):
        return "Vote de " + self.user.username + " à la question " + self.question.question_text
