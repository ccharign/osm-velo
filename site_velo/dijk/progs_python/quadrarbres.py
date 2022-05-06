# -*- coding:utf-8 -*-
"""
Arbres quaternaires. Le type correspond plutôt aux R-arbres, mais la fonction of_list crée a priori quatre fils par nœud.

But : enregistrer l’id osm et les coords de chaque sommet
"""
from petites_fonctions import distance_euc, R_TERRE
from math import cos, pi

def union_bb(lbb):
    """
    Entrée : une liste de bounding box
    Sortie : la plus petite bounding box contenant celles de lbb
    """

    return (
        min(bb[0] for bb in lbb),
        min(bb[1] for bb in lbb),
        max(bb[2] for bb in lbb),
        max(bb[3] for bb in lbb)
    )

class Quadrarbre():
    """
    Attributs :
        fils (liste de Quadarbres)
        bb (float, float, float, float) : bounding box minimale contenant les nœuds de l’arbre. (s,o,n,e)
             Pour une feuille, ouest==est et nord==sud.
        id_osm (int) : id d’un nœud osm. Seulement pour les feuilles.
    """


    def __init__(self):
        """
        Renvoie un arbre vide
        """
        self.fils=None
        self.bb = None
        self.id_osm=None
    
    
    @classmethod
    def feuille(cls, coords, id_osm:int):
        lon, lat = coords
        res = cls()
        res.bb = lat, lon, lat, lon
        res.id_osm = id_osm
        return res
        
    
    @classmethod
    def of_list(cls, l):
        """
        Entrée : l (((float×float)×int) list), list de (coords, id_osm)
        Sortie (Quadrarbre) : arbre quad contenant les nœuds osm de l
        """
        assert isinstance(l, list), f"Pas une liste : {l}"
        assert l, "Reçu une liste vide"

        if len(l)==1:
            return cls.feuille(*l[0])
        
        else:
            l.sort(key=lambda x:x[0][0]) # tri selon la longitude.
            ouest = l[:len(l)//2]
            est = l[len(l)//2:]

            ouest.sort(key=lambda x :x[0][1]) # tri selon la latitude
            so = ouest[:len(ouest)//2]
            no = ouest[len(ouest)//2:]

            est.sort(key=lambda x :x[0][1]) # tri selon la latitude
            se = est[:len(est)//2]
            ne = est[len(est)//2:]

            res = cls()
            res.fils = [cls.of_list(sl) for sl in (so,no,ne,se) if sl]
            res.bb = union_bb([f.bb for f in res.fils])
            return res

        
    def __len__(self):
        if self.fils is None:
            return 1
        else:
            return sum(len(f) for f in self.fils)
        
    
    def majorant_de_d_min(self, coords:(float,float)):
        """
        Sortie : en O(1) un majorant de la plus petite distance entre coords et un élément de l’arbre. (Pour le branch and bound de la recherche de nœud le plus proche.)
        """
        # Il existe au moins un élément sur chaque bord de la bounding box
        dno = distance_euc(coords, (self.ouest, self.nord))
        dso = distance_euc(coords, (self.ouest, self.sud))
        dne = distance_euc(coords, (self.est, self.nord))
        dse = distance_euc(coords, (self.est, self.sud))
        
        # Il existe un élément sur le bord ouest
        d1 = max(dno, dso)
        # bord est
        d2 = max(dne, dse)
        # sud
        d3 = max(dse, dso)
        # nord
        d4 = max(dno, dne)
        
        return min(d1, d2, d3, d4)
    
    
    def minorant_de_d_min(self, coords:(float,float)):
        """
        Sortie : en O(1), un minorant de la distance min entre coords et un nœud de l’arbre.
        C’est la distance entre coords et la bounding box de self.
        """
        s,o,n,e = self.bb
        lon, lat = coords #lon : ouest-est
        res_carré=0
        le_cos = cos(lat*pi/180)
        
        if lon < o:
            res_carré+=(o-lon)**2 * le_cos
        elif lon >e :
            res_carré+=(lon-e)**2 * le_cos
        if lat<s:
            res_carré+=(s-lat)**2
        elif lat >n:
            res_carré+=(lat-n)**2
        
        return res_carré**.5  * R_TERRE * pi/180
        
        
    def nœud_le_plus_proche(self, coords:(float,float)):
        """
        Sortie ((float×float)×int×float) : (coords, id_osm, distance) du nœud le plus proche de coords.
        """
        
        if not self.fils:
            return self.bb[1:3], self.id_osm, distance_euc(coords, self.bb[1:3]) # o, n ce qui fait lon, lat
        
        else:
            d_min = float("inf")
            res = None
            for m, fils in sorted( ((f.minorant_de_d_min(coords), f) for f in self.fils) ): # Om commence par le fils qui a le plus probablement le nœud le plus proche.
                if m < d_min:
                    c, id_osm, dist = fils.nœud_le_plus_proche(coords)
                    if dist<d_min:
                        d_min, res = dist, (c, id_osm)
            return res+(d_min,)
                    
