# -*-coding:Utf-8 -*

from django.contrib import admin, messages
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import Sum

from weasyprint import HTML, CSS

import os

from .models import (
    Company,
    Event,
    Question,
    Choice,
    UserVote,
    EventGroup,
    Result,
    Procuration,
)
from .pollsmail import PollsMail


class CompanyAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["company_name", "logo"]}),
        (
            "Informations administratives",
            {
                "fields": [
                    "statut",
                    "siret",
                    "street_num",
                    "street_cplt",
                    "address1",
                    "address2",
                    "zip_code",
                    "city",
                ]
            },
        ),
        (
            "Configuration de la messagerie",
            {
                "fields": ["host", "port", "hname", "fax", "use_tls"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["test_email"]

    def test_email(self, request, queryset):
        for comp in queryset:
            PollsMail("test_mail", None, comp=comp)


class ChoiceInLine(admin.TabularInline):
    model = Choice
    ordering = ("choice_no",)
    fields = ["choice_text", "choice_no"]
    extra = 3


class QuestionInLine(admin.TabularInline):
    model = Question
    ordering = ("question_no",)
    fields = ["question_text", "question_no"]
    extra = 3


class EventAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("event_name", "event_date")}
    fields = [
        "event_name",
        "event_date",
        "slug",
        "company",
        "groups",
        "quorum",
        "rule",
        "current",
    ]
    list_display = ("event_name", "event_date", "quorum", "rule", "current")
    ordering = ("event_date", "event_name")
    filter_horizontal = ("groups",)
    inlines = [QuestionInLine, ChoiceInLine]

    actions = ["invite_users", "reinit_event"]

    def invite_users(self, request, queryset):
        for event in queryset:
            # Check total groups' weight is 100
            if (
                EventGroup.objects.filter(event=event).aggregate(Sum("weight"))[
                    "weight__sum"
                ]
                != 100
            ):
                self.message_user(
                    request,
                    "Le total des poids des groupes doit être égal à 100",
                    level=messages.ERROR,
                )
            else:
                # Generate list of questions
                company = Company.objects.get(event=event)
                question_list = Question.get_question_list(event.slug)
                context_data = {
                    "company": company,
                    "event": event,
                    "question_list": question_list,
                }

                html_string = render_to_string("polls/resolutions.html", context_data)
                html = HTML(string=html_string, base_url=request.build_absolute_uri())
                document = html.write_pdf(
                    os.path.join(settings.MEDIA_ROOT, "pdf/resolutions.pdf"),
                    stylesheets=[
                        CSS(os.path.join(settings.STATIC_ROOT, "polls/css/polls.css")),
                        CSS(
                            os.path.join(
                                settings.STATIC_ROOT, "polls/css/bootstrap.min.css"
                            )
                        ),
                    ],
                )

                # Send email to users
                PollsMail("invite", event, attach="pdf/resolutions.pdf")

                # Message acknowledgement
                message_usr = "Les participants à l'événement {} ont été invités".format(
                    event.event_name
                )
                self.message_user(request, message_usr)

    invite_users.short_description = "Inviter les participants"

    def reinit_event(self, request, queryset):
        # =================================================================
        # SUPERUSER ONLY : allows to set event to "not started" for tests
        # =================================================================
        for event in queryset:
            # Set event to "not started"
            event.current = False
            event.save()

            Procuration.objects.filter(event=event).delete()
            question_list = Question.objects.filter(event=event)

            # Resets users vote status
            for question in question_list:
                UserVote.objects.filter(question=question).delete()
                Result.objects.filter(question=question).delete()

            # Reinitialize complete view
            nb_questions = len(question_list)

            user_can_vote = False
            if EventGroup.user_in_event(event.slug, request.user):
                user_can_vote = True

    reinit_event.short_description = "Réinitialiser l'événement"


class EventGroupAdmin(admin.ModelAdmin):
    fields = ["group_name", "weight", "users"]
    filter_horizontal = ("users",)


class UserVoteAdmin(admin.ModelAdmin):
    list_display = ("uservote_label", "has_voted", "date_vote")

    def uservote_label(self, obj):
        return "Vote de %s pour la question n° %s" % (
            obj.user.username,
            str(obj.question.question_no),
        )

    uservote_label.short_description = "Vote utilisateur"


class ResultAdmin(admin.ModelAdmin):
    list_display = ("event_label", "eventgroup", "question", "choice", "votes")
    ordering = ("eventgroup", "question", "choice")

    def event_label(self, obj):
        event = Event.objects.get(
            groups=obj.eventgroup, question=obj.question, choice=obj.choice
        )
        return event.event_name

    event_label.short_description = "Evènement"


class ProcurationAdmin(admin.ModelAdmin):
    list_display = ("procuration_detail", "utilisateur_id", "recipiendaire_id")

    def procuration_detail(self, obj):
        return "Procuration de %s pour l'événement %s" % (
            obj.user.last_name,
            obj.event.event_name,
        )

    procuration_detail.short_description = "Procuration"

    def utilisateur_id(self, obj):
        return obj.user.id

    def recipiendaire_id(self, obj):
        return obj.proxy.id


admin.site.register(Company, CompanyAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(EventGroup, EventGroupAdmin)
admin.site.register(Result, ResultAdmin)
