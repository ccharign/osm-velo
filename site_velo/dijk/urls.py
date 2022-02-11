from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views

urlpatterns = [
    #path("itinéraireDirect/<str:départ>/<str:arrivée>/<int:pourcentage_détour>", views.vue_itinéraire_direct),
    path("resultat", views.vue_itinéraire, name="résultat"),
    
    path("contribution", views.contribution, name="contribution"),
    path("mode_demploi", views.mode_demploi, name="mode d’emploi"),
    path("limitations", views.limitations, name="limitations"), 
    path("visu_nv_chemin", views.visualisation_nv_chemin, name="visu nv chemin"),
    path("confirme_nv_chemin", views.confirme_nv_chemin, name = "confirme nv chemin"),

    path("pourcentages/", views.recherche_pourcentages, name = "recherche pourcentages"),
    path("pourcentages_res/<str:ville>", views.vue_pourcentages_piétons_pistes_cyclables, name = "stats"),
    path("pourcentages_res/", views.vue_pourcentages_piétons_pistes_cyclables, name = "stats"),
    
    path("cycla/<str:zone_t>", views.carte_cycla, name="carte cycla"),
    path("cycla/", views.cycla_choix, name = "cycla"),    

    path("telechargement/", views.téléchargement, name = "téléchargement"),
    
    path('<str:zone_t>/', views.recherche, name='recherche'),
    path('', views.index, name='index'),



] + staticfiles_urlpatterns()
