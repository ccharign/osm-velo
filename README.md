 Recherche d'itinéaires cyclables par apprentissage supervisé.
 =============================================================


 Ce projet permet d'utiliser les données d'openstreetmap pour calculer des itinéraires cyclables.

 Son intérêt est d'implémenter une partie apprentissage supervisé : après récupération d'une banque d'itinéraires entrés par des cyclistes, un note de cyclabilité est attribuée à chaque tronçon, et les itinéraires sont calculés en en tenant compte.

 Les sens interdits sont gérés uniquement au niveau de l'IA : en pratique si un tronçon n'est jamais emprunté dans un sens, il sera rarement proposé dans ce sens.

 Dans les différentes fonction, pourcentage_détour est le pourcentage de détour accepté par le cycliste. 0 signifie aucun détour, 100 signifie qu'un trajet deux fois plus long serait accepté pour remplacer entièrement une rue non aménagée (réérence : rue Faisans) par une piste cyclable (référence : celle du Fébus).

 Le notebook démo.ipynb montre le fonctionnement.

 Pour l'instant, seule la ville de Pau est en mémoire, mais les fonctions dans init_graphe et dans récup_données permettent de charger n'inporte quelle zone.

 Pour contribuer en fournissant des trajets c'est ici https://framaforms.org/entrainement-du-calculateur-participatif-ditineraires-version-clic-1618406941
  