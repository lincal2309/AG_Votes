# AG_Votes

Gestion de votes électroniques avec prise en compte de groupes de votant

## Présentation

L'application est disponible à cette adresse : 51.254.139.125

Son principe de fonctionnement est le suivant :

- Le représentant de la structure (superviseur) crée un événement ; il y adjoint des groupes dans lesquels il répartit les votants.
- Il a la possibilité d'envoyer une invitation à l'ensemble des votants, avec en pièce jointe la liste des résolutions à voter.
- Avant l'événement, les votants ont la possibilité, via l'application, de transmettre une procuration à un autre membre de leur groupe ; le récipiendaire valide alors (ou refuse) cette procuration.
- Le jour de l'événement (ou pendant la période de vote), chaque votant peut se connecter à l'application et voter pour les diofférentes résolution. De son côté, le superviseur dispose des résultats en temlps réel.
- Une fois les votes clos, les résultats sont présentés pour chaque résolution.

## Installation

Pour utiliser le programme dans votre environnement, vous devez créer un environnement virtuel et récupérer les fichiers du dépôt GitHub.
Vous devez obligatoirement créer un superuser pour accéder au panneau d'administration.

## Utilisation

Créez une société (pour le moment, l'application ne'en gère qu'une seule : si vous en créez une seconde, elle ne sera pas prise en compte à moins de supprimer la première) et renseignez les différentes informations associées.
Créez un compte "superviseur" : il doit voir les droits équipe, sans plus.

Ensuite, créez les utilisateurs, puis les groupes dans lesquels vous souhaitez les rassembler. Pour chaque groupe, vous pouvez indiquer un "poids" relatif qui représente leur importance les uns par rapport aux autres dans le résultat final du vote.
Créez un événement, associez les groupes, ajoutez la liste des résolutions ainsi que les choix possibles (ce sont les mêmes pour toutes les résolutions).

Notez que seul le superviseur (ou l'administrateur) peut créer des utilisateurs. Ces derniers ne DOIVENT PAS avoir un rôle équipe pour pouvoir voter.

Les votants recevront l'invitation et, à partir de ce moment, pourront se connecter pour gérez les éventuelles procurations.

Enfin, le jour de l'événement, chacun pourra exprimer son choix ; le superviseur aura acès aux résultats en temps réel, avec la répartition par groupe.
