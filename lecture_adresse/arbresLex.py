# -*- coding:utf-8 -*-

### Implantation des arbres lexicographiques ###


class ArbreLex():
    """
    Attributs:
        term (bool), indique si la racine est terminale
        fils (str -> ArbreLex), dictionnaire lettre -> fils
    """
    
    def __init__(self):
        """ Renvoie un arbre vide"""
        self.fils = {}
        self.term = False
            

    def insère(self, mot):
        """
        Entrée : mot (str)
        Effet : insère mot dans l’arbre.
        """

        if mot == "": self.term = True
        else:
            if mot[0] in self.fils:
                self.fils[mot[0]].insère(mot[1:])
            else:
                self.fils[mot[0]] = ArbreLex()
                self.fils[mot[0]].insère(mot[1:])

    @classmethod
    def of_iterable(cls, l):
        """ Crée l’arbre contenant les mots de l."""
        res = cls()
        for mot in l:
            res.insère(mot)
        return res

    
    def __contains__(self, mot):
        if mot=="":
            return self.term
        else:
            return mot[0] in self.fils and  mot[1:] in self.fils[mot[0]]


    def contientPresque(self, mot, dmax):
        """
        Entrées : mot (str)
                  dmax (int), distance max (de Levenstein) à laquelle chercher.
        Sortie : indique si l’arbre contient un élément à distance dmax ou moins de mot.
        """

        if dmax == 0:
            return mot in self
        else:
            if len(mot)==0:
                #Seule possibilité : ajouter des lettres
                for lettre, f in self.fils.items():
                    if f.contientPresque(mot, dmax-1):
                        return True
                    
            else:
                # Premier essai : la bonne première lettre
                if mot[0] in self.fils:
                    if self.fils[mot[0]].contientPresque(mot[1:], dmax):
                        return True

                # Deuxième essai : supprimant une lettre
                if self.contientPresque(mot[1:], dmax-1) :
                    return True

                # Troisième essai : en changeant une lettre ou en ajoutant une
                for lettre, f in self.fils.items():
                    if lettre!=mot[0] and f.contientPresque(mot[1:], dmax-1) or f.contientPresque(mot, dmax-1):
                        return True

                return False


            
    def mots_les_plus_proches(self, mot, d_actuelle=0, d_max = float("inf")):
        """ Renvoie le couple (liste des mots à distance minimale de mot, la distance minimale elle-même).
        Renvoie [] si aucun mot à distance <= dmax.
        """

        def rassemble_possibs(p1, p2):
            """ p1 et p2 sont des couples (liste d’éléments de l’arbre, distance à mot)"""
            l1, d1 = p1
            l2, d2 = p2
            if d1==d2:
                return (l1+l2, d1)
            elif d1<d2:
                return p1
            else:
                return p2

        def prefixed(lettre, possib):
            """ possib est un couple (mots, distance).
            Renvoie le couple obtenu en mettant lettre devant chacun des mots.
            """
            mots, d = possib
            return ([lettre+m for m in mots], d)
        
        
        if d_max == d_actuelle:
            # Seule possibilité : le mot lui-même
            if mot in self: return [mot], d_actuelle
            else: return [], float("inf")
            
        else:
            res = [], float("inf")
            if len(mot)==0:
                if self.term:
                    return ([""], d_actuelle)
                else:
                    #Seule possibilité : ajouter des lettres
                    for lettre, f in self.fils.items():
                        res = rassemble_possibs(
                            res,
                            prefixed(lettre, f.mots_les_plus_proches(mot[1:], d_actuelle=d_actuelle+1, d_max=d_max))
                        )
                    return res
                    
            else:
                # Premier essai : la bonne première lettre
                if mot[0] in self.fils:
                    res = rassemble_possibs(
                        res,
                        prefixed(mot[0], self.fils[mot[0]].mots_les_plus_proches(mot[1:], d_actuelle=d_actuelle, d_max=d_max))
                    )

                # Deuxième essai : supprimant une lettre
                res = rassemble_possibs(res,  self.mots_les_plus_proches(mot[1:], d_actuelle=d_actuelle+1, d_max=d_max))

                # Troisième essai : en changeant une lettre ou en ajoutant une
                for lettre, f in self.fils.items():
                    res = rassemble_possibs(
                        res,
                        prefixed(lettre, f.mots_les_plus_proches(mot, d_actuelle=d_actuelle+1, d_max=d_max))
                        )
                    if lettre != mot[0]:
                        res = rassemble_possibs(
                            res,
                            prefixed(lettre, f.mots_les_plus_proches(mot[1:], d_actuelle=d_actuelle+1, d_max=d_max))
                        )
                                            
                return res


        
#test = ArbreLex.of_iterable(["bal", "blaa", "blu"])
