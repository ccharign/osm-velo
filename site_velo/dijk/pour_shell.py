# -*- coding:utf-8 -*-
from importlib import reload
import dijk.models as mo
import dijk.views as v
import progs_python.initialisation.vers_django as vd
import progs_python.initialisation.initialisation as ini
import ini.charge_fichier_cycla_défaut as charge_cycla_defaut
from progs_python.utils import lecture_tous_les_chemins, réinit_cycla
from django.db import close_old_connections
