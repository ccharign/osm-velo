from django.urls import path

from . import views

urlpatterns = [
    path("itinéraireDirect/<str:départ>/<str:arrivée>/<int:pourcentage_détour>", views.vue_itinéraire_direct),
    path("itinéraire", views.vue_itinéraire, name="itinéraire"),
    path("contribution", views.contribution, name="contribution"),
    path("vérif_nv_chemin", views.vérif_nv_chemin, name="vérif nouveau chemin"),
    path("visu_nv_chemin", views.visualisation_nv_chemin, name="visu nv chemin"),
    path('', views.index, name='index'), # Création d'une url pointant vers la vue « index »
]
