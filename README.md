 Recherche d'itinéaires cyclables par apprentissage supervisé.
 =============================================================


 Ce projet permet d'utiliser les données d'openstreetmap pour calculer des itinéraires cyclables. Il se présente sous la forme d’une appli Django.

 Son intérêt est d'implémenter une partie apprentissage supervisé : après récupération d'une banque d'itinéraires entrés par des cyclistes, une note de cyclabilité est attribuée à chaque tronçon, et les itinéraires sont calculés en en tenant compte.

 Les sens interdits sont gérés uniquement au niveau de l'IA : en pratique si un tronçon n'est jamais emprunté dans un certain sens, il sera rarement proposé dans ce sens.

 Dans les différentes fonctions, pourcentage_détour est le pourcentage de détour accepté par le cycliste. 0 signifie aucun détour, 100 signifie qu'un trajet deux fois plus long serait accepté pour remplacer un trajet entièrement sur une rue non aménagée par un trajet entièrement sur une vraie piste cyclable. 


Installation
============

 - Une fois le dépôt cloné, le settings.py configuré (notamment pour paramétrer le serveur de base de données), le 'python manage.py makemigrations' et le 'python manage.py migrate' effectués, ouvrir un shell pour remplir la base ('python manage.py shell')
 - 'import dijk.pour_shell'
 - 'charge_zone([("ville 1", code postal1), ("ville2", code postal 2), ...], zone = "nom_de_la_zone", ville_défaut = "nom_de_la_ville_par_défaut", code = code_postal_de_la_ville_par_défaut)
 - patience, l’appli va télécharger et analyser les données osm de toutes les villes indiquées...
