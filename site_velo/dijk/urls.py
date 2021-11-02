from django.urls import path

from . import views

urlpatterns = [
    #path("itinéraireDirect/<str:départ>/<str:arrivée>/<int:pourcentage_détour>", views.vue_itinéraire_direct),
    path("resultat", views.vue_itinéraire, name="résultat"),
    
    path("contribution", views.contribution, name="contribution"), 
    path("limitations", views.limitations, name="limitations"), 
    path("visu_nv_chemin", views.visualisation_nv_chemin, name="visu nv chemin"), # Affichage du folium.
    path("confirme_nv_chemin", views.confirme_nv_chemin, name = "confirme nv chemin"),

    path("cycla", views.carte_cycla, name="carte cycla"),
    
    path('', views.index, name='index'), # Création d'une url pointant vers la vue « index », ou se trouve le formulaire d’itinéraire simple.
]
