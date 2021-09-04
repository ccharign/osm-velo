from django.urls import path

from . import views

urlpatterns = [
    path("itinéraireDirect/<str:départ>/<str:arrivée>/<int:pourcentage_détour>", views.vue_itinéraire_direct),
    path("itinéraire", views.vue_itinéraire, name="itinéraire"),
    path("contribution", views.contribution, name="contribution"),
    path('', views.index, name='index'), # Création d'une url pointant vers la vue « index »
]
