 Recherche d'itinéaires cyclables par apprentissage supervisé.
 =============================================================


 Ce projet permet d'utiliser les données d'openstreetmap pour calculer des itinéraires cyclables.

 Son intérêt est d'implémenter une partie apprentissage supervisé : après récupération d'une banque d'itinéraires entrés par des cyclistes, un note de cyclabilité est attribuée à chaque tronçon, et les itinéraires sont calculés en en tenant compte.

 Les sens interdits sont gérés uniquement au niveau de l'IA : en pratique si un tronçon n'est jamais emprunté dans un sens, il sera rarement proposé dans ce sens.

 Dans les différentes fonction, pourcentage_détour est le pourcentage de détour accepté par le cycliste. 0 signifie aucun détour, 100 signifie qu'un trajet deux fois plus long serait accepté pour remplacer entièrement une rue non aménagée (réérence : rue Faisans) par une piste cyclable (référence : celle du Fébus).

 Le notebook démo.ipynb ou test.py montrent le fonctionnement. Le notebook est testable en ligne grâce à Binder :
 [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ccharign/osm-velo/HEAD?filepath=d%C3%A9mo.ipynb)

 Les trajet calculés sont affichés dans une page web interactive.

 Pour l'instant, seule la ville de Pau et son agglomération est en mémoire, mais les fonctions dans init_graphe et dans récup_données permettent de charger n'inporte quelle zone.

 Ce projet ne pourra devenir pertinent que lorsque j’aurai récupérer disons une centaine de trajets ! Je compte sur vous pour m’en fournir un ou deux,  c'est ici https://framaforms.org/entrainement-du-calculateur-participatif-ditineraires-version-clic-1618406941

 Je compte également sur vous pour m’indiquer les erreurs et les problèmes que vous aurez détectés.


 Limitations connues :
 - Il y a très peu de numéros de rue sur openstreetmap. Ainsi lorsque vous indiquez un tel numéro dans l’adresse, il y des chances que je ne puisse pas le prendre en compte, et l’algo vous aménera au point de la rue d’arrivée le plus proche de la rue de départ. (Ceci a des conséquences subtiles sur l’apprentissage ; au vu des choix que j’ai fait il y aura plutôt sous-apprentissage dans ce genre de cas, si vous voulez les détails payez moi une bière.)
  