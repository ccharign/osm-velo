
À FAIRE :

Pb de collision si deux utilisateurs en même temps
    -> donner un nom personalisé aux fichiers html produits
    -> les nettoyer après coup

Mettre dans le cache les noms osm de lieux récupérés via nominatim

Afficher les étapes sur la carte


Il existe des rues qui figurent dans rue_num_coord, donc qui étaient dans le .osm, mais qui ne sont pas dans nœuds_rue. Ce dernier est créé par nœuds_des_rues.py. Par exemple place reine marguerite, dont le nœud du graphe est 339262446.
Problème lorsqu’une rue ne contient qu’un sommet de g, donc aucune arête.
-> Il faut mettre le nom de la rue et de la ville dans le nœud plutôt que l’arête, et reprendre extrait_nœuds_des_rues

À FAIRE (un jour)

 - Liste de toutes les villes de France ? Pour l’instant dans normalisation.py il y a une variable globale avec la liste des (noms, code)

 - ergonomie :
     - case pour les villes avec menu déroulant
        -> mettre dans la base de Django
	-> Classe Ville_django avec les mêmes méthodes que Ville. Càd code, nom_complet et nom_norm


- Accélérer l'apprentissage. Sauvegarder les trajets calculé par Dijkstra ?

- Gestion des transitions entre deux rues.


