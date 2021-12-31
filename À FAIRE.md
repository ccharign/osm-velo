
À FAIRE :


initialisation de la cycla:
       - piste cyclables
       - zone 30

modif du graphe:
      - ronds points
      - place_en_clique
      - private

màj / recalcul de la cycla
    - mettre les chemins dans la base
    - fonction de relecture des chemins. Renvoyer les chemins qui modifient le plus d'arêtes par km.
    - formulaire avec sélection d'un chemin et affichage de l'iti correspondant.
    - avertissement si sens interdit ?

Mettre les nœuds aux feuilles des arbres lex de rue ?

Création des arbres lex depuis la bdd

script de mise à jour/agrandissement du graphe :
       - rajouter un modèle Zone. Associer chaque Sommet à une (ou plusieurs?) zone.
       - interface ? Faire une page cachée exprès. Avec mot de passe ? Mettre le import initialisation dans la vue.
       - Charger le graphe via osmnx
       - Charger les nœuds dans la base.
       - Charger les arêtes
       - récup les rues et leur nœuds
       - et pour les villes ? Recherche overpass des villes d'une zone ?


Charger la zone au moyen d'un get.   



NOTES :

recup_nœuds.tous_les_nœuds : Pour l'instant la recherche Nominatim n'est utilisée que pour récupérer le nom officiel osm de la rue, avant de lancer g.nœuds_of_rue.
 En revanche, recup_donnees.nœuds_of_rue prend tous les ways renvoyés par Nominatim.

 Réfléchir à la situation d'une recherche ne correspondant pas à un way ?
 Pour l'instant :
      - recup des coords
      - récup de l'adresse via data.gouv
      - nœud__sur_rue_le_plus_proche


Vaut-il mieux mettre les nœuds d'une rue en texte dans la base, ou avec une relation many to many ? Benchmarking ?




À FAIRE (un jour)

Géolocalisation : y-a-t-il une fonction idoine dans folium ?

Afficher les étapes sur la carte

export du gpx

À terme faire un abre lex des cles du cache ?
Si un sommet change lors d’une màj de g, que se passe-t-il dans le cache ? -> recréer (à partir de la liste des chemins) ou supprimer le cache lors d’une màj ?

Mettre une case pour donner un bonus/malus à une rue dans la recherche ?

Y-a-t-il des risques de conflit si deux utilisateurs en même temps ?


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

