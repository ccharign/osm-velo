
À FAIRE :


page de rapport de bug
   - Table rapport de bug

Ménage:
   - static dans dijk

Amenities : les charger dans la base, et les mettre dans la complétion auto.
    Chercher dedans dans chemins.Étape
    Traduire en français
    Faire un passer par un(e) ...


Type polyline de Django pour le champ nœuds des rues



BUG de la place Clémenceau. Il semble qu’il y manque des arêtes.



Recherche dans l’arbre lex dans la complétion automatique, avec tolérance à faute de frappe.
    -> Enregistrer l’arbre de chaque zone
    -> Mettre le nom de rue aux feuilles


Rechargement et entraînement pratique...
   - apprentissage auto. Tous les chemin qui ont un score de dernière modif>0
   - réinit base ?


Mettre une case à cocher pour enregistrer dans le cache ?
   -> utils.itinéraire renvoie les corrections qui ont été faites
   -> voir le template rés_itinéraire_base
Voire récup dans osm tous les noms de lieux ?



Tester vue générique pour chemins


corriger géom ville
Graphe des villes
Recherche dans ville voisine


modif du graphe:
      - place_en_clique


NOTES :


Vaut-il mieux mettre les nœuds d'une rue en texte dans la base, ou avec une relation many to many ? Benchmarking ?



À FAIRE (un jour)

Afficher les étapes sur la carte


Si un sommet change lors d’une màj de g, que se passe-t-il dans le cache ? -> recréer (à partir de la liste des chemins) ou supprimer le cache lors d’une màj ?

Mettre une case pour donner un bonus/malus à une rue dans la recherche ?

Y-a-t-il des risques de conflit si deux utilisateurs en même temps ?

- Accélérer l'apprentissage ?
  	    Éliminer au fur et à mesure les zones où plus de changement
  	    Sauvegarder les trajets calculé par Dijkstra ?


- Gestion des transitions entre deux rues.
  	  - rajouter un coeff de transition entre deux arêtes

