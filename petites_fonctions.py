# -*- coding:utf-8 -*-

import math

R_TERRE = 6378137  # en mètres


def distance_euc(c1, c2):
    """ Formule simplifiée pour petites distances."""
    long1, lat1 = c1
    long2, lat2 = c2
    dx = R_TERRE * (long2-long1) * math.pi / 180
    dy = R_TERRE * (lat2-lat1) * math.pi / 180
    return (dx**2+dy**2)**.5
