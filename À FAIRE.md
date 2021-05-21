
À FAIRE :


- Recherche locale des rues
	- laisser le nom des rues et des villes dans le xml
	- recherche par nom de rue
	- continuer d'utiliser nominatim pour trouver le nom de rue et de ville

- tests

- enregistrer  cycla

- page php

À FAIRE (un jour)

- Chargement du XML : passer à une lecture au fur et à mesure. Ou transférer dans une bdd.
  - table voies avec colonnes id, nom, ville. table nœud_sur_rue avec col id_voie, id_nœud
  - classe BDD pour interfaçage.

- Normaliser les clefs d'adresses (pour le cache)

- Accélérer l'apprentissage. Sauvegarder les trajets calculé par Dijkstra ?


-  Pour chaque rue présente dans les données de Pau à vélo, mettre un coeff dans un dico pour chaque arrête.

- Sauvegarde et chargement des données :
	     - la cyclabilité -> csv (s,t,cyclabilité de l'arête (s,t)). 

- Gestion des transitions entre deux rues.

- Sauvegarde hors de osmnx pour portabilité. Voir la doc de networkx.


