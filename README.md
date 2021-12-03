 Recherche d'itinéaires cyclables par apprentissage supervisé.
 =============================================================


 Ce projet permet d'utiliser les données d'openstreetmap pour calculer des itinéraires cyclables.

 Son intérêt est d'implémenter une partie apprentissage supervisé : après récupération d'une banque d'itinéraires entrés par des cyclistes, une note de cyclabilité est attribuée à chaque tronçon, et les itinéraires sont calculés en en tenant compte.

 Les sens interdits sont gérés uniquement au niveau de l'IA : en pratique si un tronçon n'est jamais emprunté dans un certain sens, il sera rarement proposé dans ce sens.

 Dans les différentes fonctions, pourcentage_détour est le pourcentage de détour accepté par le cycliste. 0 signifie aucun détour, 100 signifie qu'un trajet deux fois plus long serait accepté pour remplacer un trajet entièrement sur une rue non aménagée par un trajet entièrement sur une vraie piste cyclable. 


Installation
============

 - cloner le dépôt
 - se placer dans le dossier site_velo
 - dans dijk/progs_python/params.py régler la zone géographique. Il faut préciser la bounding box de la zone géographique à charger sur openstreetmap, la ville par défaut dans les recherches d’adresses, le pays par défaut, et la liste des villes qui apparaissent dans la zone avec leur code postal.
 - Lancer dijk/progs_python/initialisation/initialisation.py pour télécharger et extraire les données de la zone indiquée.
 - Pour tester l’appli, python3 manage.py runserver. Ouvrir alors dans un navigateur http://localhost:8000/itineraires.
 - Pour l’installer pour de vrai, je vous laisse vous reporter à la doc de votre hébergeur et de Django... Il faudra éditer site_velo/settings.py pour régler les paramètres de sécurité et de la base de données notamment.
 
