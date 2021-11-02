 Recherche d'itinéaires cyclables par apprentissage supervisé.
 =============================================================


 Ce projet permet d'utiliser les données d'openstreetmap pour calculer des itinéraires cyclables.

 Son intérêt est d'implémenter une partie apprentissage supervisé : après récupération d'une banque d'itinéraires entrés par des cyclistes, un note de cyclabilité est attribuée à chaque tronçon, et les itinéraires sont calculés en en tenant compte.

 Les sens interdits sont gérés uniquement au niveau de l'IA : en pratique si un tronçon n'est jamais emprunté dans un certain sens, il sera rarement proposé dans ce sens.

 Dans les différentes fonctions, pourcentage_détour est le pourcentage de détour accepté par le cycliste. 0 signifie aucun détour, 100 signifie qu'un trajet deux fois plus long serait accepté pour remplacer un trajet entièrement sur une rue non aménagée par un trajet entièrement sur une vraie piste cyclable. 


 Limitations connues :
 - Il y a très peu de numéros de rue sur openstreetmap. Ainsi lorsque vous indiquez un tel numéro dans l’adresse, il y des chances que je ne puisse pas le prendre en compte, et l’algo vous aménera au point de la rue d’arrivée le plus proche de la rue de départ. (Ceci a des conséquences subtiles sur l’apprentissage ; au vu des choix que j’ai fait il y aura plutôt sous-apprentissage dans ce genre de cas, si vous voulez les détails payez moi une bière.)
 - À l’affichage d’un itinéraire, lorsqu’il existe plusieurt arêtes entre deux sommets, elles sont toutes dessinées, ce qui produit des boucles. C’est uniquement un problème d’affichage : dans les calculs seules l’arête la plus intéressante est prise en compte.


Installation
============

 - cloner le dépôt
 - se placer dans le dossier site_velo
 - dans dijk/progs_python/params.py régler la zone géographique. Il faut préciser la bounding box de la zone géographique à charger sur openstreetmap, la ville par défaut dans les recherches d’adresse, le pays par défaut, et la liste des villes qui apprraissent dans la zone avec leur code postal.
 - Lancer dijk/progs_python/initialisation/initialisation.py pour télécharger et extraire les données de la zone indiquée.
 - Pour tester l’appli, python3 manage.py runserver. Ouvrir alors dans un navigateur http://localhost:8000/itineraires.
 - Pour l’installer pour de vrai, je vous laisse vous reporter à la doc de votre hébergeur... Il faudra éditer site_velo/settings.py pour régler les paramètre de la base de données notamment.
 