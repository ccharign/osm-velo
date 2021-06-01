
À FAIRE :




- Recherche d’un numéro dans une rue
  - rajouter la ville dans le dico pour interpolation
  - programmer l’interpolation.


- page php

- Peut-on se passer complètement du xml ?

- limiter les imports de osmnx (seulement les modules utiles). Notamment le gros ne sert que pour la création du graphe -> ne pas mettre un import pour init_graph mais un subprocess ?

À FAIRE (un jour)

- Chargement du XML : passer à une lecture au fur et à mesure. Ou transférer dans une bdd.
  - table voies avec colonnes id, nom, ville. table nœud_sur_rue avec col id_voie, id_nœud
  - classe BDD pour interfaçage.

- Normaliser les clefs d'adresses (pour le cache)

- A*

- Accélérer l'apprentissage. Sauvegarder les trajets calculé par Dijkstra ?

- Gestion des transitions entre deux rues.

- Sauvegarde hors de osmnx pour portabilité. Voir la doc de networkx.


