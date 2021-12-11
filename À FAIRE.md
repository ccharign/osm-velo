
À FAIRE :

réécrire folium...

Afficher les étapes sur la carte

Gélocalisation : y-a-t-il une fonction idoine dans folium ?

Si un sommet change lors d’une màj de g, que se passe-t-il dans le cache ? -> recréer (à partir de la liste des chemins) ou supprimer le cache lors d’une màj ?

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

