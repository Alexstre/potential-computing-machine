# Utilisé pour créer une classe énumérable (voir Quadrant)
from enum import IntEnum

# Utilisé pour les tests seulement
import random
from time import process_time


###############################################################################
# QuadTree implementation along with test application (battleship-like game)
# Alex Marcotte
###############################################################################


class Point():

    """Représente un point dans la grille de jeu"""

    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def position(self):
        return (self.x, self.y)

    def __str__(self):
        return str(self.x) + ' ' + str(self.y)

    def __eq__(self, autre):
        return self.x == autre.x and self.y == autre.y

    def __ne__(self, autre):
        return not (self == autre)


class Rectangle():

    """Représente un rectangle formé par deux points"""

    def __init__(self, bas_gauche, haut_droit):
        if not isinstance(bas_gauche, Point) or not isinstance(haut_droit, Point):
            raise ValueError("Le rectangle doit être formé de deux points (Point) ou tuple")

        self.x1 = bas_gauche.x
        self.x2 = haut_droit.x
        self.y1 = bas_gauche.y
        self.y2 = haut_droit.y

    def __str__(self):
        return "<Rectangle: (%s, %s) - (%s, %s)>" % (self.x1, self.y1, self.x2, self.y2)

    def __eq__(self, autre):
        return (self.x1 == autre.x1) and (self.x2 == autre.x2) and (self.y1 == autre.y1) and (self.y2 == autre.y2)

    @staticmethod
    def overlap(r1, r2):

        """Analyse l'intersection entre deux Rectangles et retourne un nouveau rectangle
        si l'intersection n'est pas vide, None sinon.
        """

        x1 = max(r1.x1, r2.x1)
        y1 = max(r1.y1, r2.y1)
        x2 = min(r1.x2, r2.x2)
        y2 = min(r1.y2, r2.y2)

        if x1 > x2 or y1 > y2:
            return None
        else:
            return Rectangle(Point(x1, y1), Point(x2, y2))

    def origine():

        """Retourne un rectangle couvrant complètement la zone de jeu initiale"""

        return Rectangle(Point(0, 0), Point(10315, 10315))


class Node():

    """Représente une feuille dans le Quadtree."""

    def __init__(self, point):
        if not isinstance(point, Point):
            raise ValueError("Point doit être une instance de la classe Point")
        else:
            self.point = point

    def __str__(self):
        return '[' + str(self.point) + ']'


class Quadrant(IntEnum):

    """Enumérateur pour les quadrants. Permet d'itérer sur le plan plus facilement"""

    # NO  |  NE
    # ----|-----
    # SO  |  SE

    NO = 0
    NE = 1
    SE = 2
    SO = 3


class QuadTree():

    """Représente le QuadTree"""

    def __init__(self, rectangle=Rectangle.origine()):
        """Construction du QuadTree. rectangle doit être une instance de la classe Rectangle"""

        # Initialisation du QuadTree, vide au début
        self._quadrants = [None, None, None, None]
        self._rectangle = rectangle

    def insertion(self, point):
        """Insertion d'un bateau dans le QuadTree à la position définie par le point"""

        if not isinstance(point, Point):
            raise ValueError("Point doit être une instance de la classe Point")

        # On cherche où placer le point en utilisant ses coordonnées
        #  _______ _______ D
        # |       |       |
        # |  NO   |  NE   |
        # |-------|-------|C
        # |  SO   |  SE   |
        # |_______|_______|
        # A       B
        #
        # Les points A et D forment le rectangle pour le QuadTree actual (self._rectangle)
        # A = (self._rectangle.x1, self._rectangle.y1) D = (self._rectangle.x2,
        # self._rectangle.y2)

        # On calcul les position en x pour B et y pour C, on les utilisera pour déterminer dans
        # quel quadrant placer le point
        demi_x = (self._rectangle.x2 + self._rectangle.x1) / 2
        demi_y = (self._rectangle.y2 + self._rectangle.y1) / 2

        if self._rectangle.x1 <= point.x < demi_x:  # On sera dans SO ou NO
            if self._rectangle.y1 <= point.y < demi_y:
                self._insertionRecursive(point, Quadrant.SO)
            else:
                self._insertionRecursive(point, Quadrant.NO)
        else:  # On sera dans NE ou SE
            if self._rectangle.y1 <= point.y < demi_y:
                self._insertionRecursive(point, Quadrant.SE)
            else:
                self._insertionRecursive(point, Quadrant.NE)

    def _insertionRecursive(self, point, quadrant):
        """Méthode pour l'insertion d'un bateau dans le quadrant spécifié.
        Cette méthode est récursive avec la méthode insertion() plus haut"""

        # Il n'y a rien dans ce quadrant, on créer un nouveau Node
        if self._quadrants[quadrant] is None:
            self._quadrants[quadrant] = Node(point)

        # On remplace le bateau en place par un Node
        elif not isinstance(self._quadrants[quadrant], QuadTree):
            # On garde le node présentement en place
            en_place = self._quadrants[quadrant]
            nouvelle_sous_region = self.sous_region(quadrant)
            self._quadrants[quadrant] = QuadTree(rectangle=nouvelle_sous_region)

            # On a remplacé le point par un nouveau QuadTree, on y ajoute maintenant l'ancient
            # point et le nouveau qu'on voulait ajouter initialement
            self._quadrants[quadrant].insertion(point)
            self._quadrants[quadrant].insertion(en_place.point)

        else: # On ajoute le bateau directement
            self._quadrants[quadrant].insertion(point)

    def detruire(self, rectangle):
        """Détruit tous les bateaux se trouvant à l'intérieur de la région
        déterminée par le rectangle (voir classe Rectangle)"""

        if self.est_vide():
            return True

        for quad in Quadrant:
            if self._quadrants[quad] is not None:
                if isinstance(self._quadrants[quad], QuadTree): # On descend dans un arbre
                    region = Rectangle.overlap(self._quadrants[quad]._rectangle, rectangle)

                    if region is not None: # La bombe intersecte avec une région du plan
                        self._quadrants[quad].detruire(region)
                        # Si la bombe a détruit tous les bateaux, on détruit le sous-arbre
                        if self._quadrants[quad].est_vide():
                            self._quadrants[quad] = None
                else: # On se trouve dans un node
                    if Rectangle.overlap(self.sous_region(quad), rectangle) is not None:
                        self._quadrants[quad] = None

    def est_vide(self):
        """Retourne True is le QuadTree est vide (ie. tout ses quadrants sont None),
        False sinon"""

        for quad in Quadrant:
            if self._quadrants[quad] is not None:
                return False
        return True

    def sous_region(self, quadrant):
        """Retourne le rectangle qui forme le quadrant d'une région d'un noeud"""

        # Points importants
        #  _______f_______g
        # |       |       |
        # |  NO   |  NE   |
        # c-------d-------e
        # |  SO   |  SE   |
        # a_______b_______|
        #
        # a et g sont les points du rectangle qui contient la région.
        # Les autres sont calculé ci-dessous

        a = Point(self._rectangle.x1, self._rectangle.y1)
        b = Point((self._rectangle.x1 + self._rectangle.x2) / 2, self._rectangle.y1)
        c = Point(self._rectangle.x1, (self._rectangle.y1 + self._rectangle.y2) / 2)
        d = Point((self._rectangle.x1 + self._rectangle.x2) / 2, (self._rectangle.y1 + self._rectangle.y2) / 2)
        e = Point(self._rectangle.x2, (self._rectangle.y1 + self._rectangle.y2) / 2)
        f = Point((self._rectangle.x1 + self._rectangle.x2) / 2, self._rectangle.y2)
        g = Point(self._rectangle.x2, self._rectangle.y2)

        # Puis on retourne un rectangle qui correspond au quadrant désiré en utilisant les 
        # points plus haut comme bornes. Rectangle(<Point Inférieur Gauche>, <Point Supérieur Droit>)
        if quadrant is Quadrant.NE:
            return Rectangle(d, g)
        elif quadrant is Quadrant.NO:
            return Rectangle(c, f)
        elif quadrant is Quadrant.SO:
            return Rectangle(a, d)
        elif quadrant is Quadrant.SE:
            return Rectangle(b, e)

    def __str__(self):
        """Override pour pouvoir utiliser print() directement sur un arbre"""

        pile = []
        self._ajoutPile(0, pile)

        return '\n'.join(str(niveau) for niveau in pile) + '\n'

    def _ajoutPile(self, niveau, pile):
        """Ajoute chaque niveau du QuadTree à la pile."""

        if niveau == len(pile):
            pile.append('')

        # Chaque noeud est représenté par un string <a b c d> où chacunes des coordonnées est
        # 1 si le pointeur a un enfant (un autre Node ou QuadTree), 0 sinon (None)
        # Par l'énoncé du devoir: <NO, NE, SE, SO> (l'ordre est établie dans la classe Quadrant)
        pile[niveau] += '<' + ' '.join(str(int(self._quadrants[quad] is not None)) for quad in Quadrant) + '>'

        for quad in Quadrant:  # On utilise le fait que Quadrant soit itérable
            if self._quadrants[quad] is not None:
                if isinstance(self._quadrants[quad], Node):
                    # On ajoute le node directement (casté en string, voir classe Node)
                    pile[niveau] += str(self._quadrants[quad])
                elif isinstance(self._quadrants[quad], QuadTree):
                    # On doit récursivement ajouter les enfants du Tree
                    self._quadrants[quad]._ajoutPile(niveau + 1, pile)

###########################################################################################################
# Fin de la classe QuadTree
###########################################################################################################

def jouer(bateaux, bombes):
    
    """Méthode pour lancer la partie. Les paramètres sont les noms de fichiers"""

    quadtree = QuadTree()
    fichiers = {'bateaux': bateaux, 'bombes': bombes}

    print("Début de la partie!")

    # On ajoute les bateaux à partir du fichier de coordonnées
    print("\nAvant les bombes")
    try:
        with open(fichiers['bateaux']) as fichier:
            for coord in fichier:
                x, y = coord.split()
                quadtree.insertion(Point(x, y))
    except FileNotFoundError:
        print("Impossible de lire le fichier", fichiers['bateaux'])
        return
    else:
        print(quadtree)

    # On détruit les bateaux avec les bombes
    print("\nAprès les bombes")
    try:
        with open(fichiers['bombes']) as fichier:
            for coord in fichier:
                x1, y1, x2, y2 = coord.split()
                quadtree.detruire(Rectangle(Point(x1, y1), Point(x2, y2)))
    except FileNotFoundError:
        print("Impossible de lire le fichier", fichiers['bombes'])
        return
    else:
        print(quadtree)

    print("\nFin de la partie!")

class BattleshipTest():

    """Permet de tester le QuadTree"""

    def __init__(self, nb_bateaux = 10000, nb_bombes = 50):
        self._quadtree = QuadTree()
        self._nb_bateaux = nb_bateaux
        self._nb_bombes = nb_bombes

    def go(self):

        """Lance le test avec les paramètres spécifiés lors de l'initialisation de la classe"""

        print("Début du test. On génère", self._nb_bateaux, "bateaux...")
        bateaux = self._generePositionsBateaux(self._nb_bateaux)
        bombes = self._generePositionBombres(self._nb_bombes)

        temp_debut = process_time()
        for bateau in bateaux:
            self._quadtree.insertion(Point(bateau[0], bateau[1]))
        print("Temps requis pour ajouter", self._nb_bateaux, "bateaux:", '%.5f' % round(process_time() - temp_debut, 5), "secondes")

        temp_debut = process_time()
        for bombe in bombes:
            self._quadtree.detruire(Rectangle(Point(bombe[0], bombe[1]), Point(bombe[2], bombe[3])))
        print("Temps requis pour lancer", self._nb_bombes, "bombes sur", self._nb_bateaux, ":", '%.5f' % round(process_time() - temp_debut, 5), "secondes")

        print("Fin du test.")

    def _generePositionsBateaux(self, nombre):

        """Génère <nombre> bateaux au hasard"""

        p = range(0, 10315)
        bateaux = set()

        while len(bateaux) < nombre:
            bateaux.add((random.choice(p), random.choice(p)))
        
        return bateaux

    def _generePositionBombres(self, nombre):

        """Génère <nombre> bombes au hasard"""

        p = range(0, 10315)
        bombes = set()

        while len(bombes) < nombre:
            # On s'assure que x1 <= x2, y1 <= y2
            (a, b, c, d) = (random.choice(p), random.choice(p), random.choice(p), random.choice(p))
            bombes.add((min(a, b), max(a, b), min(c, d), max(c, d)))

        return bombes


if __name__ == '__main__':
    jouer('positionDesBateaux', 'bombes')

    # Pour tester seulement. Génère aléatoirement les bateaux et les bombes
    #test = BattleshipTest(1000000, 100)
    #test.go()