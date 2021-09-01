from django.urls import path

from . import views

urlpatterns = [
    path("itinéraire/<str:départ>/<str:arrivée>/", views.itinéraire),
    path('', views.index, name='index'), # Création d'en url pointant vers la vue « index »
]
