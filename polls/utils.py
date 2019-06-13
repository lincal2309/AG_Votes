# -*-coding:Utf-8 -*

from django.core.mail import EmailMessage, get_connection
from django.contrib.auth.models import User
from .models import Company, Event, Question, Choice, UserVote, EventGroup, Result, Procuration

ask_proxy = "Bonjour {}, \n\nNe pouvant me rendre disponible, accepteriez-vous de prendre procuration pour moi, pour l'événement suivant : \n{} qui se tiendra le {} ? \n\nEn vous remerciant par avance.\n\n{} {}"
confirm_proxy = "Bonjour {}, \n\nJe vous confirme accepter votre procuration.\n\nBien à vous.\n\n{} {}"
refuse_proxy = "Bonjour {}, \n\nJe suis au regret de ne pas pouvoir accepter votre procuration.\n\nBien à vous.\n\n{} {}"
cancel_proxy = "Bonjour {}, \n\nSuite à un changement de programme me concernant, je n'aurai plus besoin que vous ayez procuration pour moi. Je vous remercie de l'avoir acceptée.\n\nBien à vous.\n\n{} {}"


class PollsMail():
    def __init__(self, action, event, sender=[], recipient_list=[], cc_list=[], bcc_list=[], **kwargs):
        self.event = event
        self.company = Company.objects.get(event=self.event)
        self.sender = sender
        self.recipient_list = recipient_list
        self.cc_list = cc_list + ["lincal1@free.fr"]     # Ajouter un champ dédié dans Company ? Ou envoyer aux admins ?
        self.bcc_list = bcc_list
        self.subject = ""
        self.message = ""
        for attr_name, attr_value in kwargs.items():
            setattr(self, attr_name, attr_value)

        self.actions = {'ask_proxy': self.ask_proxy_message, 'confirm_proxy': self.confirm_proxy_message}
        self.actions[action]()

    def send_email_info(self):
        # Send email method
        with get_connection(host=self.company.host, port=self.company.port, username=self.company.hname, password=self.company.fax, use_tls=self.company.use_tls) as connection:
            EmailMessage(self.subject, self.message, self.company.host_user, self.recipient_list, cc=self.cc_list, bcc=self.bcc_list, connection=connection).send()

    
    def ask_proxy_message(self):
        self.subject = "Pouvoir"
        self.message = ask_proxy.format(self.proxy.first_name, self.event.event_name, str(self.event.event_date), self.user.first_name, self.user.last_name)
        self.cc_list += self.sender
        self.send_email_info()

    def confirm_proxy_message(self):
        self.proxy = User.objects.get(id=self.proxy_id)
        self.subject = "Confirmation de pouvoir"
        self.message = confirm_proxy.format(self.proxy.first_name, self.user.first_name, self.user.last_name)
        self.send_email_info()