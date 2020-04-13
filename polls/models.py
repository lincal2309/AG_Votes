# -*-coding:Utf-8 -*

from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q
from django.conf import settings


class Company(models.Model):
    """
    Company informations
    - Detailed information for display purposes in the application
      but also used in documents built and sent by the application
    - Mail information to be able to send emails
    """
    company_name = models.CharField("nom", max_length=200)
    comp_slug = models.SlugField("slug")
    logo = models.ImageField(upload_to="img/", null=True, blank=True)
    statut = models.CharField("forme juridique", max_length=50)
    siret = models.CharField("SIRET", max_length=50)
    street_num = models.IntegerField("N° de rue", null=True, blank=True)
    street_cplt = models.CharField("complément", max_length=50, null=True, blank=True)
    address1 = models.CharField("adresse", max_length=300)
    address2 = models.CharField(
        "complément d'adresse", max_length=300, null=True, blank=True
    )
    zip_code = models.IntegerField("code postal")
    city = models.CharField("ville", max_length=200)
    host = models.CharField("serveur mail", max_length=50, null=True, blank=True)
    port = models.IntegerField("port du serveur", null=True, blank=True)
    hname = models.EmailField("utilisateur", max_length=100, null=True, blank=True)
    fax = models.CharField("mot de passe", max_length=50, null=True, blank=True)
    use_tls = models.BooleanField("authentification requise", default=True, blank=True)

    class Meta:
        verbose_name = "Société"
        constraints = [
            models.UniqueConstraint(fields=["comp_slug"], name="unique_comp_slug")
        ]

    def __str__(self):
        return self.company_name

    @classmethod
    def get_company(cls, slug):
        """ Retreive company from its slug """
        return cls.objects.get(comp_slug=slug)


class UserComp(models.Model):
    """
    Link between users and companies
    Used to restrict display to companie(s) the users belong to
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Société")
    is_admin = models.BooleanField("administrateur", default=False)

    class Meta:
        verbose_name = "Liens Utilisateurs / Sociétés"
        verbose_name_plural = "Liens Utilisateurs / Sociétés"

    @classmethod
    def create_usercomp(cls, user, company, is_admin=False):
        """ Create a new UserComp """
        usr_comp = UserComp(user=user, company=company, is_admin=is_admin)
        usr_comp.save()
        return usr_comp


class EventGroup(models.Model):
    """
    Groups of users - Need to be linked to a company
    The link with events is supported by the Event
    (as groups can be reused in several Events)
    """
    # TO DO : link to a company (direct or indirect, the link should be unique)
    # Note that users are linked to a Company => functional rules could be convenient
    users = models.ManyToManyField(UserComp, verbose_name="utilisateurs", blank=True)
    group_name = models.CharField("nom", max_length=100)
    weight = models.IntegerField("poids", default=0)

    def __str__(self):
        return self.group_name

    class Meta:
        verbose_name = "Groupe d'utilisateurs"
        verbose_name_plural = "Groupes d'utilisateurs"

    @classmethod
    def get_list(cls, event_slug):
        """ Retreive list of groups linked to an event identified with its slug """
        return cls.objects.filter(event__slug=event_slug)

    @classmethod
    def user_in_event(cls, event_slug, user):
        """ Checks whether a user belongs to the group or not """
        user_in_group = False
        if len(user.eventgroup_set.filter(event__slug=event_slug)) > 0:
            user_in_group = True
        return user_in_group


class Event(models.Model):
    """
    Class defining Events and related information
    Events are mandatory linked to a Company
    Events should contain at least one group of users
    """
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, verbose_name="société"
    )
    groups = models.ManyToManyField(EventGroup, verbose_name="groupes", blank=True)
    rules = [("MAJ", "Majorité"), ("PROP", "Proportionnelle")]
    event_name = models.CharField("nom", max_length=200)
    event_date = models.DateField("date de l'événement")
    slug = models.SlugField()
    current = models.BooleanField("en cours", default=False)
    quorum = models.IntegerField(default=33)
    rule = models.CharField(
        "mode de scrutin", max_length=5, choices=rules, default="MAJ"
    )

    class Meta:
        # Constraint(s) : an event_slug can be linked to only one company
        #       This allow several companies to use the same event_slugs,
        #       unless one sngle event_slug is used by company
        verbose_name = "Evénement"
        constraints = [
            models.UniqueConstraint(fields=["company_id", "slug"], name="unique_event_slug")
        ]

    def __str__(self):
        return self.event_name

    @classmethod
    def get_event(cls, comp_slug, event_slug):
        """ Retreive event from its slug """
        # TO DO : add the company in the parameters to ensure one single row is returned
        # company = Company.get_company(comp_slug)
        return get_object_or_404(Event, slug=event_slug, company__comp_slug=comp_slug)

    @classmethod
    def get_next_events(cls, company):
        """ Retreive all events releted to a company that are planned in the future """
        return cls.objects.filter(
            company=company, event_date__gte=timezone.now()
        ).order_by("event_date")

    def set_current(self):
        """ Set the event to be "in progress" """
        self.current = True
        self.save()


class Question(models.Model):
    """
    Questions / resolutions class
    Each quesiton or resolution is linked to a unique event and has a unique number
    (which defines the order)
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="événement")
    question_text = models.TextField("texte de la résolution")
    question_no = models.IntegerField("numéro de résolution")

    class Meta:
        verbose_name = "Résolution"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "question_no"], name="unique_question_no_per_event"
            ),
            models.CheckConstraint(check=Q(question_no__gt=0), name="question_no_gt_0"),
        ]

    def __str__(self):
        return self.question_text

    @classmethod
    def get_question_list(cls, event):
        """ Retreives all questions for an event, ordered by number """
        return cls.objects.filter(event=event).order_by("question_no")

    @classmethod
    def get_question(cls, event, question_no):
        """ Retreives a question from its and numer and the related event's slug """
        return cls.objects.get(event=event, question_no=question_no)

    def get_results(self):
        """ Calculates votes' results for a question """
        # Calcultate global results for the question
        evt_group_list = EventGroup.get_list(self.event.slug)

        # Initialize global results data
        global_choice_list = Choice.get_choice_list(self.event.slug).values(
            "choice_text"
        )
        group_vote = {}
        group_vote = {}
        for choice in global_choice_list:
            group_vote[choice["choice_text"]] = 0

        # Gather votes info for each group
        for evt_group in evt_group_list:
            total_votes = EventGroup.objects.filter(id=evt_group.id).aggregate(
                Count("users")
            )["users__count"]

            result_list = Result.get_vote_list(
                self.event, evt_group, self.question_no
            ).values("choice__choice_text", "votes", "group_weight")

            labels = [choice["choice__choice_text"] for choice in result_list]
            values = [choice["votes"] for choice in result_list]

            # Calculate aggregate results
            weight = result_list[0]["group_weight"]
            if self.event.rule == "MAJ":
                # Règles à définir : cas d'égalité, cas où pas de valeur
                max_val = values.index(max(values))
                group_vote[labels[max_val]] += weight
            elif self.event.rule == "PROP":
                # Calculate totals per choice, including group's weight
                # Addition of each group's result
                for i, choice in enumerate(labels):
                    if choice in group_vote:
                        group_vote[choice] += values[i] * weight / 100

        if self.event.rule == "PROP":
            # Calculate percentage for each choice
            total_votes = 0
            for val in group_vote.values():
                total_votes += val
            if total_votes > 0:
                for choice, value in group_vote.items():
                    group_vote[choice] = round((value / total_votes) * 100, 2)

        return group_vote

    def get_chart_results(self):
        """  Set up results data to be displayed """
        group_vote = self.get_results()

        # Setup global info for charts
        global_labels = []
        global_values = []
        for label, value in group_vote.items():
            global_labels.append(label)
            global_values.append(value)

        nb_votes = sum(global_values)

        group_data = {"labels": global_labels, "values": global_values}

        chart_background_colors = settings.BACKGROUND_COLORS
        chart_border_colors = settings.BORDER_COLORS

        # Extends color lists to fit with nb values to display
        while len(chart_background_colors) < nb_votes:
            chart_background_colors += settings.BACKGROUND_COLORS
            chart_border_colors += settings.BACKGROUND_COLORS

        data = {
            "chart_data": group_data,
            "backgroundColor": chart_background_colors,
            "borderColor": chart_border_colors,
        }

        return data


class Choice(models.Model):
    """
    Choices class
    For each event, the possible answers are stored globally 
        and will be proposed for each quesiton / resolution
    Each choise has a unique number that defines the display order
    """
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, null=True, verbose_name="événement"
    )
    choice_text = models.CharField("libellé", max_length=200)
    choice_no = models.IntegerField("numéro de question")

    class Meta:
        verbose_name = "Choix"
        verbose_name_plural = "Choix"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "choice_no"], name="unique_choice_no_per_event"
            )
        ]

    def __str__(self):
        return self.choice_text

    @classmethod
    def get_choice_list(cls, event_slug):
        """ Retreives all choices for an event, ordered by number """
        return Choice.objects.filter(event__slug=event_slug).order_by("choice_no")


class UserVote(models.Model):
    """
    Follow up users' votes for an event
    Indicates, for each Evznt / User / question :
        Number of votes (in case of procuration)
        If he has voted, and when
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="événement")
    user = models.ForeignKey(UserComp, on_delete=models.CASCADE, verbose_name="utilisateur")
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, verbose_name="résolution"
    )
    nb_user_votes = models.IntegerField()
    has_voted = models.BooleanField("a voté", default=False)
    date_vote = models.DateTimeField("date du vote", null=True)

    class Meta:
        verbose_name = "Vote utilisateurs et pouvoirs"
        verbose_name_plural = "Votes utilisateurs et pouvoirs"

    def __str__(self):
        return (
            "Vote de "
            + self.user.username
            + " pour la question n° "
            + str(self.question.question_no)
        )

    @classmethod
    def get_user_vote(cls, event_slug, user, question_no):
        """ Return user's vote status """
        return cls.objects.get(
            user=user,
            event__slug=event_slug,
            question__event__slug=event_slug,
            question__question_no=question_no,
        )

    @classmethod
    def init_uservotes(cls, event):
        """
        Initializae user votes table
        When the event is lauchend, gather all info related to the vote, including procurations,
            to define each user rights to vote
        """
        event_user_list = [
            user for user in UserComp.objects.filter(eventgroup__event=event)
        ]
        question_list = Question.get_question_list(event)
        user_group_list = EventGroup.objects.filter(event=event)
        event_choice_list = Choice.get_choice_list(event.slug)
        for question in question_list:
            for event_user in event_user_list:
                nb_user_votes = 1
                proxy_list, user_proxy, user_proxy_list = Procuration.get_proxy_status(
                    event.slug, event_user
                )
                if user_proxy:
                    nb_user_votes = 0
                elif user_proxy_list:
                    nb_user_votes += len(user_proxy_list)
                cls.objects.create(
                    event=event, user=event_user, question=question, nb_user_votes=nb_user_votes
                )
            for event_choice in event_choice_list:
                for usr_group in user_group_list:
                    Result.objects.create(
                        event=event,
                        eventgroup=usr_group,
                        choice=event_choice,
                        question=question,
                        group_weight=usr_group.weight,
                    )

    @classmethod
    def set_vote(cls, event_slug, user, question_no, choice_id):
        """ Update info while user's voting """
        user_vote = cls.get_user_vote(event_slug, user, question_no)
        user_vote.nb_user_votes, user_vote.has_voted, user_vote.date_vote = (
            user_vote.nb_user_votes - 1,
            True,
            timezone.now(),
        )
        user_vote.save()
        Result.add_vote(user, event_slug, question_no, choice_id)
        return user_vote


class Result(models.Model):
    """
    Manage votes results
    Results are strored for each group
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="événement")
    eventgroup = models.ForeignKey(
        EventGroup, on_delete=models.CASCADE, verbose_name="groupe d'utilisateurs"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, verbose_name="choix")
    votes = models.IntegerField("nombre de votes", default=0)
    group_weight = models.IntegerField("poids", default=0)

    def __str__(self):
        return (
            "Votes du groupe "
            + self.eventgroup.group_name
            + " pour le choix "
            + str(self.choice.choice_no)
            + " de la question "
            + str(self.question.question_no)
        )

    class Meta:
        verbose_name = "Résultat des votes"
        verbose_name_plural = "Résultats des votes"

    @classmethod
    def add_vote(cls, user, event_slug, question_no, choice_id):
        res = cls.objects.get(
            event__slug=event_slug,
            eventgroup__users=user,
            eventgroup__event__slug=event_slug,
            question__question_no=question_no,
            choice__id=choice_id,
        )
        res.votes += 1
        res.save()

    @classmethod
    def get_vote_list(cls, event, evt_group, question_no):
        return cls.objects.filter(
            event=event,
            eventgroup=evt_group,
            eventgroup__event=event,
            question__question_no=question_no,
        ).order_by("choice__choice_no")


class Procuration(models.Model):
    """
    Procuration management
    Store all information about user, proxy, and procuration formal acceptance
    """
    user = models.ForeignKey(UserComp, on_delete=models.CASCADE, verbose_name="utilisateur")
    proxy = models.ForeignKey(
        UserComp,
        on_delete=models.CASCADE,
        related_name="proxy",
        verbose_name="récipiendaire",
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="événement")
    proxy_date = models.DateField("date de procuration")
    proxy_confirmed = models.BooleanField("procuration confirmée", default=False)
    confirm_date = models.DateField("date de confirmation", null=True, blank=True)

    def __str__(self):
        return (
            "Procuration de "
            + self.user.last_name
            + " pour l'événement "
            + self.event.event_name
        )

    class Meta:
        verbose_name = "Procuration"

    @classmethod
    def get_proxy_status(cls, event_slug, user):
        user_proxy_list = []
        proxy_list = []
        user_proxy = None
        if len(cls.objects.filter(proxy=user, event__slug=event_slug)) > 0:
            # Case user is proxyholder => get proxy list
            user_proxy_list = cls.objects.filter(
                proxy=user, event__slug=event_slug
            ).order_by("usercomp__user__last_name")
        elif len(cls.objects.filter(user=user)) > 0:
            # Case user has given proxy => get proxyholder
            usv = cls.objects.get(user=user)
            user_proxy = UserComp.objects.get(id=usv.proxy.id)
        else:
            # Case user has no proxy and is not proxyholder
            # => get list of users that could receive his proxy
            # Get list of users from the same group, except the user himself
            # and those who already gave proxy
            # As values are restricted to user_id, we need to transform them
            # into a list usable in the next request
            id_list = [
                int(proxy["user__id"]) for proxy in cls.objects.all().values("user__id")
            ]
            proxy_list = (
                UserComp.objects.filter(eventgroup__users=user)
                .exclude(id=user.id)
                .exclude(id__in=id_list)
                .order_by("user__last_name")
            )
        return proxy_list, user_proxy, user_proxy_list

    @classmethod
    def set_user_proxy(cls, event, user, proxy):
        cls.objects.create(
            event=event, user=user, proxy=proxy, proxy_date=timezone.now()
        )

    @classmethod
    def confirm_proxy(cls, event, user, proxy_id):
        proc = cls.objects.get(user__id=proxy_id, proxy=user, event=event)
        if not proc.proxy_confirmed:
            proc.proxy_confirmed, proc.confirm_date = True, timezone.now()
            proc.save()

    @classmethod
    def cancel_proxy(cls, event_slug, user, *args):
        if len(args) == 1:
            # Case a proxyholder refuse a proxy request
            cls.objects.filter(
                event__slug=event_slug, user__id=user, proxy=args[0]
            ).delete()
        else:
            # Case a user cancels his proxy's request
            cls.objects.filter(event__slug=event_slug, user=user).delete()
