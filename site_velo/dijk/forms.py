# -*- coding:utf-8 -*-
from django import forms
import dijk.models as mo


class FormCycla(forms.Form):
    """
    Pour demander la zone de laquelle afficher la carte de cycla.
    """
    zone = forms.ModelChoiceField(queryset=mo.Zone.objects.all(), label='Zone')
    force_calcul = forms.BooleanField(label="Forcer le calcul", required=False)
    
class ChoixZone(forms.Form):
    """
    Choix de zone. A priori pour la page d'index.
    """
    zone = forms.ModelChoiceField(queryset=mo.Zone.objects.all(), label='Zone')
