#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

##This file is part of PySylic
#############################################################################
#############################################################################
##                                                                         ##
##                                 globdef                                 ##
##                                                                         ##
#############################################################################
#############################################################################

## Copyright (C) 2009-2012 C�drick FAURY

#    pySyLiC is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

#    pySyLiC is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with PySylic; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


DEBUG = True
PSYCO = False
MARKER = 'None'

import os.path, sys, wx
import getpass


#
# Les deux lignes suivantes permettent de lancer le script pysylic.py depuis n'importe
# quel répertoire (par exemple : C:\python .\0.3\pysylic.py) sans que l'utilisation de chemins
# relatifs ne soit perturbée
#
PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
PATH = os.path.split(PATH)[0]
os.chdir(PATH)
sys.path.append(PATH)
print("Dossier de l'application :",PATH)

# 
# On récupère là le dossier "Application data" 
# où devra être enregistré le fichier .cfg de pysylic
#
if sys.platform == 'win32':
    import winreg
#    import win32api
#    import win32con
    # On récupère le répertoire d'installation de pySyLiC
    try:
        regkey = winreg.OpenKey( winreg.HKEY_CLASSES_ROOT, 'pySyLiC.system\DefaultIcon', 0, winreg.KEY_READ )
        (value,keytype) = winreg.QueryValueEx(regkey , '') 
        INSTALL_PATH = os.path.dirname(value)
        print ("INSTALL_PATH", INSTALL_PATH)
    except:
        INSTALL_PATH = None # Pas installé sur cet ordi
        
    PORTABLE = INSTALL_PATH != os.path.join(PATH , "images")

    
    if not PORTABLE: # Ce n'est pas une version portable qui tourne
        
        # On lit la clef de registre indiquant le type d'installation
        try: # Machine 32 bits
            regkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\pySyLiC', 0, winreg.KEY_READ )
        except: # Machine 64 bits
            regkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Wow6432Node\\pySyLiC', 0, winreg.KEY_READ )

        try:
            (value,keytype) = winreg.QueryValueEx(regkey, 'DataFolder' ) 
            APP_DATA_PATH = value
            
        except:
            import wx
            dlg = wx.MessageDialog(None, u"L'installation de pySyLiC est incorrecte !\nVeuillez désinstaller pySequence puis le réinstaller." ,
                                   u"Installation incorrecte",
                                   wx.OK | wx.ICON_WARNING
                                   #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                   )
            dlg.ShowModal()
            dlg.Destroy()
            APP_DATA_PATH = PATH
        
        if not os.path.exists(APP_DATA_PATH):
            os.mkdir(APP_DATA_PATH)
            
            
    else: # C'est une version portable qui tourne
        APP_DATA_PATH = PATH
        print ("Version portable !!")
        
else:
    APP_DATA_PATH = PATH
    PORTABLE = False #Notion inutile sur Linux ?

#if PORTABLE:
##    os.putenv('MPLCONFIGDIR', os.path.join(PATH, 'bin', 'mpl-data'))
#    os.environ['MPLCONFIGDIR'] = os.path.join(PATH, 'bin', 'mpl-data')

# Ce qui suit renvoie : C:\Users\Cedrick\AppData\Roaming\pySyLiC
# Permission refusée d'y enregistrer les options !!
#APP_DATA_PATH = os.path.join(os.environ[u'appdata'], u'pySyLiC')

print ("Dossier des donnees", APP_DATA_PATH)

ERROR_FILE = os.path.join(APP_DATA_PATH, 'pySyLiC.exe' + '.log')
print ("Fichier erreur :",ERROR_FILE)
#
# Pour internationalisation ...
#
import gettext, locale
LOCALEDIR = os.path.join(PATH, "locale")
print ("Dossier Locale", LOCALEDIR)
LANG = "" # "" = langage par defaut
#print "  defaultlocale", locale.getdefaultlocale()[0][:2]

# On déclare le nom _
#__builtins__._ = lambda text:text
gettext.install("pysylic", LOCALEDIR)

def SetInternationalization():
    if LANG == "fr" or LANG == "":
        gettext.install("pysylic", LOCALEDIR)
        return
    
    print ("SetInternationalization", locale.normalize(LANG))
    try:
        cur_lang = gettext.translation("pysylic", localedir = LOCALEDIR, \
                                       languages=[LANG])
        #locale.setlocale(locale.LC_ALL,'en')
        cur_lang.install()
    except IOError:
        # Si la langue locale n'est pas support�e, on d�finit tout de m�me _()
        # On le fait dans les __builtins__ pour que la fonction soit d�finie dans
        # les modules import�s (c'est ce que fait gettext.install()).
        print ("Langue", LANG, "non suport�e !")

listLang = {"fr" : u"Fran�ais",
            "en" : u"English",
            ""   : _(u"d�faut")}

def GetInstalledLang():
#    from babel import Locale, core
    langs = ["fr", ""]

#    # Tester la localisation en vigueur sur ce syst�me
#    lc, encoding = locale.getdefaultlocale()
#    if (lc):
#            # Si une localisation par d�faut existe,
#            # la mettre en premier dans la liste
#            langs += [lc]
#    print langs
#    # Maintenant, r�cup�rer la liste des langages du syst�me
#    language = os.environ.get('LANGUAGE', None)
#    if (language):
#            # language contient une cha�ne du style en_CA:en_US:en_GB:en
#            # pour un system Linux, sur Windows c'est vide. Il faut d�couper
#            # la cha�ne en une liste
#            langs += language.split(":")
    
    langs += os.listdir(LOCALEDIR)
    
    # Ajouter les traductions install�es
    noms = {}
    for n in langs:
        l = n.split("_")[0]
        try:
            lang_name = listLang[l]
            noms[l] = lang_name.capitalize()
        except:
            pass
#    langs += os.listdir(LOCALEDIR)

    
    return noms

INSTALLED_LANG = GetInstalledLang()
print ("Langues installees :",INSTALLED_LANG)

#gettext.install("messages", globdef.LOCALEDIR)
#
#if locale.getdefaultlocale()[0] != "fr_FR" or globdef.LANG == "en_EN":
#    lang=gettext.translation("messages", globdef.LOCALEDIR, languages=['en_EN'])
#    
#    lang.install()
#for n in os.listdir(LOCALEDIR):
#    print locale.normalize(n)


# Test des langues install�es
#languages = []
#for envar in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
#    print envar,
#    val = os.environ.get(envar)
#    print val
#    if val:
#        languages = val.split(':')
#        break
#print languages

#print locale.getlocale()


#DOSSIER_IMAGES = os.path.join(PATH,"Images")


#
# Type de police
#
FONT_TYPE = 2


##########################################################################################################
#
# Constantes utilis�es en OPTIONS de pySyLiC
#
##########################################################################################################

SELECTEUR_FT = None
DOSSIER_EXEMPLES = None
VAR_COMPLEXE = None
MAJ_AUTO = None
NB_PERIODES_REP_TEMPO = None
TEMPS_REPONSE = None
DEPHASAGE = None

NBR_PTS_REPONSE = None
ANTIALIASED = None
TRACER_FLECHE = None

PRINT_PROPORTION = None
IMPRIMER_NOM = None
TEXTE_NOM = None
POSITION_NOM = None
IMPRIMER_TITRE = None
TEXTE_TITRE = None
POSITION_TITRE = None
MAX_PRINTER_DPI = None
COUL_MARGE_GAIN_OK = None
COUL_MARGE_GAIN_NO = None
FORM_GRILLE = None
FORM_ISOGAIN = None
FORM_ISOPHASE = None
COUL_PT_CRITIQUE = None
COUL_LAMBDA = None
COUL_POLES = None
COUL_CONSIGNE = None
COUL_REPONSE = None
COUL_REPONSENC = None

    
def DefOptionsDefaut():
    global  NBR_PTS_REPONSE, ANTIALIASED, TRACER_FLECHE, DEPHASAGE, \
            COUL_MARGE_GAIN_OK, COUL_MARGE_GAIN_NO, FORM_GRILLE, FORM_ISOGAIN, FORM_ISOPHASE, \
            COUL_LAMBDA, COUL_POLES, COUL_PT_CRITIQUE, COUL_CONSIGNE, COUL_REPONSE, COUL_REPONSENC, \
            SELECTEUR_FT, DOSSIER_EXEMPLES, VAR_COMPLEXE, MAJ_AUTO, NB_PERIODES_REP_TEMPO, TEMPS_REPONSE, \
            PRINT_PROPORTION, IMPRIMER_NOM, POSITION_NOM, TEXTE_NOM, \
            IMPRIMER_TITRE, POSITION_TITRE, TEXTE_TITRE, MAX_PRINTER_DPI
    
    from LineFormat import LineFormat
    
    #
    # Options générales
    #
    SELECTEUR_FT = 0
    DOSSIER_EXEMPLES = os.path.join(PATH,"Exemples")
    VAR_COMPLEXE = u"p"   # Nom de la variable complexe
    MAJ_AUTO = True  # Mise à jour automatique des tracés
    NB_PERIODES_REP_TEMPO = 5   # Nombre de périodes affichées en cas d'echelle automatique
    TEMPS_REPONSE = 0.05    # % du temps de réponse calculé
    DEPHASAGE = False
    
    #
    # Options d'affichage
    #
    NBR_PTS_REPONSE = 200 # C'est un minimum pour avoir des valeurs correctes !
    ANTIALIASED = True
    TRACER_FLECHE = True
    
    #
    # Options d'impression
    #
    PRINT_PROPORTION = True
    IMPRIMER_NOM = True
    TEXTE_NOM = ""    # NOM par défaut (NOM)
    POSITION_NOM = "BL" # "TL","BL","TC","BC","TR","BR"
    IMPRIMER_TITRE = True
    TEXTE_TITRE = ""  # TITRE par défaut (Fichier Courant)
    POSITION_TITRE = "BR" # "TL","BL","TC","BC","TR","BR" 
    MAX_PRINTER_DPI = 200 # Définition largement suffisante (600 est le maximum sous peine de provoquer une erreur sous MPL)

    #
    # Options de couleurs
    #
    COUL_MARGE_GAIN_OK = wx.Colour(10,200,10).GetAsString(wx.C2S_HTML_SYNTAX)
    COUL_MARGE_GAIN_NO = wx.Colour(200,10,10).GetAsString(wx.C2S_HTML_SYNTAX)
    FORM_GRILLE = LineFormat(coul = wx.Colour(130,130,130), styl = ":", epais = 0.5)
    FORM_ISOGAIN = LineFormat(coul = wx.Colour(230,230,250), epais = 0.5)
    FORM_ISOPHASE = LineFormat(coul = wx.Colour(200,250,200), epais = 0.5)
    COUL_PT_CRITIQUE = wx.Colour(250,100,100).GetAsString(wx.C2S_HTML_SYNTAX)
    COUL_LAMBDA = wx.Colour(10,180,10).GetAsString(wx.C2S_HTML_SYNTAX)
    COUL_POLES = wx.Colour(10,10,150).GetAsString(wx.C2S_HTML_SYNTAX)
    COUL_CONSIGNE = wx.Colour(10,10,150).GetAsString(wx.C2S_HTML_SYNTAX)
    COUL_REPONSE = wx.Colour(250,10,10).GetAsString(wx.C2S_HTML_SYNTAX)
    COUL_REPONSENC = wx.Colour(10,240,10).GetAsString(wx.C2S_HTML_SYNTAX)

DefOptionsDefaut() 



##########################################################################################################
#
# Autres constantes
#
##########################################################################################################

# Symbole Multiplier
#SYMBOLE_MULT = r"\times "
SYMBOLE_MULT = r"\cdot "

#
USE_MATPLOTLIB = True

# Type de selecteur de FT
TYPE_SELECTEUR_TF = 0 # 0 : FT Factorisée   1 : FT Développée                                # en option

# Nombre de chiffres significtatifs
NB_CHIFFRES = 4

# Nombre de sous FT
#NBR_MAXI_SSFT = 30

# Précision calcul de racines
PRECISION = 0.001
EPSILON = 1E-6

# Densité d'isos (nbr d'iso visibles)
DENSITE_ISOS = 20

# Methode de décomposition en sous-fonction
DECOMP_2ND_ORDRE = True

#
# Style des fen�tres "enfant"
#
STYLE_FENETRE = wx.SYSTEM_MENU | wx.MAXIMIZE_BOX | wx.CAPTION | wx.MINIMIZE_BOX | \
                wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.FRAME_FLOAT_ON_PARENT
#
# Curseurs
#
CURSEUR_DEFAUT = wx.CURSOR_ARROW
CURSEUR_INTERDIT = wx.CURSOR_NO_ENTRY
CURSEUR_MAIN = wx.CURSOR_HAND
CURSEUR_ORIENTATION = wx.CURSOR_SIZEWE
CURSEUR_CROIX = wx.CURSOR_CROSS
CURSEUR_ISO = wx.CURSOR_POINT_RIGHT#wx.CURSOR_BLANK
CURSEUR_CURSEUR = wx.CURSOR_SIZEWE
CURSEUR_ECHELLE = wx.CURSOR_SIZING 
#CURSEUR_CADENA = os.path.join(DOSSIER_IMAGES,'Punaise.png')
CURSEUR_HAUT_BAS = wx.CURSOR_SIZENS 


#
# Couleurs
#
COUL_MARGE_GAIN = wx.Colour(100,100,200).GetAsString(wx.C2S_HTML_SYNTAX)
COUL_MARGE_PHAS = wx.Colour(50,200,200).GetAsString(wx.C2S_HTML_SYNTAX)
#COUL_MARGE_GAIN_OK = wx.Colour(10,200,10).GetAsString(wx.C2S_HTML_SYNTAX)
#COUL_MARGE_GAIN_NO = wx.Colour(200,10,10).GetAsString(wx.C2S_HTML_SYNTAX)
COUL_MARGE_PHAS_OK = COUL_MARGE_GAIN_OK
COUL_MARGE_PHAS_NO = COUL_MARGE_GAIN_NO

COUL_LIGNE_RAPPEL = wx.Colour(50,50,80)

#COUL_GRILLE = wx.Colour(130,130,130).GetAsString(wx.C2S_HTML_SYNTAX)

#COUL_ISOGAIN = wx.Colour(230,230,250).GetAsString(wx.C2S_HTML_SYNTAX)
#COUL_ISOPHASE = wx.Colour(200,250,200).GetAsString(wx.C2S_HTML_SYNTAX)
COUL_LABEL_ISOGAIN = wx.Colour(130,130,250).GetAsString(wx.C2S_HTML_SYNTAX)
COUL_LABEL_ISOPHASE = wx.Colour(130,250,130).GetAsString(wx.C2S_HTML_SYNTAX)

#COUL_PT_CRITIQUE = wx.Colour(250,100,100).GetAsString(wx.C2S_HTML_SYNTAX)

COUL_ZOOM = wx.Colour(200,50,50)
COUL_TEXT_CURSEUR = wx.Colour(200,50,50).GetAsString(wx.C2S_HTML_SYNTAX)
COUL_BLANC = wx.Colour(255,255,255).GetAsString(wx.C2S_HTML_SYNTAX)


#COUL_LAMBDA = wx.Colour(10,180,10).GetAsString(wx.C2S_HTML_SYNTAX)

#COUL_CONSIGNE = wx.Colour(10,10,150).GetAsString(wx.C2S_HTML_SYNTAX)
#COUL_REPONSEWX = wx.Colour(250,10,10)
#COUL_REPONSE = COUL_REPONSEWX.GetAsString(wx.C2S_HTML_SYNTAX)
#COUL_REPONSENCWX = wx.Colour(10,240,10)
#COUL_REPONSENC = COUL_REPONSENCWX.GetAsString(wx.C2S_HTML_SYNTAX)
COUL_LIGNE_TR = wx.Colour(10,100,10).GetAsString(wx.C2S_HTML_SYNTAX)

#COUL_POLES = wx.Colour(10,10,150).GetAsString(wx.C2S_HTML_SYNTAX)

#
# Epaisseurs des traits
#
EP_MARGES = 3

#
# Options de tracé par défaut (modifiable par les outils)
#
TRACER_GRILLE = True
TRACER_ISO = True
TRACER_DIAG_REEL = True
TRACER_DIAG_ASYMP = False

DIVISION_ORDRE2_MINI = 6 # espace mini (en pixel) entre 2 graduations


#
# Options pour l'optimisation de la rapidité d'affichage
#
TRACER_SPLINE = True # pas utile avec mpl
NBR_PTS_ISOGAIN = 150
NBR_PTS_COURBES = 80
INTERPOLER = False # Ca ne marche pas terrible en cas de variation rapide ...
DELTA_PHI_MAXI = 10  # Variation maximum de Phi entre 2 points (On ressert les points avec lisserReponse())
USE_AGG = True # Ca marche pas en WX :(
#ANTIALIASED = True     # en option
USE_THREAD = False # Ca ne marche pas avec les threads ...

#
# Options pour le calcul de la réponse temporelle
#
#NBR_PTS_REPONSE = 200 # C'est un minimum pour avoir des valeurs correctes !                 # en option
INTERPOLATION = 0 # linear (1) or zero-order hold (0)
LSIM_SOLVER = 1 # normal (0) ODE solver (1) ... résultats parfois incohérents avec "0" !
LSIM_TOLERANCE = 1.49012e-8
#NB_PERIODES_REP_TEMPO = 3   # Nombre de périodes affichées en cas d'echelle automatique  # en option
#TEMPS_REPONSE = 0.05    # en option

#
# Options pour l'export
#
DPI_EXPORT = 300
ZORDER_MAXI = 1000

#
# Nombre maxi de sous fonctions (d'ou une limite du nombre de plots mpl)
#
NBR_MAXI_PLOT = 10
MAXI_NBR_MAXI_PLOT = 20

#
#
#
NBR_MAXI_MULTIPLE_VAR = 8


#
# Options pour l'impression
#
#PRINT_PROPORTION = True
PRINT_PAPIER_DEFAUT = wx.PAPER_A4
PRINT_MODE_DEFAUT = wx.PRINT_MODE_PRINTER

#IMPRIMER_NOM = True
#TEXTE_NOM = ""    # NOM par défaut (NOM)
#POSITION_NOM = "BL" # "TL","BL","TC","BC","TR","BR"                
NOM = getpass.getuser()

#IMPRIMER_TITRE = True
#TEXTE_TITRE = ""  # TITRE par défaut (Fichier Courant)
#POSITION_TITRE = "BR" # "TL","BL","TC","BC","TR","BR" 

#MAX_PRINTER_DPI = 200 # Définition largement suffisante (600 est le maximum sous peine de provoquer une erreur sous MPL)



#
# Tailles des polices
#
FONT_SIZE_EXPR = 18
FONT_SIZE_GRAD = 9
FONT_SIZE_LABEL_AXE = 10
FONT_SIZE_LABEL = 11
FONT_SIZE_CURSEUR = 9

FONT_SIZE_FT_SELECT = 120
FONT_SIZE_FT_DECOMP = 140
FONT_SIZE_SSFT = 100
FONT_SIZE_VARIABLE = 100
FONT_SIZE_FT_HD = 300

#
# Propriétés de la flèche sur diagrammes de Black et Nyquist
#
FLECHE_TANA = 0.4
FLECHE_LONG = 10
#TRACER_FLECHE = True # en options
