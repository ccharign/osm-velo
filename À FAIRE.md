
À FAIRE :


Afficher les étapes sur la carte

Si un sommet change lors d’une màj de g, que se passe-t-il dans le cache ? -> recréer (à partir da la liste des chemins) ou supprimer le cache lors d’une màj ?

Il existe des rues qui figurent dans rue_num_coord, donc qui étaient dans le .osm, mais qui ne sont pas dans nœuds_rue. Ce dernier est créé par nœuds_des_rues.py. Par exemple place reine marguerite, dont le nœud du graphe est 339262446.

Mettre une case pour donner un bonus/malus à une rue dans la recherche ?

Y-a-t-il des risques de conflit si deux utilisateurs en même temps ?


À FAIRE (un jour)

 - Liste de toutes les villes de France ? Pour l’instant dans normalisation.py il y a une variable globale avec la liste des (noms, code)

 - ergonomie :
     - case pour les villes avec menu déroulant
        -> mettre dans la base de Django
	-> Classe Ville_django avec les mêmes méthodes que Ville. Càd code, nom_complet et nom_norm


- Accélérer l'apprentissage.
  	    Éliminer au fur et à mesure les zones où plus de changement
  	    Sauvegarder les trajets calculé par Dijkstra ?


- Gestion des transitions entre deux rues.
  	  - rajouter un coeff de transition entre deux arêtes

