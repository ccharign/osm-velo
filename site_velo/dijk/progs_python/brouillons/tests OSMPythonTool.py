# -*- coding:utf-8 -*-


from OSMPythonTools.nominatim import Nominatim # Recherche inverse
nominatim = Nominatim()
#Pau = nominatim.query('Pau, France')
coord_maison = 43.319346, -0.337842
maison = nominatim.query(*coord_maison, reverse=True, zoom=18)#le niveau de zoom 18 est celui du bâtiment
