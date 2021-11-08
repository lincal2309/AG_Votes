# -*-coding:Utf-8 -*

from django.core.mail import EmailMessage, get_connection
from django.conf import settings

from .models import Company, UserComp

# Base texts for emails
invite_text = """Bonjour {} {},

Veuillez trouver ci-joint l'ordre du jour pour l'événement suivant :
       {} qui se tiendra le {}.

En vous remerciant par avance."""


ask_proxy = """Bonjour {},
Ne pouvant me rendre disponible, accepteriez-vous de prendre procuration pour moi, pour l'événement suivant :
       {} qui se tiendra le {} ?

En vous remerciant par avance.

{} {}"""


confirm_proxy = """Bonjour {},

Je vous confirme accepter votre procuration.

Bien à vous.

{} {}"""


refuse_proxy = """Bonjour {},

Je suis au regret de ne pas pouvoir accepter votre procuration.

Bien à vous.

{} {}"""


cancel_proxy = """Bonjour {},

Suite à un changement de programme me concernant, je n'aurai plus besoin que vous ayez procuration pour moi. Je vous remercie de l'avoir acceptée.

Bien à vous.

{} {}"""


class PollsMail:
    """
        Class dedicated to emails management 

        Email configuration info come from Company model (managed in admin
        panel only)
        Requered info to send email come as attributes
        An "action dict" allows to launch action according to the keyword
        given as first parameter
    
    """

    def __init__(
        self,
        action,
        event,
        sender=[],
        recipient_list=[],
        cc_list=[],
        bcc_list=[],
        **kwargs
    ):
        """ At class instanciation, all parameters are converted into attributes 
            In some few cases, kwargs are defined and also converted into
            attributes, to ease future evolutions
        """
        self.event = event
        if event:
            self.company = Company.objects.get(event=self.event)
        self.sender = sender
        self.recipient_list = recipient_list
        self.cc_list = cc_list
        self.bcc_list = bcc_list
        self.subject = ""
        self.message = ""
        for attr_name, attr_value in kwargs.items():
            setattr(self, attr_name, attr_value)

        self.actions = {
            "invite": self.invite_users_message,
            "ask_proxy": self.ask_proxy_message,
            "confirm_proxy": self.confirm_proxy_message,
            "test_mail": self.test_mail,
        }

        self.actions[action]()

    def send_email_info(self):
        # Send email method
        with get_connection(
            host=self.company.host,
            port=self.company.port,
            username=self.company.hname,
            password=self.company.fax,
            use_tls=self.company.use_tls,
        ) as connection:

            self.msg = EmailMessage(
                self.subject,
                self.message,
                self.company.hname,
                self.recipient_list,
                cc=self.cc_list,
                bcc=self.bcc_list,
                connection=connection,
            )

            self.msg.send()

    def invite_users_message(self):
        # Send invitation to all users
        # Do not use send_email_info() method to open connexion only once
        connection = get_connection(
            host=self.company.host,
            port=self.company.port,
            username=self.company.hname,
            password=self.company.fax,
            use_tls=self.company.use_tls,
        )

        self.subject = "Invitation et ordre du jour"
        for user in UserComp.objects.filter(usergroup__event=self.event):
            if user.user.email:
                self.recipient_list = [user.user.email]
                self.message = invite_text.format(
                    user.user.first_name,
                    user.user.last_name,
                    self.event.event_name,
                    str(self.event.event_date),
                )

                self.msg = EmailMessage(
                    self.subject,
                    self.message,
                    self.company.hname,
                    self.recipient_list,
                    cc=self.cc_list,
                    bcc=self.bcc_list,
                    connection=connection,
                )

                if hasattr(self, "attach"):
                    self.msg.attach_file(settings.MEDIA_ROOT + self.attach)
                self.msg.send()

        connection.close()

    def ask_proxy_message(self):
        self.subject = "Pouvoir"
        self.cc_list += self.sender
        self.message = ask_proxy.format(
            self.proxy.user.first_name,
            self.event.event_name,
            str(self.event.event_date),
            self.user.user.first_name,
            self.user.user.last_name,
        )

        self.send_email_info()

    def confirm_proxy_message(self):
        self.proxy = UserComp.objects.get(id=self.proxy_id)
        self.subject = "Confirmation de pouvoir"
        self.message = confirm_proxy.format(
            self.proxy.user.first_name, self.user.user.first_name, self.user.user.last_name
        )

        self.send_email_info()

    def test_mail(self):
        self.company = self.comp
        self.subject = "Test envoi de mail " + self.company.company_name
        self.message = (
            "Ceci est un message de test pour la société " + self.company.company_name
        )
        self.recipient_list = ["gressinc@gmail.com"]

        self.send_email_info()
