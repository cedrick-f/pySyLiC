#!/usr/bin/env python
# -*- coding: utf-8 -*-

##This file is part of PySylic
#############################################################################
#############################################################################
##                                                                         ##
##                                  graph                                  ##
##                                                                         ##
#############################################################################
#############################################################################

## Copyright (C) 2009-2012 Cédrick FAURY

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
#    along with pySyLiC; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import Images
import wx
try:
    from agw import aui
except ImportError:
    import wx.lib.agw.aui as aui

import globdef
import os

import matplotlib
matplotlib.interactive(True)
import matplotlib.transforms as mtransforms
from matplotlib.ticker import MultipleLocator, IndexLocator, MaxNLocator
from matplotlib.ticker import Formatter

#if globdef.PORTABLE:
#    matplotlib.set_configdir(os.path.join(globdef.INSTALL_PATH, 'bin', 'mpl-data'))
#print matplotlib.get_configdir()

from numpy import errstate, array, arange, meshgrid, pi, \
                  absolute, cos, sin, log10, arctan2, exp, real, imag, vstack
#from scipy.sparse import vstack
import scipy.interpolate

from CedWidgets import chronometrer, strScCx, strSc, mathText, setToggled, \
                        mathtext_to_wxbitmap, CopierBitmap, CopierTeX, \
                        _min, _max, _m

# On zappe les warnings
import warnings
warnings.filterwarnings('ignore', '.*converting a masked element to nan.', UserWarning)

import exportExcel
import tempfile

# Type de police
#
# Type de police
#
from matplotlib.mathtext import MathTextParser
mathtext_parser = MathTextParser("path")
def AppliquerTypeFont():
#    print "AppliquerTypeFont", globdef.FONT_TYPE
    #global mathtext_parser
    #mathtext_parser.__init__("path")
    if globdef.FONT_TYPE == 0:
        matplotlib.rcParams['mathtext.default'] = 'regular'
        matplotlib.rcParams['mathtext.fontset'] = 'cm'
    elif globdef.FONT_TYPE == 1:
        matplotlib.rcParams['mathtext.default'] = 'it'
        matplotlib.rcParams['mathtext.fontset'] = 'cm'
    elif globdef.FONT_TYPE == 2:
        matplotlib.rcParams['mathtext.default'] = 'it'
        matplotlib.rcParams['mathtext.fontset'] = 'stix'
        
    elif globdef.FONT_TYPE == 3: #mpl 1.0.0 : mauvais affichage des mathtext en svg
        matplotlib.rcParams['mathtext.fontset'] = 'stixsans'
        matplotlib.rcParams['mathtext.fallback_to_cm'] = True
        
AppliquerTypeFont()


if globdef.USE_AGG:
    matplotlib.use('WXagg')
    from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
#    from matplotlib.backends.backend_wx import PrintoutWx
    from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
else:
    from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
    matplotlib.use('WX')
    from matplotlib.backends.backend_wx import FigureCanvasWx# as FigureCanvas2

from matplotlib.figure import Figure
from matplotlib.pyplot import setp, getp, gca#, gcf, getp
from matplotlib.collections import LineCollection
#from matplotlib.text import Text
from matplotlib.axis import XTick, YTick
#from matplotlib.patches import Rectangle
#from matplotlib.transforms import identity_transform

#matplotlib.rcParams['text.usetex']=True


#import scipy
from scipy import *
#from scipy import log10, arctan2, array, cos, sin, exp, imag, real, sign
import calcul
#import numpy
#import Principal
import fonctions

from LineFormat import LineFormatSelector, LineFormat, SelecteurFormatLigne, EVT_FORMAT_MODIFIED
if globdef.USE_THREAD:
    import threading

# Pour optimisation
#import time




lineStyleMpl = ['-', '--', '-.', ':']

##########################################################################################################
#
# Zone graphique complete
#
##########################################################################################################
class ZoneGraph(aui.AuiNotebook):
    def __init__(self, parent, app, fctTracer, 
                 outilsBode = None, outilsBlack = None, outilsNyquist = None):#,
#                 nomBode = "", nomBlack = "", nomNyquist = ""):
        aui.AuiNotebook.__init__(self, parent,
                                 agwStyle = aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT | aui.AUI_NB_TAB_MOVE | aui.AUI_NB_SCROLL_BUTTONS
                                 )
#                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
#                             )
        self.parent = parent
        self.app = app
        self.tracer = fctTracer
        self.fenetreDiagramme = [None] * 3
        
        self.nomsPages = [_("Diagrammes de Bode"), 
                          _("Diagramme de Black"),
                          _("Diagramme de Nyquist")]
        
        if outilsBode == None:
            outilsBode = ["BReel", "BAsymp", "", "BGrille", "BExpre", "", "BZoomA", "BZoomP", "BDepla", "BEchel", "", "BCurse", "", "BExpor", 'BParam', "", "BFenet"]
        
        self.ZoneBode = ZoneGraphOutils(self, app, 0, outilsBode)
        self.ZoneBode.Add(ZoneGraphBode(self.ZoneBode, self.ZoneBode))
        self.AddPage(self.ZoneBode, self.nomsPages[0])
        
        
        
        if outilsBlack == None:
            outilsBlack = ["BGrille", "BIsoGP", "BExpre", "", "BZoomA", "BZoomP", "BDepla", "BEchel", "", "BCurse", "", "BExpor", 'BParam', "", "BFenet"]
        self.ZoneBlack = ZoneGraphOutils(self, app, 1, outilsBlack)
        self.ZoneBlack.Add(ZoneGraphBlack(self.ZoneBlack, self.ZoneBlack))#, app.isoPhase, app.isoGain))
        self.AddPage(self.ZoneBlack, self.nomsPages[1])
        
        if outilsNyquist == None:
            outilsNyquist = ["BGrille", "BExpre", 'BPoles', "", "BZoomA", "BZoomP", "BDepla", "BEchel", "", "BCurse", "", "BExpor", 'BParam', "", "BFenet"]
        self.ZoneNyquist = ZoneGraphOutils(self, app, 2, outilsNyquist)
        self.ZoneNyquist.Add(ZoneGraphNyquist(self.ZoneNyquist, self.ZoneNyquist))
        self.AddPage(self.ZoneNyquist, self.nomsPages[2])
        
        
#        self.ZoneBode = ZoneGraphBode(self)
#        self.AddPage(self.ZoneBode, "Bode")
#        
#        self.ZoneBlack = ZoneGraphBlack(self)
#        self.AddPage(self.ZoneBlack, "Black")
        
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
#        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
        self.Bind(aui.EVT_AUINOTEBOOK_DRAG_DONE, self.OnDragDone)
        self.Bind(aui.EVT_AUINOTEBOOK_ALLOW_DND, self.OnAllowNotebookDnD)
        self.Bind(aui.EVT_AUINOTEBOOK_BEGIN_DRAG, self.OnBeginDrag)
        self.Bind(aui.EVT_AUINOTEBOOK_END_DRAG , self.OnEndDrag)
#        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
        
        
#    def OnPageChanging(self, event):
#        
#        new = event.GetSelection()
#        print "OnPageChanging", new
#        event.Skip()
        
    def OnAllowNotebookDnD(self, event):
        # for the purpose of this test application, explicitly
        # allow all notebook drag and drop events
#        print "OnAllowNotebookDnD"
        event.Allow()
        
        
  
    def OnBeginDrag(self, event):
        for z in self.getZonesGraph():
            if not z.IsFrozen():
                z.Freeze()
        
    def OnEndDrag(self, event):
        for z in self.getZonesGraph():
            if z.IsFrozen():
                z.Thaw()
        event.Skip()
        
    def OnDragDone(self, event):
#        print "OnDragDone"
#        for z in self.getZonesGraph():
#            z.Thaw()
        wx.CallAfter(self.calculerEtRedessinerRanges)
        
        
#        wx.CallAfter(self.tracer)
#        self.tracer()
#        event.Skip()
        
    def getPlan(self):
        return self.GetSelection()
    
    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        
#        print "PageChanged", new, old, sel
        
        # Si pas de réel changement de page
#        if old == -1:
#            return 
        
        event.Skip()
        
        #
        # On ferme toutes les fenêtres de réglage des paramètres
        #
        for z in self.getZonesGraph():
            z.zoneParam.Close()
    
        wx.CallAfter(self.calculerEtRedessinerRanges)
            
#        wx.CallAfter()
#        wx.CallAfter(self.tracer)
        

    ######################################################################################################
    def mettreAJourEtRedessiner(self, *args, **kwargs): #lstFTNum, lstCoul, winMarges, HC = None):
        self.ZoneBode.activerCurseur(False)
        self.ZoneBlack.activerCurseur(False)
        self.ZoneNyquist.activerCurseur(False)
        
        for z in self.getZonesGraph():
#            print "Mise à jour", z.nom
            z.mettreAJour(*args, **kwargs)
            
        self.calculerEtRedessinerRanges()


    ######################################################################################################
    def calculerEtRedessinerRanges(self):
        self.Freeze()
        for z in self.getZonesGraphVisibles():
            z.calculerEtRedessinerRanges()
        self.Thaw()
        
    ######################################################################################################
    def modifierAntialiased(self):
        for z in self.getZonesGraph():
            z.modifierAntialiased()

    ######################################################################################################
    def setCouleurs(self):
        for z in self.getZonesGraph():
            z.setCouleurs()
            
    ######################################################################################################
    def setCurseur(self, etat):
        for z in self.getZonesGraph():
            z.setCurseur(etat)
    
    ######################################################################################################
    def SetAffComplet(self):
        return
        
    ######################################################################################################
    def PrintPreview(self, event = None):
        self.getZonesGraphVisibles()[0].PrintPreview(event)
        
        
    ######################################################################################################
    def getBitmap(self):
        return self.getZonesGraphVisibles()[0].canvas.bitmap
        
        
    ######################################################################################################
    def setEstFTBF(self, etat):
        for z in self.getZonesGraph():
            z.setEstFTBF(etat)
        
        
    ######################################################################################################
    def getZonesGraph(self):
        """ Renvoie toutes les zones graphiques (Bode, Black et Nyquist)
        """
#        print "getZonesGraph"
        
        return [self.ZoneBode.child[0], 
                self.ZoneBlack.child[0],
                self.ZoneNyquist.child[0]]
        
    ######################################################################################################
    def getZonesGraphOutils(self):
        """ Renvoie toutes les zones outils (Bode, Black et Nyquist)
        """
        return [self.ZoneBode, 
                self.ZoneBlack,
                self.ZoneNyquist]
        
    ######################################################################################################
    def getZonesGraphVisibles(self):
        """ Renvoie les zones graphiques visibles
        """
#        print "getZonesGraphVisibles",
        
        lst = self.getZonesGraphVisiblesNoteBook()
        
        for f in self.fenetreDiagramme:
            if f != None and f.IsShownOnScreen():
                lst.append(f.GetChildren()[0].child[0])

#        print lst
        return lst
        
    ######################################################################################################
    def getZonesGraphVisiblesNoteBook(self):
        lst = []
        for n in range(self.GetPageCount()):
            p = self.GetPage(n)
            if p.IsShownOnScreen():
                lst.append(p.child[0])
        return lst
        
    #########################################################################################################
    def OnSystemeChange(self):
        a = self.app.nbGauche.getPage() == 2 or self.app.getTypeSysteme() == 0
        self.ZoneNyquist.gererActivationPoles(a)
        
        
    ###############################################################################################
    def fenetre(self, zoneGraphOutils, etat):
        """ Fait apparaite <zoneGraph> dans une fenêtre séparée
        """
#        print "Fenetre", zoneGraphOutils.num, etat,
        
        def fenetreSeparee():
#            print "Séparation"
            numPage = self.GetPageIndex(zoneGraphOutils)
            nom = self.GetPageText(numPage)
            
            frame = wx.Frame(self.app, -1, nom, size = (550, 450), 
                             style = globdef.STYLE_FENETRE)
            frame.SetIcon(self.app.GetIcon())
            zoneGraphOutils.Reparent(frame)
            self.fenetreDiagramme[zoneGraphOutils.num] = frame
            frame.Show()
            self.RemovePage(numPage)
            frame.Bind(wx.EVT_CLOSE, fenetrePrincipale)
            
            
        def fenetrePrincipale(event = None):
#            print "Retour"
            self.Freeze()
            frame = self.fenetreDiagramme[zoneGraphOutils.num]
            zoneGraphOutils.Reparent(self)
            self.InsertPage(0, zoneGraphOutils, frame.GetLabel())
            self.fenetreDiagramme[zoneGraphOutils.num].Destroy()
            self.fenetreDiagramme[zoneGraphOutils.num] = None
            self.SetSelection(0)
            zoneGraphOutils.tbar.ToggleTool(50, False)
            zoneGraphOutils.child[0].TracerTout()
            self.Thaw()
        
        if etat:   
            fenetreSeparee()
        else:    
            fenetrePrincipale()
            
#        self.SetLabelFenetre()
            
    def reinitialiserBoutons(self):
        for z in self.getZonesGraphOutils():
            z.reinitialiserBoutons()
        
            
##########################################################################################################
#
# Panel contenant la(les) ZoneGraphBase et des outils de visualisation
#
##########################################################################################################
class ZoneGraphOutils(wx.Panel):
    def __init__(self, parent, app, num, outils, tempo = False):
        wx.Panel.__init__(self, parent, -1)
        self.SetAutoLayout(True)
        
        self.AffComplet = True
        
#        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.tempo = tempo
        self.app = app
        self.num = num
        self.child = []
        self.outils = outils
        self.parent = parent
        
        self.zoomPlus = False
        self.deplacer = False
        self.zoomAuto= True
        self.curseur = False
        self.echelle = False
        
#        self.boutonTR = None
        
        self.mgr = aui.AuiManager()
        self.mgr.SetManagedWindow(self)
        
        self.tbar = aui.AuiToolBar(self)#, style = aui.AUI_TB_OVERFLOW)
        self.setOutils()
        
        self.mgr.AddPane(self.tbar, 
                         aui.AuiPaneInfo().
#                         Name("tb1").
#                         ToolbarPane().
                         Top().Layer(1).
                         Floatable(False).
                         DockFixed().
                         Gripper(False).
                         Movable(False).
                         Maximize().
#                         Caption("Big Toolbar").
                         CaptionVisible(False).
                         PaneBorder(False).
                         CloseButton(False).
                         Show())
        
        self.CreateMenu()
        self.mgr.Update()
        
    ######################################################################################################
    def CreateMenu(self):
        self.menu = wx.Menu()
        id = 101
        for i in [_("Imprimer"), _("Aperç"), _("Mise en page"), _("Options")]:
            self.menu.Append(id, i)
            self.Bind(wx.EVT_MENU, self.OnMenu, id = id)
            id += 1
            
#        self.sizer.Add(self.tbar, flag = wx.EXPAND)
        
#        self.SetSizer(self.sizer)
        
        
    ######################################################################################################
    def SetAffComplet(self, etat = None):
        ancienEtat = self.AffComplet
        if etat == None:
            self.AffComplet = not self.AffComplet
        else:
            self.AffComplet = etat
            
        if self.AffComplet == ancienEtat:
            return ancienEtat
        
#        print "SetAffComplet", self.child[0].nom, self.AffComplet
        if self.AffComplet:
            self.tbar.Show(True)
            self.mgr.ShowPane(self.tbar, True)
        else:
            self.tbar.Show(False)
            self.mgr.ShowPane(self.tbar, False)
        
        self.mgr.Repaint()
        self.Layout()
        self.parent.SetAffComplet()
        return ancienEtat
        
        
    ######################################################################################################
    def Add(self, win):
        self.child.append(win)
#        self.sizer.Add(win, 1, flag = wx.EXPAND)
        
        self.mgr.AddPane(win, 
                         aui.AuiPaneInfo().
                         CenterPane().
                         PaneBorder(False).
                         Floatable(False).
                         CloseButton(False))
        
        self.mgr.Update()
#        win.FitInside()
#        self.sizer.FitInside(self)
        
#        self.SetSizer(self.sizer)
#        self.Fit()

#    def tracer(self):
#        self.parent.tracer()
        
    ######################################################################################################
    def mettreAJourEtRedessiner(self, *args, **kwargs):
        for win in self.child:
            win.mettreAJourEtRedessiner(*args, **kwargs)
     
        
    ######################################################################################################
    def OnMenu(self, event):
        id = event.GetId()
        if id == 101:
            self.Parent.OnDoPrint(self.getChild(), titre = self.app.getNomFichierCourantCourt())
        elif id == 102:
            self.Parent.OnPrintPreview(self.getChild(), titre = self.app.getNomFichierCourantCourt())
        elif id == 103:
            self.Parent.OnPageSetup()
        elif id == 104:
            self.app.OnOptionsClick(page = 2)
            
    ######################################################################################################
    def setOutils(self):
        """ Crée et renvoie une ToolBar contenant des <outils>
        """
        
        tbar = self.tbar
        outils = self.outils
        tbar.ClearTools()
        tbar.SetOverflowVisible(True)
        tbar.SetToolBitmapSize((32,32))
        
        def AddSimpleTool(id, label, bitmap, short_help_string):
            tbar.AddSimpleTool(id, label, 
                               bitmap, 
                               short_help_string = short_help_string)
            tbar.Bind(wx.EVT_TOOL, self.OnClick, id=id)  
            self.Bind(wx.EVT_MENU, self.OnOverflowClick, id = id)
             
        def AddToggleTool(id, label, bitmap, short_help_string, toggle):
            bouton = tbar.AddSimpleTool(id, label, 
                                        bitmap,
                                        short_help_string = short_help_string,
                                        kind = wx.ITEM_CHECK)
            tbar.Bind(wx.EVT_TOOL, self.OnClick, id = id)  
            self.Bind(wx.EVT_MENU, self.OnOverflowClick, id = id)
            tbar.ToggleTool(id, toggle)
            return bouton
                
#        tsize = (32,32)
        
        lstFichImg = {'BReel'   :Images.Bouton_Reel,
                      'BAsymp'  :Images.Bouton_Asymp,
                      'BGrille' :Images.Bouton_Grille,
#                      'BMarges' :'Bouton Marges.png',
                      'BIsoGP'  :Images.Bouton_Iso, 
                      'BZoomP'  :Images.Bouton_ZoomPlus,
                      'BZoomA'  :Images.Bouton_ZoomAuto,
                      'BCurse'  :Images.Bouton_Curseur,
                      'BDepla'  :Images.Bouton_Deplacer,
                      'BExpor'  :Images.Bouton_Exporter,
                      'BExpre'  :Images.Bouton_Expression,
                      'BParam'  :Images.Bouton_Param,
                      'BEchel'  :Images.Bouton_Echelle,
                      'BImpri'  :Images.Bouton_Imprimer,
                      'BTRepo'  :Images.Bouton_TempsReponse,
                      'BPoles'  :Images.Bouton_Poles,
                      'BFenet'  :Images.Bouton_Fenetre
                      }
        self.lstFichImg = lstFichImg
        
        lstLabel   = {'BReel'   :"",
                      'BAsymp'  :"",
                      'BGrille' :"",
#                      'BMarges' :,
                      'BIsoGP'  :"", 
                      'BZoomP'  :_("Selectionner une zone à visualiser"),
                      'BZoomA'  :_("Adapter automatiquement la zone à visualiser"),
                      'BCurse'  :_("Activer le curseur sur les courbes"),
                      'BDepla'  :_("Déplacer la zone à visualiser"),
                      'BExpor'  :_("Exporter le Tracé"),
                      'BExpre'  :"",
                      'BParam'  :_("Ajuster les tailles des caractère"),
                      'BEchel'  :_("Modifier l'echelle"),
                      'BImpri'  :_("Imprimer le Tracé"),
                      'BTRepo'  :"",
                      'BPoles'  :"",
                      'BFenet'  :""
                      }
        self.lstLabel = lstLabel
        
        lstToolTip = {'BReel'   :"",
                      'BAsymp'  :"",
                      'BGrille' :"",
#                      'BMarges' :_(u'Tracer les marges de stabilité et afficher leurs valeurs'),
                      'BIsoGP'  :"", 
                      'BZoomP'  :_(u'Permet de sélectionner par un rectangle\nla zone à visualiser'),
                      'BZoomA'  :_(u'Determine automatiquement la zone à visualiser'),
                      'BCurse'  :_(u'Passer en mode "curseur" :\n'\
                                   u'  déplacer la souris latéralement pour faire varier'),
                      'BDepla'  :_("Permet de déplacer la zone à visualiser (pas de changement d'échelle)"),
                      'BExpor'  :_("Permet de sauvegarder la totalité du Tracé à l'écran\n(courbes, expressions, marges, ...)\n"\
                                   "sous divers formats de fichiers (png, pdf, svg, ...)"),
                      'BExpre'  :"",
                      'BParam'  :_("Permet d'ajuster les tailles polices de caractère pour ce Tracé"),
                      'BEchel'  :_("Permet de modifier l'echelle de représentation (étendue de la zone à visualiser)\n"
                                   u'Remarque :\n'\
                                   u'  Cette fonction est également accessible directement avec la roulette de la souris'),
                      'BImpri'  :_("Permet d'imprimer la totalité du Tracé à l'écran"),
                      'BTRepo'  :"",
                      'BPoles'  :"",
                      'BFenet'  :""
                      }
        if self.tempo:
            lstToolTip["BCurse"] += " "+_(u'le temps')
        else:
            lstToolTip["BCurse"] += " "+_("la pulsation")
        lstToolTip["BCurse"] += "\n"+_(u'  cliquer pour figer le curseur')
        self.lstToolTip = lstToolTip
        
        lstID =      {'BReel'   :10,
                      'BAsymp'  :11,
                      'BGrille' :12,
#                      'BMarges' :,
                      'BIsoGP'  :17, 
                      'BZoomP'  :20,
                      'BZoomA'  :21,
                      'BCurse'  :22,
                      'BDepla'  :23,
                      'BExpor'  :30,
                      'BExpre'  :31,
                      'BParam'  :40,
                      'BEchel'  :24,
                      'BImpri'  :25,
                      'BTRepo'  :32,
                      'BPoles'  :13,
                      'BFenet'  :50
                      }
        self.lstID = lstID
        
        lstToggle =  {'BReel'   :globdef.TRACER_DIAG_REEL,
                      'BAsymp'  :globdef.TRACER_DIAG_ASYMP,
                      'BGrille' :globdef.TRACER_GRILLE,
                      'BIsoGP'  :globdef.TRACER_ISO, 
                      'BZoomP'  :False,
                      'BZoomA'  :self.zoomAuto,
                      'BCurse'  :False,
                      'BDepla'  :False,
                      'BExpre'  :False,
                      'BEchel'  :False,
                      'BTRepo'  :False,
                      'BPoles'  :self.app.TracerPoles,
                      'BFenet'  :False
                      }
        
        self.labelF = {'BFenet'  :_("Ouvrir  dans une fenêtre séparée"),
                       'BReel'   :_("Tracer les diagrammes Réels"),
                       'BAsymp'  :_("Tracer les diagrammes Asymptotiques"),
                       'BGrille' :_(u'Afficher une grille'),
                       'BIsoGP'  :_(u'Afficher les isogains et les isophases'),
                       'BTRepo'  :_("Afficher Le temps de réponse"),
                       'BPoles'  :_("Afficher les Pôles/Zéros de la FTBF"),
                       'BExpre'  :_("Afficher les expressions des FT"),
                      }
        self.labelP = {'BFenet'  :_("Remettre dans la fenêtre principale"),
                       'BReel'   :_(u'Masquer les diagrammes Réels'),
                       'BAsymp'  :_("Masquer les diagrammes Asymptotiques"),
                       'BGrille' :_(u'Masquer la grille'),
                       'BIsoGP'  :_(u'Masquer les isogains et les isophases'),
                       'BTRepo'  :_("Masquer Le temps de réponse"),
                       'BPoles'  :_("Masquer les Pôles/Zéros de la FTBF"),
                       'BExpre'  :_("Masquer les expressions des FT"),
                      }
        self.tipF =   {'BFenet'  :_("Ouvrir le Tracé dans une fenêtre séparée"),
                       'BReel'   :_(u'Tracer les diagrammes de Bode réels'),
                       'BAsymp'  :_(u'Tracer les diagrammes de Bode asymptotiques'),
                       'BGrille' :_(u'Afficher une grille'),
                       'BIsoGP'  :_(u'Afficher les isogains et les isophases'),
                       'BTRepo'  :_("Afficher et donner la valeur du temps de réponse à %s %%") %(int(globdef.TEMPS_REPONSE*100),),
                       'BPoles'  :_("Afficher les Pôles/Zéros de la FTBF dans le plan complexe"),
                       'BExpre'  :_(u'Afficher les expressions des fonctions de transfert directement sur les courbes'),
                      }
        self.tipP =   {'BFenet'  :_("Remettre le Tracé dans la fenêtre principale"),
                       'BReel'   :_(u'Masquer les diagrammes de Bode réels'),
                       'BAsymp'  :_(u'Masquer les diagrammes de Bode asymptotiques'),
                       'BGrille' :_(u'Masquer la grille'),
                       'BIsoGP'  :_(u'Masquer les isogains et les isophases'),
                       'BTRepo'  :_("Masquer le temps de réponse à %s %%") %(int(globdef.TEMPS_REPONSE*100),),
                       'BPoles'  :_("Masquer les Pôles/Zéros de la FTBF dans le plan complexe"),
                       'BExpre'  :_(u'Masquer les expressions des fonctions de transfert'),
                      }
                
        lstImg = {}        
        for k, f in lstFichImg.items():
            lstImg[k] = f.GetBitmap()
        
        
        for o in outils:
            if o in ["BGrille", "BPoles", "BReel", "BAsymp", "BIsoGP", "BDepla", "BZoomP", "BZoomA",
                     "BExpre", "BTRepo", "BCurse", "BEchel", 'BFenet']:
#                if lstLabel[o] == "":
#                    label, toolTip = self.GetLabel(o)
#                else:
                label, toolTip = lstLabel[o], lstToolTip[o]
                AddToggleTool(lstID[o], label, lstImg[o], short_help_string = toolTip,
                              toggle = lstToggle[o])
                if lstLabel[o] == "":
                    self.SetLabel(o)

            elif o in ["BExpor", "BParam"]:
                AddSimpleTool(lstID[o], lstLabel[o], lstImg[o],
                              short_help_string = lstToolTip[o])

            elif o == "BImpri":
                AddSimpleTool(lstID[o], lstLabel[o], lstImg[o],
                              short_help_string = lstToolTip[o])
                tbar.SetToolDropDown(25, True)
                self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnMenuClick, id=25)

            elif o == "":
                tbar.AddSeparator()
                
        tbar.Realize()
        
    def SetLabel(self, code):
        if type(code) == str or type(code) == unicode:
            id = self.lstID[code]
        else:
            id = code
            code = self.GetCode(code)
        if self.tbar.GetToolToggled(self.lstID[code]):
            self.tbar.SetToolLabel(self.lstID[code], self.labelP[code])
            self.tbar.SetToolShortHelp(self.lstID[code], self.tipP[code])
        else:
            self.tbar.SetToolLabel(self.lstID[code], self.labelF[code])
            self.tbar.SetToolShortHelp(self.lstID[code], self.tipF[code])
        
    def GetCode(self, id):
        try:
            code = self.lstID.keys()[self.lstID.values().index(id)]
        except:
            code = None
        return code
        
    def GetLabel(self, code):
        return self.tbar.GetToolLabel(self.lstID[code]), self.tbar.GetToolShortHelp(self.lstID[code])
    
     
    def OnMenuClick(self, event):
        if event.IsDropDownClicked():
            self.PopupMenu(self.menu)
            
    def getChild(self):
        return self.child[0]

    def OnOverflowClick(self, event):
#        print "OnOverflowClick",
        id = event.GetId()
#        print id,
#        menuitem = self.tbar.FindTool(id)
        etat = not self.tbar.GetToolToggled(id)
#        print etat
        
        self.Click(id, etat, event = event)
        
#        print dir(event)
#        menuitem = event.GetMenuId()
#        print menuitem

        self.tbar.ToggleTool(id, etat)

#        event.Skip()
    
    def OnClick(self, event, num = None):
        id = event.GetId()
        etat = self.tbar.GetToolToggled(id)
#        print "OnClick", id, etat
        
        self.Click(id, etat, event = event, num = num)
        
        
    def activerZoomPlus(self, etat):
        if etat != self.zoomPlus:
            self.zoomPlus = not self.zoomPlus
            self.child[0].setZoomPlus(etat)
        if self.tbar.GetToolToggled(20) != etat:
            self.tbar.ToggleTool(20, etat)
        

    def activerDeplacer(self, etat):
        if etat != self.deplacer:
            self.deplacer = not self.deplacer
            self.child[0].setDeplacer(etat)
#            self.child[0].ntb.pan()
        if self.tbar.GetToolToggled(23) != etat:
            self.tbar.ToggleTool(23, etat)
        
        
        
    def activerEchelle(self, etat):
        if etat != self.echelle:
            self.echelle = not self.echelle
        if self.tbar.GetToolToggled(24) != etat:
            self.tbar.ToggleTool(24, etat)
        self.child[0].setEchelle(etat)    
        
            
    def activerCurseur(self, etat):
        if etat != self.curseur:
            self.curseur = not self.curseur
        self.tbar.ToggleTool(22, etat)
        self.child[0].setCurseur(etat)
        self.tbar.EnableTool(10, not etat)
        self.tbar.EnableTool(11, not etat)
        self.tbar.EnableTool(12, not etat)
        self.tbar.EnableTool(17, not etat)
        self.tbar.EnableTool(31, not etat)
        self.tbar.Refresh()
        
        
    def activerZoomAuto(self, etat):
        if etat != self.zoomAuto:
            self.zoomAuto = not self.zoomAuto
        self.tbar.ToggleTool(21, etat)
        self.child[0].setZoomAuto(etat)
#            self.child[0].calculerEtRedessiner()    
    
    def Click(self, id, etat = False, reel = True, event = None, num = None):
#        print "Click", id, etat
            
        #
        #
        #

        if id == 10:
            self.GererActivation()
            self.child[0].setTracerReel(self.tbar.GetToolToggled(id))
    
        elif id == 11:
            self.GererActivation()
            self.child[0].setTracerAsymp(self.tbar.GetToolToggled(id))
    
        elif id == 12:
            self.child[0].setTracerGrille(etat)
    
        elif id == 17:
            self.child[0].setTracerIsoGP(etat)
            
        elif id == 13:
            self.child[0].setTracerPoles(etat)
            self.child[0].calculerEtRedessiner()
           
        # 
        # Outils de visualisation
        #
        
        elif id == 20: # Zoom rectangle
            self.activerZoomAuto(False)
            self.activerCurseur(False)
            self.activerDeplacer(False)
            self.activerEchelle(False)
            self.activerZoomPlus(etat)
        
        elif id == 21: # Zoom Auto
            self.activerCurseur(False)
            self.activerDeplacer(False)
            self.activerZoomPlus(False)
            self.activerEchelle(False)
            self.activerZoomAuto(etat)
            if etat:
                self.child[0].calculerEtRedessiner()
        
        elif id == 22: # Curseur
#            self.activerZoomAuto(False)
            self.activerDeplacer(False)
            self.activerZoomPlus(False)
            self.activerEchelle(False)
            self.activerCurseur(etat)
    
        elif id == 23: # Déplacement
            self.activerZoomAuto(False)
            self.activerCurseur(False)
            self.activerZoomPlus(False)
            self.activerEchelle(False)
            self.activerDeplacer(etat)
            
        elif id == 24: # Echelle
            self.activerZoomAuto(False)
            self.activerCurseur(False)
            self.activerZoomPlus(False)
            self.activerDeplacer(False)
            self.activerEchelle(etat)
        
        elif id == 25: # Imprimer
            event.SetId(101)
            self.OnMenu(event)
            
        elif id == 30: # Export du Tracé
            self.child[0].exporter()
            
        elif id == 31: # Expression des FT
            self.child[0].setAffichExpress(etat)
            
        elif id == 32: # Temps de réponse
            self.child[0].setAffichTempsRep(etat)

        elif id == 40: # paramètres d'affichage
            self.child[0].zoneParam.RendreTotal()
            self.child[0].setAffichParam()
            
        elif id == 50: # Fenetre séparée
            self.parent.fenetre(self, etat)

        elif id == 100: # Menu contextuel : Format de ligne FT
            cb, form = self.app.lstFTTracees[num]
            evt = wx.CommandEvent(wx.EVT_BUTTON.typeId, form.btn.GetId())
            form.btn.GetEventHandler().ProcessEvent(evt)
            
        elif id == 102: # Menu contextuel : Format de ligne réponse
            keys = ["Cons", "Rep", "RepNc"]
            format = self.app.formats[keys[num]]
            lfs = LineFormatSelector(self.app, format)
            if lfs.ShowModal() == wx.ID_OK:
                self.child[0].TracerTout()
                self.parent.MiseAJourBmp()
            lfs.Destroy()
            
            
        elif id == 101: # Menu contextuel : Affichage FT
            cb, form = self.app.lstFTTracees[num]
            cb.SetValue(False)
            evt = wx.CommandEvent(wx.EVT_CHECKBOX.typeId, cb.GetId())
            cb.GetEventHandler().ProcessEvent(evt)
            
        elif id in [110, 111, 112, 113, 114, 115]: # Menu contextuel : Tailles de police
            self.child[0].zoneParam.RendrePartiel((id-110,))
            self.child[0].setAffichParam()
    
            
        elif id in [123, 124, 125, 126, 127]: # Menu contextuel : Couleurs
#            self.app.OnOptionsClick(page = 3)
            lstID = ["COUL_POLES", "COUL_PT_CRITIQUE", "COUL_MARGE_OK", "COUL_MARGE_NO",]
            colourData = wx.ColourData()
            colourData.SetColour(wx.NamedColour(self.app.options.optCouleurs[lstID[id-123]]))
            dlg = wx.ColourDialog(self.app, colourData)
            dlg.GetColourData().SetChooseFull(True)
            if dlg.ShowModal() == wx.ID_OK:
                self.app.options.optCouleurs[lstID[id-123]] = dlg.GetColourData().GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
                self.app.DefinirOptions(self.app.options)
                self.app.AppliquerOptions()
        
        elif id in [120, 121, 122]: # Menu contextuel : Couleurs
#            self.app.OnOptionsClick(page = 3)
            lstID = ["FORM_GRILLE", "FORM_ISOGAIN", "FORM_ISOPHASE"]
            dlg = LineFormatSelector(self, self.app.options.optCouleurs[lstID[id-120]])
        
            if dlg.ShowModal() == wx.ID_OK:
#                self.app.options.optCouleurs[lstID[id-120]] = dlg.GetColourData().GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
                self.app.DefinirOptions(self.app.options)
                self.app.AppliquerOptions()
                
#                self.SetFormatBouton()
#                evt = FormatEvent(myEVT_FORMAT_MODIFIED, self.GetId())
#                evt.SetId(self.id)
#                evt.SetFormat(self.format)
#                self.GetEventHandler().ProcessEvent(evt)
                
            dlg.Destroy()
        
#        
#            colourData = wx.ColourData()
#            colourData.SetColour(wx.NamedColour(self.app.options.optCouleurs[lstID[id-120]]))
#            dlg = wx.ColourDialog(self.app, colourData)
#            dlg.GetColourData().SetChooseFull(True)
#            if dlg.ShowModal() == wx.ID_OK:
#                self.app.options.optCouleurs[lstID[id-120]] = dlg.GetColourData().GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
#                self.app.DefinirOptions(self.app.options)
#                self.app.AppliquerOptions()
                
        elif id == 130: # Menu contextuel : Copier
            CopierBitmap(self.child[0].GetBmpExpression(num))
        
        elif id == 131: # Menu contextuel : Copier
            CopierTeX(self.child[0].GetTeXExpression(num))
            
        code = self.GetCode(id)
        if code in ['BFenet', 'BReel', 'BAsymp', 'BGrille', 'BIsoGP', 'BTRepo', 'BPoles', 'BExpre']:
            
            self.SetLabel(code)
            
            
        
    def initZoomPlus(self):
        self.tbar.ToggleTool(20, False)
#        self.child[0].setZoomPlus(False)

    def setCurseur(self, etat):
        self.activerCurseur(etat)
        
    ######################################################################################################
    def GererActivation(self):
        """ Gère l'activation/désactivation des outils :
            diagrammes Réels & diagrammes Asymptotiques
        """
        if (not self.tbar.GetToolToggled(10) and not self.tbar.GetToolToggled(11)):
            self.tbar.ToggleTool(10, True)
            self.child[0].setTracerReel(True)
            self.child[0].calculerEtRedessiner()
            
    ######################################################################################################
    def gererBoutonTR(self, etat):
        if etat :
            if not 'BTRepo' in self.outils:
                self.outils.insert(6, 'BTRepo')
                self.setOutils()
                self.tbar.GetAuiManager().Update()
        else:
            if 'BTRepo' in self.outils:
                self.tbar.DeleteTool(32)
                self.outils.remove('BTRepo')
                self.tbar.GetAuiManager().Update()
            
            
            
    #########################################################################################################
    def gererActivationPoles(self, etat):
        self.tbar.EnableTool(13, etat)
        self.child[0].setPolesAffichables(etat)


    #########################################################################################################
    def reinitialiserBoutons(self):
        self.tbar.ToggleTool(31, False)
        self.child[0].afficherExpress = False
    
########################################################################################################## 
#
# Zone graphique de base
#
##########################################################################################################
class ZoneGraphBase(wx.Panel):
    def __init__(self, parent, zoneOutils, nom, double = False):
        wx.Panel.__init__(self, parent, style = wx.FULL_REPAINT_ON_RESIZE)
        self.SetAutoLayout(True)
        self.parent = parent
        self.zoneOutils = zoneOutils
        
        self.thread = None
        
#        print "init ZoneGraph", nom
        self.nom = nom

        #
        # Les variables d'état de visualisation
        #
        self.zoomAuto = True
        self.zoomPlus = False
        self.curseur = False
        self.deplacer = False
        self.echelle = False
        self.curseurFixe = False
        self.afficherExpress = False
        self.mouseInfo = None
        self.valCurseurSurCote = True
        self.listeArtistsCurseur = []
        self.tracerGrille = globdef.TRACER_GRILLE
        self.rangesAJour = False
        
        #
        # La liste des artists qui sont modifiables
        #
        self.lstArtists = []
        
        #
        # D'eventuels artists additionnels à tracer APRES
        #
        self.artistsPlus = []
        
        #
        # Le contexte où se situe la souris
        #
        self.context = ""
        self.contextOn = False
        
        self.backgroundFig = None
        
        #
        # Les variables d'affichage
        #
        self.fontSizes = {"FONT_SIZE_EXPR"      : globdef.FONT_SIZE_EXPR,
                          "FONT_SIZE_GRAD"      : globdef.FONT_SIZE_GRAD,
                          "FONT_SIZE_LABEL_AXE" : globdef.FONT_SIZE_LABEL_AXE,
                          "FONT_SIZE_LABEL"     : globdef.FONT_SIZE_LABEL, 
                          "FONT_SIZE_CURSEUR"   : globdef.FONT_SIZE_CURSEUR,
                          }
        
        
        #
        # Les éléments de base pour MatPlotLib
        #
        self.figure = Figure(figsize = (1,1))
        self.figure.subplots_adjust(left = 0.08, right = 0.98, top = 0.98, bottom = 0.08, hspace = 0.0)
        
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.ntb = NavigationToolbar(self.canvas)
        self.ntb.Show(False)
        
        #
        # La fenêtre de réglage des paramètres d'affichage
        #
        self.zoneParam = ParamZoneGraph(self.parent, self, nom, double = double)
        self.afficherZoneParam = False
        
        
        
        #
        # Connection des evenements
        #
        self.connectAllEvents()
        self.canvas.mpl_connect('draw_event', self.on_draw)
        self.canvas.mpl_connect('resize_event', self.onSizeMPL)
#        self.canvas.mpl_connect('draw_event', self.OnDraw)
        self.Bind(wx.EVT_SIZE, self.sizeHandler)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
#        self.parent.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)

    ######################################################################################################
    def __repr__(self):
        return "ZoneGragh "+self.nom
    
    
    ######################################################################################################
    def OnEnter(self, event):
#        print "OnEnter"
        self.SetFocus()
#        event.Skip()
#        self.Update()
        
    ######################################################################################################
    def OnContextMenu(self, event):

        self.contextOn = True
        #
        # RAZ du num de contexte
        #
        self.num = None

        # 
        # Création du menu
        #
        menu = wx.Menu()
        
        #
        # Items communs (quel que soit le contexte)
        #
        itemMasquerBarre = wx.MenuItem(menu, 0,"a")
        if self.parent.AffComplet:
            itemMasquerBarre.SetItemLabel(_("Masquer la barre d'outils"))
        else:
            itemMasquerBarre.SetItemLabel(_("Afficher la barre d'outils"))
        menu.AppendItem(itemMasquerBarre)
        self.Bind(wx.EVT_MENU, self.OnMasquerBarre, id=0)
        
        #
        # Items de la barre d'outils (contexte par défaut "")
        # 
        if self.context == "":
            menu.AppendSeparator()
            for o in self.zoneOutils.outils:
                if o == "":
                    menu.AppendSeparator()
                else:
                    id = self.zoneOutils.lstID[o]
                    if self.zoneOutils.tbar.GetToolEnabled(id):
                        if o in["BGrille", "BPoles", "BReel", "BAsymp", "BIsoGP", "BDepla", "BZoomP", "BZoomA", 
                                "BExpre", "BTRepo", "BCurse", "BEchel", 'BFenet']:
                            label, toolTip = self.zoneOutils.GetLabel(o)
                            item = menu.AppendCheckItem(id, label, toolTip)
                            bmp = self.zoneOutils.lstFichImg[o].GetImage().Scale(20, 20, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
#                            bmp = getBitmap(self.zoneOutils.lstFichImg[o], (20,20))
                            bmp2 = setToggled(bmp, wx.Brush(item.GetBackgroundColour()))
                            item.Check(self.zoneOutils.tbar.GetToolToggled(id))
                            item.SetBitmaps(bmp2, bmp)
                            
                            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
        
                        elif o in ["BExpor", "BParam"]:
                            label = self.zoneOutils.tbar.GetToolLabel(id)
                            toolTip = self.zoneOutils.tbar.GetToolShortHelp(id)
                            item = menu.Append(id, label, toolTip)
                            bmp = self.zoneOutils.lstFichImg[o].GetImage().Scale(20, 20, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
#                            bmp = getBitmap(self.zoneOutils.lstFichImg[o], (20,20))
                            item.SetBitmap(bmp)
                            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
                        elif o == "BImpri":
                            item = menu.AppendMenu(id, self.zoneOutils.lstLabel[o], 
                                                   self.zoneOutils.menu)
#                            bmp = getBitmap(self.zoneOutils.lstFichImg[o], (20,20))
                            bmp = self.zoneOutils.lstFichImg[o].GetImage().Scale(20, 20, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
                            item.SetBitmap(bmp)
                            
        #
        # Items FT
        #                     
        elif self.context[0] == "F":
            menu.AppendSeparator()
            self.num = eval(self.context[1])
            id = 100
            label = _("Modifier le format de cette FT")
            toolTip = _("Modifier le format (couleur, style de ligne, ...) de cette FT")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)

            id = 101
            label = _("Masquer cette FT")
            toolTip = _("Masquer cette FT")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
        #
        # Items Réponse
        #                     
        elif self.context[0] == "R":
            menu.AppendSeparator()
            self.num = eval(self.context[1])
            text = [("consigne"), _("réponse"), _("réponse du système non corrigé")]
            id = 102
            label = _("Modifier le format de la ") + text[self.num]
            toolTip = _("Modifier le format (couleur, style de ligne, ...) de la ") + text[self.num]
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)

#            id = 101
#            label = _("Masquer cette FT")
#            toolTip = _("Masquer cette FT")
#            item = menu.Append(id, label, toolTip)
#            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
        #
        # Items Expressions
        #                     
        elif self.context[0] == "E":
            menu.AppendSeparator()
            o = 'BExpre'
            id = self.zoneOutils.lstID[o]
            item = menu.Append(id, self.zoneOutils.labelP[o], self.zoneOutils.tipP[o])
            bmp = self.zoneOutils.lstFichImg[o].GetImage().Scale(20, 20, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
#            bmp = getBitmap(self.zoneOutils.lstFichImg[o], (20,20))
            bmp = setToggled(bmp, wx.Brush(item.GetBackgroundColour()))
            item.SetBitmap(bmp)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
            menu.AppendSeparator()
            self.num = eval(self.context[1])
            id = 100
            label = _("Modifier le format de cette FT")
            toolTip = _("Modifier le format (couleur, style de ligne, ...) de cette FT")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)

            id = 101
            label = _("Masquer cette FT")
            toolTip = _("Masquer cette FT")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)

            id = 110
            label = _("Modifier la taille")
            toolTip = _("Modifier la taille de caractère des expressions")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
            id = 130
            label = _("Copier comme une image")
            toolTip = _("Copier cette expression dans le presse-papier\n"\
                        "sous la forme d'une image")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
            id = 131
            label = _("Copier comme une expression LaTeX")
            toolTip = _("Copier cette expression dans le presse-papier\n"\
                        "sous la forme d'une expression LaTeX")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
        #
        # Items isoGain isoPhase
        #                     
        elif self.context[0] in ["G", "P"]:
            menu.AppendSeparator()
            o = 'BIsoGP'
            id = self.zoneOutils.lstID[o]
            item = menu.Append(id, self.zoneOutils.labelP[o], self.zoneOutils.tipP[o])
            bmp = self.zoneOutils.lstFichImg[o].GetImage().Scale(20, 20, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
#            bmp = wx.Image(os.path.join(globdef.DOSSIER_IMAGES, self.zoneOutils.lstFichImg[o]), 
#                           wx.BITMAP_TYPE_PNG).Scale(20, 20, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
            bmp = setToggled(bmp, wx.Brush(item.GetBackgroundColour()))
            item.SetBitmap(bmp)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
            menu.AppendSeparator()
            self.num = eval(self.context[1])
            id = 113
            label = _("Modifier la taille des informations contextuelles")
            toolTip = _("Modifier la taille de caractère des isoGains et isoPhases")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
            if self.context[0] == "G":
                id = 121
                typ = _("isoGains")
            else:
                id = 122
                typ = _("isoPhases")
            label = _("Modifier le format des lignes ")+typ
            toolTip = label
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)

        #
        # Items Axes
        #                     
        elif self.context[0] == "A":
            menu.AppendSeparator()
            id = 112
            label = _("Modifier la taille des titres")
            toolTip = _("Modifier la taille de caractère des titres des axes")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
            id = 111
            label = _("Modifier la taille des valeurs")
            toolTip = _("Modifier la taille de caractère des valeurs des graduations")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
            id = 120
            label = _("Modifier le format de la grille")
            toolTip = label
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
        #
        # Items Point Critique
        #                     
        elif self.context[0] == "C":
            menu.AppendSeparator()
            id = 113
            label = _("Modifier la taille de caractère")
            toolTip = _("Modifier la taille de caractère")
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
            
            id = 124
            label = _("Modifier la couleur du point critique")
            toolTip = label
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
      
        #
        # Items Pôles
        #                     
        elif self.context[0] == "Z":
            menu.AppendSeparator()
            id = 123
            label = _("Modifier la couleur des Pôles")
            toolTip = label
            item = menu.Append(id, label, toolTip)
            self.Bind(wx.EVT_MENU, self.OnClick, id = id)
        self.PopupMenu(menu)
        menu.Destroy()
            
        
        
        #
        # On refait le menu Impression (détruit par le 'Destroy' précédent)
        #
        self.zoneOutils.CreateMenu()
        
        self.contextOn = False

    def OnMasquerBarre(self, event):
        self.SetAffComplet()
        
    
    def OnClick(self, event):
        id = event.GetId()
        if hasattr(self.zoneOutils, "men") and  event.GetEventObject() == self.zoneOutils.menu:
            event.Skip()
        else:
            self.zoneOutils.tbar.ToggleTool(id, not self.zoneOutils.tbar.GetToolToggled(id))
            self.zoneOutils.OnClick(event, num = self.num)
            self.zoneOutils.tbar.Refresh()
            
    ######################################################################################################
    def getsubplot(self):   
        return self.subplot
    
    ######################################################################################################
    def getsubplots(self):   
        return [self.subplot]
        
    ######################################################################################################
    def getXYlim(self):
        return (self.subplot.get_xlim(), self.subplot.get_ylim())
    
    ######################################################################################################
    def adapterPositions(self):
        return
    
    
        
        
    ######################################################################################################
    def on_draw(self, event):
#        print "Ondraw", 
        if self.IsShownOnScreen() and self.calculerMargesFigure():
#            print self.nom,
            self.adapterPositions() # Uniquement pour Bode : gestion de la proportion 2/3 - 1/3
            self.canvas.draw()
            return
#        print
        return False


    ######################################################################################################
    def onSizeMPL(self, event):
#        print "onSizeMPL"
        if self.isVisible() and not self.IsFrozen():
#            print "..."
#            wx.CallAfter(self.restoreBackground())
#            print "Resize", self.nom
#            print self.calculerMarges()
#            self.adapterPositions()
#            self.canvas.draw()
#            self.drawCanvas()

            wx.CallAfter(self.drawCanvas)
            return
        return
        
    
    ######################################################################################################
    def sizeHandler(self, event):
        if self.canvas.GetSize() != self.GetSize():
#            print "OnSize", self.nom,
            self.canvas.SetSize(self.GetSize())
            return 
#             if self.isVisible():# and self.backgroundFig != None:
# #                print "...", self.IsDoubleBuffered()
#     #            wx.CallAfter(self.restoreBackground())
#     #            print "Resize", self.nom
#     #            print self.calculerMarges()
#     #            self.adapterPositions()
#     #            self.canvas.draw()
#     #            self.drawCanvas()
    
#                 wx.CallAfter(self.drawCanvas)
#                 return
#            print
            
            
    ######################################################################################################
    def calculerMargesFigure(self, agrandir = False):
        """ Calcule les marges latérales 'left' et 'bottom' de la figure
            pour un affichage optimal des ticksLabels et ticks
            renvoie True si une modif a été apportée
        """
        
        # On récupère les bbox de tous les textes des axis
        labelsx, labelsy = [], []
        ticksx, ticksy = [], []
        for ax in self.getsubplots():
            labelsy.append(ax.get_yaxis().get_label())
            for yticks in ax.get_yaxis().get_majorticklabels():
                ticksy.append(yticks)
        
        if hasattr(self, "tickS"):
            ticksy.append(self.tickS.label1)
            
        ax = self.getsubplots()[-1]
        labelsx.append(ax.get_xaxis().get_label())
        for xticks in ax.get_xaxis().get_majorticklabels():
            ticksx.append(xticks)
                
        bboxesx = []        
        for label in labelsx+ticksx:
            bbox = label.get_window_extent()
            # the figure transform goes from relative coords->pixels and we
            # want the inverse of that
            #bboxi = bbox.inverse_transformed(self.figure.transFigure)
            bboxi = bbox.transformed(self.figure.transFigure.inverted())
            bboxesx.append(bboxi)
            
        bboxesy = []        
        for label in labelsy+ticksy:
            bbox = label.get_window_extent()
            # the figure transform goes from relative coords->pixels and we
            # want the inverse of that
            #bboxi = bbox.inverse_transformed(self.figure.transFigure)
            bboxi = bbox.transformed(self.figure.transFigure.inverted())
            bboxesy.append(bboxi)

        # this is the bbox that bounds all the bboxes, again in relative
        # figure coords
        bboxx = mtransforms.Bbox.union(bboxesx)
        bboxy = mtransforms.Bbox.union(bboxesy)
        
        ypad = self.getsubplot().get_yaxis().get_major_ticks()[0].get_pad()
        xpad = self.getsubplot().get_xaxis().get_major_ticks()[0].get_pad()

        xpad += self.getsubplot().get_xaxis().OFFSETTEXTPAD 
        ypad += self.getsubplot().get_yaxis().OFFSETTEXTPAD 
        

        ypad, xpad = self.figure.transFigure.inverted().transform((ypad, xpad))

#        left =1.2*bboxy.width
#        bottom = 1.2*bboxx.height
        
        left = 1.1*(bboxy.width + ypad)
        if agrandir:
            left = left*2
        bottom = 1.1*(bboxx.height + xpad)
        
        def dif(a,b):
            return abs(a-b)>0.001
        


        if dif(left,self.figure.subplotpars.left) or dif(bottom,self.figure.subplotpars.bottom):
            try:
                self.figure.subplots_adjust(left = left, bottom = bottom)
            except ValueError:
                return False
            return True
            
        return False

    ######################################################################################################
    def isVisible(self):
        return self.IsShownOnScreen()
    
    
    ######################################################################################################
    def ajusterMarges(self, left = 0.11, right = 0.98, top = 0.93, bottom = 0.16, wspace =0.1, hspace = 0.1):
        self.figure.subplots_adjust(left = left, right = right,
                                    top = top, bottom = bottom, 
                                    wspace = wspace, hspace = hspace)
        self.adapterPositions()


    
    
    ######################################################################################################
    def BloquerCurseur(self):
        self.curseurFixe = not self.curseurFixe
        if self.curseurFixe:
            self.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
        else:
            self.SetCursor(wx.StockCursor(globdef.CURSEUR_CURSEUR))
            
    ######################################################################################################
    def OnMouseDown(self, evt):
        if evt.button == 1:
            self.mouseInfo = None
    
            if self.afficherExpress and not self.deplacer and not self.echelle:
                i = 0
                numExpr = None
                continuer = True
                while continuer:
                    if i >= len(self.lstFTNum):
                        continuer = False
                    elif self.exprFT[i].contains(evt)[0]:
                        continuer = False
                        numExpr = i
                    i += 1
                    
                if numExpr != None:
                    _x, _y = evt.x, evt.y 
                    if _x != None and _y != None:
                        _x = _x / self.figure.get_window_extent().get_points()[1][0]
                        _y = _y / self.figure.get_window_extent().get_points()[1][1]
    
                        x0, y0 = self.exprFT[numExpr].get_position()
    
                        self.mouseInfo = (_x-x0, _y-y0, numExpr)
            
            
            elif self.echelle:
                _x, _y = evt.x, evt.y 
    #            if _x != None and _y != None:
    #                _x = _x / self.figure.get_window_extent().get_points()[1][0]
    #                _y = _y / self.figure.get_window_extent().get_points()[1][1]
    #
    #                x0, y0 = self.exprFT[numExpr].get_position()
                self.mouseInfo = (_x, _y, self.getXYlim())
                
        elif evt.button == 2:
            print ("roulette")
#            self.ntb.pan()
        
#            self.SetAffComplet()
    

    ######################################################################################################
    def OnRelease(self, event):
        if self.zoomPlus:
#            self.zoomAuto = False
#            self.drawCanvas()
            wx.CallAfter(self.calculerEtRedessiner)
            
        elif self.deplacer:
#            self.calculerEtRedessiner( None, None)
            
            wx.CallAfter(self.calculerEtRedessiner)
            
        elif self.curseur:
            self.BloquerCurseur()
            
        elif self.afficherExpress:
            if self.mouseInfo != None:
                self.mouseInfo = None
                self.drawCanvas()
                
        elif self.echelle:
            self.mouseInfo = None
            
            
    ######################################################################################################
    def OnLeave(self, event):
        if self.deplacer:
            return
        elif self.curseur and not self.curseurFixe:
            self.effacerCurseur()
        elif not(self.curseurFixe or self.zoomPlus or self.echelle):
            self.effacerLabels()
        
        if self.contextOn:
            return
        
        self.parent.app.SetFocus()
            
    ######################################################################################################
    def OnMove(self, event):
        
        _xdata, _ydata = event.xdata, event.ydata
#        if _xdata == None or _ydata == None:
##            self.canvas.SetCursor(wx.StockCursor(CURSEUR_DEFAUT))
#            self.effacerInfos()
#            return
        _x, _y = event.x, event.y

#        liste = self.figure.hitlist(event)
        axe = event.inaxes
#        if axe != None:
#            liste = self.figure.hitlist(event)
#        else:
#            liste = []
            
        #
        # Mode Curseur
        #
        if self.curseur and not self.curseurFixe:
            if _xdata == None or _ydata == None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
                self.effacerCurseur()
            else:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_CURSEUR))
                self.OnMoveCurseur(_xdata, _ydata, axe)

        #
        # Mode déplacer
        #
        elif self.deplacer:
            return    
        
        #
        # Mode zoom
        #
        elif self.zoomPlus:
            return
        
        #
        # Mode Echelle
        #
        elif self.echelle:
            self.OnMoveEchelle(_x, _y, axe)
            
        #
        # Mode Curseur fixe
        #
        elif self.curseurFixe:
            return
        
        #
        # Mode défaut
        #
        else:
            # On est dans la zone du Tracé
            if _xdata != None and _ydata != None:
                self.OnMoveDefaut(_xdata, _ydata, axe, event)
            
            # On est sur les axes
            else:
                self.context = "A"
            
            
    ######################################################################################################
    def OnWheel(self, event):
        self.effacerLabels()
        self.zoneOutils.activerZoomAuto(False)
        self.setZoomAuto(False)
        
        step = event.step
        
        rangeX = self.getXYlim()[0]
        coefX = 1.0 * step /100
        rangeX = self.getNewEchelleAxe(coefX, rangeX, event.xdata)
        
        rangeY = self.getXYlim()[1]
        coefY = 1.0 * step /100
        rangeY = self.getNewEchelleAxe(coefY, rangeY, event.ydata)
        
        self.calculerEtRedessiner(rangeX, rangeY, initMousInfo = False)
        
        
    ######################################################################################################
    def modifierAntialiased(self):
        
        def setAA(f):
            for e in f.get_children():
                if hasattr(e, 'set_antialiased'):
                    e.set_antialiased(globdef.ANTIALIASED)
                elif hasattr(e, 'get_children'):
                    setAA(e)

        setAA(self.figure)


    ######################################################################################################
    def setEstFTBF(self, etat):
        self.estFTBF = etat
        
        
    ######################################################################################################
    def setTracerGrille(self, etat):
        if self.tracerGrille != etat:
            for s in self.getsubplots():
                s.grid(None, which = 'both')
        self.tracerGrille = etat
        self.drawCanvas()
             
        
    ######################################################################################################
    def setZoomAuto(self, etat):
#        print "zoomAuto", etat
        self.zoomAuto = etat
        for subplot in self.getsubplots():
            subplot.set_autoscale_on(etat)

    ######################################################################################################
    def setZoomPlus(self, etat):
#        self.getsubplot().set_autoscale_on(False)
        self.zoomPlus = etat
        for a in self.lstArtists:
            a.set_animated(not etat)
        self.ntb.zoom()
        
    ######################################################################################################
    def setDeplacer(self, etat):
        self.deplacer = etat
#        self.sauveBackGroundFond()
#        for a in self.lstArtists:
#            a.set_animated(not etat)
        self.ntb.pan()
        
    ######################################################################################################
    def SetAffComplet(self, etat = None):
        return self.parent.SetAffComplet(etat)
        
    ######################################################################################################
    def setEchelle(self, etat):
#        self.getsubplot().set_autoscale_on(False)
        if etat:
            self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ECHELLE))
        else:
            self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
        self.zoomAuto = False
        self.echelle = etat
        
    ######################################################################################################
    def setCurseurOff(self):
        self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
        
        for a in self.listeArtistsCurseur:
            removeArtist(a)
        
        # Effacement isoGain 
        if hasattr(self, "isoGainsCurseur"):
            self.isoGainsCurseur.remove()
            # for i in self.isoGainsCurseur.collections: 
            #     i.remove()
            delattr(self, "isoGainsCurseur")
            
        if hasattr(self, "labelIsoGCurs"):
            for i in self.labelIsoGCurs: 
                i.remove()
            delattr(self, "labelIsoGCurs")  
        
        # Effacement isoPhase
        if hasattr(self, "isoPhasesCurseur"):
            self.isoPhasesCurseur.remove()
            
        if hasattr(self, "labelIsoPCurs"):
            for i in self.labelIsoPCurs: 
                removeArtist(i)
#                i.remove()

        self.drawCanvas()
#        self.canvas.draw()   
        
        
    ######################################################################################################
    def effacerCurseur(self):
#        print "Effacer Curseur", self.valCurseurSurCote
        if self.valCurseurSurCote:
            self.restoreBackgroundFig()
        else:
            self.restoreBackground()
            
        for a in self.listeArtistsCurseur:
            a.set_visible(False)
#            a.get_axes().draw_artist(a)
            a.axes.draw_artist(a)
        
        if self.valCurseurSurCote:
            self.canvas.blit()
        else:
            for ax in self.getsubplots():
                self.canvas.blit(ax.bbox)


    ######################################################################################################
    def getxlim(self): 
        return self.getsubplot().get_xlim()
    
    ######################################################################################################
    def getylim(self): 
        return self.getsubplot().get_ylim()
    
    
    ######################################################################################################
    def exporter(self):
        mesFormats = _("Scalable Vector Graphics (.svg)|*.svg|" \
                       "Portable Document Format (.pdf)|*.pdf|" \
                       "Portable Network Graphics (.png)|*.png|" \
                       "PostScript (.ps)|*.ps|" \
                       "Encapsulated PostScript (.eps)|*.eps|" \
                       "Microsoft Excel (.xls)|*.xls"
                       )
        
        dlg = wx.FileDialog(
            self, message=_("Exporter le Tracé courant sous ..."), 
                            defaultDir = self.zoneOutils.app.DossierSauvegarde , 
                            defaultFile="", wildcard=mesFormats, style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR
                            )
        dlg.SetFilterIndex(0)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if os.path.splitext(path)[1] == '.xls':
                exportExcel.createBook(path, self)
            else:
                for a in self.lstArtists:
                    a.set_animated(False)
                try:
                    self.figure.savefig(path, dpi = globdef.DPI_EXPORT)
                except IOError:
                    dlge = wx.MessageDialog(self, _("Permission d'enregistrer reffusée !"),
                                                   _("Erreur d''enregistrement"),
                                                   wx.OK | wx.ICON_ERROR
                                                   )
                    dlge.ShowModal()
                    dlge.Destroy()
                for a in self.lstArtists:
                    a.set_animated(True)
            
        dlg.Destroy()

    ######################################################################################################
    def setAffichParam(self, etat = None):
        if etat == None:
            self.afficherZoneParam = not self.afficherZoneParam
        else:
            self.afficherZoneParam = etat

                                 
        self.zoneParam.Show(self.afficherZoneParam)
        
        

    ######################################################################################################
    def setAffichExpress(self,etat):
        self.afficherExpress = etat
        if etat:
            self.miseAJourExpressions()
            self.afficherExpressions()
        else:
            self.effacerExpressions()
        
    def mettreAJourPoles(self, poles, zeros):
        return
        
    ######################################################################################################
    def calculerEtRedessinerRanges(self):
        """ CalculerEtRedessiner ... avec redéfinition des ranges (après changement vue)
        """
#        print "calculerEtRedessinerRanges", self.nom
        self.calculerEtRedessiner(rangeX = self.subplot.get_xaxis().get_view_interval(),
                                  rangeY = self.subplot.get_yaxis().get_view_interval())
        
    ######################################################################################################
    def mettreAJour(self, lstFTNum, lstCoul, lstPosE, marges, HC, poles = [], zeros = []):
#        print "  mettreAJour", self.nom

        self.lstFTNum = lstFTNum
        self.lstCoul = lstCoul
        self.lstPosE = lstPosE[self.nom]
        self.HC = HC
        self.miseAJour = True
        
        # Mise à jour des expressions
        self.miseAJourExpressions()
        
        # Mise à jour des poles (uniquement pour Nyquist)
        self.mettreAJourPoles(poles, zeros)
        
            
        self.marges = marges
        
        
        
    ######################################################################################################
    def afficherExpressions(self):
        for e in self.exprFT:
            setp(e, visible = True)
#            self.getsubplot().draw_artist(self.exprFT[i])
        self.drawCanvas()
#        self.canvas.blit(self.getsubplot().bbox)
        
    def effacerExpressions(self):
        for e in self.exprFT:
            setp(e, visible = False)
        self.drawCanvas()

        
        
#    def expressionEstDansPlan(self, i):
#        _x, _y = self.exprFT[i].get_window_extent().get_points()[0][0], self.exprFT[i].get_window_extent().get_points()[0][1]
#        print _x, _y
#        w = self.exprFT[i].get_window_extent().get_points()[1][0] - self.exprFT[i].get_window_extent().get_points()[0][0]
#        h = self.exprFT[i].get_window_extent().get_points()[1][1] - self.exprFT[i].get_window_extent().get_points()[0][1]
#        
#        bbox = self.getsubplot().get_window_extent().get_points()
#        print bbox
#        return (_x >= bbox[0][0], _x <= bbox[1][0] - w ,
#                _y >= bbox[0][1] + h , _y <= bbox[1][1])
    
    
#    def mettreExpressionDansPlan(self, i):
#        _x, _y = self.exprFT[i].get_position()
#        print _x, _y
#        
#        p = self.expressionEstDansPlan(i)
#        print p
#        if not p[0]:
#            _x = self.getxlim()[0]
#        elif not p[1]:
#            _x = self.getxlim()[1]
#            
#        if not p[2]:
#            _y = self.getylim()[0]
#        elif p[3]:
#            _y = self.getylim()[1]
#        
#        print "-->", _x, _y
#        setp(self.exprFT[i], x = _x, y = _y)
#       
    def GetBmpExpression(self, id):
        return mathtext_to_wxbitmap(self.lstFTNum[id].getMathTextNom(), 
                                    taille = globdef.FONT_SIZE_FT_HD,
                                    color = self.lstCoul[id].coul)
        
    def GetTeXExpression(self, id):
        return self.lstFTNum[id].getMathTextNom()

#    def miseAJourExpressions(self):
#        for i, ft in enumerate(self.lstFTNum):
#            coul = self.lstCoul[i].get_coul_str()
#            pos = self.lstPosE[i]
#            setp(self.exprFT[i], x = pos.x, y = pos.y, text = mathText(ft.getMathTextNom()), 
#                 color = coul, visible = False)
            
    ######################################################################################################
    def initExpressions(self):
        #
        # réinitialisation des expressions des FT
        #
        for e in self.exprFT:
            self.figure.texts.remove(e)
        self.exprFT = []



    ######################################################################################################
    def miseAJourExpressions(self):
        self.initExpressions()
        for i, ft in enumerate(self.lstFTNum):
            coul = self.lstCoul[i].get_coul_str()
            pos = self.lstPosE[i]
            self.exprFT.append(self.figure.text(pos.x, pos.y, mathText(ft.getMathTextNom()), 
                                                   color = coul, transform = None, 
                                                   visible = self.afficherExpress,
                                                   fontsize = self.fontSizes["FONT_SIZE_EXPR"]))

            
    ######################################################################################################
    def moveExpression(self, event):
        dx, dy, i = self.mouseInfo
        xf, yf = self.figure.get_window_extent().get_points()[1]
        x, y = event.x/xf - dx, event.y/yf - dy
        setp(self.exprFT[i], x = x, y = y)
        self.lstPosE[i].setPos(x,y)
        
        self.drawCanvas()
        
        
#    def razPositionExpressions(self):
#        for i, ft in enumerate(self.lstFTNum):
#            _x, _y = self.getxlim()[0], self.getylim()[0]
#            setp(self.exprFT[i], x = _x, y = _y)
        

#    ######################################################################################################
#    def draw_artists_visibles(self):
#        self.draw_artists(self.artists_visibles)
        
        
    ######################################################################################################
    def draw_artists(self, lstartists, ax = None):
        if ax == None:
            ax = self.getsubplot()

        
        def draw():
            self.restoreBackground(ax)
            
            for a in lstartists:
                ax.draw_artist(a)
                
            self.canvas.blit(ax.bbox)
        

        wx.CallAfter(draw)
            
    
    
    ######################################################################################################
    def sauveBackGroundFig(self):
        self.backgroundFig = self.canvas.copy_from_bbox(self.figure.bbox)

    ######################################################################################################
    def restoreBackgroundFig(self):
        self.canvas.restore_region(self.backgroundFig)
        
    ######################################################################################################    
    def sauveBackGroundFond(self):
        self.backgroundFond = self.canvas.copy_from_bbox(self.figure.bbox)
        
    ######################################################################################################
    def restoreBackgroundFond(self):
        self.canvas.restore_region(self.backgroundFond)
        
    ######################################################################################################
    def disconnectAllEvents(self):
        for id in self.cid:
            self.canvas.mpl_disconnect(id)
    
    ######################################################################################################
    def connectAllEvents(self):
        self.cid = []
        self.cid.append(self.canvas.mpl_connect('button_press_event', self.OnMouseDown))
        self.cid.append(self.canvas.mpl_connect('button_release_event', self.OnRelease))
        self.cid.append(self.canvas.mpl_connect('scroll_event', self.OnWheel))
        self.cid.append(self.canvas.mpl_connect('motion_notify_event', self.OnMove))
        self.cid.append(self.canvas.mpl_connect('figure_leave_event', self.OnLeave))
        self.cid.append(self.canvas.mpl_connect('figure_enter_event', self.OnEnter))
       
#        self.cid.append(self.canvas.mpl_connect('draw_event', self.on_draw))

    
    ######################################################################################################
    def drawCanvas(self):
        #
        # Tracé !!
        #
        if not self.isVisible():
            return
        
        if globdef.USE_THREAD:
            if self.thread != None:
                self.thread._Thread__stop() 
            self.thread = threading.Thread(None, self._drawCanvas)
            self.thread.start()
        else:
            self._drawCanvas()
#            print "drawCanvas", self.nom, ":",chronometrer(self._drawCanvas)


    ######################################################################################################
    def _drawCanvas(self):
        
        #
        # On deconnecte
        #
        self.disconnectAllEvents()
        
        #
        # On redessinne tout
        #
        self.canvas.draw()

        #
        # On sauvegarde le fond du Tracé
        #
        self.sauveBackGroundFond()
        
        #
        # On dessine les artists modifiables
        #
#        for a in self.lstArtists:
##            if a.get_visible():
##                getp(a)
#            self.figure.draw_artist(a)
        
        #
        # Sans oublier les artists supplémentaires
        #    pour dessiner par dessus les ticks !
        #
        for a in self.artistsPlus:
            self.getsubplot().draw_artist(a)
        
        
        if self.artistsPlus != [] or self.lstArtists != []:
#            print "blit"
            self.canvas.blit()
            
        #
        # Sauvegarde du background
        #
#        self.sauveBackGround()
        wx.CallAfter(self.sauveBackGround)

        #
        # On reconnecte
        #
        self.connectAllEvents()
        
        
    ######################################################################################################
    def drawArtists(self):
#        print "DrawArtists"
        self.restoreBackgroundFond()
        for a in self.lstArtists:
            self.figure.draw_artist(a)
        self.canvas.blit()
        self.sauveBackGround()
    
    
#    ######################################################################################################
#    def getXY_Fleche2(self, p0,  p1):
#        print "getXY_Fleche", p0, type(p0),  type(p0[0]),  type(p0[1])
#        ax = self.getsubplot()
#        
#        _x0, _y0 = ax.transAxes.transform(p0)
#        _x1, _y1 = ax.transAxes.transform(p1)
#        
#        b = arctan2(_y1-_y0, _x1-_x0)
#        cosb = cos(b)
#        sinb = sin(b)
#        l = globdef.FLECHE_LONG
#        h = l*globdef.FLECHE_TANA
#        _xa, _ya = _x0+l*cosb + h*sinb, _y0+l*sinb - h*cosb
#        _xb, _yb = _x0+l*cosb - h*sinb, _y0+l*sinb + h*cosb
#        
#        _xy = [[_x0, _y0], [_xa, _ya], [_xb, _yb], [_x0, _y0]]
#        
#        xy = ax.transAxes.inverted().transform(_xy)
#        return xy
    
    ######################################################################################################
    def getXY_Fleche(self, p0,  p1, ax = None):
#        print "getXY_Fleche", p0, type(p0),  type(p0[0]),  type(p0[1])
        if ax == None:
            ax = self.getsubplot()
        
        p0 = array([p0])
        p1 = array([p1])
        
        _p0 = ax.transData.transform(p0)
        _p1 = ax.transData.transform(p1)
        
        _x0, _y0 = _p0[0][0], _p0[0][1]
        _x1, _y1 = _p1[0][0], _p1[0][1]
        
        b = arctan2(_y1-_y0, _x1-_x0)
        cosb = cos(b)
        sinb = sin(b)
        l = globdef.FLECHE_LONG
        h = l*globdef.FLECHE_TANA
        _xa, _ya = _x0+l*cosb + h*sinb, _y0+l*sinb - h*cosb
        _xb, _yb = _x0+l*cosb - h*sinb, _y0+l*sinb + h*cosb
        

        _xy = vstack(([_x0, _y0], [_xa, _ya], [_xb, _yb], [_x0, _y0]))
        
        xy = ax.transData.inverted().transform(_xy)
        return xy
    
    
    ######################################################################################################
    def getNewEchelleAxe(self, coef, range, centre = None, log = False):
        delta = range[1] - range[0]
        ecart = delta * coef /2
        
        # Prise en compte du centre (position de la souris
        if centre != None:
            if log:
                k = 1.0 + 2*log10(coef)/log10(range[1] / range[0])
                _0 = centre * (range[0]/centre) ** k
                _1 = _0 * range[1] * coef**2/range[0]
            else:
                e1 = (centre - range[0])*((delta+2*ecart)/delta -1)
                e2 = 2 * ecart - e1
        else:
            if log:
                _0 = range[0]/coef
                _1 = range[1]*coef
            else:
                e1 = e2 = ecart
            
        if log:
            return _0, _1
        else:
            return range[0] - e1, range[1] + e2
        
        
    
    
######################################################################################################
######################################################################################################
#
#  Fenetre de réglages des paramètres d'affichage intrinsèques à chaque ZoneGraphBase
#
######################################################################################################
######################################################################################################
class ParamZoneGraph(wx.MiniFrame):
    def __init__(self, parent, zoneGraph, nom, double = False):
        self.zoneGraph = zoneGraph
        
#        print "init ParamZoneGraph", _("paramètres ")+nom
        wx.MiniFrame.__init__(self, parent.app, -1, _("Tailles de caractères")+" - "+nom, 
                              style = wx.DEFAULT_FRAME_STYLE|wx.CLIP_CHILDREN#|wx.STAY_ON_TOP
                              )
        
        lstParamFont = range(5)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        #
        # Notebook
        #
#        self.nb = wx.Notebook(self, -1)
        
        #
        # Marges
        #
#        self.subplotParam = self.zoneGraph.figure.subplotpars
#        self.echelle = 200 # Pour résolution des sliders
        
#        self.param = {0: [_("Marge gauche") , "left"],
#                      1: [_("Marge droite") , "right"],
#                      2: [_("Marge bas") , "bottom"],
#                      3: [_("Marge haut") , "top"],
#                      4: [_("Ecart horizontal") , "hspace"],
#                      }
#        if not double:
#            del(self.param[4])
            
#        self.panel = wx.Panel(self.nb, -1)
#
#        bsizer = wx.BoxSizer(wx.VERTICAL)
#        for id in range(len(self.param.keys())):
#            bsizer.Add(self.creerParamSlider(id, self.param[id][0], self.param[id][1]),
#                        0, wx.ALIGN_RIGHT|wx.ALL, 3)
#        
#        self.panel.SetSizerAndFit(bsizer)
#        
#        self.panel.Bind(wx.EVT_SCROLL, self.OnScroll)
        
        
        #
        # Tailles de polices
        #
        self.paramSize = {0: [_("Expressions des FT")         , "FONT_SIZE_EXPR"],
                          1: [_("Valeurs des graduations")   , "FONT_SIZE_GRAD"],
                          2: [_("Titres des axes")          , "FONT_SIZE_LABEL_AXE"],
                          3: [_("Informations contextuelles") , "FONT_SIZE_LABEL"],
                          4: [_("Valeurs du curseur")         , "FONT_SIZE_CURSEUR"],
                          }
        
        self.panel2 = wx.Panel(self, -1, style = wx.BORDER_SIMPLE )

        bsizer = wx.BoxSizer(wx.VERTICAL)
        self.lstSpin = []
        for id in lstParamFont:
            sizerSpin, spin, txt = self.creerFontSpin(id, self.paramSize[id][0], self.paramSize[id][1])
            bsizer.Add(sizerSpin, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
            self.lstSpin.append((spin, txt))
            
        self.panel2.SetSizerAndFit(bsizer)
        
        self.panel2.Bind(wx.EVT_SPINCTRL, self.OnSpin)
        
        #
        # Insersion dans le NoteBook
        #
#        self.nb.AddPage(self.panel, _("Marges"))
#        self.nb.AddPage(self.panel2, _("Tailles de police"))
#        
#        self.nb.Fit()
        
#        self.SetClientSize(self.nb.GetSize())
#        self.SetMaxSize(self.GetSize())
#        self.SetMinSize(self.GetSize())
        
#        sizer = wx.BoxSizer(wx.VERTICAL)
#        sizer.Add(self.panel)
#        self.SetSizerAndFit(sizer)
        
#        self.nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        
    def doLayout(self):
        self.Layout()
        self.panel2.Fit()
        
        
#        self.nb.SetClientSize(self.panel2.GetSize())
#        self.panel2.Layout()
        
        
#        self.nb.Layout()
#        self.nb.Fit()
        
        
        self.Fit()
        
        
        
    ######################################################################################################
    def RendrePartiel(self, lstParamFont):
#        print "Partiel"
        for i, spintxt in enumerate(self.lstSpin):
            if i not in lstParamFont:
                spintxt[0].Show(False)
                spintxt[1].Show(False)
            else:
                spintxt[0].Show(True)
                spintxt[1].Show(True)
        
        self.doLayout()
        
#        
#        

                
    ######################################################################################################
    def RendreTotal(self):
#        print "Total"
        for spintxt in self.lstSpin:
            spintxt[0].Show(True)
            spintxt[1].Show(True)
            
        wx.CallAfter(self.doLayout)
        
    ######################################################################################################
    def OnPageChanged(self, event):
        event.Skip()
        return

    ######################################################################################################
    def OnCloseWindow(self, event):
        self.zoneGraph.setAffichParam(False)
        
        
        
    ######################################################################################################
    def creerParamSlider(self, id, nom, param):
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        txt = wx.StaticText(self.panel, -1, nom)

        slider = wx.Slider(self.panel, id, getattr(self.subplotParam, param)*self.echelle, 0, self.echelle, size = (300,-1),
                           style = wx.SL_HORIZONTAL )
        
        bsizer.Add(txt, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 3)
        bsizer.Add(slider, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, 3)
        
        return bsizer
    
    ######################################################################################################
    def creerFontSpin(self, id, nom, param):
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        txt = wx.StaticText(self.panel2, -1, nom)

        slider = wx.SpinCtrl(self.panel2, id, str(self.zoneGraph.fontSizes[param]), min = 6, max = 30,
                             style = wx.SP_VERTICAL|wx.TE_READONLY#|wx.SP_ARROW_KEYS|wx.SP_WRAP| 
                             )
  
        bsizer.Add(txt, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
        bsizer.Add(slider, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, 3)
        
        return bsizer, slider, txt
    
    ######################################################################################################
    def OnScroll(self, event):
        id = event.GetId()
        
        setattr(self.subplotParam, self.param[id][1], 1.0*event.GetPosition()/self.echelle)
#        print 1.0*event.GetPosition()/self.echelle
        if self.subplotParam.right - self.subplotParam.left < 0.1:
            self.subplotParam.right = self.subplotParam.left + 0.1
        if self.subplotParam.top - self.subplotParam.bottom < 0.1:
            self.subplotParam.top = self.subplotParam.bottom + 0.1
        
        self.subplotParam.update()
        self.zoneGraph.figure.subplots_adjust()
        self.zoneGraph.adapterPositions()
        self.zoneGraph.drawCanvas()


    ######################################################################################################
    def OnSpin(self, event):
        id = event.GetId()
        sp = event.GetEventObject()
        self.zoneGraph.fontSizes[self.paramSize[id][1]] = sp.GetValue()
        
        self.zoneGraph.modifierTaillePolices()
        self.zoneGraph.drawCanvas()
        
        
##########################################################################################################
#
#  Zone graphique Bode
#
##########################################################################################################
class ZoneGraphBode(ZoneGraphBase):
    def __init__(self, parent, zoneOutils, nom = "Bode"):
        ZoneGraphBase.__init__(self, parent, zoneOutils, nom, double = True)
        
        self.estFTBF = False
        self.nom = nom
        
        #
        # Variables d'état de visualisation spécifiques
        #
        self.tracerAsymp = globdef.TRACER_DIAG_ASYMP
        self.tracerReel = globdef.TRACER_DIAG_REEL
        
        #
        # Ecart entre les 2 tracés
        #
        self.ecart = 0.08
        
        #
        # Définition des Artists MPL
        #
        self.initDraw()
        self.modifierTaillePolices()
        self.modifierAntialiased()
        
        self.setZoomAuto(True)
        

    ######################################################################################################
    def initDraw(self):
#        print "initdraw Bode"
        
        if not hasattr(self, 'subplot1'):
            self.subplot1 = self.figure.add_subplot(311)
            self.subplot2 = self.figure.add_subplot(313, sharex = self.subplot1)
        
        self.adapterPositions()
        
        
        #
        # Tracé de la Grille
        #
        for sub in self.getsubplots():
            sub.grid(globdef.TRACER_GRILLE, 
                     color = globdef.FORM_GRILLE.get_coul_str(), zorder = 0, 
                     lw = globdef.FORM_GRILLE.epais, 
                     ls = globdef.FORM_GRILLE.styl)#,
                     #visible = globdef.TRACER_GRILLE)
            sub.get_xaxis().grid(which = 'both', 
                                 lw = globdef.FORM_GRILLE.epais,
                                 ls = globdef.FORM_GRILLE.styl,
                                 color = globdef.FORM_GRILLE.get_coul_str())
                
        self.subplot2.yaxis.set_major_formatter(DegreeFormatter())
        self.subplot2.yaxis.set_major_locator(MaxNLocator(nbins = 5, 
                                                          steps = [1.0, 1.5, 3.0, 4.5, 9.0],
                                                          integer = True))
#        self.subplot2.yaxis.set_minor_locator(MultipleLocator(1))
        
        #
        # Définition des deux "axes"
        #
        self.subplot1.set_ylabel(_("Gain (dB)"))
        self.subplot2.set_ylabel(_("Phase (deg)"))
        self.subplot2.set_xlabel(_("Pulsation (rad/s)"))
#        self.subplot1.autoscale_view(tight=True, scalex=False, scaley=True)
#        self.subplot2.autoscale_view(tight=True, scalex=False, scaley=True)
        self.subplot1.set_xscale('log')
        self.subplot2.set_xscale('log')
        
        #
        # Pré définition des Tracés des FT
        #
        self.lines1 = []
        self.lines2 = []

        
        # Le label de la TF apparaissant au passage de la souris
        self.labelFT1 = self.subplot1.text(1, 0, "", visible = False, url = "labelFT1")
        self.labelFT2 = self.subplot2.text(1, 0, "", visible = False, url = "labelFT2")
        
        #
        # Prédéfinition des expressions des FT
        #
        self.exprFT = []
        
        #
        # Définition des lignes de marges
        #
        coul = globdef.COUL_MARGE_GAIN
        
#        setp(self.ligneMargeGain, transform = self.subplot2.transData)
#        setp(self.ligneMargeGain,  
#             xdata = array([1]), 
#             ydata = [-0.1,0.1])
        
        self.margeGain = self.subplot1.plot([0, 0], color = coul, linewidth = globdef.EP_MARGES,
                                               visible = False, 
                                               transform = self.subplot1.transData)
#        setp(self.margeGain, transform = self.subplot1.transData)
        
        
#        setp(self.ligneMargePhase, transform = self.subplot1.transData)
        
        self.margePhase = self.subplot2.plot([0, 0], color = globdef.COUL_MARGE_PHAS, 
                                             linewidth = globdef.EP_MARGES,
                                             visible = False,
                                             transform = self.subplot2.transData)

        self.ligneMargePhase = self.subplot1.axvline(1,# -1.0, 1.0, 
                                                     visible = False, color = coul)
        
        self.ligneMargeGain = self.subplot2.axvline(1,# -1.0, 1.0, 
                                                    visible = False, color = coul)
        #
        # Définition des axes "origine"
        #
        self.subplot1.axhline(0, linewidth=1, color='k')
        self.subplot2.axhline(0, linewidth=1, color='k')
        
#        for a in self.lstArtists:
#            a.set_animated(True)
        
        try:
            self.calculerMargesFigure()
        except:
            pass
        
    
    ######################################################################################################
    def modifierTaillePolices(self):
        setp(self.subplot1.get_xaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        setp(self.subplot1.get_yaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        setp(self.subplot2.get_xaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        setp(self.subplot2.get_yaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        
        setp(self.subplot1.get_yaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        setp(self.subplot2.get_xaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        setp(self.subplot2.get_yaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        
        setp(self.labelFT1, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        setp(self.labelFT2, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        
        for e in self.exprFT:
            setp(e, fontsize = self.fontSizes["FONT_SIZE_EXPR"])
    
    
    ######################################################################################################
    def adapterPositions(self):
        s = self.figure.subplotpars
        self.posit = [s.left,
                      s.bottom + (s.top - s.bottom - self.ecart)/3 + self.ecart,
                      s.right - s.left,
                      2.0*(s.top - s.bottom - self.ecart)/3]
        self.subplot1.set_position(self.posit)
        
    
    def getsubplot(self, numax = None): 
        if numax == None:
            return self.subplot1
        elif numax == 1:
            return self.subplot1
        elif numax == 2:
            return self.subplot2
    
    def getsubplots(self):   
        return [self.subplot1, self.subplot2]
    
    def getXYlim(self):
        return (self.subplot1.get_xlim(), self.subplot1.get_ylim(), self.subplot2.get_ylim())
    
#    def getxlim(self): 
#        return self.subplot1.get_xlim()
#    
#    def getylim(self): 
#        return self.subplot1.get_ylim()

#    def initZoomPlus(self):
#        self.zoneOutils.initZoomPlus()
            
#    def setZoomAuto(self, etat):
#        self.zoomAuto = etat
#        self.subplot1.set_autoscale_on(True)
#        
#    def setZoomPlus(self, etat):
#        self.subplot1.set_autoscale_on(False)
#        self.zoomPlus = etat
    
#    def setDeplacer(self, etat):
#        self.subplot1.set_autoscale_on(False)
#        self.deplacer = etat    
        
    # Gestion du curseur ################################################################################
    def setCurseur(self, etat):
        if self.curseur != etat:
            self.curseurFixe = False
            self.curseur = etat
            
            if not etat:
                self.setCurseurOff() 
            else:
                self.sauveBackGroundFig()
                coul = globdef.COUL_TEXT_CURSEUR
                size = globdef.FONT_SIZE_CURSEUR
                halign = 'center'
                bgcolor = globdef.COUL_BLANC
                    
                if self.valCurseurSurCote:
                    #
                    # La valeur de la pulsation
                    #
                    self.tickOmega1 = XTick(self.subplot1, 1.0, gridOn = True)
                    self.tickOmega2 = XTick(self.subplot2, 1.0, gridOn = True)
                    for t in [self.tickOmega1, self.tickOmega2]:
                        t.gridline.set_color('black')
                        t.gridline.set_linestyle('-')
                        t.label1.set_size(globdef.FONT_SIZE_GRAD)
                        t.label1.set_backgroundcolor(self.figure.get_facecolor())
                        t.label1.set_verticalalignment('top')

                    #
                    # Les valeurs de gain et de phase
                    #
                    self.tickGain, self.tickPhas = [], []
                    for i in range(len(self.lstFTNum)):
                        coul = self.lstCoul[i].get_coul_str()
                        tickGain = YTick(self.subplot1, 1.0, gridOn = True)
                        tickPhas = YTick(self.subplot2, 1.0, gridOn = True)
                        for t in [tickGain, tickPhas]:
                            t.gridline.set_color(coul)
                            t.gridline.set_linestyle('-')
                            t.label1.set_size(globdef.FONT_SIZE_GRAD)
                            t.label1.set_backgroundcolor(self.figure.get_facecolor())
                            t.label1.set_color(coul)
                        self.tickGain.append(tickGain)
                        self.tickPhas.append(tickPhas)
                        
                    self.listeArtistsCurseur = [self.tickOmega1, self.tickOmega2]
                    self.listeArtistsCurseur.extend(self.tickGain)
                    self.listeArtistsCurseur.extend(self.tickPhas)
                    
                        
                else:     
                    bbox = dict(facecolor = bgcolor, alpha = 0.7, 
                                edgecolor = "none", linewidth = 2.0,
                                zorder = globdef.ZORDER_MAXI)   
                    #
                    # La valeur de la pulsation
                    #
                    self.txtCurs1 = self.subplot1.text(1.0, 0.0, "", visible = False, color = coul,
                                                       fontsize = size, horizontalalignment = halign,
                                                       animated = True, bbox = bbox)
                    self.txtCurs2 = self.subplot2.text(1.0, 0.0, "", visible = False, color = coul,
                                                       fontsize = size, horizontalalignment = halign,
                                                       animated = True, bbox = bbox)
                    
                    #
                    # Les lignes verticales
                    #
                    self.vlineG = self.subplot1.axvline(1.0, 0.0, 1.0, animated = True, color = coul)
                    self.vlineP = self.subplot2.axvline(1.0, 0.0, 1.0, animated = True, color = coul)
                    
                    #
                    # Les lignes horizontales
                    #
                    self.hlineG, self.hlineP = [], []
                    for i in range(len(self.lstFTNum)):
                        coul = self.lstCoul[i].get_coul_str()
                        self.hlineG.append(self.subplot1.axhline(0.0, 0.0, 1.0, animated = True, color = coul))
                        self.hlineP.append(self.subplot2.axhline(0.0, 0.0, 1.0, animated = True, color = coul))
                    
                    #
                    # Les valeurs de gain et de phase
                    #
                    self.txtcursG, self.txtcursP = [], []
                    for i in range(len(self.lstFTNum)):
                        self.txtcursG.append(self.subplot1.text(1.0, 0.0, "", visible = False, color = coul,
                                                       fontsize = size, horizontalalignment = halign, animated = True,
                                                       bbox = bbox))
                        self.txtcursP.append(self.subplot2.text(1.0, 0.0, "" ,visible = False, color = coul,
                                                       fontsize = size, horizontalalignment = halign, animated = True,
                                                       bbox = bbox))
                    self.listeArtistsCurseur = [self.txtCurs1, self.txtCurs2, self.vlineG, self.vlineP]
                    self.listeArtistsCurseur.extend(self.txtcursG)
                    self.listeArtistsCurseur.extend(self.txtcursP)
                
                
                
       
                    

            

#    ######################################################################################################
#    def setAffichExpress(self,etat):
#        self.afficherExpress = etat
#        if etat:
#            for i, ft in enumerate(self.lstFTNum):
#                coul = self.lstCoul[i].GetAsString(wx.C2S_HTML_SYNTAX)
#                _x, _y = self.subplot1.get_xlim()[0], self.subplot1.get_ylim()[0]
#                setp(self.exprFT[i], x = _x, y = _y,
#                     text = ft.getMplText('H'), visible = True, color = coul)
#        else:
#            for e in self.exprFT:
#                setp(e, visible = False)
#        self.drawCanvas()
        
    
        
        
    ######################################################################################################
    def setTracerAsymp(self, etat):
        self.tracerAsymp = etat
        for i in range(len(self.lstFTNum)):
            setp(self.lines1[2*i+1], visible = etat)
            setp(self.lines2[2*i+1], visible = etat)
        self.drawCanvas()
    
    
    ######################################################################################################
    def setTracerReel(self, etat):
        self.tracerReel = etat
        for i in range(len(self.lstFTNum)):
            setp(self.lines1[2*i], visible = etat)
            setp(self.lines2[2*i], visible = etat)
        self.drawCanvas()
        
    ######################################################################################################
    def setCouleurs(self):
        for s in self.getsubplots():
            s.grid(self.tracerGrille, color = globdef.FORM_GRILLE.get_coul_str(),
                   lw = globdef.FORM_GRILLE.epais,
                   ls = globdef.FORM_GRILLE.styl)
            s.get_xaxis().grid(which = 'both', 
                               lw = globdef.FORM_GRILLE.epais,
                               ls = globdef.FORM_GRILLE.styl,
                               color = globdef.FORM_GRILLE.get_coul_str())
        for m in self.margeGain:
            m.set_color(globdef.COUL_MARGE_GAIN)
        for m in self.margePhase:
            m.set_color(globdef.COUL_MARGE_PHAS)
            
#        if retracer:
#            self.drawCanvas()
        

    #######################################################################################################
    def effacerLabels(self):      
        self.restoreBackground()
        
        setp(self.labelFT1, visible = False)
        setp(self.labelFT2, visible = False)
        self.subplot1.draw_artist(self.labelFT1)
        self.subplot2.draw_artist(self.labelFT2)
        
        self.canvas.blit(self.subplot1.bbox)
        self.canvas.blit(self.subplot2.bbox)


    ######################################################################################################
    def Detection(self, event, axe, lines):
        detect = {"FT": None,
                  "EX": None,
                  "IP": None,
                  "IG": None,
                  "PC": None,
                  "MA": None}

#        print "detection", lines
        # Détection des FT
        if axe != None:
            continuer = True
            i = 0
             
            while continuer:
                if i >= len(self.lstFTNum):
                    continuer = False
                elif lines[2*i].contains(event)[0] \
                    or (lines[2*i+1].contains(event)[0] and self.tracerAsymp):
                    continuer = False
                    detect["FT"] = i
                i += 1
        if detect["FT"] != None: return detect
        
        # Détection des expressions
        continuer = True
        i = 0
        while continuer:
            if i >= len(self.lstFTNum):
                continuer = False
            elif self.exprFT[i].contains(event)[0]:
                continuer = False
                detect["EX"] = i
            i += 1
        if detect["EX"] != None: return detect
        
        # Détection des marges
        if "marges" in self.contenu:
            if self.margeGain[0].contains(event)[0]:
                detect["MA"] = 'g'
            elif self.margePhase[0].contains(event)[0]:
                detect["MA"] = 'p'
            if detect["MA"] != None: return detect
            
        return detect
    
    
    ######################################################################################################
    def OnMoveDefaut(self, _xdata, _ydata, axe, event = None):
        #
        # Déplacement d'une expression
        #
        if self.mouseInfo != None:
            self.moveExpression(event)

        if not hasattr(self, 'background1'):
            self.sauveBackGround()
        
        #
        # Détections ...
        #
        else:
            if axe == self.subplot1:
                lines = self.lines1
                labelFT = self.labelFT1
            elif axe == self.subplot2:
                lines = self.lines2
                labelFT = self.labelFT2
            
            with errstate(invalid='ignore'):
                detect = self.Detection(event, axe, lines)
            
            # Affichage ...
            if detect["EX"] != None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_MAIN))
                self.context = "E"+str(detect["EX"])
                
            elif detect["FT"] != None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
                coul = self.lstCoul[detect["FT"]].get_coul_str()
                setp(labelFT, text = r"$"+self.lstFTNum[detect["FT"]].nom + " $",
                     x = _xdata, y = _ydata, visible = True, color = coul)
                
#                self.artists_visibles.append(labelFT, axe)
                self.draw_artists([labelFT], axe)
                self.context = "F"+str(detect["FT"])

            elif detect["MA"] != None:
                marges = self.contenu["marges"]
#                print marges
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
#                coul = self.lstCoul[detect["FT"]].get_coul_str()
                if detect["MA"] == 'g':
                    texte = marges.getMathTexteMg()
                    coul = marges.getCoulG()
                else:
                    texte = marges.getMathTexteMp()
                    coul = marges.getCoulP()
            
                setp(labelFT, text = texte,
                     x = _xdata, y = _ydata, visible = True,
                     color = coul)
                
#                self.artists_visibles.append(labelFT, axe)
                self.draw_artists([labelFT], axe)
                self.context = "M"+str(detect["MA"])
                
            else:
                self.effacerLabels()
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
                self.context = ""
            

    ######################################################################################################
    def OnMoveEchelle(self, _x, _y, axe):
        if self.mouseInfo != None:
            dx = _x-self.mouseInfo[0]
            rangeX = self.mouseInfo[2][0]
            coefX = exp(1.0 * dx /100)
            
            rangeX = self.getNewEchelleAxe(coefX, rangeX, log = True)
#            rangeX = [rangeX[0]/coefX, rangeX[1]*coefX]
            
            dy = _y-self.mouseInfo[1]
            if axe == self.subplot1:
                rangeY = self.mouseInfo[2][1]
            else:
                rangeY = self.mouseInfo[2][2]
            coefY = 1.0 * dy /100
            rangeY = self.getNewEchelleAxe(coefY, rangeY)
#            deltaY = rangeY[1] - rangeY[0]
#            ecartY = deltaY * coefY /2
#            rangeY = [rangeY[0] - ecartY, rangeY[1] + ecartY]
            
            if axe == self.subplot1:
                self.calculerEtRedessiner(rangeX, rangeY1 = rangeY, initMousInfo = False)
            else:
                self.calculerEtRedessiner(rangeX, rangeY2 = rangeY, initMousInfo = False)

    
    ######################################################################################################
    def OnWheel(self, event):
        self.effacerLabels()
        self.zoneOutils.activerZoomAuto(False)
        self.setZoomAuto(False)
        step = event.step
        axe = event.inaxes
        coefX = exp(1.0 * step /100)
        coefY = 1.0 * step /100
        
        if axe != None:
            if axe == self.subplot1:
                rangeY = self.getXYlim()[1]
                rangeY1 = self.getNewEchelleAxe(coefY, rangeY, event.ydata)
                rangeY2 = []
            else:
                rangeY = self.getXYlim()[2]
                rangeY2 = self.getNewEchelleAxe(coefY, rangeY, event.ydata)
                rangeY1 = []
            rangeX = self.getNewEchelleAxe(coefX, self.getXYlim()[0], event.xdata, log = True)
        else:
            if self.subplot1.get_xaxis().contains(event)[0] or self.subplot2.get_xaxis().contains(event)[0]:
                rangeX = self.getNewEchelleAxe(coefX, self.getXYlim()[0], event.xdata, log = True)
                rangeY1 = rangeY2 = []
            elif self.subplot1.get_yaxis().contains(event)[0]:
                rangeY1 = self.getNewEchelleAxe(coefY, self.getXYlim()[1], event.ydata)
                rangeX = []
                rangeY2 = []
            elif self.subplot2.get_yaxis().contains(event)[0]:
                rangeY2 = self.getNewEchelleAxe(coefY, self.getXYlim()[2], event.ydata)
                rangeX = []
                rangeY1 = []
            else:
                rangeX = []
                rangeY1 = rangeY2 = []
#                print " coefY =", coefY,
#        deltaY = rangeY[1] - rangeY[0]
#        ecartY = deltaY * coefY /2
#        rangeY = [rangeY[0] - ecartY, rangeY[1] + ecartY]
#                print rangeY
        
    
        
        self.calculerEtRedessiner(rangeX, rangeY1 = rangeY1, rangeY2 = rangeY2, initMousInfo = False)

        
        

    ######################################################################################################
    def OnMoveCurseur(self, _xdata, _ydata, axe):
        
        
            
        self.restoreBackground()
        
        if self.valCurseurSurCote:
            #
            # La valeur de la pulsation
            #
            text = fonctions.strSc(_xdata)
            self.tickOmega1.update_position(_xdata)
            self.tickOmega1.label1.set_text(text)
            self.tickOmega1.set_visible(True)
            self.tickOmega2.update_position(_xdata)
            self.tickOmega2.label1.set_text(text)
            self.tickOmega2.set_visible(True)
            
            axe.draw_artist(self.tickOmega1)
            axe.draw_artist(self.tickOmega2)
#                
            for i, ft in enumerate(self.lstFTNum):
                _yG = ft.HdB(_xdata)
                _yP = ft.Phi(_xdata)
                self.tickGain[i].update_position(_yG)
                #self.tickGain[i].set_label(fonctions.strSc(_yG))
                self.tickGain[i].label1.set_text(fonctions.strSc(_yG))
                self.tickGain[i].set_visible(True)
                
                self.tickPhas[i].update_position(_yP)
                #self.tickPhas[i].set_label(fonctions.strSc(_yP))
                self.tickPhas[i].label1.set_text(fonctions.strSc(_yG))
                self.tickPhas[i].set_visible(True)
                
                self.subplot1.draw_artist(self.tickGain[i])
                self.subplot2.draw_artist(self.tickPhas[i])

            self.canvas.blit()

        else:
            if axe == self.subplot1:
                txtcurs = self.txtCurs1
            elif axe == self.subplot2:
                txtcurs = self.txtCurs2
            text = r"$\omega="+fonctions.strSc(_xdata)+r" rad/s$"+"\n"
            setp(txtcurs, position = (_xdata, _ydata),
                 text = text, visible = True)
            axe.draw_artist(txtcurs)

        
            #
            # Les lignes et les valeurs de gain et de phase
            #
            yGmoy = (self.subplot1.get_ylim()[0] + self.subplot1.get_ylim()[1])/2
            yPmoy = (self.subplot2.get_ylim()[0] + self.subplot2.get_ylim()[1])/2
            
            # Lignes verticales
            setp(self.vlineG, xdata = array([_xdata]))
            self.subplot1.draw_artist(self.vlineG)
            setp(self.vlineP, xdata = array([_xdata]))
            self.subplot2.draw_artist(self.vlineP)
            
            for i, ft in enumerate(self.lstFTNum):
                _yG = ft.HdB(_xdata)
                _yP = ft.Phi(_xdata)
                
                # Lignes horizontales
                setp(self.hlineG[i], ydata = array([_yG]))
                self.subplot1.draw_artist(self.hlineG[i])
                setp(self.hlineP[i], ydata = array([_yP]))
                self.subplot2.draw_artist(self.hlineP[i])
                
                # Valeur gain
                dG = ft.derivee(ft.HdB, _xdata)# * coefG
                va, ha, s1, s2 = getAlignment(dG, _yG < yGmoy)
                setp(self.txtcursG[i], x = _xdata , y = _yG ,
                     horizontalalignment = ha, verticalalignment = va, zorder = globdef.ZORDER_MAXI-i+1,
                     text = s1+r"$H_{dB}="+fonctions.strSc(_yG)+r" dB$"+s2, visible = True)
                self.subplot1.draw_artist(self.txtcursG[i])
                
                # Valeur Phase
                dP = ft.derivee(ft.Phi, _xdata)# * coefP
                va, ha, s1, s2 = getAlignment(dP, _yP < yPmoy)
                setp(self.txtcursP[i], x = _xdata, y = _yP,
                     horizontalalignment = ha, verticalalignment = va,
                     text = s1+r"$\varphi="+fonctions.strSc(_yP)+r"°$"+s2, visible = True)
                self.subplot2.draw_artist(self.txtcursP[i])   
        
            self.canvas.blit(self.subplot1.bbox)
            self.canvas.blit(self.subplot2.bbox)

        if self.estFTBF:
            self.zoneOutils.app.winReponse.SynchroniserPulsationSinus(_xdata)
                
#    ######################################################################################################
#    def OnMove(self, event):
#        
#        _xdata, _ydata = event.xdata, event.ydata
#        
##        if (_xdata == None or _ydata == None):
##            self.canvas.SetCursor(wx.StockCursor(CURSEUR_DEFAUT))
##            self.effacerInfos()
##            return
##        
#        axe = event.inaxes
#        
#        if axe == self.subplot1:
#            lines = self.lines1
#            labelFT = self.labelFT1
#        elif axe == self.subplot2:
#            lines = self.lines2
#            labelFT = self.labelFT2
#        
#        liste = self.figure.hitlist(event)
#        
#        #
#        # Mode Curseur
#        #
#        if self.curseur and not self.curseurFixe:
#            self.OnMoveCurseur(_xdata, _ydata, axe)
#                
#        #
#        # Mode déplacer
#        #
#        elif self.deplacer:
#            return    
#        
#        #
#        # Mode zoom
#        #
#        elif self.zoomPlus:
#            return
#        
#        #
#        # Mode Curseur fixe
#        #
#        elif self.curseurFixe:
#            return
#        
#        #
#        # Mode Echelle
#        #
#        elif self.echelle:
#            _x, _y = event.x, event.y 
#            if self.mouseInfo != None:
#                dx = _x-self.mouseInfo[0]
#                rangeX = self.mouseInfo[2][0]
#                coefX = exp(1.0 * dx /100)
#                print " coefX =", coefX,
#                rangeX = [rangeX[0]/coefX, rangeX[1]*coefX]
#                print rangeX
#                
#                dy = _y-self.mouseInfo[1]
#                if axe == self.subplot1:
#                    rangeY = self.mouseInfo[2][1]
#                else:
#                    rangeY = self.mouseInfo[2][2]
#                coefY = 1.0 * dy /100
#                print " coefY =", coefY,
#                deltaY = rangeY[1] - rangeY[0]
#                ecartY = deltaY * coefY /2
#                rangeY = [rangeY[0] - ecartY, rangeY[1] + ecartY]
#                print rangeY
#                
#                if axe == self.subplot1:
#                    self.calculerEtRedessiner(rangeX, rangeY1 = rangeY, initMousInfo = False)
#                else:
#                    self.calculerEtRedessiner(rangeX, rangeY2 = rangeY, initMousInfo = False)
#                
#        
#        #
#        # Mode défaut
#        #        
#        else:
#            #
#            # Déplacement d'une expression
#            #
#            if self.mouseInfo != None:
#                self.moveExpression(event)
#
#            
#            #
#            # Détections ...
#            #
#            else:
#                # Détection des FT
#                numFT = None
#                if axe != None:
#                    continuer = True
#                    i = 0
#                    while continuer:
#                        if i >= len(self.lstFTNum):
#                            continuer = False
#                        elif lines[2*i] in liste or lines[2*i+1] in liste:
#                            continuer = False
#                            numFT = i
#                        i += 1
#                    
#                # Détection des expressions
#                numExpr = None
#                continuer = True
#                i = 0
#                while continuer:
#                    if i >= len(self.lstFTNum):
#                        continuer = False
#                    elif self.exprFT[i] in liste or self.exprFT[i] in liste:
#                        continuer = False
#                        numExpr = i
#                    i += 1
#                
#                # Affichage ...
#                if numExpr != None:
#                    self.canvas.SetCursor(wx.StockCursor(CURSEUR_MAIN))
#                    
#                elif numFT != None:
#                    self.canvas.SetCursor(wx.StockCursor(CURSEUR_ISO))
#                    coul = self.lstCoul[numFT].GetAsString(wx.C2S_HTML_SYNTAX)
#                    setp(labelFT, text = r"$"+self.lstFTNum[numFT].nom + " $",
#                         x = _xdata, y = _ydata, visible = True, color = coul)
#                    self.draw_artists([labelFT], axe)
#
#                else:
#                    self.effacerInfos()
#                    self.canvas.SetCursor(wx.StockCursor(CURSEUR_DEFAUT))
         
                

#    ######################################################################################################
#    def draw_artists(self, lstartists, ax):
#        if hasattr(self, "background1"):
#            if ax == self.subplot1:
#                self.canvas.restore_region(self.background1)
#            elif ax == self.subplot2:
#                self.canvas.restore_region(self.background2)
#            else:
#                self.canvas.restore_region(self.backgroundFig)
#        
#        for a in lstartists:
#            ax.draw_artist(a)
#    
#        self.canvas.blit(ax.bbox)
#        if ax == self.subplot1:
#            self.canvas.blit(self.subplot1.bbox)
#        elif ax == self.subplot2:
#            self.canvas.blit(self.subplot2.bbox)
#        elif ax == None:
#            self.canvas.blit(self.figure.bbox)

    
            
    ######################################################################################################    
    def getDiagrammes(self, lstFTNum, lstCoul, marges, rangeX = []):
        """ Renvoie les diagrammes à tracer (contenu)
            ... après avoir calculé les intervalles
        """
        
#        if globdef.DEBUG:
#        print "getDiagrammes Bode ..."
        #
        # determination du minmax en pulsation
        #
        if self.zoomAuto:
            # Calcul automatique
            mini, maxi = [], []
            for i, ft in enumerate(lstFTNum):
                minmaxD = ft.getRangeDecade()
                mini.append(minmaxD[0])
                maxi.append(minmaxD[1])
            if len(lstFTNum) == 0:
                contenu = {"minmax" : [0.1,10.0]}
                return contenu
            else:
                minmaxD = [min(mini), max(maxi)]
                minmax = ft.getRange(minmaxD)
                pulsas = calcul.getPulsationsD(minmaxD)
        else:
            if len(rangeX) == 0 or rangeX is None:
                rangeX = self.subplot1.get_xlim()
            pulsas = calcul.getPulsations(rangeX)
            minmax = rangeX
            
#        if globdef.DEBUG:
#            print "pulsas",pulsas
        #
        # on construit les diagrammes
        #
        lstDiagAsympGain = []
        lstDiagAsympPhas = []
        lstDiagReelsGain = []
        lstDiagReelsPhas = []
        
        for i, ft in enumerate(lstFTNum):
            diagG, diagP = ft.getDiagAsympGainPhase()
            lstDiagAsympGain.append(diagG)
            lstDiagAsympPhas.append(diagP)
#            if globdef.DEBUG:
#                print "diag asymp : OK"
            lstDAPhase, lstDAGain= ft.getDiagBode(pulsas)
            lstDiagReelsGain.append(lstDAGain)
            lstDiagReelsPhas.append(lstDAPhase)
#            print lstDAGain.reponse
#            if globdef.DEBUG:
#                print "diag reel : OK"

        contenu = {}
        contenu["diagAsymp"] = (lstDiagAsympGain, lstDiagAsympPhas)
        contenu["diagReel"] = (lstDiagReelsGain, lstDiagReelsPhas)
        contenu["minmax"] = minmax
        
        if marges != None:
            contenu["marges"] = marges
            
        
#        if globdef.DEBUG: 
#            print "  ", contenu
        
        return contenu
        
    ######################################################################################################
    def getDiagAsympGain(self, diag):
#        print "Tracé diag asymp Gain :", diag
        rangeX = self.contenu["minmax"]
        x0 = rangeX[0]
        y0 = diag.HdB(rangeX[0])
        
        lstX = [x0]
        lstY = [y0]
    
        r = 1
        continuer = True
        while r < len(diag.Asymp) and continuer:
            omega = diag.Asymp[r].omega
            if omega >= rangeX[1]:
                omega = rangeX[1]
                continuer = False  
            lstX.append(omega)
            lstY.append(diag.HdB(omega))
            r += 1
            
        if continuer:
            omega = rangeX[1]
            lstX.append(omega)
            lstY.append(diag.HdB(omega))
        
        return lstX, lstY
    
    
    #####################################################################################################  
    def getDiagAsympPhase(self, diag):
#        print "Tracé diag Phase :", diag
        
        # Premier point
        rangeX = self.contenu["minmax"]
        x = rangeX[0]
        y = diag.Phi(rangeX[0])
        
        lstX = [x]
        lstY = [y]
        
        r = 1
        continuer = True
        while r < len(diag.Asymp) and continuer:
            omega = diag.Asymp[r].omega
            if omega >= rangeX[1]:
                omega = rangeX[1]
                continuer = False  
                
            y = diag.Phi(omega)
            lstX.append(x)
            lstY.append(y)
        
            x = omega
            lstX.append(x)
            lstY.append(y)
            
            r += 1
            
        if continuer:
            omega = rangeX[1]
            
            y = diag.Phi(omega)
            lstX.append(x)
            lstY.append(y)
            lstX.append(omega)
            lstY.append(y)
        
            
        return lstX, lstY
        
    
    
    
    
    ######################################################################################################
#    def mettreAJourEtRedessiner(self, lstFTNum, lstCoul, winMarges, HC, poles = None):
#        """
#        """
##        print "mettreAJourEtRedessiner", self.nom
#        self.mettreAJour(lstFTNum, lstCoul, winMarges, HC, poles)
#        self.calculerEtRedessinerRanges()
#        self.reTracerExpressions()
        
        
    
        
    
    ######################################################################################################
    def calculerEtRedessinerRanges(self):
#        print "calculerEtRedessinerRanges", self.nom
        self.calculerEtRedessiner(rangeX = self.subplot1.get_xaxis().get_view_interval())
        
        
    ######################################################################################################
    def calculerEtRedessiner(self, rangeX = [], rangeY1 = [], rangeY2 = [], initMousInfo = True):
        """ Calcul des différents diagrammes à afficher 
            et redessinner tout
        """
#        if globdef.DEBUG:
#        print "Calculer et redessiner Bode", rangeX, rangeY1, rangeY2, self.lstFTNum
        
        self.contenu = self.getDiagrammes(self.lstFTNum, self.lstCoul, self.marges, rangeX)
        
        if initMousInfo:
            self.mouseInfo = None
            
        #
        # Synchronisation automatique des axes des X
        #
        rangeX = self.contenu["minmax"]
        
        #
        # On regarde si les ranges ont changé
        #
        x1, x2 = self.subplot1.get_xlim()
        y11, y12 = self.subplot1.get_ylim()
        y21, y22 = self.subplot2.get_ylim()
        
        self.rangesAJour = rangeX is not None and rangeY1 is not None and rangeY2 is not None 
        self.rangesAJour = self.rangesAJour and \
                           (    (x1 == rangeX[0] and x2 == rangeX[1]) \
                            and (len(rangeY1) == 0 or (y11 == rangeY1[0] and y12 == rangeY1[1]))\
                            and (len(rangeY2) == 0 or (y21 == rangeY2[0] and y22 == rangeY2[1])))
        

        self.subplot1.set_xlim(rangeX)
        self.subplot2.set_xlim(rangeX)
        
        
#        for range in [rangeY1, rangeY2]:
#            if range == []:# or range == None:
#                range.extend([-1, 1])
#            elif range[0] == range[1]:
#                range[0] += -1
#                range[1] += 1
#        print rangeY1, rangeY2
#        self.subplot1.set_ylim(rangeY1)
#        self.subplot2.set_ylim(rangeY2)
        if rangeY1 != [] and rangeY1 != None:
            self.subplot1.set_ylim(rangeY1)
        if rangeY2 != [] and rangeY2 != None:
            self.subplot2.set_ylim(rangeY2)    
        
        
        self.TracerTout()
        
#        if self.afficherExpress:
#            self.miseAJourExpressions()
#            self.afficherExpressions()
#        dt = chronometrer(self.TracerTout)
#        print "TracerTout", dt
#        self.TracerTout()
        
        
    #####################################################################################################    
    def TracerTout(self):
        """ Tracé de tout 
#        """
#        print "TracerTout Bode ..."
#        print self.lstFTNum
        self.zoneOutils.activerCurseur(False)
        
        #
        # On efface les lignes
        #
        for l in self.lines1+self.lines2:
            l.remove()    
        self.lines1 = []
        self.lines2 = []
        
        #
        # Séparation des contenus "Gain" et "Phase"
        #
        if "diagReel" in self.contenu.keys():
            lR = self.contenu["diagReel"]
        else:
            lR = ([],[])
            
        if "diagAsymp" in self.contenu.keys():
            lA = self.contenu["diagAsymp"]
        else:
            lA = ([],[])
        
        contenuGain = {"diagA" : lA[0],
                       "diagR" : lR[0]}
        
        contenuPhas = {"diagA" : lA[1],
                       "diagR" : lR[1]}
                
        #
        # Propriétés des diagrammes
        #
        for i, ft in enumerate(self.lstFTNum):
            coul = self.lstCoul[i].get_coul_str()
            width = self.lstCoul[i].epais
            style = self.lstCoul[i].styl
            
            diagG = contenuGain["diagR"][i]
            self.lines1 += self.subplot1.plot(diagG.reponse[0],diagG.reponse[1],
                                            color = coul, 
                                            linewidth = width, 
                                            linestyle = style,
                                            zorder = globdef.ZORDER_MAXI-i, 
                                            visible = self.tracerReel,
                                            marker = globdef.MARKER)
            
            diagP = contenuPhas["diagR"][i]
            self.lines2 += self.subplot2.plot(diagP.reponse[0],diagP.reponse[1] ,
                                        color = coul, 
                                        linewidth = width, 
                                        linestyle = style,
                                        zorder = globdef.ZORDER_MAXI-i,
                                        visible = self.tracerReel,
                                        marker = globdef.MARKER)
            

            diagG = contenuGain["diagA"][i]
            lstX, lstY = self.getDiagAsympGain(diagG)
            self.lines1 += self.subplot1.plot(lstX,lstY,
                                        color = coul, 
                                        linewidth = max(1, width/2), 
                                        linestyle = style,
                                        zorder = globdef.ZORDER_MAXI-i, 
                                        visible = self.tracerAsymp)
            
            diagP = contenuPhas["diagA"][i]
            lstX, lstY = self.getDiagAsympPhase(diagP)
            self.lines2 += self.subplot2.plot(lstX, lstY ,
                                        color = coul, 
                                        linewidth = max(1, width/2), 
                                        linestyle = style,
                                        zorder = globdef.ZORDER_MAXI-i,
                                        visible = self.tracerAsymp)
            
            
        if self.zoomAuto:
            self.subplot1.relim()
            self.subplot1.autoscale_view(tight=False, scalex=False, scaley=True)
            self.subplot2.relim()
            self.subplot2.autoscale_view(tight=False, scalex=False, scaley=True)

#        print "lim"
#        print self.subplot1.get_xlim()
#        print self.subplot1.get_ylim()
#        print self.subplot2.get_xlim()
#        print self.subplot2.get_ylim()
#        print self.subplot2.get_xscale()
#        print self.subplot2.get_yscale()
        
        #
        # Propriétés des marges de stabilité
        #
        if "marges" in self.contenu.keys():
            self.tracerMarges(self.contenu["marges"])
        else:
            self.effacerMarges()
#        
#        #
#        # Propriétés des expressions des FT
#        #
#        self.afficherExpressions(self.afficherExpress)

        if self.zoomAuto or not self.rangesAJour or self.miseAJour:
            self.drawCanvas()
        else:
            self.drawArtists()
        
    ######################################################################################################    
    def getContenuExport(self):
        contenu = []
        images = []
        
        if "diagReel" in self.contenu.keys():
            lR = self.contenu["diagReel"]
        else:
            lR = ([],[])
            
        if "diagAsymp" in self.contenu.keys():
            lA = self.contenu["diagAsymp"]
        else:
            lA = ([],[])
        
        contenuGain = {"diagA" : lA[0],
                       "diagR" : lR[0]}
        
        contenuPhas = {"diagA" : lA[1],
                       "diagR" : lR[1]}
                
        #
        # Propriétés des diagrammes
        #
        for i, ft in enumerate(self.lstFTNum):
            diagG = contenuGain["diagR"][i]
            diagP = contenuPhas["diagR"][i]
            contenu.append(("Pulsation", diagG.reponse[0])) 
            contenu.append(("Gain", diagG.reponse[1])) 
            contenu.append(("Phase", diagP.reponse[1])) 
            
            diagG = contenuGain["diagA"][i]
            lstX, lstY = self.getDiagAsympGain(diagG)
            contenu.append(("Asymp Puls", lstX)) 
            contenu.append(("Asymp Gain", lstY)) 
            
            diagP = contenuPhas["diagA"][i]
            lstX, lstY = self.getDiagAsympPhase(diagP)
            contenu.append(("Asymp Puls", lstX)) 
            contenu.append(("Asymp Phase", lstY)) 
            
            file, h = getFileBitmap(ft, i)
            
            images.append((file,i*7, h))
            
        return contenu, images
        
    ######################################################################################################    
    def sauveBackGround(self):
        self.background2 = self.canvas.copy_from_bbox(self.subplot2.bbox)
        self.background1 = self.canvas.copy_from_bbox(self.subplot1.bbox)
        self.backgroundFig = self.canvas.copy_from_bbox(self.figure.bbox)
        
    
        
    ######################################################################################################
    def restoreBackground(self, ax = None):
        if ax == self.subplot1:
            self.canvas.restore_region(self.background1)
        elif ax == self.subplot2:
            self.canvas.restore_region(self.background2)
        else:
            self.canvas.restore_region(self.backgroundFig)

    
        
    #####################################################################################################
    def tracerMarges(self, marges):
#        print "Tracé Marges", self.nom#, marges.Phi0, marges.HdB180

        
        #
        # Marge de Phase
        #
        if marges.Om0 != None:
            setp(self.ligneMargePhase, xdata = array([marges.Om0]), 
                 #ydata = self.subplot1.get_ylim(),
                 visible = True)

            xy = [(marges.Om0, marges.Phi0), (marges.Om0, float64(-180.0))] 
            xy.extend(self.getXY_Fleche(xy[0], xy[1], ax = self.subplot2))
            xy = array(xy).transpose()
            setp(self.margePhase, data = xy,
                 visible = True, color = marges.getCoulP())

        else:
            setp(self.margePhase, visible = False)
            self.ligneMargePhase.set_visible(False)
        
        #
        # Marge de Gain
        #
        if marges.Om180 != None:
            setp(self.ligneMargeGain, xdata = array([marges.Om180]), 
                 #ydata = self.subplot2.get_ylim(),
                 visible = True)
            
            xy = [(marges.Om180, float64(0.0)), (marges.Om180, marges.HdB180)]
            xy.extend(self.getXY_Fleche(xy[0], xy[1]))
            xy = array(xy).transpose()
            setp(self.margeGain, data = xy,
                 visible = True, color = marges.getCoulG())
        else:
            self.ligneMargeGain.set_visible(False)
            setp(self.margeGain, visible = False)

#        self.lstArtists.extend(self.margePhase)
#        self.lstArtists.extend(self.margeGain)
#        self.lstArtists.append(self.ligneMargeGain)
#        self.lstArtists.append(self.ligneMargePhase)



    #####################################################################################################
    def effacerMarges(self):
        self.ligneMargeGain.set_visible(False)
        setp(self.margePhase, visible = False)
        setp(self.margeGain, visible = False)
        self.ligneMargePhase.set_visible(False)

    ######################################################################################################
    def getReponse(self, ft):
        return ft.getReponseHarmoniqueBode()

    
##########################################################################################################
#
#  Zone graphique Black
#
##########################################################################################################
class ZoneGraphBlack(ZoneGraphBase):
    def __init__(self, parent, zoneOutils, nom = "Black"):
        ZoneGraphBase.__init__(self, parent, zoneOutils, nom)
        
        self.estFTBF = False
        self.nom = nom
        
        
        
        #
        # Définition des Artists MPL
        #
        self.initDraw()
        self.modifierTaillePolices()
        self.modifierAntialiased()
        
        #
        # Variables d'état de visualisation spécifiques
        #
        self.tracerIsoGP = globdef.TRACER_ISO
        self.densite = 1.
        self.listeIsoPhasesVisibles = listeIsoPhases

        # Premier Tracé
        wx.CallAfter(self.setTracerIsoGP, True)
        

        
        
        
    ######################################################################################################
    def initDraw(self):
#        print "initdraw Black"
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)

        #
        # Tracé de la Grille
        #
        coul = globdef.FORM_GRILLE.get_coul_str()
        self.subplot.grid(globdef.TRACER_GRILLE, color = coul, zorder = 0, 
                          lw = globdef.FORM_GRILLE.epais, 
                          ls = globdef.FORM_GRILLE.styl)#, visible = globdef.TRACER_GRILLE)
        
        
        #
        # Définition des deux "axes"
        #
        self.subplot.set_ylabel(_("Gain (dB)"))
        self.subplot.set_xlabel(_("Phase (deg)"))
        self.subplot.autoscale_view(tight=True, scalex=False, scaley=True)
        
        self.subplot.xaxis.set_major_formatter(DegreeFormatter())
        self.subplot.xaxis.set_major_locator(MaxNLocator(nbins = 9, steps = [1.0, 1.5, 3.0, 4.5, 9.0],
                                                          integer = True))
        
        #
        # Pré définition des Tracés des FT
        #
        self.lines = []
        
        # Le label de la FT apparaissant au passage de la souris
        self.labelFT = self.subplot.text(1, 0, "", visible = False)
        
        #
        # Prédéfinition des expressions des FT
        #
        self.exprFT = []
        
        #
        # Définition des axes "origine"
        #
        self.subplot.axvline(0, linewidth=1, color='k')
        self.subplot.axhline(0, linewidth=1, color='k')
        
        
        #
        # Définition des isogains
        #
        self.nappeIsoGains = getIsoGains()
        G,P,iso = self.nappeIsoGains
        matplotlib.rcParams['contour.negative_linestyle'] = 'solid'
        
        self.isoGains = self.subplot.contour(P,G,iso, listeIsoGains ,  
                                               colors = globdef.FORM_ISOGAIN.get_coul_str(), 
                                               ls = globdef.FORM_ISOGAIN.styl,
                                               linewidth = globdef.FORM_ISOGAIN.epais, zorder = 1)#,
#                                               visible = False)
       
        self.labelIsoGain = self.subplot.text(1, 0, "", visible = False, 
                                              color = globdef.COUL_LABEL_ISOGAIN, zorder = 2)
        
        #
        # Définition des isophases
        #
        self.segmentsIsoPhases = getIsoPhases(globdef.FORM_ISOPHASE.get_coul_str())
        self.isoPhases = LineCollection(self.segmentsIsoPhases, linewidth = globdef.FORM_ISOPHASE.epais, 
                                        colors = globdef.FORM_ISOPHASE.get_coul_str(), 
                                        linestyle = globdef.FORM_ISOPHASE.styl, zorder = 1)
        self.subplot.add_collection(self.isoPhases)
        self.labelIsoPhase = self.subplot.text(1, 0, "", visible = False, 
                                               color = globdef.COUL_LABEL_ISOPHASE, zorder = 2)
        
        
        #
        # Définition des lignes de marges
        #
        self.margeGain = self.subplot.plot([0, 0], color = globdef.COUL_MARGE_GAIN, 
                                           linewidth = globdef.EP_MARGES,
                                           visible = False)
        setp(self.margeGain, transform = self.subplot.transData)
        
        self.margePhase = self.subplot.plot([0, 0], color = globdef.COUL_MARGE_PHAS, 
                                            linewidth = globdef.EP_MARGES,
                                            visible = False)
        setp(self.margePhase, transform = self.subplot.transData)
#
#        self.isoGainsCurseur = self.subplot.contour(P,G,iso, [1] , zorder = globdef.ZORDER_MAXI-2,  
#                                                        linewidth = 0.5, visible = False)
#        self.lstArtists.extend(self.margePhase)
#        self.lstArtists.extend(self.margeGain)
        
        #
        # Définition du point critique et limite de stabilité
        #
        coul = globdef.COUL_PT_CRITIQUE
        self.ptCritique = self.subplot.plot([-180], [0], marker = 'o', mfc = coul)
        self.labelptCritique = self.subplot.text(1, 0, "", visible = False, 
                                                 color = coul, zorder = 2)
        self.limiteLambda = self.subplot.contour(P,G,iso, [2.3], colors = coul, linewidth = 0.5)
        self.labelLambda = self.subplot.clabel(self.limiteLambda, inline = 0, inline_spacing = 1, fmt = '%1.1f')
        #print('labelLambda', self.labelLambda)
        #
        # Définition des flèches sur les courbes
        #
        self.fleche = []
        
        
#        self.lstArtists.extend(self.fleche)
        
#        for a in self.lstArtists:
#            a.set_animated(True)
            
        try:
            self.calculerMargesFigure()
        except:
            pass
        
        
    ######################################################################################################
    def modifierTaillePolices(self):
        setp(self.subplot.get_xaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        setp(self.subplot.get_yaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        
        setp(self.subplot.get_yaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        setp(self.subplot.get_xaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        
        setp(self.labelFT, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        
        for e in self.exprFT:
            setp(e, fontsize = self.fontSizes["FONT_SIZE_EXPR"])
            
        setp(self.labelIsoGain, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        setp(self.labelIsoPhase, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        setp(self.labelLambda, fontsize = self.fontSizes["FONT_SIZE_LABEL"])

        
    # Gestion du curseur ################################################################################
    def setCurseur(self, etat):
        if self.curseur != etat:
            self.curseurFixe = False
            self.curseur = etat
            
            if not etat:
                self.setCurseurOff()
                
            else:
                self.sauveBackGroundFig()
                coul = globdef.COUL_TEXT_CURSEUR
                size = globdef.FONT_SIZE_CURSEUR
                halign = 'center'
                bgcolor = globdef.COUL_BLANC
                
                bbox = dict(facecolor = bgcolor, alpha = 0.7, 
                            edgecolor = "none", linewidth = 2.0,
                            zorder = globdef.ZORDER_MAXI)
                
                # Le texte sur le curseur de la souris
                self.txtCurs = self.subplot.text(1.0, 0.0, "", visible = False, color = coul,
                                                 fontsize = size, horizontalalignment = halign,
                                                 bbox = bbox)
                self.listeArtistsCurseur = [self.txtCurs]
                
                # Les isophases "curseur"
                self.isoPCurs = []
                self.labelIsoPCurs = []
                
                for i in range(len(self.lstFTNum)):
                    self.isoPCurs += self.subplot.plot([0], [1], visible = False, zorder = 1)
                    self.labelIsoPCurs.append(self.subplot.text(1.0, 0.0, "", visible = False,
                                                            fontsize = size, horizontalalignment = halign, 
                                                            transform = self.subplot.transData))
#                    self.labelIsoGCurs.append(self.subplot.text(1.0, 0.0, "", visible = False,
#                                                            fontsize = size, horizontalalignment = halign, 
#                                                            transform = self.subplot.transData))
                    
                self.listeArtistsCurseur.extend(self.isoPCurs)
                self.listeArtistsCurseur.extend(self.labelIsoPCurs)
                
#                self.listeArtistsCurseur.append(self.labelIsoGCurs)
                
                
                
                if self.valCurseurSurCote:
                    #                    
                    # Les valeurs de gain et de phase
                    #
                    self.tickGain, self.tickPhas = [], []
                    for i in range(len(self.lstFTNum)):
                        coul = self.lstCoul[i].get_coul_str()
                        tickGain = YTick(self.subplot, 1.0, gridOn = True)
                        tickPhas = XTick(self.subplot, 1.0, gridOn = True)
                        for t in [tickGain, tickPhas]:
                            t.gridline.set_color(coul)
                            t.gridline.set_linestyle('-')
                            t.label1.set_size(globdef.FONT_SIZE_GRAD)
                            t.label1.set_backgroundcolor(self.figure.get_facecolor())
                            t.label1.set_color(coul)
                        self.tickGain.append(tickGain)
                        self.tickPhas.append(tickPhas)
                        
                    
                    self.listeArtistsCurseur.extend(self.tickGain)
                    self.listeArtistsCurseur.extend(self.tickPhas)
                    
                else:
                    #
                    # Les lignes horizontales et verticales
                    #
                    self.hline, self.vline = [], []
                    for i in range(len(self.lstFTNum)):
                        self.vline.append(self.subplot.axvline(1.0, 0.0, 1.0))
                        self.hline.append(self.subplot.axhline(0.0, 0.0, 1.0))
            
                    #
                    # Les textes sur les courbes
                    #
                    self.txtCursGP = []
                    for i in range(len(self.lstFTNum)):
                        self.txtCursGP.append(self.subplot.text(1.0, 0.0, "", visible = False, color = coul,
                                                       fontsize = size, horizontalalignment = halign,
                                                       bbox = bbox))
                    
                    self.listeArtistsCurseur.extend(self.hline)
                    self.listeArtistsCurseur.extend(self.vline)
                    self.listeArtistsCurseur.extend(self.txtCursGP)
                    
    ######################################################################################################
    def setCouleurs(self):
        for s in self.getsubplots():
            s.grid(self.tracerGrille, color = globdef.FORM_GRILLE.get_coul_str(),
                   lw = globdef.FORM_GRILLE.epais,
                   ls = globdef.FORM_GRILLE.styl)   
      
        for m in self.margeGain:
            m.set_color(globdef.COUL_MARGE_GAIN)
        for m in self.margePhase:
            m.set_color(globdef.COUL_MARGE_PHAS)
    
        self.isoPhases.set_color(globdef.FORM_ISOPHASE.get_coul_str())
        self.isoPhases.set_linestyle(globdef.FORM_ISOPHASE.styl)
        self.isoPhases.set_linewidth(globdef.FORM_ISOPHASE.epais)
        self.isoPhases.update_scalarmappable()
        
        self.isoGains.set_color(globdef.FORM_ISOGAIN.get_coul_str())
        self.isoGains.set_linestyle(globdef.FORM_ISOGAIN.styl)
        self.isoGains.set_linewidth(globdef.FORM_ISOGAIN.epais)
        self.isoGains.update_scalarmappable()

        # for i in self.isoGains.collections:
        #     i.set_color(globdef.FORM_ISOGAIN.get_coul_str())
        #     i.set_linestyle(globdef.FORM_ISOGAIN.styl)
        #     i.set_linewidth(globdef.FORM_ISOGAIN.epais)
        #     i.update_scalarmappable()
        
        globdef.COUL_LABEL_ISOPHASE = globdef.FORM_ISOPHASE.get_coul_str()
        globdef.COUL_LABEL_ISOGAIN = globdef.FORM_ISOGAIN.get_coul_str()
        self.labelIsoPhase.set_color(globdef.COUL_LABEL_ISOPHASE)
        self.labelIsoGain.set_color(globdef.COUL_LABEL_ISOGAIN)
        
        self.ptCritique[0].set_mfc(globdef.COUL_PT_CRITIQUE)

        self.limiteLambda.set_color(globdef.COUL_PT_CRITIQUE)
        self.limiteLambda.update_scalarmappable()
        # for i in self.limiteLambda.collections:
        #     i.set_color(globdef.COUL_PT_CRITIQUE)
        #     i.update_scalarmappable()
        for l in self.labelLambda:
            l.set_color(globdef.COUL_PT_CRITIQUE)
        
#        self.drawCanvas()
        
        
    ######################################################################################################
    def effacerLabels(self):
        self.canvas.restore_region(self.background)
            
        # Effacement labelIso
        setp(self.labelIsoGain, x = 0, y = 0, text = "", visible = False)
        setp(self.labelIsoPhase, x = 0, y = 0, text = "", visible = False)
        setp(self.labelptCritique, x = 0, y = 0, text = "", visible = False)
        
        self.subplot.draw_artist(self.labelIsoGain)
        self.subplot.draw_artist(self.labelIsoPhase)
        
        setp(self.labelFT, visible = False)
        self.subplot.draw_artist(self.labelFT)
                    
        self.canvas.blit(self.subplot.bbox)
                     


#    ######################################################################################################
#    def effacerCurseur(self):
#        self.canvas.restore_region(self.background)
#        for a in self.listeArtistsCurseur:
#            a.set_visible(False)
#            a.get_axes().draw_artist(a)
#            
##        # Effacement curseur
##        if self.curseur and not self.curseurFixe:
##            setp(self.txtCurs, visible = False)
##            self.subplot.draw_artist(self.txtCurs)
##            for i, ft in enumerate(self.txtCursGP):
##                setp(self.txtCursGP[i], visible = False)
##                self.subplot.draw_artist(self.txtCursGP[i])
##            
##            for i, ft in enumerate(self.vline):
##                setp(self.vline[i], visible = False)
##                self.subplot.draw_artist(self.vline[i])
##                
##            for i, ft in enumerate(self.hline):
##                setp(self.hline[i], visible = False)
##                self.subplot.draw_artist(self.hline[i])
#        
#        # Effacement des Iso "curseur"
#        if hasattr(self, "isoGainsCurseur"):
#            for i in self.isoGainsCurseur.collections: 
#                i.set_visible(False)
#                    
#        if hasattr(self, "isoPhasesCurseur"):
#            self.isoPhasesCurseur.remove()
#
#        self.canvas.blit(self.subplot.bbox)
        
        
    def Detection(self, event):
        """
        """
        #print("Detection", event)
        x, y = event.x, event.y
        #print(x, y)
        detect = {"FT": None,
                  "EX": None,
                  "IP": None,
                  "IG": None,
                  "PC": None,
                  "MA": None}
        
        # Détection des FT
        continuer = True
        i = 0
        while continuer:
            if i >= len(self.lstFTNum):
                continuer = False
            elif self.lines[i].contains(event)[0]:
                continuer = False
                detect["FT"] = i
            i += 1
        if detect["FT"] != None: return detect
    
        
    
        # Détection des expressions
        continuer = True
        i = 0
        while continuer:
            if i >= len(self.lstFTNum):
                continuer = False
            elif self.exprFT[i].contains(event)[0]:
                continuer = False
                detect["EX"] = i
            i += 1
        if detect["EX"] != None: return detect
    
        
        # Détection des marges
        if "marges" in self.contenu:
            if self.margeGain[0].contains(event)[0]:
                detect["MA"] = 'g'
            elif self.margePhase[0].contains(event)[0]:
                detect["MA"] = 'p'
            elif hasattr(self, "isoGainsMarge") and self.isoGainsMarge.contains(event)[0]: 
                detect["MA"] = 's'
            if detect["MA"] != None: return detect
        
        
        # Détection des IsosGains
        #print(self.isoGains.find_nearest_contour(x, y))
        c, d = self.isoGains.contains(event)
        if c:
            detect["IG"] = d['ind'][0]
        # continuer = True
        # i = 0
        # while continuer:
        #     if i >= len(self.isoGains.collections):
        #         continuer = False
        #     else:
        #         self.isoGains.collections[i]._picker = True
        #         if self.isoGains.collections[i].contains(event)[0]:
        #             continuer = False
        #             detect["IG"] = i
        #     #print self.isoGains.collections[i]._picker
        #     i += 1
        if detect["IG"] != None: return detect
    

        # Détection des IsosPhases
        self.isoPhases._picker = True
        a, numIso = self.isoPhases.contains(event)
        if a:
            detect["IP"] = numIso['ind'][0]
        if detect["IP"] != None: return detect    
        
    
        # Détection du point critique
        self.ptCritique[0]._picker = True
        a, numIso = self.ptCritique[0].contains(event)
        
        # self.limiteLambda.collections[0]._picker = True
        self.limiteLambda._picker = True
        # b, numiso = self.limiteLambda.collections[0].contains(event)
        b, numiso = self.limiteLambda.contains(event)
        if a:
            detect["PC"] = 1
        elif b:
            detect["PC"] = 2
        if detect["PC"] != None: return detect
        
        
        return detect
            
    ######################################################################################################
    def OnMoveDefaut(self, _xdata, _ydata, axe, event = None):
        if self.mouseInfo != None:
            self.moveExpression(event)

        else:
            if _xdata == None or _ydata == None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
                self.effacerLabels()
                return
            
            with errstate(invalid='ignore'):
                detect = self.Detection(event)
            
            # Affichage ...
            if detect["EX"] != None:
                self.effacerLabels()
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_MAIN))
                self.context = "E"+str(detect["EX"])
                
            elif detect["FT"] != None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
                coul = self.lstCoul[detect["FT"]].get_coul_str()
                setp(self.labelFT, text = r"$"+self.lstFTNum[detect["FT"]].nom + " $",
                     x = _xdata, y = _ydata, visible = True, color = coul)
                self.draw_artists([self.labelFT])
                self.context = "F"+str(detect["FT"])

            elif detect["IG"] != None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
                setp(self.labelIsoGain, text = " " + str(listeIsoGains[detect["IG"]]) + " dB",
                     x = _xdata, y = _ydata, visible = True)
                self.draw_artists([self.labelIsoGain])
                self.context = "G"+str(detect["IG"])

            elif detect["IP"] != None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
                setp(self.labelIsoPhase, text = " " + str(self.listeIsoPhasesVisibles[detect["IP"]]) + " °",
                     x = _xdata, y = _ydata, visible = True)
                self.draw_artists([self.labelIsoPhase])
                self.context = "P"+str(detect["IP"])
                
            elif detect["PC"] != None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
                if detect["PC"] == 1:
                    text = _("Point critique")
                else:
                    text = r"$"+_(u'Limite')+ r"\/\lambda$"
                setp(self.labelptCritique, text = text,
                     x = _xdata, y = _ydata, visible = True)
                self.draw_artists([self.labelptCritique])
                self.context = "C"

            elif detect["MA"] != None:
                marges = self.contenu["marges"]
#                print marges
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
#                coul = self.lstCoul[detect["FT"]].get_coul_str()
                if detect["MA"] == 'g':
                    texte = marges.getMathTexteMg()
                    coul = marges.getCoulG()
                elif detect["MA"] == 'p':
                    texte = marges.getMathTexteMp()
                    coul = marges.getCoulP()
                else:
                    texte = marges.getMathTexteQ()
                    coul = marges.getCoulQ()
                
                
                setp(self.labelFT, text = texte,
                     x = _xdata, y = _ydata, visible = True,
                     color = coul)
                
#                self.artists_visibles.append(labelFT, axe)
                self.draw_artists([self.labelFT], axe)
                self.context = "M"+str(detect["MA"])
                
            else:
                self.effacerLabels()
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
                self.context = ""

    
    
    
    ######################################################################################################
    def OnMoveEchelle(self, _x, _y, axe):
        if self.mouseInfo != None:
            dx = _x-self.mouseInfo[0]
            rangeX = self.mouseInfo[2][0]
            coefX = 1.0 * dx /100
            rangeX = self.getNewEchelleAxe(coefX, rangeX)

#            deltaX = rangeX[1] - rangeX[0]
#            ecartX = deltaX * coefX /2
#            rangeX = [rangeX[0] - ecartX, rangeX[1] + ecartX]

            
            dy = _y-self.mouseInfo[1]
            rangeY = self.mouseInfo[2][1]
            coefY = 1.0 * dy /100
            rangeY = self.getNewEchelleAxe(coefY, rangeY)

#            deltaY = rangeY[1] - rangeY[0]
#            ecartY = deltaY * coefY /2
#            rangeY = [rangeY[0] - ecartY, rangeY[1] + ecartY]

            
            self.calculerEtRedessiner(rangeX, rangeY, initMousInfo = False)
        

    ######################################################################################################
    def OnMoveCurseur(self, _xdata, _ydata, axe):

        self.restoreBackgroundFig()
        
        # Calcul de la valeur de Omega
        xl = self.subplot.get_xlim()
        pc = (xl[1] - _xdata)/ (xl[1] - xl[0])
        logOm = (log10(self.rangeOm[1]) - log10(self.rangeOm[0]))*pc + log10(self.rangeOm[0])
        Om = 10**logOm
        
        
        
        #
        # Les isoPhases ...
        #
        for i, ft in enumerate(self.lstFTNum):
            coul = self.lstCoul[i].get_coul_str()
            if self.HC == i:
                FTBF = ft.FTBF()
                G = FTBF.HdB(Om)
                P = FTBF.Phi(Om)
                valIsoGainsCurseur = [G]
                coulIsoGainsCurseur = [coul]
                
                xp, yp  = getIsoPhasePlot(P, 34)
                setp(self.isoPCurs[i], xdata = xp, ydata = yp, visible = True, color = coul, zorder = globdef.ZORDER_MAXI-i-2)
                
                n = len(xp)-1
                continuer = True
                x, y = None, None
                while continuer:
                    if n < 0:
                        continuer = False
                    elif    xp[n] > self.getxlim()[0] and xp[n] < self.getxlim()[1] \
                        and yp[n] > self.getylim()[0] and yp[n] < self.getylim()[1]:
                        x = xp[n]
                        y = yp[n]
                        continuer = False
                    else:
                        n += -1
                
                if x != None:
                    setp(self.labelIsoPCurs[i], x = x, y = y, visible = True, color = coul,
                         text = r"$"+fonctions.strSc(P)+r" °$")
                    self.subplot.draw_artist(self.labelIsoPCurs[i])
                self.subplot.draw_artist(self.isoPCurs[i])
                
                # Le label de l'isogain
#                y = getValIsoGain(xl[1],G)

#                setp(self.labelIsoGCurs[0],x = xl[1], y = y, visible = True, color = coul,
#                         text = r"$"+fonctions.strSc(G)+r" dB$")
                
        #
        # Les IsoGains ...
        #
          
        # Effacement des anciens isoGains
        if hasattr(self, "isoGainsCurseur"):
            self.isoGainsCurseur.remove()
            # for i in self.isoGainsCurseur.collections: 
            #     i.remove()
                
        if hasattr(self, "labelIsoGCurs"):
            for i in self.labelIsoGCurs: 
                i.remove()
                
        if self.HC != None:
            # Définition des nouveaux ...
            G,P,iso = self.nappeIsoGains
            G,P,iso = getIsoGains(self.subplot.get_xlim(), self.subplot.get_ylim())
            self.isoGainsCurseur = self.subplot.contour(P,G,iso, valIsoGainsCurseur , zorder = globdef.ZORDER_MAXI-2,  
                                                        linewidth = 0.5, colors = coulIsoGainsCurseur)
            
            self.labelIsoGCurs = self.subplot.clabel(self.isoGainsCurseur, 
                                                     fontsize = globdef.FONT_SIZE_CURSEUR)
            
            
            # for i in self.isoGainsCurseur.collections + self.labelIsoGCurs: 
            #     axe.draw_artist(i)
            for i in self.labelIsoGCurs: 
                axe.draw_artist(i)
            self.isoGainsCurseur.draw()
                
        if self.valCurseurSurCote:
            #
            # Les valeurs de gain et de phase
            #        
            for i, ft in enumerate(self.lstFTNum):
                _yG = ft.HdB(Om)
                _yP = ft.Phi(Om)
                self.tickGain[i].update_position(_yG)
                self.tickGain[i].label1.set_text(fonctions.strSc(_yG))
                self.tickGain[i].set_visible(True)
                
                self.tickPhas[i].update_position(_yP)
                self.tickPhas[i].label1.set_text(fonctions.strSc(_yP))
                self.tickPhas[i].set_visible(True)
                
                self.subplot.draw_artist(self.tickGain[i])
                self.subplot.draw_artist(self.tickPhas[i])

            
            
            
        else:
            e = 30
    
            ymoy = (self.subplot.get_ylim()[0] + self.subplot.get_ylim()[1])/2
#            xmoy = (self.subplot.get_xlim()[0] + self.subplot.get_xlim()[1])/2

            for i, ft in enumerate(self.lstFTNum):
                _x = ft.Phi(Om)
                _y = ft.HdB(Om)
                coul = self.lstCoul[i].get_coul_str()
                
                # Lignes verticales
                setp(self.vline[i], xdata = array([_x]), color = coul, visible = True)
                self.subplot.draw_artist(self.vline[i])
    
                # Lignes horizontales
                setp(self.hline[i], ydata = array([_y]), color = coul, visible = True)
                self.subplot.draw_artist(self.hline[i])
 
                # Valeurs gain et phase
                dHdP = ft.deriveedHdP(ft.HdB, ft.Phi, Om)# * coefG
                va, ha, s1, s2 = getAlignment(dHdP, _y < ymoy)
                setp(self.txtCursGP[i], x = _x , y = _y ,
                     horizontalalignment = ha, verticalalignment = va, zorder = globdef.ZORDER_MAXI-i+1,
                     text = s1+r"$\varphi="+fonctions.strSc(_x)+" à $"+"\n"+r"$H_{dB}"+fonctions.strSc(_y)+" dB$"+s2, visible = True)
                self.subplot.draw_artist(self.txtCursGP[i])
            
            
        # Affichage de Omega sur le curseur
        setp(self.txtCurs, position = (_xdata, _ydata),
             text = r"$\omega="+fonctions.strSc(Om)+r" rad/s$"+"\n", visible = True)
        axe.draw_artist(self.txtCurs)
        
        if self.valCurseurSurCote:
            self.canvas.blit()
        else:
            self.canvas.blit(self.subplot.bbox)
            
        # Pour synchronisation avec réponse temporelle
        if self.estFTBF:
#            self.pulsationCurseur = Om
            self.zoneOutils.app.winReponse.SynchroniserPulsationSinus(Om)


#    ######################################################################################################
#    def OnMove(self, event):
#        
#        _xdata, _ydata = event.xdata, event.ydata
##        if _xdata == None or _ydata == None:
###            self.canvas.SetCursor(wx.StockCursor(CURSEUR_DEFAUT))
##            self.effacerInfos()
##            return
#        
#        _x, _y = event.x, event.y
#        
#        liste = self.figure.hitlist(event)
#        
#        axe = event.inaxes
#            
#        #
#        # Mode Curseur
#        #
#        if self.curseur and not self.curseurFixe:
##            coul = COUL_TEXT_CURSEUR.GetAsString(wx.C2S_HTML_SYNTAX)
##            size = 9
##            halign = 'center'
##            bgcolor = COUL_BLANC.GetAsString(wx.C2S_HTML_SYNTAX)
#            
#            # restore the clean slate background
#            self.canvas.restore_region(self.background)
#
##                if txtcurs != None:
##                    txtcurs.remove()
##                txtcurs = axe.annotate(fonctions.strSc(_x), (_x, _y), xytext = (0,8), color = coul,
##                                       fontsize = size, horizontalalignment = halign,
##                                       backgroundcolor = bgcolor, textcoords='offset points')
#            xl = self.subplot.get_xlim()
#            pc = (xl[1] - _xdata)/ (xl[1] - xl[0])
#            logOm = (log10(self.rangeOm[1]) - log10(self.rangeOm[0]))*pc + log10(self.rangeOm[0])
#            Om = 10**logOm
#            setp(self.txtCurs, position = (_xdata, _ydata),
#                 text = fonctions.strSc(Om)+" rad/s"+"\n", visible = True)
#
#            e = 30
#            
##                coefG = get_coefy(self.subplot1) / get_coefx(self.subplot1)
##                coefP = get_coefy(self.subplot2) / get_coefx(self.subplot2)

#
#            ymoy = (self.subplot.get_ylim()[0] + self.subplot.get_ylim()[1])/2
#            xmoy = (self.subplot.get_xlim()[0] + self.subplot.get_xlim()[1])/2
#            
##            if hasattr(self, "isoPhasesCurseur"):
##                for i in self.isoPhasesCurseur: 
##                    i.remove()
#                    
#            
#            valIsoGainsCurseur = []
#            coulIsoGainsCurseur = []
#            
#            for i, ft in enumerate(self.lstFTNum):
#                _x = ft.Phi(Om)
#                _y = ft.HdB(Om)
#                coul = self.lstCoul[i].GetAsString(wx.C2S_HTML_SYNTAX)
#                # Lignes verticales
#                setp(self.vline[i], xdata = array([_x]), color = coul, visible = True)
#                self.subplot.draw_artist(self.vline[i])
#
#                # Lignes horizontales
#                setp(self.hline[i], ydata = array([_y]), color = coul, visible = True)
#                self.subplot.draw_artist(self.hline[i])
#
#                # Valeur gain
#                dHdP = ft.deriveedHdP(ft.HdB, ft.Phi, Om)# * coefG
#                va, ha, s1, s2 = getAlignment(dHdP, _y < ymoy)
#                setp(self.txtCursGP[i], x = _x , y = _y ,
#                     horizontalalignment = ha, verticalalignment = va, zorder = ZORDER_MAXI-i+1,
#                     text = s1+fonctions.strSc(_x)+" à "+"\n"+fonctions.strSc(_y)+" dB "+s2, visible = True)
#                self.subplot.draw_artist(self.txtCursGP[i])
#                
#                # Les isoPhases et isoGains ...
#                if self.HC and i == 0:
#                    FTBF = ft.FTBF()
#                    FTBF.getReponseHarmoniqueGainPhase(calcul.getPulsations(self.rangeOm))
#                    G = FTBF.HdB(Om)
#                    P = FTBF.Phi(Om)
#                    valIsoGainsCurseur = [G]
#                    coulIsoGainsCurseur = [coul]
#                    
#                    xp, yp  = getIsoPhasePlot(P, 34)
#                    setp(self.isoPCurs[i], xdata = xp, ydata = yp, visible = True, color = coul, zorder = ZORDER_MAXI)
#                    self.subplot.draw_artist(self.isoPCurs[i])
#                
#            # Effacement des anciens isoGains
#            if hasattr(self, "isoGainsCurseur"):
#                for i in self.isoGainsCurseur.collections: 
#                    i.remove()
#            if self.HC:
#                # Définition des nouveaux ...
#                G,P,iso = self.nappeIsoGains
#                self.isoGainsCurseur = self.subplot.contour(P,G,iso, valIsoGainsCurseur , zorder = ZORDER_MAXI,  
#                                                            linewidth = 0.5, colors = coulIsoGainsCurseur)
#                for i in self.isoGainsCurseur.collections: 
#                    axe.draw_artist(i)
#            
#            axe.draw_artist(self.txtCurs)
#            self.canvas.blit(self.subplot.bbox)
#
#        #
#        # Mode déplacer
#        #
#        elif self.deplacer:
#            return    
#        
#        #
#        # Mode zoom
#        #
#        elif self.zoomPlus:
#            return
#        
#        #
#        # Mode Echelle
#        #
#        elif self.echelle:
#            _x, _y = event.x, event.y 
#            if self.mouseInfo != None:
#                dx = _x-self.mouseInfo[0]
#                rangeX = self.mouseInfo[2][0]
#                coefX = 1.0 * dx /100

#                deltaX = rangeX[1] - rangeX[0]
#                ecartX = deltaX * coefX /2
#                rangeX = [rangeX[0] - ecartX, rangeX[1] + ecartX]

#                
#                dy = _y-self.mouseInfo[1]
#                rangeY = self.mouseInfo[2][1]
#                coefY = 1.0 * dy /100

#                deltaY = rangeY[1] - rangeY[0]
#                ecartY = deltaY * coefY /2
#                rangeY = [rangeY[0] - ecartY, rangeY[1] + ecartY]

#                
#                self.calculerEtRedessiner(rangeX, rangeY, initMousInfo = False)
#        
#        #
#        # Mode Curseur fixe
#        #
#        elif self.curseurFixe:
#            return
#        
#        #
#        # Mode défaut
#        #
#        else:
#            if self.mouseInfo != None:
#                self.moveExpression(event)
#
#            else:
#                # Détection des FT
#                numFT = None
#                continuer = True
#                i = 0
#                while continuer:
#                    if i >= len(self.lstFTNum):
#                        continuer = False
#                    elif self.lines[i] in liste:
#                        continuer = False
#                        numFT = i
#                    i += 1
#                    
#                # Détection des expressions
#                numExpr = None
#                continuer = True
#                i = 0
#                while continuer:
#                    if i >= len(self.lstFTNum):
#                        continuer = False
#                    elif self.exprFT[i] in liste:
#                        continuer = False
#                        numExpr = i
#                    i += 1
#                    
##                if numExpr != None:
##                    self.canvas.SetCursor(wx.StockCursor(CURSEUR_MAIN))
##                else:
##                    self.canvas.SetCursor(wx.StockCursor(CURSEUR_DEFAUT))
#                
#                # Détection des IsosGains
#                numIsoG = None
#                continuer = True
#                i = 0
#                while continuer:
#                    if i >= len(self.isoGains.collections):
#                        continuer = False
#                    elif self.isoGains.collections[i] in liste:
#                        continuer = False
#                        numIsoG = i
#                    i += 1
#                    
#                # Détection des IsosPhases
#                numIsoP = None
#                a, numIso = self.isoPhases.contains(event)
#                if a:
#                    numIsoP = numIso['ind'][0]
#                
#                # Affichage ...
#                if numExpr != None:
#                    self.effacerInfos()
#                    self.canvas.SetCursor(wx.StockCursor(CURSEUR_MAIN))
#                    
#                elif numFT != None:
#                    self.canvas.SetCursor(wx.StockCursor(CURSEUR_ISO))
#                    coul = self.lstCoul[numFT].GetAsString(wx.C2S_HTML_SYNTAX)
#                    setp(self.labelFT, text = r"$"+self.lstFTNum[numFT].nom + " $",
#                         x = _xdata, y = _ydata, visible = True, color = coul)
#                    self.draw_artists([self.labelFT])
#
#                elif numIsoG != None:
#                    self.canvas.SetCursor(wx.StockCursor(CURSEUR_ISO))
#                    setp(self.labelIsoGain, text = " " + str(listeIsoGains[numIsoG]) + " dB",
#                         x = _xdata, y = _ydata, visible = True)
#                    self.draw_artists([self.labelIsoGain])
#
#                elif numIsoP != None:
#                    self.canvas.SetCursor(wx.StockCursor(CURSEUR_ISO))
#                    setp(self.labelIsoPhase, text = " " + str(listeIsoPhases[numIsoP]) + " °",
#                         x = _xdata, y = _ydata, visible = True)
#                    self.draw_artists([self.labelIsoPhase])
#
#                else:
#                    self.effacerInfos()
##                    self.canvas.restore_region(self.background)
#                    self.canvas.SetCursor(wx.StockCursor(CURSEUR_DEFAUT))
##                    setp(self.labelIsoGain, x = 0, y = 0, text = "", visible = False)
##                    setp(self.labelIsoPhase, x = 0, y = 0, text = "", visible = False)
###                    self.canvas.draw()
##                    self.subplot.draw_artist(self.labelIsoGain)
##                    self.subplot.draw_artist(self.labelIsoPhase)
##                    self.canvas.blit(self.subplot.bbox)
                    
                
#    def draw_artists(self, lstartists):
#        self.canvas.restore_region(self.background)
#        for a in lstartists:
#            self.subplot.draw_artist(a)
#        self.canvas.blit(self.subplot.bbox)
        
    
        
        
    ######################################################################################################
    def setTracerIsoGP(self, etat):
        self.tracerIsoGP = etat
        self.tracerIsoGainsPhases(etat)
        self.drawCanvas()
        
        
    ######################################################################################################
    def tracerIsoGainsPhases(self, etat):
        """ Trace les isoGains et les isoPhases sur le canvas
            en tenant compte de la densité (self.densite)
        """
        #
        # Répartition des isoGains
        #
        d = 1
        s=[]
        for _ in self.isoGains.get_paths():#collections: 
            if d >= self.densite:
                s += [True]
                d = 1
            else:
                s += [False]
                d += 1
        self.isoGains.set_visible(s)
            
        #
        # Répartition des isoPhases
        #
        if etat:
            d = 1
            segments = []
            phases = []
            for seg, pha in zip(self.segmentsIsoPhases, listeIsoPhases):
                if d >= self.densite:
                    segments.append(seg)
                    phases.append(pha)
                    d = 1
                else:
                    d += 1
                
            self.isoPhases.set_segments(segments)
            self.listeIsoPhasesVisibles = phases
        self.isoPhases.set_visible(etat)
        
        #
        # On redessine le canvas
        #
#        self.drawCanvas()

 

    def getRangeTotal(self, lstFTNum):
        """ Renvoie l'intervalle de pulsations Om 
            le mieux adapté
        """
        mini, maxi = [], []
        for i, ft in enumerate(lstFTNum):
            minmaxD = ft.getRangeDecade()
            mini.append(minmaxD[0])
            maxi.append(minmaxD[1])
        minmaxD = [min(mini), max(maxi)]
        minmax = ft.getRange(minmaxD)
        return minmax

    ######################################################################################################
    def getRangePulsation(self, lstFTNum, rangeX = [], rangeY = []):
        """ Renvoie les pulsations pour le calcul de la réponse
        """
        
        minmax = self.getRangeTotal(lstFTNum)
        
        if len(rangeX) == 0 or len(rangeY) == 0:
            pulsas = calcul.getPulsations(minmax)
        else:
            mini, maxi = [], []
            intMinGain, intMaxGain = [], []
            intMinPhas, intMaxPhas = [], []
            
            for i, ft in enumerate(lstFTNum):
                intMinGain += ft.getIntervalle(2, rangeY[0])
                intMaxGain += ft.getIntervalle(2, rangeY[1])
                intMinPhas += ft.getIntervalle(1, rangeX[0])
                intMaxPhas += ft.getIntervalle(1, rangeX[1])
                
#                tout = tout + intMinGain+intMaxGain+intMinPhas+intMaxPhas
            rangeOmGain = [min(intMinGain+intMaxGain), max(intMinGain+intMaxGain)]
            rangeOmPhas = [min(intMinPhas+intMaxPhas), max(intMinPhas+intMaxPhas)]
            
            mini = [rangeOmGain[0], rangeOmPhas[0], minmax[0]]
            maxi = [rangeOmGain[1], rangeOmPhas[1], minmax[1]]
            try:
                while True : mini.remove(None)
            except:
                pass  
            try:
                while True : maxi.remove(None)
            except:
                pass

            minmax = [max(mini), 
                      min(maxi)]

#            minmax = [min(tout, minmax[0]), max(tout, minmax[1])]

            pulsas = lstFTNum[0].getPulsations(minmax)
            
        self.rangeOm = minmax
        return pulsas
            
    ######################################################################################################
    def getListePulsations(self, lstFTNum, ax, raz = False):
        """ Renvoie la listes des pulsations pour le calcul de la réponse
            (calcul en fonction des intervalles définis par l'axe MPL <ax>)
            <raz> == True : on recalcule la réponse
        """
#        print "getListePulsations", raz
#        minmax = self.getRangeTotal(lstFTNum)

            
        minmax = [None, None]
        for ft in lstFTNum:
            if not hasattr(ft, 'reponseB') or raz:

                ft.getDiagBlack(self.getListePulsationAuto(lstFTNum), rapide = True)
#                ft.reponseB = ft.getReponseHarmoniqueBlack(self.getListePulsationAuto(lstFTNum))

            rangeOm = ft.getIntervallePulsMpl(ax, ft.reponseB)
#            print "   ",rangeOm
            if rangeOm[0] != None:
                minmax[0] = _m(minmax[0], rangeOm[0], min)
                minmax[1] = _m(minmax[1], rangeOm[1], max)
        
#        print "   ",minmax
        if None in minmax:
            return []

        self.rangeOm = minmax
        return calcul.getPulsations(minmax)


    ######################################################################################################
    def getListePulsationAuto(self, lstFTNum):
        """ Renvoie la listes des pulsations pour le calcul de la réponse
            (calcul automatique en fonction des cassures)
        """
        
        rangeOm = self.getRangeTotal(lstFTNum)
        pulsas = calcul.getPulsations(rangeOm)
        self.rangeOm = rangeOm
        return pulsas        
    
    
    ######################################################################################################
    def getDiagrammes(self, lstFTNum, pulsas, rapide = False):
        """ Renvoie tous les diagrammes de Black
        """
        # on construit les diagrammes
        lstDiag = []
        
        for i, ft in enumerate(lstFTNum):
            lstDiag.append(ft.getDiagBlack(pulsas, rapide))
            
        return lstDiag
    
    
    ######################################################################################################
    def getDiagrammesEtMarges(self, lstFTNum, marges, pulsas):
        """ Renvoie tous les diagrammes de Black
            et calcule les marges et le lambda
        """

        contenu = {"diagB" : self.getDiagrammes(lstFTNum, pulsas)}
        
        # On calcule les marges
#        if winMarges != None:
#            contenu["marges"] = winMarges.calculerMarges()
#            winMarges.MiseAJour()
            
            
        if marges != None:
            contenu["marges"] = marges
            contenu["lambda"] = lstFTNum[0].getLambda()

        return contenu


#    ######################################################################################################
#    def mettreAJourEtRedessiner(self, lstFTNum, lstCoul, winMarges, HC, poles = None):
#        self.mettreAJour(lstFTNum, lstCoul, winMarges, HC, poles)
#        self.calculerEtRedessinerRanges()
        
    
    ######################################################################################################
    def calculerEtRedessiner(self, rangeX = [], rangeY = [], initMousInfo = True):
        """ Calcul de intervalle des Omega ...
            ... recalcul des diagrammes ...
            ... et Tracé de tout ! """
            
        if initMousInfo:
            self.mouseInfo = None
            
#        print "Calculer et redessiner Black", rangeX , rangeY
        
        #
        # Determination des intervalles phase et gain
        #
            
        # Mémorisation des anciens ranges
        _rangeX = self.subplot.get_xlim()
        _rangeY = self.subplot.get_ylim()
        
        if self.zoomAuto:
            #
            # Calcul des mini maxi Automatique
            #

            # Obtention des diagrammes (juste pour le calcul des mini/maxi
            pulsas = self.getListePulsationAuto(self.lstFTNum)

            diag = self.getDiagrammes(self.lstFTNum, pulsas, rapide = True)
            
            _minX, _maxX, _minY, _maxY = [],[],[],[]
            
            for d in diag:
                minX, maxX, minY, maxY = self.getMinMaxReel(d, _rangeX[0], _rangeX[1], \
                                                               _rangeY[0], _rangeY[1])
                _minX.append(minX)
                _maxX.append(maxX)
                _minY.append(minY)
                _maxY.append(maxY)
            
            minX, maxX, minY, maxY = _min(_minX, _rangeX[0]), \
                                     _max(_maxX, _rangeX[1]), \
                                     _min(_minY, _rangeY[0]), \
                                     _max(_maxY, _rangeY[1])
            
            # On évite les intervalles nuls
            if minX == maxX:
                minX += -180.0
                maxX += 180.0
            if minY == maxY:
                minY += -1.0
                maxY += 1.0
            
            # On adopte les intervalles
            self.subplot.set_xlim([minX, maxX])
            self.subplot.set_ylim([minY, maxY])

        else:
            #
            # On regarde si les ranges ont changé
            #
            x1, x2 = self.subplot.get_xlim()
            y1, y2 = self.subplot.get_ylim()
            self.rangesAJour = rangeX is not None and rangeY is not None 
            self.rangesAJour = self.rangesAJour and \
                               (    (len(rangeX) == 0 or (x1 == rangeX[0] and x2 == rangeX[1])) \
                                and (len(rangeY) == 0 or (y1 == rangeY[0] and y2 == rangeY[1])))
    
            
            if rangeX != [] and rangeX is not None: # Est-ce encore utile ???
                self.subplot.set_xlim(rangeX)
                self.subplot.set_ylim(rangeY)
        
        
        #
        # Recalcul des diagrammes (plus sérré)
        #
        
        # Est-ce que les intervalles ont grandi depuis le dernier calcul des diagrammes ?
        raz =  self.subplot.get_xlim()[0] < _rangeX[0] \
            or self.subplot.get_xlim()[1] > _rangeX[1] \
            or self.subplot.get_ylim()[0] < _rangeY[0] \
            or self.subplot.get_ylim()[1] > _rangeY[1]
            
#        _rangeY = self.subplot.get_ylim()
        
        pulsas = self.getListePulsations(self.lstFTNum, self.subplot, raz)
        
        if len(pulsas) == 0: return
        
        self.contenu = self.getDiagrammesEtMarges(self.lstFTNum, self.marges, pulsas)

        # On garde ça pour le Tracé des flèches ...
        self.pulsas = pulsas
         
        
        # On vérifie si ça a changé ...
#        self.rangeModifie = _rangeX != self.graduations.axeX.range or _rangeY != self.graduations.axeY.range

        self.CalculerDensiteIso()
        self.tracerIsoGainsPhases(self.tracerIsoGP)
        
        self.TracerTout()
        
        
    #####################################################################################################    
    def CalculerDensiteIso(self):
        mini, maxi = self.subplot.get_xaxis().get_view_interval()
        self.densite = max(1.,(maxi-mini)/180)
       
    
    
    #####################################################################################################    
    def TracerTout(self):
        """ Tracé de tout 
        """
#        print "TracerTout", self.nom
        self.zoneOutils.activerCurseur(False)
        
        #
        # On efface les textes et les lignes
        #
#        for axe in self.getsubplots():
#            axe.texts = []
#            axe.lines = []
        for l in self.lines:
            l.remove()
            
        for f in self.fleche:
            f.remove()
            
#        self.lstArtists = []
        self.lines = []
        self.fleche = []
        
        #
        # Propriétés des diagrammes
        #
        for i in range(len(self.lstFTNum)):
            coul = self.lstCoul[i].get_coul_str()
            width = self.lstCoul[i].epais
            style = self.lstCoul[i].styl
            
            diag = self.contenu["diagB"][i]
            p = len(self.pulsas)//2
            x0, y0 = diag.reponse[1][p], diag.reponse[2][p]
            x1, y1 = diag.reponse[1][p-1], diag.reponse[2][p-1]
            if (x0, y0) != (x1, y1):
                marker = globdef.MARKER
            else:
                marker = '.' 
            
            self.lines += self.subplot.plot(diag.reponse[1], diag.reponse[2],
                                            color = coul, 
                                            linewidth = width, 
                                            linestyle = style, marker = marker,
                                            visible = True, zorder = globdef.ZORDER_MAXI-i)
            if globdef.TRACER_FLECHE:
                if (x0, y0) != (x1, y1):
                    xy = self.getXY_Fleche((x0, y0),  (x1, y1))
                    
                    self.fleche.append(self.subplot.arrow(0, 0, 1, 1,
                                                          color = coul, 
                                                          linewidth = 1, 
                                                          visible = True, 
                                                          zorder = globdef.ZORDER_MAXI-i))
                    setp(self.fleche[-1], xy = xy)
        #
        # Propriétés des marges de stabilité
        #
        if "marges" in self.contenu.keys():
            self.tracerMarges(self.contenu["marges"])
        else:
            self.effacerMarges()
            
        
        if self.zoomAuto or (not self.rangesAJour) or self.miseAJour:
            self.drawCanvas()
        else:
            self.drawArtists()
   
    
    ######################################################################################################    
    def getContenuExport(self):
        contenu = []
        images = []
        
        for i, ft in enumerate(self.lstFTNum):
            diag = self.contenu["diagB"][i]
            contenu.append(("Pulsation", diag.reponse[0])) 
            contenu.append(("Gain", diag.reponse[1])) 
            contenu.append(("Phase", diag.reponse[2])) 

            file, h = getFileBitmap(ft, i)
            
            images.append((file,i*7, h))
            
        return contenu, images
    
    ######################################################################################################
    def sauveBackGround(self):
        self.background = self.canvas.copy_from_bbox(self.subplot.bbox)

    ######################################################################################################
    def restoreBackground(self, ax = None):
        self.canvas.restore_region(self.background)
        
        
    
        
        
    #####################################################################################################
    def tracerMarges(self, marges):
#        print "Tracé Marges", marges

        self.effacerMarges()
        
        #
        # Marge de Phase
        #
        if marges.Om0 != None:
            mp = marges.Phi0
        else:
            mp = self.subplot.get_xlim()[1]
#            marge = [marges.Phi0, -180]
#            marge.sort()
        xy = [[mp, 0], [-180, 0]]
        xy.extend(self.getXY_Fleche(xy[0],xy[1]))
        xy = array(xy).transpose()
        setp(self.margePhase, data = xy,
             visible = True, color = marges.getCoulP())


            
        #
        # Marge de Gain
        #
        if marges.Om180 != None:
            mg = marges.HdB180
        else:
            mg = self.subplot.get_ylim()[0]
        xy = [[-180, 0],[-180, mg]]
        xy.extend(self.getXY_Fleche(xy[0],xy[1]))
        xy = array(xy).transpose()
        setp(self.margeGain, data = xy,
             visible = True, color = marges.getCoulG())


        #
        # Surtension
        #
        if marges.OmS != None:
            G,P,iso = getIsoGains(self.subplot.get_xlim(), self.subplot.get_ylim())
            self.isoGainsMarge = self.subplot.contour(P,G,iso, [marges.HdBF] , zorder = globdef.ZORDER_MAXI-2,  
                                                      linewidth = 0.5, colors = marges.getCoulQ() )

    #####################################################################################################
    def effacerMarges(self):
        setp(self.margePhase, visible = False)
        setp(self.margeGain, visible = False)
        # Effacement des anciens isoGainsMarge
        if hasattr(self, "isoGainsMarge"):
            self.isoGainsMarge.remove()
            # for i in self.isoGainsMarge.collections: 
            #     i.remove()
            delattr(self, "isoGainsMarge")

    
    ######################################################################################################
    def getMinMaxReel(self, diag, defMinX, defMaxX, defMinY, defMaxY):
        minX, maxX = diag.getMinMaxPhase()
        minY, maxY = diag.getMinMaxGain()
#        minX = _min(diag.lstPt[0], defMinX)
#        maxX = _max(diag.lstPt[0], defMaxX)
#    
#        minY = _min(diag.lstPt[1], defMinY)
#        maxY = _max(diag.lstPt[1], defMaxY)

        return minX, maxX, minY, maxY
    
    ######################################################################################################
    def getReponse(self, ft):
        return ft.getReponseHarmoniqueBlack()
    
    
    
##########################################################################################################
#
#  Zone graphique Nyquist
#
##########################################################################################################
class ZoneGraphNyquist(ZoneGraphBase):
    def __init__(self, parent, zoneOutils, nom = "Nyquist"):
        ZoneGraphBase.__init__(self, parent, zoneOutils, nom)
        
        self.estFTBF = False
        self.nom = nom
        
        #
        # Définition des Artists MPL
        #
        self.initDraw()
        self.modifierTaillePolices()
        self.modifierAntialiased()

        self.tracerPoles = False
        self.polesAffichables = False
        
        
        
    ######################################################################################################
    def initDraw(self):
#        print "initdraw Nyquist"
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)

        #
        # Tracé de la Grille
        #
        coul = globdef.FORM_GRILLE.get_coul_str()
        self.subplot.grid(globdef.TRACER_GRILLE, color = coul, 
                          lw = globdef.FORM_GRILLE.epais, 
                          ls = globdef.FORM_GRILLE.styl, zorder = 0)#, visible = globdef.TRACER_GRILLE)
        
        
        #
        # Définition des deux "axes"
        #
        self.subplot.set_ylabel(r"$\Im$")
        self.subplot.set_xlabel(r"$\Re$")
        self.subplot.autoscale_view(tight=True, scalex=False, scaley=True)
        
        #
        # Pré définition des Tracés des FT
        #
        
        self.lines = []
        
#        self.lstArtists.extend(self.lines)
        
        # Le label de la FT apparaissant au passage de la souris
        self.labelFT = self.subplot.text(1, 0, "", visible = False)
        
        #
        # Prédéfinition des expressions des FT
        #
        self.exprFT = []
        
        #
        # Définition des axes "origine"
        #
        self.subplot.axvline(0, linewidth=1, color='k')
        self.subplot.axhline(0, linewidth=1, color='k')
        
#        #
#        # Définition des lignes de marges
#        #
#        coul = globdef.COUL_MARGE_GAIN
#        self.margeGain = self.subplot.axvline(1, 0, 1, color = coul, linewidth = 3,
#                                               visible = False)
#        setp(self.margeGain, transform = self.subplot.transData)
#        
#        coul = globdef.COUL_MARGE_PHAS
#        self.margePhase = self.subplot.axhline(1, 0, 1, color = coul, linewidth = 3,
#                                               visible = False)
#        setp(self.margePhase, transform = self.subplot.transData)

        #
        # Définition du point critique
        #
        self.ptCritique = self.subplot.plot([-1], [0], marker = 'o', mfc = globdef.COUL_PT_CRITIQUE)
        self.labelptCritique = self.subplot.text(1, 0, "", visible = False, 
                                                 color = globdef.COUL_PT_CRITIQUE, zorder = 2)
        
        #
        # Définition des flèches sur les courbes
        #
        self.fleche = []
            
#        self.lstArtists.extend(self.fleche)
        
        #
        # Pré définition des Tracés des Pôles
        #
        
        self.poles = []
        self.zeros = []
#        for n in range(globdef.NBR_MAXI_PLOT): 
#            self.poles += self.subplot.plot([0], [0], visible = False, marker = 'o', mfc = coul)
        self.label = self.figure.text(0, 0, "", visible = False, color = globdef.COUL_REPONSE)
            
#        self.lstArtists.extend(self.poles)
#        self.lstArtists.extend(self.label)
#                               
#        for a in self.lstArtists:
#            a.set_animated(True)
            
        try:
            self.calculerMargesFigure()
        except:
            pass

    ######################################################################################################
    def modifierTaillePolices(self):
        setp(self.subplot.get_xaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        setp(self.subplot.get_yaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        
        setp(self.subplot.get_yaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        setp(self.subplot.get_xaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        
        setp(self.labelFT, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        setp(self.label, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        setp(self.labelptCritique, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        
        for e in self.exprFT:
            setp(e, fontsize = self.fontSizes["FONT_SIZE_EXPR"])



    #########################################################################################################
    def setTracerPoles(self, etat):
        self.tracerPoles = etat
        
    #########################################################################################################
    def setPolesAffichables(self, etat):
        self.polesAffichables = etat
        
        
    # Gestion du curseur ################################################################################
    def setCurseur(self, etat):
        if self.curseur != etat:
            self.curseurFixe = False
            self.curseur = etat
            
            if not etat:
                self.setCurseurOff()
                
            else:
                self.sauveBackGroundFig()
                coul = globdef.COUL_TEXT_CURSEUR
                size = globdef.FONT_SIZE_CURSEUR
                halign = 'center'
                bgcolor = globdef.COUL_BLANC
                
                bbox = dict(facecolor = bgcolor, alpha = 0.7, 
                            edgecolor = "none", linewidth = 2.0,
                            zorder = globdef.ZORDER_MAXI)
                
                # Le texte sur le curseur de la souris
                self.txtCurs = self.subplot.text(1.0, 0.0, "", visible = False, color = coul,
                                                 fontsize = size, horizontalalignment = halign,
                                                 bbox = bbox)
                
                
                if self.valCurseurSurCote:
                    #                    #
                    # Les valeurs de gain et de phase
                    #
                    self.tickGain, self.tickPhas = [], []
                    for i in range(len(self.lstFTNum)):
                        coul = self.lstCoul[i].get_coul_str()
                        tickGain = YTick(self.subplot, 1.0, gridOn = True)
                        tickPhas = XTick(self.subplot, 1.0, gridOn = True)
                        for t in [tickGain, tickPhas]:
                            t.gridline.set_color(coul)
                            t.gridline.set_linestyle('-')
                            t.label1.set_size(globdef.FONT_SIZE_GRAD)
                            t.label1.set_backgroundcolor(self.figure.get_facecolor())
                            t.label1.set_color(coul)
                        self.tickGain.append(tickGain)
                        self.tickPhas.append(tickPhas)
                        
                    self.listeArtistsCurseur = [self.txtCurs]
                    self.listeArtistsCurseur.extend(self.tickGain)
                    self.listeArtistsCurseur.extend(self.tickPhas)
                    
                else:
                    #
                    # Les lignes horizontales et verticales
                    #
                    self.hline, self.vline = [], []
                    for i in range(len(self.lstFTNum)):
                        self.vline.append(self.subplot.axvline(1.0, 0.0, 1.0))
                        self.hline.append(self.subplot.axhline(0.0, 0.0, 1.0))
            
                    #
                    # Les textes sur les courbes
                    #
                    self.txtCursGP = []
                    for i in range(len(self.lstFTNum)):
                        self.txtCursGP.append(self.subplot.text(1.0, 0.0, "", visible = False, color = coul,
                                                       fontsize = size, horizontalalignment = halign,
                                                       bbox = bbox))
                        
                        
                        
                        
                        
        
    ######################################################################################################
    def setCouleurs(self):
        for s in self.getsubplots():
            s.grid(self.tracerGrille, color = globdef.FORM_GRILLE.get_coul_str(),
                   ls = globdef.FORM_GRILLE.styl,
                   lw = globdef.FORM_GRILLE.epais)

#        for m in self.margeGain:
#            m.set_color(globdef.COUL_MARGE_GAIN)
#        for m in self.margePhase:
#            m.set_color(globdef.COUL_MARGE_PHAS)

        for p in self.poles: 
            p.set_mfc(globdef.COUL_POLES)
            
        self.ptCritique[0].set_color(globdef.COUL_PT_CRITIQUE)
        
#        self.drawCanvas()
      
    ######################################################################################################
    def effacerLabels(self):
        self.canvas.restore_region(self.backgroundFig)
        
        setp(self.labelFT, visible = False)
        setp(self.labelptCritique, x = 0, y = 0, text = "", visible = False)
        setp(self.label, visible = False)
        
        self.subplot.draw_artist(self.labelFT)
        self.subplot.draw_artist(self.label)
        self.subplot.draw_artist(self.labelptCritique)
#        self.drawArtists([self.labelFT], self.figure)
#        self.drawArtists([self.labelptCritique], self.figure)
          
        
#        self.draw_artists([self.labelFT, self.label, self.labelptCritique], self.figure)
              
            
#        for l in self.label:
#            setp(l, visible = False)
#            self.figure.draw_artist(l)
        
        self.canvas.blit()
           

    ######################################################################################################
    def Detection(self, event):
        detect = {"FT": None,
                  "EX": None,
                  "PO": None,
                  "ZE": None,
                  "PC": None}
        
        # Détection des FT
        continuer = True
        i = 0
        while continuer:
            if i >= len(self.lstFTNum):
                continuer = False
            elif self.lines[i].contains(event)[0]:
                continuer = False
                detect["FT"] = i
            i += 1
        if detect["FT"] != None: return detect
        
        # Détection des expressions
        continuer = True
        i = 0
        while continuer:
            if i >= len(self.lstFTNum):
                continuer = False
            elif self.exprFT[i].contains(event)[0]:
                continuer = False
                detect["EX"] = i
            i += 1
        if detect["EX"] != None: return detect
        
        # Détection des Pôles
        continuer = True
        i = 0
        while continuer:
            if i >= len(self.poles):
                continuer = False
            elif self.poles[i].contains(event)[0]:
                continuer = False
                detect["PO"] = i
            i += 1
        if detect["PO"] != None: return detect
        
        # Détection des zeros
        continuer = True
        i = 0
        while continuer:
            if i >= len(self.zeros):
                continuer = False
            elif self.zeros[i].contains(event)[0]:
                continuer = False
                detect["ZE"] = i
            i += 1
        if detect["ZE"] != None: return detect
                
        # Détection du point critique
        a, numIso = self.ptCritique[0].contains(event)
        if a:
            detect["PC"] = 1
        if detect["PC"] != None: return detect
        
        return detect
        
    ######################################################################################################
    def OnMoveDefaut(self, _xdata, _ydata, axe, event = None):
        
        if self.mouseInfo != None:
            self.moveExpression(event)

        else:
            if _xdata == None or _ydata == None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
                self.effacerLabels()
                return
            
            with errstate(invalid='ignore'):
                detect = self.Detection(event)
            
            # Affichage ...
            if detect["EX"] != None:
                self.effacerLabels()
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_MAIN))
                self.context = "E"+str(detect["EX"])
                
            elif detect["FT"] != None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
                coul = self.lstCoul[detect["FT"]].get_coul_str()
                setp(self.labelFT, text = r"$"+self.lstFTNum[detect["FT"]].nom + " $",
                     x = _xdata, y = _ydata, visible = True, color = coul)
                self.draw_artists([self.labelFT])
                self.context = "F"+str(detect["FT"])

            elif detect["PO"] != None or detect["ZE"] != None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
                
                inv = self.figure.transFigure.inverted()
                
                _x, _y = inv.transform((event.x, event.y))
                
                if detect["PO"] != None:
                    text = r"$p_{"+str(detect["PO"])+"}="+strScCx(self.lstPoles[detect["PO"]], nbChiffres = 2)+"$"
                    self.context = "Z"+str(detect["PO"])
                else:
                    text = r"$z_{"+str(detect["ZE"])+"}="+strScCx(self.lstZeros[detect["ZE"]], nbChiffres = 2)+"$"
                    self.context = "Z"+str(detect["ZE"])
                    
                setp(self.label, x = _x, y = _y, 
                     text = text, visible = True)
                
                self.draw_artists([self.label], self.figure)
                
#                
#            elif detect["ZE"] != None:
#                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
#                
#                inv = self.figure.transFigure.inverted()
#                
#                _x, _y = inv.transform((event.x, event.y))
#                
#                setp(self.label, x = _x, y = _y, 
#                     text = strScCx(self.lstZeros[detect["ZE"]]), visible = True)
#                
#                self.draw_artists([self.label], self.figure)
#                self.context = "Z"+str(detect["ZE"])
                
            elif detect["PC"] != None:
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
                text = _("Point critique")
                setp(self.labelptCritique, text = text,
                     x = _xdata, y = _ydata, visible = True)
                self.draw_artists([self.labelptCritique])
                self.context = "C"
                
            else:
                self.effacerLabels()
                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
                self.context = ""


    ######################################################################################################
    def OnMoveEchelle(self, _x, _y, axe):
        if self.mouseInfo != None:
            dx = _x-self.mouseInfo[0]
            rangeX = self.mouseInfo[2][0]
            coefX = 1.0 * dx /100
            rangeX = self.getNewEchelleAxe(coefX, rangeX)
#            deltaX = rangeX[1] - rangeX[0]
#            ecartX = deltaX * coefX /2
#            rangeX = [rangeX[0] - ecartX, rangeX[1] + ecartX]
            
            dy = _y-self.mouseInfo[1]
            rangeY = self.mouseInfo[2][1]
            coefY = 1.0 * dy /100
            rangeY = self.getNewEchelleAxe(coefY, rangeY)
#            deltaY = rangeY[1] - rangeY[0]
#            ecartY = deltaY * coefY /2
#            rangeY = [rangeY[0] - ecartY, rangeY[1] + ecartY]
            
            self.calculerEtRedessiner(rangeX, rangeY, initMousInfo = False)
        

    ######################################################################################################
    def OnMoveCurseur(self, _xdata, _ydata, axe):    
            
        self.restoreBackgroundFig()
        
        # Calcul de la valeur de Omega
        xl = self.subplot.get_xlim()
        pc = (xl[1] - _xdata)/ (xl[1] - xl[0])
        logOm = (log10(self.rangeOm[1]) - log10(self.rangeOm[0]))*pc + log10(self.rangeOm[0])
        Om = 10**logOm
        
        
            
        if self.valCurseurSurCote:
            #
            # Les valeurs de gain et de phase
            #        
            for i, ft in enumerate(self.lstFTNum):
                _x, _y = ft.H_real_imag(Om)
                self.tickGain[i].update_position(_y)
                self.tickGain[i].label1.set_text(fonctions.strSc(_y))
                self.tickGain[i].set_visible(True)
                
                self.tickPhas[i].update_position(_x)
                self.tickPhas[i].label1.set_text(fonctions.strSc(_x))
                self.tickPhas[i].set_visible(True)
                
                self.subplot.draw_artist(self.tickGain[i])
                self.subplot.draw_artist(self.tickPhas[i])

            
            
            
        else:
            e = 30
    
            ymoy = (self.subplot.get_ylim()[0] + self.subplot.get_ylim()[1])/2
#            xmoy = (self.subplot.get_xlim()[0] + self.subplot.get_xlim()[1])/2

            for i, ft in enumerate(self.lstFTNum):
                _x, _y = ft.H_real_imag(Om)
                coul = self.lstCoul[i].get_coul_str()
                
                # Lignes verticales
                setp(self.vline[i], xdata = array([_x]), color = coul, visible = True)
                self.subplot.draw_artist(self.vline[i])
    
                # Lignes horizontales
                setp(self.hline[i], ydata = array([_y]), color = coul, visible = True)
                self.subplot.draw_artist(self.hline[i])
 
                # Valeurs gain et phase
                dHdP = ft.deriveeNyquist(Om)
                va, ha, s1, s2 = getAlignment(dHdP, _y < ymoy)
                setp(self.txtCursGP[i], x = _x , y = _y ,
                     horizontalalignment = ha, verticalalignment = va, zorder = globdef.ZORDER_MAXI-i+1,
                     text = s1+r"$\Re="+fonctions.strSc(_x)+r"$"+"\n"+"$\Im="+fonctions.strSc(_y)+r"$"+s2, visible = True)
                self.subplot.draw_artist(self.txtCursGP[i])
            
            
        # Affichage de Omega sur le curseur
        setp(self.txtCurs, position = (_xdata, _ydata),
             text = r"$\omega="+fonctions.strSc(Om)+r" rad/s$"+"\n", visible = True)
        axe.draw_artist(self.txtCurs)
        
        if self.valCurseurSurCote:
            self.canvas.blit()
        else:
            self.canvas.blit(self.subplot.bbox)
            
        # Pour synchronisation avec réponse temporelle
        if self.estFTBF:
#            self.pulsationCurseur = Om
            self.zoneOutils.app.winReponse.SynchroniserPulsationSinus(Om)
            
#        return
            
#        self.canvas.restore_region(self.background)
#
#        xl = self.subplot.get_xlim()
#        pc = (xl[1] - _xdata)/ (xl[1] - xl[0])
#        logOm = (log10(self.rangeOm[1]) - log10(self.rangeOm[0]))*pc + log10(self.rangeOm[0])
#        Om = 10**logOm
#        setp(self.txtCurs, position = (_xdata, _ydata),
#             text = r"$\omega="+fonctions.strSc(Om)+r" rad/s$"+"\n", visible = True)
#        
#        
#            
#        e = 30
#
#        ymoy = (self.subplot.get_ylim()[0] + self.subplot.get_ylim()[1])/2
##        xmoy = (self.subplot.get_xlim()[0] + self.subplot.get_xlim()[1])/2
#                
#        for i, ft in enumerate(self.lstFTNum):
#            _x, _y = ft.H_real_imag(Om)
#
#            coul = self.lstCoul[i].get_coul_str()
#            # Lignes verticales
#            setp(self.vline[i], xdata = array([_x]), color = coul, visible = True)
#            self.subplot.draw_artist(self.vline[i])
#
#            # Lignes horizontales
#            setp(self.hline[i], ydata = array([_y]), color = coul, visible = True)
#            self.subplot.draw_artist(self.hline[i])
#
#            # Valeur gain
#            dHdP = ft.deriveeNyquist(Om)
#            va, ha, s1, s2 = getAlignment(dHdP, _y < ymoy)
#            
#            setp(self.txtCursGP[i], x = _x , y = _y ,
#                 horizontalalignment = ha, verticalalignment = va, zorder = globdef.ZORDER_MAXI-i+1,
#                 text = s1+r"$\Re="+fonctions.strSc(_x)+r"$"+"\n"+"$\Im="+fonctions.strSc(_y)+r"$"+s2, visible = True)
#            self.subplot.draw_artist(self.txtCursGP[i])
#            
#        
#        axe.draw_artist(self.txtCurs)
#        self.canvas.blit(self.subplot.bbox)

        

    def getRangeTotal(self, lstFTNum):
        """ Renvoie l'intervalle de pulsations Om 
            le mieux adapté
        """
        mini, maxi = [], []
        for i, ft in enumerate(lstFTNum):
            minmaxD = ft.getRangeDecade()
            mini.append(minmaxD[0])
            maxi.append(minmaxD[1])
        minmaxD = [min(mini), max(maxi)]
        minmax = ft.getRange(minmaxD)
        return minmax

    def getRangePulsation(self, lstFTNum, rangeX = [], rangeY = []):
        """ Renvoie les pulsations pour le calcul de la réponse
        """
        
        minmax = self.getRangeTotal(lstFTNum)
        
        if len(rangeX) == 0 or len(rangeY) == 0:
            pulsas = calcul.getPulsations(minmax)
        else:
            mini, maxi = [], []
            intMinGain, intMaxGain = [], []
            intMinPhas, intMaxPhas = [], []
            
            for i, ft in enumerate(lstFTNum):
                intMinGain += ft.getIntervalle(2, rangeY[0])
                intMaxGain += ft.getIntervalle(2, rangeY[1])
                intMinPhas += ft.getIntervalle(1, rangeX[0])
                intMaxPhas += ft.getIntervalle(1, rangeX[1])
                
#                tout = tout + intMinGain+intMaxGain+intMinPhas+intMaxPhas
            rangeOmGain = [min(intMinGain+intMaxGain), max(intMinGain+intMaxGain)]
            rangeOmPhas = [min(intMinPhas+intMaxPhas), max(intMinPhas+intMaxPhas)]
            
            mini = [rangeOmGain[0], rangeOmPhas[0], minmax[0]]
            maxi = [rangeOmGain[1], rangeOmPhas[1], minmax[1]]
            try:
                while True : mini.remove(None)
            except:
                pass  
            try:
                while True : maxi.remove(None)
            except:
                pass

            minmax = [max(mini), 
                      min(maxi)]

#            minmax = [min(tout, minmax[0]), max(tout, minmax[1])]

            pulsas = lstFTNum[0].getPulsations(minmax)
            
        self.rangeOm = minmax
        return pulsas
            
    def getListePulsations(self, lstFTNum, ax, raz = False):
        """ Renvoie la listes des pulsations pour le calcul de la réponse
            (calcul en fonction des limites de l'Axes <ax>)
        """

#        minmax = self.getRangeTotal(lstFTNum)
            
        minmax = [None, None]
        for ft in lstFTNum:
            if not hasattr(ft, 'reponseN') or raz:
                ft.reponseN = ft.getReponseHarmoniqueNyquist(self.getListePulsationAuto(lstFTNum))
            rangeOm = ft.getIntervallePulsMpl(ax, ft.reponseN)
            if rangeOm[0] != None:
                minmax[0] = _m(minmax[0], rangeOm[0], min)
                minmax[1] = _m(minmax[1], rangeOm[1], max)

        if None in minmax:
            return []
        
        self.rangeOm = minmax
        return calcul.getPulsations(minmax)


    ######################################################################################################
    def getListePulsationAuto(self, lstFTNum):
        """ Renvoie la listes des pulsations pour le calcul de la réponse
            (calcul automatique en fonction des cassures)
        """
        rangeOm = self.getRangeTotal(lstFTNum)
        pulsas = calcul.getPulsations(rangeOm)
        self.rangeOm = rangeOm
        return pulsas        
    
    
    ######################################################################################################
    def getDiagrammes(self, lstFTNum, pulsas, rapide = False):
        lstDiag = []
        for i, ft in enumerate(lstFTNum):
            lstDiag.append(ft.getDiagNyquist(pulsas, rapide))
        return lstDiag
        
    ######################################################################################################
    def getDiagrammesEtMarges(self, lstFTNum, marges, pulsas):
        # on construit les diagrammes
        contenu = {"diagB" : self.getDiagrammes(lstFTNum, pulsas)}
        
        # On calcule les marges
#        if marges != None:
#            contenu["marges"] = marges
          
            
        
        return contenu


    ######################################################################################################
    def mettreAJourPoles(self, poles, zeros):
        self.lstPoles = poles
        self.lstZeros = zeros
        return
#        for i, p in enumerate(self.lstPoles):
#            for i,p in enumerate(self.lstPoles):
#                self.label.append(self.figure.text(0, 0, "", visible = False, color = coul))
#            setp(self.label[i], x = real(p), y = imag(p), text = strScCx(p))
            
            
#    ######################################################################################################
#    def mettreAJourEtRedessiner(self, lstFTNum, lstCoul, winMarges, HC, poles = None):
#        self.mettreAJour(lstFTNum, lstCoul, winMarges, HC, poles)
#        self.calculerEtRedessinerRanges()
            
    
    ######################################################################################################
    def calculerEtRedessiner(self, rangeX = [], rangeY = [], initMousInfo = True):
        """ Calcul de intervalle des Omega ...
            ... recalcul des diagrammes ...
            ... et Tracé de tout ! """
            
        if initMousInfo:
            self.mouseInfo = None

        
        #
        # Determination des intervalles phase et gain
        #

            
        # Mémorisation des anciens ranges
        _rangeX = self.subplot.get_xlim()
        _rangeY = self.subplot.get_ylim()
        
        if self.zoomAuto:
            #
            # Calcul des mini maxi Automatique
            #

            # Obtention des diagrammes (juste pour le calcul des mini/maxi)
            pulsas = self.getListePulsationAuto(self.lstFTNum)
            
            diag = self.getDiagrammes(self.lstFTNum, pulsas, rapide = True)
            
            _minX, _maxX, _minY, _maxY = [],[],[],[]
            
            for d in diag:
                minX, maxX, minY, maxY = self.getMinMaxReel(d, _rangeX[0], _rangeX[1], \
                                                               _rangeY[0], _rangeY[1])
                _minX.append(minX)
                _maxX.append(maxX)
                _minY.append(minY)
                _maxY.append(maxY)
            
            minX, maxX, minY, maxY = _min(_minX, _rangeX[0]), \
                                     _max(_maxX, _rangeX[1]), \
                                     _min(_minY, _rangeY[0]), \
                                     _max(_maxY, _rangeY[1])
            
            if minX == maxX:
                minX += -1.0
                maxX += 1.0
            if minY == maxY:
                minY += -1.0
                maxY += 1.0
#            minY, maxY = max(-40,minY), min(40, maxY)
#           
#            if [minX, maxX] == [0,0]:
#                minX, maxX = -1, 1
#            if [minY, maxY] == [0,0]:
#                minY, maxY = -1, 1
            
            # Prise en compte des poles
            if self.tracerPoles and self.polesAffichables \
               and (self.lstPoles != None or self.lstZeros != None) \
               and (self.lstPoles + self.lstZeros != []):
                minXp, maxXp, minYp, maxYp = self.getMinMaxPoles()
                minX = min(minX, minXp)
                minY = min(minY, minYp)
                maxX = max(maxX, maxXp)
                maxY = max(maxY, maxYp)
                
            self.subplot.set_xlim([minX, maxX])
            self.subplot.set_ylim([minY, maxY])    

        else:
            #
            # On regarde si les ranges ont changé
            #
            x1, x2 = self.subplot.get_xlim()
            y1, y2 = self.subplot.get_ylim()
            self.rangesAJour = rangeX is not None and rangeY is not None 
            self.rangesAJour = self.rangesAJour and \
                               (    (len(rangeX) == 0 or (x1 == rangeX[0] and x2 == rangeX[1])) \
                                and (len(rangeY) == 0 or (y1 == rangeY[0] and y2 == rangeY[1])))
            
            if rangeX != [] and rangeX is not None: # Est-ce encore utile ???
                self.subplot.set_xlim(rangeX)
                self.subplot.set_ylim(rangeY)
        
        
        #
        # Recalcul des diagrammes (plus sérré)
        #
        
        # pour détecter si on a reculé ...
        raz =  self.subplot.get_xlim()[0] < _rangeX[0] \
            or self.subplot.get_xlim()[1] > _rangeX[1] \
            or self.subplot.get_ylim()[0] < _rangeY[0] \
            or self.subplot.get_ylim()[1] > _rangeY[1]
            

        pulsas = self.getListePulsations(self.lstFTNum, self.subplot, raz)

        if len(pulsas) == 0: return
        self.contenu = self.getDiagrammesEtMarges(self.lstFTNum, self.marges, pulsas)
        
        self.pulsas = pulsas
        
        # On vérifie si ça a changé ...
#        self.rangeModifie = _rangeX != self.graduations.axeX.range or _rangeY != self.graduations.axeY.range
        
        self.TracerTout()
        
        
    #####################################################################################################    
    def TracerTout(self):
        """ Tracé de tout 
        """
#        print "Tracé tout", self.nom, self.zoomAuto
        self.zoneOutils.activerCurseur(False)
        
        #
        # On efface les textes et les lignes
        #
#        for axe in self.getsubplots():
#            axe.texts = []
#            axe.lines = []
            
        for l in self.lines:
            l.remove()
            
        for f in self.fleche:
            f.remove()
            
        for f in self.poles + self.zeros:
            f.remove()
            
#        self.lstArtists = []
        self.lines = []
        self.fleche = []
        self.poles = []
        self.zeros = []
        
        #
        # Propriétés des diagrammes
        #
        for i in range(len(self.lstFTNum)):
            coul = self.lstCoul[i].get_coul_str()
            width = self.lstCoul[i].epais
            style = self.lstCoul[i].styl
            
            diag = self.contenu["diagB"][i]
            p = len(self.pulsas) // 2
            x0, y0 = diag.reponse[1][p], diag.reponse[2][p]
            x1, y1 = diag.reponse[1][p-1], diag.reponse[2][p-1]
            if (x0, y0) != (x1, y1):
                marker = globdef.MARKER
            else:
                marker = '.'
           
            self.lines += self.subplot.plot(diag.reponse[1], diag.reponse[2],
                                            color = coul, 
                                            linewidth = width, 
                                            linestyle = style, marker = marker,
                                            visible = True, zorder = globdef.ZORDER_MAXI-i)
            
            if globdef.TRACER_FLECHE:
                if (x0, y0) != (x1, y1):
                    xy = self.getXY_Fleche((x0, y0),  (x1, y1))
                    self.fleche.append(self.subplot.arrow(0, 1, 0, 1,
                                                          color = coul, 
                                                          linewidth = 1, 
                                                          visible = True, zorder = globdef.ZORDER_MAXI-i))
                    setp(self.fleche[-1], xy = xy)
#        #
#        # Propriétés des marges de stabilité
#        #
#        if "marges" in self.contenu.keys():
#            self.tracerMarges(self.contenu["marges"])
#        else:
#            self.effacerMarges()

            
        #
        # Propriétés des Pôles
        #
        if self.tracerPoles and self.polesAffichables:
            coul = globdef.COUL_POLES
            for i,p in enumerate(self.lstPoles):
                self.poles += self.subplot.plot([real(p)], [imag(p)], visible = True,
                                                marker = 'o', mfc = coul)
            for i,p in enumerate(self.lstZeros):
                self.zeros += self.subplot.plot([real(p)], [imag(p)], visible = True,
                                                marker = 'x', mfc = 'None', mec = 'k')
#                self.label.append(self.figure.text(real(p), imag(p), strScCx(p),
#                                                   visible = False, color = coul))
                
        else:
            for p in self.poles + self.zeros:
                setp(p, visible = False)
            
            
        if self.zoomAuto or not self.rangesAJour or self.miseAJour:
            self.drawCanvas()
        else:
            self.drawArtists()
        
    
    ######################################################################################################    
    def getContenuExport(self):
        contenu = []
        images = []
        
        for i, ft in enumerate(self.lstFTNum):
            diag = self.contenu["diagB"][i]
            contenu.append(("Pulsation", diag.reponse[0])) 
            contenu.append(("Gain", diag.reponse[1])) 
            contenu.append(("Phase", diag.reponse[2])) 

            file, h = getFileBitmap(ft, i)
            
            images.append((file,i*7, h))
            
        return contenu, images
    
    
    ######################################################################################################
    def sauveBackGround(self):
        self.background = self.canvas.copy_from_bbox(self.subplot.bbox)
        self.backgroundFig = self.canvas.copy_from_bbox(self.figure.bbox)
        
    ######################################################################################################
    def restoreBackground(self, ax):
        if ax == self.figure:
            self.canvas.restore_region(self.backgroundFig)
        else:
            self.canvas.restore_region(self.background)
            
#    #####################################################################################################
#    def tracerMarges(self, marges):
##        print "Tracé Marges Black", marges.Phi0, marges.HdB180
#
#        #
#        # Marge de Phase
#        #
#        if marges.Om0 != None:
#            if marges.Phi0 < -180:
#                coul = globdef.COUL_MARGE_GAIN_NO
#            else:
#                coul = globdef.COUL_MARGE_GAIN_OK
#            
#            marge = [marges.Phi0, -180]
#            marge.sort()
#            setp(self.margePhase, xdata = array(marge), ydata = array([0]),
#                 transform = self.subplot.transData,
#                 visible = True, color = coul)
#            getp(self.margePhase)
#        else:
#            setp(self.margePhase, visible = False)
#        
#        #
#        # Marge de Gain
#        #
#        if marges.Om180 != None:
#            if marges.HdB180 > 0:
#                coul = globdef.COUL_MARGE_GAIN_NO
#            else:
#                coul = globdef.COUL_MARGE_GAIN_OK
#            
#            marge = [0, marges.HdB180]
#            marge.sort()
#            setp(self.margeGain, xdata = array([-180]), ydata = array(marge),
#                 transform = self.subplot.transData,
#                 visible = True, color = coul)
#        else:
#            setp(self.margeGain, visible = False)
#
#
#
#    #####################################################################################################
#    def effacerMarges(self):
#        setp(self.margePhase, visible = False)
#        setp(self.margeGain, visible = False)

            
    ######################################################################################################
    def getMinMaxPoles(self):
        im = imag(self.lstPoles+self.lstZeros)
        re = real(self.lstPoles+self.lstZeros)
        return min(re), max(re), min(im), max(im)
    
    
    ######################################################################################################
    def getMinMaxReel(self, diag, defMinX, defMaxX, defMinY, defMaxY):
        minX, maxX = diag.getMinMaxReel()
        minY, maxY = diag.getMinMaxImag()
#        minX = _min(diag.lstPt[0], defMinX)
#        maxX = _max(diag.lstPt[0], defMaxX)
#    
#        minY = _min(diag.lstPt[1], defMinY)
#        maxY = _max(diag.lstPt[1], defMaxY)
        return minX, maxX, minY, maxY
    
    
    ######################################################################################################
    def getReponse(self, ft):
        return ft.getReponseHarmoniqueNyquist()
    

###########################################################################################################
#
#
#
###########################################################################################################
class ZoneGraphReponse(ZoneGraphBase):
    def __init__(self, parent, zoneOutils, nom):
        self.reponse = None
        self.nom = "Reponse"
        ZoneGraphBase.__init__(self, parent, zoneOutils, nom)
        
        self.ajusterMarges(left = 0.11, right = 0.98, top = 0.93, bottom = 0.16)
        
#        self.lstCoul = [zoneOutils.app.formats["Cons"],
#                        zoneOutils.app.formats["Rep"],
#                        zoneOutils.app.formats["RepNc"]]
        #
        # Variables d'état de visualisation spécifiques
        #
        self.tracerIsoGP = globdef.TRACER_ISO
        self.tracerTR = False
        
        #
        # Définition des Artists MPL
        #
        self.initDraw()
        self.modifierTaillePolices()
        self.modifierAntialiased()

        self.plotInteractor = PlotInteractor(self, self.subplot, self.lines[0], 
                                             self.calculerEtRedessiner, self.effacerLabels, self.plotInterActif)
        
    ######################################################################################################
    def plotInterActif(self):
        return self.fctConsigne == None \
                and self.zoomPlus == False \
                and self.curseur == False \
                and self.deplacer == False \
                and self.echelle == False
        
    ######################################################################################################
    def initDraw(self):
#        print "initdraw réponse"
        
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)

        #
        # Tracé de la Grille
        #
        coul = globdef.FORM_GRILLE.get_coul_str()
        self.subplot.grid(globdef.TRACER_GRILLE, color = coul, 
                          ls = globdef.FORM_GRILLE.styl,
                          lw = globdef.FORM_GRILLE.epais, zorder = 0)#, visible = globdef.TRACER_GRILLE)
        
        #
        # Définition des deux "axes"
        #
#        self.subplot1.set_title("Click and drag waveforms to change frequency and amplitude", fontsize=12)
#        self.subplot.set_ylabel("E/S")
        self.subplot.set_xlabel("t (s)")
        self.subplot.autoscale_view(tight=True, scalex=False, scaley=True)
        
        #
        # Pré définition des Tracés des FT
        #
        self.lines = []
        for n in range(3): 
            self.lines += self.subplot.plot([0], [0], visible = False)
        
        # Le label de la TF apparaissant au passage de la souris
        self.labelFT = self.subplot.text(0.5, 0, "", visible = False)
        
        
        # Information
        t = _("Cette Fonction de Transfert\n"\
              "ne peut pas représenter\n" \
              "un système physique réel.\n" \
              "Impossible de tracer une réponse temporelle.")
        self.info = self.figure.text(0.5, 0.5, t, visible = False, ha = 'center', va = 'center', color = 'r')
        
#        #
#        # Prédéfinition des expressions des FT
#        #
#        self.exprFT = []
#        for n in range(2):
#            self.exprFT.append(self.figure.text(0.5, 0.5, "", visible = False,
#                                                fontsize=FONT_SIZE_EXPR, transform = None))
        
        #
        # Définition des axes "origine"
        #
        self.subplot.axvline(0, linewidth=1, color='k')
        self.subplot.axhline(0, linewidth=1, color='k')
        
        #
        # Définition des lignes de Temps de réponse
        #
        coul = globdef.COUL_LIGNE_TR
        self.limites = []
        self.tick = []
        for i in range(2):
            self.limites.append(self.subplot.axhspan(0, 0, edgecolor = coul, facecolor = "g", alpha = 0.3, \
                                                     visible = False, transform = self.subplot.transData))
            self.tick.append(XTick(self.subplot, 0.5, gridOn = True))
            
        for t in self.tick:
            t.gridline.set_color(coul)
            t.gridline.set_linestyle('-')
            t.label1.set_size(globdef.FONT_SIZE_GRAD)
            t.label1.set_backgroundcolor(self.figure.get_facecolor())
            t.label1.set_verticalalignment('top')
            setp(t, transform = self.subplot.transData)
            self.subplot.add_artist(t)
        
        self.tick[0].label1.set_color(globdef.COUL_REPONSE)
        self.tick[1].label1.set_color(globdef.COUL_REPONSENC)
        
        try:
            self.calculerMargesFigure()
        except:
            pass

    ######################################################################################################
    def modifierTaillePolices(self):
        setp(self.subplot.get_xaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        setp(self.subplot.get_yaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        
        setp(self.subplot.get_yaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        setp(self.subplot.get_xaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        
        setp(self.labelFT, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        

    
    # Gestion du curseur ################################################################################
    def setCurseur(self, etat):
        if self.curseur != etat:
            self.curseurFixe = False
            self.curseur = etat
            
            if not etat:
                self.tickS.label1.set_text('')
                self.setCurseurOff() 
            else:
                if self.valCurseurSurCote:
                    
                    #
                    # La valeur de t
                    #
                    self.tickT = XTick(self.subplot, 1.0, gridOn = True)
                    self.tickT.gridline.set_color('black')
                    self.tickT.gridline.set_linestyle('-')
                    self.tickT.label1.set_size(globdef.FONT_SIZE_GRAD)
                    self.tickT.label1.set_backgroundcolor(self.figure.get_facecolor())
                    self.tickT.label1.set_verticalalignment('top')

                    #
                    # Les valeurs S
                    #
                    self.tickS = YTick(self.subplot, 1.0, gridOn = True)
                    self.tickS.gridline.set_color(globdef.COUL_REPONSE)
                    self.tickS.gridline.set_linestyle('-')
                    self.tickS.label1.set_size(globdef.FONT_SIZE_GRAD)
                    self.tickS.label1.set_backgroundcolor(self.figure.get_facecolor())
                    self.tickS.label1.set_color(globdef.COUL_REPONSE)
                    
                    self.listeArtistsCurseur = [self.tickT, self.tickS]
                    
                    self.tickS.label1.set_text('*'*(globdef.NB_CHIFFRES+6))
                    self.getsubplot().draw_artist(self.tickS)
                    
                    if self.fctConsigne == calcul.sinus:
                        self.tickE = YTick(self.subplot, 1.0, gridOn = True)
                        self.tickE.gridline.set_color(globdef.COUL_CONSIGNE)
                        self.tickE.gridline.set_linestyle('-')
                        self.tickE.label1.set_size(globdef.FONT_SIZE_GRAD)
                        self.tickE.label1.set_backgroundcolor(self.figure.get_facecolor())
                        self.tickE.label1.set_color(globdef.COUL_CONSIGNE)
                        
                        self.listeArtistsCurseur.append(self.tickE)
                        
                else:   
                    #
                    # Définition des éléments "curseur"
                    #
                    coul = globdef.COUL_TEXT_CURSEUR
                    size = globdef.FONT_SIZE_CURSEUR
                    halign = 'center'
                    bgcolor = globdef.COUL_BLANC
                    
                    # Le texte sur le curseur de la souris
                    self.txtCurs = self.subplot.text(1.0, 0.0, "", visible = False, color = coul,
                                                     fontsize = size, horizontalalignment = halign,
                                                     backgroundcolor = bgcolor)
                    
                    # Les lignes horizontales et verticales
                    self.hline, self.vline = [], []
                    self.vline.append(self.subplot.axvline(1.0, 0.0, 1.0))
                    self.hline.append(self.subplot.axhline(0.0, 0.0, 1.0))
            
                    # Les textes sur les courbes
                    coul = globdef.COUL_REPONSE
                    self.txtCursGP = []
                    self.txtCursGP.append(self.subplot.text(1.0, 0.0, "", visible = False, color = coul,
                                                            fontsize = size, horizontalalignment = halign))
                
#                try:
#                    self.calculerMarges()
#                except:
#                    pass
                self.drawCanvas()
                self.sauveBackGroundFig()

    ######################################################################################################
    def setCouleurs(self):
        for s in self.getsubplots():
            s.grid(self.tracerGrille, color = globdef.FORM_GRILLE.get_coul_str(),
                   ls = globdef.FORM_GRILLE.styl,
                   lw = globdef.FORM_GRILLE.epais)
            
            
    ##################################################################################################### 
    def BloquerCurseur(self):
        self.curseurFixe = not self.curseurFixe
        if self.curseurFixe:
            self.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
        else:
            self.SetCursor(wx.StockCursor(globdef.CURSEUR_CURSEUR))        
    
#    ##################################################################################################### 
#    def effacerCurseur(self):  
#        self.canvas.restore_region(self.background)
#            
#        # Effacement curseur
#        if self.curseur and not self.curseurFixe:
#            setp(self.txtCurs, visible = False)
#            self.subplot.draw_artist(self.txtCurs)
#            for i, ft in enumerate(self.txtCursGP):
#                setp(self.txtCursGP[i], visible = False)
#                self.subplot.draw_artist(self.txtCursGP[i])
#            
#            for i, ft in enumerate(self.vline):
#                setp(self.vline[i], visible = False)
#                self.subplot.draw_artist(self.vline[i])
#                
#            for i, ft in enumerate(self.hline):
#                setp(self.hline[i], visible = False)
#                self.subplot.draw_artist(self.hline[i])
#        
#        self.canvas.blit(self.subplot.bbox)
    
    
    ##################################################################################################### 
    def effacerLabels(self):  
        self.canvas.restore_region(self.background)
        
        setp(self.labelFT, visible = False)
        self.subplot.draw_artist(self.labelFT)
                    
        self.canvas.blit(self.subplot.bbox)

    ######################################################################################################
    def Detection(self, event):
        detect = {"FT": None,
                  }

        continuer = True
        i = 0
        while continuer:
            if i >= 3:
                continuer = False
            elif self.lines[i].contains(event)[0]:
                continuer = False
                detect["FT"] = i
            i += 1
            
        return detect
    
    
    ######################################################################################################
    def OnMoveDefaut(self, _xdata, _ydata, axe, event = None):
        # Détection des courbes
        
        # Si l'event a déja été utilisé (par un PlotInteractor)
        # et qu'on ne veut pas qu'il resserve
        if hasattr(event, 'u') and event.u:
            return
        with errstate(invalid='ignore'): 
            detect = self.Detection(event)
    
        # Affichage du label ...
        if detect["FT"] != None:
            self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
            if detect["FT"] == 0:
                coul = self.lstCoul[0].get_coul_str()
                text = mathText(_("E"))
                     
            elif detect["FT"] == 1:
                coul = self.lstCoul[1].get_coul_str()
                text = mathText(_(r"S"))
            
            else:
                coul = self.lstCoul[2].get_coul_str()
                text = mathText(_(r"S_{nc}"))
                
            setp(self.labelFT, text = text,
                 x = _xdata, y = _ydata, visible = True, color = coul)
            self.draw_artists([self.labelFT])
            self.context = "R"+str(detect["FT"])

        else:
            self.effacerLabels()
            self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
            self.context = ""
            
            
    ######################################################################################################
    def OnMoveEchelle(self, _x, _y, axe):
        if self.mouseInfo != None:
            dx = _x-self.mouseInfo[0]
            rangeX = self.mouseInfo[2][0]
            coefX = 1.0 * dx /100

            deltaX = rangeX[1] - rangeX[0]
            ecartX = deltaX * coefX /2
            rangeX = [rangeX[0] - ecartX, rangeX[1] + ecartX]
            
            dy = _y-self.mouseInfo[1]
            rangeY = self.mouseInfo[2][1]
            coefY = 1.0 * dy /100

            deltaY = rangeY[1] - rangeY[0]
            ecartY = deltaY * coefY /2
            rangeY = [rangeY[0] - ecartY, rangeY[1] + ecartY]

            if rangeX[0] < rangeX[1] and rangeY[0] < rangeY[1]:
                self.calculerEtRedessiner(rangeX, rangeY, initMousInfo = False)
        
        
#    ######################################################################################################
#    def OnWheel(self, event):
#        self.effacerLabels()
#        self.zoneOutils.activerZoomAuto(False)
#        self.setZoomAuto(False)
#
#        step = event.step
#        
#        rangeX = self.getXYlim()[0]
#        coefX = 1.0 * step /100
#
#        deltaX = rangeX[1] - rangeX[0]
#        ecartX = deltaX * coefX /2
#        rangeX = [rangeX[0] - ecartX, rangeX[1] + ecartX]
#
#        
#        rangeY = self.getXYlim()[1]
#        coefY = 1.0 * step /100
#
#        deltaY = rangeY[1] - rangeY[0]
#        ecartY = deltaY * coefY /2
#        rangeY = [rangeY[0] - ecartY, rangeY[1] + ecartY]
#        
#        self.calculerEtRedessiner(rangeX, rangeY, initMousInfo = False)


        
    ######################################################################################################
    def OnMoveCurseur(self, _xdata, _ydata, axe):     
        # restore the clean slate background
#        self.canvas.restore_region(self.background)

        self.restoreBackgroundFig()
        
        if self.valCurseurSurCote:
            #
            # La valeur du temps
            #
            text = "\n"+fonctions.strSc(_xdata)
            self.tickT.update_position(_xdata)
            self.tickT.label1.set_text(text)
            self.tickT.set_visible(True)
            
            axe.draw_artist(self.tickT)
            
            #
            # La valeur de Sortie
            #
#            # On récupère le dernier point de la réponse ...
#            self.param['rangeT'] = [0, _xdata]
#            _y = self.fctReponse(**self.param)[1][-1]

            # Une méthode plus rapide ...
            f = scipy.interpolate.interp1d(self.reponse[0], self.reponse[1])
            ok = True
            try:
                _y = f(_xdata)
            except ValueError:
                ok = False
                
            if ok:
                self.tickS.update_position(_y)
                self.tickS.label1.set_text(fonctions.strSc(_y))
                self.tickS.set_visible(True)
                
                axe.draw_artist(self.tickS)

            #
            # La valeur d'Entrée
            #
            if self.fctConsigne == calcul.sinus:
                _y = self.fctConsigne(_xdata, **self.param)
                self.tickE.update_position(_y)
                self.tickE.label1.set_text(fonctions.strSc(_y))
                self.tickE.set_visible(True)
                
                axe.draw_artist(self.tickE)


            self.canvas.blit()

        else:
            # Affichage du temps
            setp(self.txtCurs, position = (_xdata, _ydata),
                 text = fonctions.strSc(_xdata)+" s \n", visible = True)
            
            # Affichage des lignes
            _x = _xdata
#            deltaT = self.getxlim()[1] - self.getxlim()[0]
            self.param['rangeT'] = [0, _x]
            
            # On récupère le dernier point de la réponse ...
            _y = self.fctReponse(**self.param)[1][-1:][0]
            
            coul = globdef.COUL_REPONSE
            # Lignes verticales
            setp(self.vline[0], xdata = array([_x]), color = coul, visible = True)
            self.subplot.draw_artist(self.vline[0])
    
            # Lignes horizontales
            setp(self.hline[0], ydata = array([_y]), color = coul, visible = True)
            self.subplot.draw_artist(self.hline[0])
    
            # Valeur
            setp(self.txtCursGP[0], x = _x , y = _y ,
    #                 horizontalalignment = ha, verticalalignment = va, zorder = ZORDER_MAXI-i+1,
                 text = fonctions.strSc(_y)+"\n", visible = True)
            self.subplot.draw_artist(self.txtCursGP[0])
            
            axe.draw_artist(self.txtCurs)
            self.canvas.blit(self.subplot.bbox)
        
    
    def getMinXY(self, reponse):
        return min(reponse[0]), min(reponse[1])
    
    def getMaxXY(self, reponse):
        return max(reponse[0]), max(reponse[1])
#        maxY = 0.0
#        for pt in diag:
#            maxY = max(maxY, pt[1])
#        return diag[:-1][0][0], maxY

#    def getDiagrammes(self, lstFTNum, lstCoul, winMarges, pulsas):
#
#        # on construit les diagrammes
#        lstDiag = []
#        
#        for i, ft in enumerate(lstFTNum):
#            coul = lstCoul[i]
#            lstDiag.append(ft.getDiagBlack(pulsas, coul))
#
#        contenu = {"diagB" : lstDiag}
#        
#        
#        # On calcule les marges
#        if winMarges != None:
#            contenu["marges"] = winMarges.calculerMarges()
#            winMarges.MiseAJour()
#            contenu["lambda"] = winMarges.FTNum.getLambda()
#        
#        return contenu

    ######################################################################################################
    def mettreAJourEtRedessiner(self, fctConsigne, fctReponse, fctReponsenc, **kwargs):
#        print "mettreAJourEtRedessiner", self.nom
        self.lstCoul = [self.zoneOutils.app.formats["Cons"],
                        self.zoneOutils.app.formats["Rep"],
                        self.zoneOutils.app.formats["RepNc"]]
        
        self.fctConsigne = fctConsigne
        self.fctReponse = fctReponse
        self.fctReponsenc = fctReponsenc
        
        self.param = kwargs
        
        # Initialisation des lines
        for line in self.lines:
            setp(line, visible = False)

        self.calculerEtRedessiner()
        
        
    ######################################################################################################
    def calculerEtRedessiner(self, rangeX = [], rangeY = [], initMousInfo = True):
        """ Calcul de intervalle de t ...
            ... recalcul des courbes ...
            ... et Tracé de tout ! """
            
#        print "Calculer et redessiner Reponse", rangeX , rangeY ,self.zoomAuto
            
        wx.BeginBusyCursor(wx.HOURGLASS_CURSOR)
        
        if initMousInfo:
            self.mouseInfo = None
        
        if self.zoomAuto:
            self.subplot.set_autoscale_on(True)
        else:
            self.subplot.set_autoscale_on(False)
            if rangeX != []:
                self.subplot.set_xlim(rangeX)
                self.subplot.set_ylim(rangeY)

        if self.zoomAuto:
            T = None
        else:
            if rangeX != []:
                T = rangeX
            else:
                T = self.subplot.get_xlim()
        
        self.reponse, self.reponsenc = self.getReponse(self.param, T)
        
#        if self.reponse == None:
#            wx.EndBusyCursor()
#            return
        
        #
        # Etablissement de la consigne à tracer
        #
        if self.reponse == None:
            rT = self.subplot.get_xlim()
            T = arange(rT[0], rT[1], (rT[1]-rT[0])/globdef.NBR_PTS_REPONSE)
        else:
            T = self.reponse[0]
        if T is not None:
            setp(self.info, visible = False)
            self.consigne = self.getConsigne(T)
            self.TracerTout()
        else:
            # pas un système physique !
            setp(self.info, visible = True)
            self.drawCanvas()
            
        wx.EndBusyCursor()
        
    def getNbrPtsIdeal(self):
        pos = self.getsubplot().get_position().get_points()
        dx = pos[1][0] - pos[0][0] + 1
        x = self.figure.get_dpi() * self.figure.get_figwidth() * dx
        return x/8
        
    
    #########################################################################################################
    def getReponse(self, param, rangeT):
        """ Etablissement de la réponse à tracer
        """
        
        def repP(fctRep, Y, T):
            re = fctRep(Y, T)

            if re[0] == None:
                gain = re[1]
                if gain == None:
                    return None, None
                x, y = self.plotInteractor.getPlot()
                _y = []
                for yy in y:
                    _y.append(yy*gain)
                return x, _y
            else:
                return re
        
        def rep(fctRep, **param):
            param['rangeT'] = rangeT
            if self.fctConsigne == calcul.sinus:
                param['nbPts'] = self.getNbrPtsIdeal()
            
            re = fctRep(**param)
            del param['rangeT']

            if re[0] is None:
                gain = re[1]
                if gain == None:
                    return None, None
                rT = re[2]
                if rT == None:
                    rT = self.subplot.get_xlim()
                if len(rT) > 2:
                    T = rT
                else:
                    T = arange(rT[0], rT[1], (rT[1]-rT[0])/globdef.NBR_PTS_REPONSE)
                return self.getConsigne(T, gain)
            else:
                return re
            
        # Cas de la consigne perso
        if self.fctConsigne == None:
            
            Y, T = self.plotInteractor.getRegularPlot2(rangeT)
#            self.consignePerso = T, Y

            if self.fctReponsenc != None:
                reponsenc = repP(self.fctReponsenc, Y, T)
            else:
                reponsenc = None
            if self.fctReponse != None:
                reponse = repP(self.fctReponse, Y, T)
            else:
                reponse = None
            return reponse, reponsenc
        
        # Cas général
        else:
#            param['rangeT'] = rangeT
            if self.fctReponsenc != None:
                reponsenc = rep(self.fctReponsenc, **param)
            else:
                reponsenc = None
            if self.fctReponse != None:
                reponse = rep(self.fctReponse, **param)
            else:
                reponse = None
#            del param['rangeT']
            return reponse, reponsenc
    
    
    
    #########################################################################################################
    def getConsigne(self, T, gain = 1):
        """ Etablissement de la consigne à tracer
            <T> est la liste des points sur l'axe du temps
        """
        # On rajoute les instants aux périodes
        if self.fctConsigne == calcul.serieImpulsions \
            or self.fctConsigne == calcul.carre \
            or self.fctConsigne == calcul.triangle:
            T = arange(0, T[-1], self.param['periode']).tolist()
        
        # Cas de la série d'impulsion
        if self.fctConsigne == calcul.serieImpulsions:
            maxi = max(1.0, max(self.reponse[1]))
            if maxi == inf: maxi = 1.0
            _R = []
            _T = []
            for t in T:
                _R.append(0.0)
                _T.append(t)
                if t/self.param['periode'] == t//self.param['periode']:
                    _T.append(t)
                    _R.append(maxi)
                    _T.append(t)
                    _R.append(0.0)
                    
            R = array(_R)
            T = array(_T)
            
            return T, R
        
        # Cas du carre
        if self.fctConsigne == calcul.carre:
            maxi = self.param['amplitude'] + self.param['decalage']
            mini = self.param['decalage']
            _R = []
            _T = []
            _R.append(0)
            _T.append(0)
            for t in T:
                _T.append(t)
                _R.append(mini)
                _T.append(t)
                _R.append(maxi)
                _T.append(t+self.param['periode']/2)
                _R.append(maxi)
                _T.append(t+self.param['periode']/2)
                _R.append(mini)
            R = array(_R)
            T = array(_T)
            
            return T, R
        
        # Cas du triangle
        if self.fctConsigne == calcul.triangle:
            maxi = self.param['pente'] * self.param['periode'] /2 + self.param['decalage']
            mini = self.param['decalage']
            _R = []
            _T = []
            _R.append(0)
            _T.append(0)
            for t in T:
                _T.append(t)
                _R.append(mini)
                _T.append(t+self.param['periode']/2)
                _R.append(maxi)
            R = array(_R)
            T = array(_T)
            
            return T, R
        
        
        # Cas de la consigne perso
        elif self.fctConsigne == None:
            return 

        
        # Cas général
        else:
            Yout = [self.fctConsigne(t, **self.param) * gain for t in T]
            return T, Yout
    
        
    
    #####################################################################################################    
    def TracerTout(self):
        """ Tracé de tout 
        """
#        print "Tracer tout réponse"
        self.zoneOutils.activerCurseur(False)
        
        #
        # Consigne
        #
        coul = self.lstCoul[0].get_coul_str()
        width = self.lstCoul[0].epais
        style = self.lstCoul[0].styl
        
        # Cas de la consigne perso
        if  self.fctConsigne == None:
            # On ne passe pas les datas (déja passées par le PlotInteractor)
            setp(self.lines[0], visible = True, marker = 'o', 
                 linewidth = width, linestyle = style, color = coul)
#            try:
#                setp(self.lines[0], xdata = self.consignePerso[0], ydata = self.consignePerso[1],
#                                    color = coul, 
#                                    linewidth = 1, 
#                                    visible = True, marker = '+')
#            except:
#                pass
            if not self.zoomAuto:
                # On repousse le dernier point de contrôle à la limite maxi en X
                self.plotInteractor.set_xMax(self.subplot.get_xlim()[1])
            
        else:
            setp(self.lines[0], xdata = self.consigne[0], ydata = self.consigne[1],
                                linewidth = width, linestyle = style, color = coul, 
                                visible = True,  marker = '')
        
        #
        # réponse corrigée
        #
        if self.reponse != None:
            coul = self.lstCoul[1].get_coul_str()
            width = self.lstCoul[1].epais
            style = self.lstCoul[1].styl
            setp(self.lines[1], xdata = self.reponse[0], ydata = self.reponse[1],
                                linewidth = width, linestyle = style, color = coul,
                                visible = True)
        else:
            setp(self.lines[1], xdata = [], ydata = [],
                 visible = False)
        
        #
        # réponse NON corrigée
        #
        if self.reponsenc != None:
            coul = self.lstCoul[2].get_coul_str()
            width = self.lstCoul[2].epais
            style = self.lstCoul[2].styl
            setp(self.lines[2], xdata = self.reponsenc[0], ydata = self.reponsenc[1],
                                linewidth = width, linestyle = style, color = coul, 
                                visible = True)
        else:
            setp(self.lines[2], xdata = [], ydata = [],
                 visible = False)
          
        #
        # Temps de réponse
        #
        if self.tracerTR and self.fctConsigne == calcul.echelon:
            Tc, Tnc = self.getTempsReponse()
            
            for limites, tick, (t, y0, y1, s) in zip(self.limites, self.tick, [Tc, Tnc]):
                if t != None:
                    xy = limites.get_xy()
                    xy[0][1] = xy[3][1] = xy[4][1] = y0
                    xy[1][1] = xy[2][1] = y1
                    xy[0][0] = xy[4][0] = xy[1][0]= 0.0
                    xy[2][0] = xy[3][0] = self.subplot.get_xlim()[1]
                    limites.set_xy(xy)
                    setp(limites, visible = True)
                    
                    text = "\n"+fonctions.strSc(t)
                    tick.update_position(t)
                    tick.label1.set_text(text)
                    tick.set_visible(True)
                    
                    self.artistsPlus.append(tick)
    
                else:
#                    xy = self.limites.get_xy()
#                    xy[0][1] = xy[3][1] = xy[4][1] = 0.0
#                    xy[1][1] = xy[2][1] = 0.0
#                    xy[0][0] = xy[4][0] = xy[1][0]= 0.0
#                    xy[2][0] = xy[3][0] = 0.0
#                    self.limites.set_xy(xy)
                    
                    setp(limites, visible = False)
                    tick.set_visible(False)
                    try:
                        self.artistsPlus.remove(tick)
                    except:
                        pass
        
        else:
#            xy = self.limites.get_xy()
#            xy[0][1] = xy[3][1] = xy[4][1] = 0.0
#            xy[1][1] = xy[2][1] = 0.0
#            xy[0][0] = xy[4][0] = xy[1][0]= 0.0
#            xy[2][0] = xy[3][0] = 0.0
#            self.limites.set_xy(xy)
            for limites, tick in zip(self.limites, self.tick):
                setp(limites, visible = False)
                tick.set_visible(False)
                try:
                    self.artistsPlus.remove(tick)
                except:
                    pass
            
        if self.zoomAuto:
            self.subplot.relim()
            self.subplot.autoscale_view(tight=False, scalex=True, scaley=True)
            
        
        self.drawCanvas()


    ######################################################################################################    
    def getContenuExport(self):
        contenu = []
        images = []
        #
        # Consigne
        #
       
        # Cas de la consigne perso
        if  self.fctConsigne == None:
            contenu.append(("Consigne Temp", getp(self.lines[0], 'xdata')))
            contenu.append(("Consigne", getp(self.lines[0], 'ydata')))
        else:
            contenu.append(("Consigne Temp", self.consigne[0]))
            contenu.append(("Consigne", self.consigne[1]))

        #
        # réponse corrigée
        #
        
        if self.reponse != None:
            contenu.append(("réponse Temp", self.reponse[0]))
            contenu.append(("réponse", self.reponse[1]))

        
        #
        # réponse NON corrigée
        #
        if self.reponsenc != None:
            contenu.append(("réponse Temp", self.reponsenc[0]))
            contenu.append(("réponse", self.reponsenc[1]))

        return contenu, images
    
    
#           
    ######################################################################################################
    def sauveBackGround(self):
        def sauv():
            self.background = self.canvas.copy_from_bbox(self.subplot.bbox)
            self.backgroundFig = self.canvas.copy_from_bbox(self.figure.bbox)

        wx.CallAfter(sauv)
        
    ######################################################################################################
    def restoreBackground(self, numax = None):
        self.canvas.restore_region(self.background)
    
    #########################################################################################################
    def setAffichTempsRep(self, etat):
        self.tracerTR = etat
        self.TracerTout()
            
    #########################################################################################################
    def getTempsReponse(self):
        """ Renvoie le temps de réponse à 5% du système, sous la forme :
            - TR = temps de réponse à 5% (en secondes)
            - v-tr*v, v+tr*v : réponses à +- 5% de l'asymptote v
            - 
        """
        if self.fctConsigne != calcul.echelon:
            return
        
        tr = globdef.TEMPS_REPONSE
        
        #
        # Calcul d'une réponse "autoscale"
        #
        reponse0, reponse0nc = self.getReponse(self.param, None)
        
        def tempsReponse(reponse):
            if reponse == None:
                return None, None, None, None
            
            #
            # Asymptote à t-->inf : Amplitude échelon x Gain statique
            #
            v = self.param['amplitude'] * reponse[2]
            
            # 
            # Détermination de l'index
            #
            iTR = None
            for i in range(len(reponse[0])):
    
                if abs(reponse[1][i]-v) <= tr*v:
    
                    if iTR == None:
                        iTR = i
                else:
                    iTR = None
                    
            s = 0
            if iTR > 0:
                s = sign(reponse[1][iTR]-v)
                TR = reponse[0][iTR-1] + (v+s*tr*v-reponse[1][iTR-1])*(reponse[0][iTR] - reponse[0][iTR-1])/(reponse[1][iTR] - reponse[1][iTR-1])
            elif iTR == None:
                TR = None
                
            return TR, v-tr*v, v+tr*v, s

        return tempsReponse(reponse0), tempsReponse(reponse0nc)


###########################################################################################################
#
#
#
###########################################################################################################
class ZoneGraphAjustement(ZoneGraphBase):
    def __init__(self, parent, zoneOutils, nom):
        self.reponse = None
        self.nom = "Ajustement"
        ZoneGraphBase.__init__(self, parent, zoneOutils, nom)
        
        self.ajusterMarges(left = 0.11, right = 0.98, top = 0.93, bottom = 0.16)
        
        #
        # Définition des Artists MPL
        #
        self.initDraw()
        self.modifierTaillePolices()
        self.modifierAntialiased()

        
        
    ######################################################################################################
    def initDraw(self):
#        print "initdraw réponse"
        
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)

        #
        # Tracé de la Grille
        #
        coul = globdef.FORM_GRILLE.get_coul_str()
        self.subplot.grid(globdef.TRACER_GRILLE, color = coul, 
                          ls = globdef.FORM_GRILLE.styl,
                          lw = globdef.FORM_GRILLE.epais, zorder = 0, visible = globdef.TRACER_GRILLE)
        
        #
        # Définition des deux "axes"
        #
        self.subplot.set_xlabel("t (s)")
        self.subplot.autoscale_view(tight=True, scalex=False, scaley=True)
        
        #
        # Pré définition des Tracés des FT
        #
        self.lines = []
        self.lines += self.subplot.plot([1], [0], linestyle='None', marker='o', visible = False)
        self.lines += self.subplot.plot([1], [0], visible = False)
        
        # Le label de la TF apparaissant au passage de la souris
        self.labelFT = self.subplot.text(1, 0, "", visible = False)
        
  
        #
        # Définition des axes "origine"
        #
        self.subplot.axvline(0, linewidth=1, color='k')
        self.subplot.axhline(0, linewidth=1, color='k')
        
        
        try:
            self.calculerMargesFigure()
        except:
            pass

    ######################################################################################################
    def modifierTaillePolices(self):
        setp(self.subplot.get_xaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        setp(self.subplot.get_yaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        
        setp(self.subplot.get_yaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        setp(self.subplot.get_xaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        
        setp(self.labelFT, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        

    
    
    # Gestion du curseur ################################################################################
    def setCurseur(self, etat):
        if self.curseur != etat:
            self.curseurFixe = False
            self.curseur = etat
            
            if not etat:
                self.tickS.label1.set_text('')
                self.setCurseurOff() 
            else:
                if self.valCurseurSurCote:
                    
                    #
                    # La valeur de t
                    #
                    self.tickT = XTick(self.subplot, 1.0, gridOn = True)
                    self.tickT.gridline.set_color('black')
                    self.tickT.gridline.set_linestyle('-')
                    self.tickT.label1.set_size(globdef.FONT_SIZE_GRAD)
                    self.tickT.label1.set_backgroundcolor(self.figure.get_facecolor())
                    self.tickT.label1.set_verticalalignment('top')

                    #
                    # Les valeurs S
                    #
                    self.tickS = YTick(self.subplot, 1.0, gridOn = True)
                    self.tickS.gridline.set_color(globdef.COUL_REPONSE)
                    self.tickS.gridline.set_linestyle('-')
                    self.tickS.label1.set_size(globdef.FONT_SIZE_GRAD)
                    self.tickS.label1.set_backgroundcolor(self.figure.get_facecolor())
                    self.tickS.label1.set_color(globdef.COUL_REPONSE)
                    
                    self.listeArtistsCurseur = [self.tickT, self.tickS]
                    
                    self.tickS.label1.set_text('*'*(globdef.NB_CHIFFRES+6))
                    self.getsubplot().draw_artist(self.tickS)
                    
                        
                else:   
                    #
                    # Définition des éléments "curseur"
                    #
                    coul = globdef.COUL_TEXT_CURSEUR
                    size = globdef.FONT_SIZE_CURSEUR
                    halign = 'center'
                    bgcolor = globdef.COUL_BLANC
                    
                    # Le texte sur le curseur de la souris
                    self.txtCurs = self.subplot.text(1.0, 0.0, "", visible = False, color = coul,
                                                     fontsize = size, horizontalalignment = halign,
                                                     backgroundcolor = bgcolor)
                    
                    # Les lignes horizontales et verticales
                    self.hline, self.vline = [], []
                    self.vline.append(self.subplot.axvline(1.0, 0.0, 1.0))
                    self.hline.append(self.subplot.axhline(0.0, 0.0, 1.0))
            
                    # Les textes sur les courbes
                    coul = globdef.COUL_REPONSE
                    self.txtCursGP = []
                    self.txtCursGP.append(self.subplot.text(1.0, 0.0, "", visible = False, color = coul,
                                                            fontsize = size, horizontalalignment = halign))
                
#                try:
#                    self.calculerMarges()
#                except:
#                    pass
                self.drawCanvas()
                self.sauveBackGroundFig()

    ######################################################################################################
    def setCouleurs(self):
        for s in self.getsubplots():
            s.grid(self.tracerGrille, color = globdef.FORM_GRILLE.get_coul_str(),
                   ls = globdef.FORM_GRILLE.styl,
                   lw = globdef.FORM_GRILLE.epais)
            
            
    ##################################################################################################### 
    def BloquerCurseur(self):
        self.curseurFixe = not self.curseurFixe
        if self.curseurFixe:
            self.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
        else:
            self.SetCursor(wx.StockCursor(globdef.CURSEUR_CURSEUR))        
    
    
    
    ##################################################################################################### 
    def effacerLabels(self):  
        self.canvas.restore_region(self.background)
        
        setp(self.labelFT, visible = False)
        self.subplot.draw_artist(self.labelFT)
                    
        self.canvas.blit(self.subplot.bbox)

    ######################################################################################################
    def Detection(self, event):
        detect = {"FT": None,
                  }

        continuer = True
        i = 0
        while continuer:
            if i >= 2:
                continuer = False
            elif self.lines[i].contains(event)[0]:
                continuer = False
                detect["FT"] = i
            i += 1
            
        return detect
    
    
    ######################################################################################################
    def OnMoveDefaut(self, _xdata, _ydata, axe, event = None):
        # Détection des courbes
        
        # Si l'event a déja été utilisé (par un PlotInteractor)
        # et qu'on ne veut pas qu'il resserve
        if hasattr(event, 'u') and event.u:
            return
        
        detect = self.Detection(event)
    
        # Affichage du label ...
        if detect["FT"] != None:
            self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
            if detect["FT"] == 0:
                coul = self.lstCoul[0].get_coul_str()
                text = _("réponse ajustée")
                     
            elif detect["FT"] == 1:
                coul = self.lstCoul[1].get_coul_str()
                text = _("réponse approximative")
            
                
            setp(self.labelFT, text = text,
                 x = _xdata, y = _ydata, visible = True, color = coul)
            self.draw_artists([self.labelFT])
            self.context = "R"+str(detect["FT"])

        else:
            self.effacerLabels()
            self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
            self.context = ""
            
            
    ######################################################################################################
    def OnMoveEchelle(self, _x, _y, axe):
        if self.mouseInfo != None:
            dx = _x-self.mouseInfo[0]
            rangeX = self.mouseInfo[2][0]
            coefX = 1.0 * dx /100

            deltaX = rangeX[1] - rangeX[0]
            ecartX = deltaX * coefX /2
            rangeX = [rangeX[0] - ecartX, rangeX[1] + ecartX]
            
            dy = _y-self.mouseInfo[1]
            rangeY = self.mouseInfo[2][1]
            coefY = 1.0 * dy /100

            deltaY = rangeY[1] - rangeY[0]
            ecartY = deltaY * coefY /2
            rangeY = [rangeY[0] - ecartY, rangeY[1] + ecartY]

            if rangeX[0] < rangeX[1] and rangeY[0] < rangeY[1]:
                self.calculerEtRedessiner(rangeX, rangeY, initMousInfo = False)
        
        
#    ######################################################################################################
#    def OnWheel(self, event):
#        self.effacerLabels()
#        self.zoneOutils.activerZoomAuto(False)
#        self.setZoomAuto(False)
#
#        step = event.step
#        
#        rangeX = self.getXYlim()[0]
#        coefX = 1.0 * step /100
#
#        deltaX = rangeX[1] - rangeX[0]
#        ecartX = deltaX * coefX /2
#        rangeX = [rangeX[0] - ecartX, rangeX[1] + ecartX]
#
#        
#        rangeY = self.getXYlim()[1]
#        coefY = 1.0 * step /100
#
#        deltaY = rangeY[1] - rangeY[0]
#        ecartY = deltaY * coefY /2
#        rangeY = [rangeY[0] - ecartY, rangeY[1] + ecartY]
#        
#        self.calculerEtRedessiner(rangeX, rangeY, initMousInfo = False)


        
    ######################################################################################################
    def OnMoveCurseur(self, _xdata, _ydata, axe):     
        # restore the clean slate background
#        self.canvas.restore_region(self.background)

        self.restoreBackgroundFig()
        
        if self.valCurseurSurCote:
            #
            # La valeur du temps
            #
            text = "\n"+fonctions.strSc(_xdata)
            self.tickT.update_position(_xdata)
            self.tickT.label1.set_text(text)
            self.tickT.set_visible(True)
            
            axe.draw_artist(self.tickT)
            
            #
            # La valeur de Sortie
            #
#            # On récupère le dernier point de la réponse ...
#            self.param['rangeT'] = [0, _xdata]
#            _y = self.fctReponse(**self.param)[1][-1]

            # Une méthode plus rapide ...
            f = scipy.interpolate.interp1d(self.reponse[0], self.reponse[1])
            _y = f(_xdata)
            
            self.tickS.update_position(_y)
            self.tickS.label1.set_text(fonctions.strSc(_y))
            self.tickS.set_visible(True)
            
            axe.draw_artist(self.tickS)



            self.canvas.blit()

        else:
            # Affichage du temps
            setp(self.txtCurs, position = (_xdata, _ydata),
                 text = fonctions.strSc(_xdata)+" s \n", visible = True)
            
            # Affichage des lignes
            _x = _xdata
#            deltaT = self.getxlim()[1] - self.getxlim()[0]
            self.param['rangeT'] = [0, _x]
            
            # On récupère le dernier point de la réponse ...
            _y = self.fctReponse(**self.param)[1][-1:][0]
            
            coul = globdef.COUL_REPONSE
            # Lignes verticales
            setp(self.vline[0], xdata = array([_x]), color = coul, visible = True)
            self.subplot.draw_artist(self.vline[0])
    
            # Lignes horizontales
            setp(self.hline[0], ydata = array([_y]), color = coul, visible = True)
            self.subplot.draw_artist(self.hline[0])
    
            # Valeur
            setp(self.txtCursGP[0], x = _x , y = _y ,
    #                 horizontalalignment = ha, verticalalignment = va, zorder = ZORDER_MAXI-i+1,
                 text = fonctions.strSc(_y)+"\n", visible = True)
            self.subplot.draw_artist(self.txtCursGP[0])
            
            axe.draw_artist(self.txtCurs)
            self.canvas.blit(self.subplot.bbox)
        
    
    def getMinXY(self, reponse):
        return min(reponse[0]), min(reponse[1])
    
    def getMaxXY(self, reponse):
        return max(reponse[0]), max(reponse[1])
#        maxY = 0.0
#        for pt in diag:
#            maxY = max(maxY, pt[1])
#        return diag[:-1][0][0], maxY



    ######################################################################################################
    def mettreAJourEtRedessiner(self, mesure, reponse):
#        print "mettreAJourEtRedessiner", self.nom
        self.lstCoul = [self.zoneOutils.app.formats["Cons"],
                        self.zoneOutils.app.formats["Rep"]]
        
        self.mesure = mesure
        self.reponse = reponse
        
        
        # Initialisation des lines
        for line in self.lines:
            setp(line, visible = False)

        self.calculerEtRedessiner()
               
        
    ######################################################################################################
    def calculerEtRedessiner(self, rangeX = [], rangeY = [], initMousInfo = True):
        """ Calcul de intervalle de t ...
            ... recalcul des courbes ...
            ... et Tracé de tout ! """
            
#        print "Calculer et redessiner Reponse", rangeX , rangeY ,self.zoomAuto
            
        wx.BeginBusyCursor(wx.HOURGLASS_CURSOR)
        
        if initMousInfo:
            self.mouseInfo = None
        
        if self.zoomAuto:
            self.subplot.set_autoscale_on(True)
        else:
            self.subplot.set_autoscale_on(False)
            if rangeX != []:
                self.subplot.set_xlim(rangeX)
                self.subplot.set_ylim(rangeY)

        if self.zoomAuto:
            T = None
        else:
            if rangeX != []:
                T = rangeX
            else:
                T = self.subplot.get_xlim()
        
        self.TracerTout()
            
        wx.EndBusyCursor()
        

    
    #####################################################################################################    
    def TracerTout(self):
        """ Tracé de tout 
        """
#        print "Tracer tout réponse"
        self.zoneOutils.activerCurseur(False)
        
        #
        # mesure
        #
        coul = self.lstCoul[0].get_coul_str()
        width = self.lstCoul[0].epais
        style = self.lstCoul[0].styl
        
        
        setp(self.lines[0], xdata = self.mesure[0], ydata = self.mesure[1],
                            linewidth = width, color = coul, 
                            visible = True)
        
        #
        # réponse 
        #
        coul = self.lstCoul[1].get_coul_str()
        width = self.lstCoul[1].epais
        style = self.lstCoul[1].styl
        setp(self.lines[1], xdata = self.reponse[0], ydata = self.reponse[1],
                            linewidth = width, linestyle = style, color = coul,
                            visible = True)
        

        if self.zoomAuto:
            self.subplot.relim()
            self.subplot.autoscale_view(tight=False, scalex=True, scaley=True)
            
        
        self.drawCanvas()

        
#           
    ######################################################################################################
    def sauveBackGround(self):
        def sauv():
            self.background = self.canvas.copy_from_bbox(self.subplot.bbox)
            self.backgroundFig = self.canvas.copy_from_bbox(self.figure.bbox)

        wx.CallAfter(sauv)
        
    ######################################################################################################
    def restoreBackground(self, numax = None):
        self.canvas.restore_region(self.background)
    
  



##########################################################################################################
#
#  Zone graphique pour affichage d'une expression
#
##########################################################################################################        
###########################################################################################################
class ZoneGraphPoles(ZoneGraphBase):
    def __init__(self, parent, zoneOutils, nom):
#        self.reponse = None
        self.nom = "Pôles"
        ZoneGraphBase.__init__(self, parent, zoneOutils, nom)
        
        self.ajusterMarges(left = 0.11, right = 0.98, top = 0.93, bottom = 0.16)
        
        #
        # Définition des Artists MPL
        #
        self.initDraw()
        self.modifierTaillePolices()
        self.modifierAntialiased()

        
        
    ######################################################################################################
    def initDraw(self):
#        print "initdraw Pôles"
        
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)

        #
        # Tracé de la Grille
        #
        coul = globdef.FORM_GRILLE.get_coul_str()
        self.subplot.grid(globdef.TRACER_GRILLE, color = coul, 
                          ls = globdef.FORM_GRILLE.styl,
                          lw = globdef.FORM_GRILLE.epais, zorder = 0)#, visible = globdef.TRACER_GRILLE)
        
        #
        # Définition des deux "axes"
        #
        self.subplot.set_ylabel(r"$\Im$")
        self.subplot.set_xlabel(r"$\Re$")
        self.subplot.autoscale_view(tight=False, scalex=False, scaley=False)
        
        self.subplot.axvline(0, linewidth=1, color='k')
        self.subplot.axhline(0, linewidth=1, color='k')
        
        #
        # Fonds colorés
        #
        self.fondVert = self.subplot.axvspan(-1, 0, color = "g", alpha = .2)
        self.fondRouge = self.subplot.axvspan(0, 1, color = "r", alpha = .2)
        
        
        #
        # Pré définition des Tracés des Pôles et des zeros
        #
        
#        self.poles = [self.subplot.plot([0], [0], visible = False, marker = 'o', mfc = coul)] * globdef.NBR_MAXI_PLOT
#        self.label = [self.figure.text(0, 0, "", visible = False, color = coul)] * globdef.NBR_MAXI_PLOT
        self.poles = []
        self.zeros = []
        self.label = self.figure.text(0, 0, "", visible = False, 
                                      color = globdef.COUL_REPONSE, animated = True)
#        for n in range(globdef.NBR_MAXI_PLOT): 
#            self.poles += self.subplot.plot([0], [0], visible = False, marker = 'o', mfc = coul)
#            self.label.append(self.figure.text(0, 0, "", visible = False, color = coul))
        
        try:
            self.calculerMargesFigure()
        except:
            pass
        
    ######################################################################################################
    def modifierTaillePolices(self):
        setp(self.subplot.get_xaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        setp(self.subplot.get_yaxis().get_ticklabels(), fontsize = self.fontSizes["FONT_SIZE_GRAD"])
        
        setp(self.subplot.get_yaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        setp(self.subplot.get_xaxis().get_label(), fontsize = self.fontSizes["FONT_SIZE_LABEL_AXE"])
        
        setp(self.label, fontsize = self.fontSizes["FONT_SIZE_LABEL"])
        

   
    ##################################################################################################### 
    def effacerLabels(self): 
#        self.canvas.restore_region(self.backgroundFig) 
        setp(self.label, visible = False)
#        self.figure.draw_artist(self.label)
        self.draw_artists([self.label], self.figure)
 

    ######################################################################################################
    def OnWheel(self, event):
        return

    ######################################################################################################
    def setCouleurs(self):
        for p in self.poles + self.zeros: 
            p.set_mfc(globdef.COUL_POLES)
        
#        self.drawCanvas()
        
    ######################################################################################################
    def Detection(self, event):
        detect = {"PO": None,
                  "ZE": None,
                  }

        continuer = True
        i = 0
        while continuer:
            if i >= len(self.poles):
                continuer = False
            elif self.poles[i].contains(event)[0]:
                continuer = False
                detect["PO"] = i
            i += 1
        
        continuer = True
        i = 0
        while continuer:
            if i >= len(self.zeros):
                continuer = False
            elif self.zeros[i].contains(event)[0]:
                continuer = False
                detect["ZE"] = i
            i += 1
            
        return detect
            
    ######################################################################################################
    def OnMoveDefaut(self, _xdata, _ydata, axe, event = None):
        # Détection des poles
  
        # Si l'event a déja été utilisé (par un PlotInteractor)
        # et qu'on ne veut pas qu'il resserve
        if hasattr(event, 'u') and event.u:
            return
        
        if _xdata == None or _ydata == None:
            self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
            self.effacerLabels()
            return
            
        detect = self.Detection(event)
    
        # Affichage du label ...
        if detect["PO"] != None or detect["ZE"] != None:
            self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_ISO))
            
            if detect["PO"] != None:
                text = r"$ p_{"+str(detect["PO"])+"}="+strScCx(self.lstPoles[detect["PO"]], nbChiffres = 2)+"$"
                self.context = "Z"+str(detect["PO"])
            else:
                text = r"$ z_{"+str(detect["ZE"])+"}="+strScCx(self.lstZeros[detect["ZE"]], nbChiffres = 2)+"$"
                self.context = "Z"+str(detect["ZE"])
                    
            
            # Position du pointeur souris (en pixels)
            x, y = event.x, event.y
            
            # Adaptation pour que le text soit visible sur la figure
            l, h = self.label.get_window_extent().size
            lf, hf = self.figure.get_window_extent().size
            if l+x > lf:
                x = lf - l
            
            # Passage en coordonnées transFigure (0-1)
            inv = self.figure.transFigure.inverted()
            _x, _y = inv.transform((x, y))
            
            setp(self.label, x = _x, y = _y, text = text,
                 visible = True)
            
            self.draw_artists([self.label], self.figure)
            
            

        else:
            self.effacerLabels()
            self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
            self.context = ""
    
    def getMinXY(self, poles):
        return min(real(poles)), min(imag(poles))
    
    def getMaxXY(self, poles):
        return max(real(poles)), max(imag(poles))




    ######################################################################################################
    def mettreAJourEtRedessiner(self, lstPoles, lstZeros,  **kwargs):
        if hasattr(self, 'lstPoles'):
            for i, p in enumerate(self.lstPoles):
                setp(self.poles[i], visible = False)
        self.lstPoles = lstPoles
        
        if hasattr(self, 'lstZeros'):
            for i, p in enumerate(self.lstZeros):
                setp(self.zeros[i], visible = False)
        self.lstZeros = lstZeros
#        for i, p in enumerate(self.lstPoles):
#            setp(self.label[i], x = real(p), y = imag(p), text = strScCx(p))

        self.calculerEtRedessiner()
     
        
    ######################################################################################################
    def calculerEtRedessiner(self, rangeX = [], rangeY = [], initMousInfo = True):
        """ Calcul de intervalle de t ...
            ... recalcul des courbes ...
            ... et Tracé de tout ! """
            
#        print "Calculer et redessiner Reponse", rangeX , rangeY ,self.zoomAuto
        self.subplot.set_autoscale_on(True)
        
        self.TracerTout()
        
        
    
    #####################################################################################################    
    def TracerTout(self):
        """ Tracé de tout 
        """
#        print "Tracer tout Pôles"
        
        #
        # Propriétés des Pôles
        #
        minX, maxX = 0, 0
        minY, maxY = 0, 0
        
        for l in self.poles:
            l.remove()
            
        self.poles = []
        
        for i,p in enumerate(self.lstPoles):
            self.poles += self.subplot.plot([real(p)], [imag(p)], 
                                            visible = True, marker = 'o', 
                                            mfc = globdef.COUL_POLES)
#            self.label.append(self.figure.text(real(p), imag(p), strScCx(p), visible = False, color = coul))
            
            minX = min(minX, real(p))
            maxX = max(maxX, real(p))
            minY = min(minY, imag(p))
            maxY = max(maxY, imag(p))
        
        for i,p in enumerate(self.lstZeros):
            self.zeros += self.subplot.plot([real(p)], [imag(p)], 
                                            visible = True, marker = 'x', 
                                            mfc = 'None', mec = 'k')
#            self.label.append(self.figure.text(real(p), imag(p), strScCx(p), visible = False, color = coul))
            
            minX = min(minX, real(p))
            maxX = max(maxX, real(p))
            minY = min(minY, imag(p))
            maxY = max(maxY, imag(p))
            
        if minX == maxX:
            minX, maxX = -0.1, 0.1
        if minY == maxY:
            minY, maxY = -0.1, 0.1
            
        self.fondVert.remove()
        self.fondRouge.remove()
        
#        minX, maxX = self.subplot.get_xlim()
#        minY, maxY = self.subplot.get_ylim()
#        
#        maxX = max(maxX, 0)
#        minX = min(minX, 0)
        
        pc = 0.1
        dx = (maxX - minX) * pc  
        dy = (maxY - minY) * pc  
        minX, maxX = minX-dx, maxX+dx
        minY, maxY = minY-dy, maxY+dy
        
        self.subplot.set_xlim([minX, maxX])
        self.subplot.set_ylim([minY, maxY])
#        self.subplot.relim()
        
        self.fondVert  = self.subplot.axvspan(self.subplot.get_xlim()[0], 0, color = "g", alpha = .2)
        self.fondRouge = self.subplot.axvspan(0, self.subplot.get_xlim()[1], color = "r", alpha = .2)

        self.subplot.set_xlim([minX, maxX])
        self.subplot.set_ylim([minY, maxY])
        
        self.drawCanvas()

    
    ######################################################################################################    
    def getContenuExport(self):
        contenu = []
        images = []
        R = []
        I = []
        for i,p in enumerate(self.lstPoles):
            R.append(real(p))
            I.append(imag(p)) 
        contenu.append(("Pôles Re", R))
        contenu.append(("Pôles Im", I))
        
        R = []
        I = []
        for i,p in enumerate(self.lstZeros):
            R.append(real(p))
            I.append(imag(p)) 
        contenu.append(("Zéros Re", R))
        contenu.append(("Zéros Im", I))

        return contenu, images
    
    
#           
    ######################################################################################################
    def sauveBackGround(self):
        self.background = self.canvas.copy_from_bbox(self.subplot.bbox)
        self.backgroundFig = self.canvas.copy_from_bbox(self.figure.bbox)
        
    ######################################################################################################
    def restoreBackground(self, ax):
        if ax == self.figure:
            self.canvas.restore_region(self.backgroundFig)
        else:
            self.canvas.restore_region(self.background)
    
    
        
##########################################################################################################
#
#  Zone graphique pour affichage d'une expression
#
##########################################################################################################        
class ZoneGraphExpression(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style = wx.FULL_REPAINT_ON_RESIZE)
        self.SetAutoLayout(True)
        self.parent = parent
        self.expression = ''
        
        #
        # Les éléments de base pour MatPlotLib
        #
        self.figure = Figure()
#        self.figure.subplots_adjust(left = 0.08, right = 0.98, top = 0.98, bottom = 0.08, hspace = 0.0)
        self.canvas = FigureCanvas(self, -1, self.figure)
#        self.ntb = NavigationToolbar(self.canvas)
#        self.ntb.Show(False)
        
        self.figure.set_facecolor(globdef.COUL_BLANC)
        
        self.texte = self.figure.text(0.05, 0.05, self.expression, fontsize = globdef.FONT_SIZE_EXPR)#, antialiased = False)
    
        self.Bind(wx.EVT_SIZE, self.sizeHandler)
    
    ######################################################################################################
    def sizeHandler(self, *args, **kwargs):
        self.canvas.SetSize(self.GetSize())
        self.canvas.draw()
        
        
    ######################################################################################################
    def calculerEtRedessiner(self, expression):
        """"""
        setp(self.texte, text = expression)
        self.tracer()
        
    def tracer(self):
        self.canvas.draw()
        

     
     


###################################################################################################
#
# Renvoie les alignements (format matplotlib) pour afficher un texte auprés d'une courbe
#  deriv  : indique le signe de la dérivée de la courbe à l'endroit de l'affichage
#  invers : indique si on veut un affichage au dessus ou au dessous
#
###################################################################################################
def getAlignment(deriv, invers):
    """ Renvoie les alignements (format matplotlib) pour afficher un texte auprés d'une courbe
            deriv  : indique le signe de la dérivée de la courbe à l'endroit de l'affichage
            invers : indique si on veut un affichage au dessus ou au dessous
    """
    if invers:
        va = 'bottom'
        if deriv > 0:
            ha = 'right'
        else:
            ha = 'left' 
    else:
        va = 'top'
        if deriv < 0:
            ha = 'right'
        else:
            ha = 'left'
        
    if va == 'bottom':
        s1 = ""
        s2 = ""#"\n"
    else:
        s1 = ""#"\n"
        s2 = ""
    return va, ha, s1, s2
        

#def get_coefx(axes):
#    deltaR = log10(axes.get_xlim()[1]/axes.get_xlim()[0])
#    deltaE = axes.bbox.get_points()[1][0] - axes.bbox.get_points()[0][0]
#    return deltaE/deltaR
#
#def get_coefy(axes):
#    deltaR = axes.get_ylim()[1]-axes.get_ylim()[0]
#    deltaE = axes.bbox.get_points()[1][1] - axes.bbox.get_points()[0][1]
#    return deltaE/deltaR

###################################################################################################
#
# Création des lignes "isoGain"
#
###################################################################################################
#
# Liste des isogains qui seront Tracés
#
listeIsoGains = [-150, -100, -80, -70, -60, -55, -50, -45, -40, -35, -30, -25, -20, -18, -16, -12, -10, -8, -6, -5, -4, -3, -2, -1, -0.5,\
                 0, 0.5, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30]

#
# Calcul de la "nappe" isoGain
#
def getIsoGains(rangeP = [-360.0, 180.0], rangeG = [-150.0, 150.0]):
    """ Renvoie une "nappe" isogain
    """
    with errstate(invalid='ignore'): 
        # Création d'une grille, dans le plan de Black (coordonnées FTBO)
        g = arange(rangeG[0], rangeG[1], (rangeG[1] - rangeG[0])/300) 
        p = arange(rangeP[0], rangeP[1], (rangeG[1] - rangeG[0])/108)
        P, G = meshgrid(p, g)
    
        # Passage GdB --> G et P° --> Prad 
        _G = 10**(G/20.0)
        _P = pi*P/180.0
        
        # Calcul des "hauteurs" isogain
        iso = _G/(absolute(cos(_P) - 1j*sin(_P) + _G))
    
        return G, P, 20*log10(iso)





###################################################################################################
#
# Création des lignes "isoPhase"
#
###################################################################################################

#
# Liste des isophases qui seront Tracés
#
listeIsoPhases = [-180, -170, -160, -150, -140, -130, -120, -110, -100, -90, -80, -70, -60, -50, \
                 -45, -40, -35, -30, -25, -20, -15, -12, -10, -9, -8, -7, -6, -5, \
                 -4, -3, -2.5, -2, -1.5, -1]

#
# Liste des bornes des isoPhases (pour qu'elles ne soient pas trop ressérrées à certains endroits)
#
listeBorneSupIsoPhases = [15, 12, 15, 12, 15, 12, 15, 12, 15, 12, 15, 12, 15, 12, \
                          15, 12, 12, 15, 12, 12, 8, 12, 5, 8, 5, 8, 5, 6, \
                          3, 6, 3, 5, 2, 5]
listeBorneInfIsoPhases = [-60, -60, -60, -60, -60, -60, -60, -60, -60, -60, -60, -60, -60, -60, \
                          -20, -60, -20, -60, -20, -60, -20, -10, -60, -5, -10, -5, -10, -5, \
                          -10, -5, -3, -10, -2, -5]

# 
# Copies et symétrie pour les intervalles [-360, -180] et [0, 180]
#
def repartir(lst, offset = 0):
    with errstate(invalid='ignore'): 
        inv = (offset - array(lst)).tolist()
        inv.reverse()
        return array(inv).tolist() + array(lst).tolist()

def inverse(lst, offset = 0):
    with errstate(invalid='ignore'): 
        inv = (offset - array(lst)).tolist()
        inv.reverse()
        return array(inv).tolist()

def repartirsym(lst):
    with errstate(invalid='ignore'): 
        inv = array(lst).tolist()
        inv.reverse()
        return array(inv).tolist() + array(lst).tolist() + array(inv).tolist()

#listeIsoPhases = repartir(listeIsoPhases, -360)
listeIsoPhases = inverse(listeIsoPhases, -360) + array(listeIsoPhases).tolist() + inverse(listeIsoPhases)
listeBorneSupIsoPhases = repartirsym(listeBorneSupIsoPhases)
listeBorneInfIsoPhases = repartirsym(listeBorneInfIsoPhases)

#
# Gains pour un bonne répartition des points des isoPhases
#
def repartirIsoGains(Gmax = 40):
    def base():
        return [0.01, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45,\
                0.5, 0.6, 0.7, 0.8, 0.9,\
                1, 1.2, 1.4, 1.6, 1.8, \
                2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18,\
                20,25,30,35,40,45,50,60]
    with errstate(invalid='ignore'): 
        moins = base()
        moins.reverse() 
        moins = -array(moins)
        moins = moins.tolist()
        return moins + [0] + base()

listePtsIsoGains = repartirIsoGains()
       

###################################################################################################
def getIsoPhases(coul):
    """ Renvoie toutes les lignes "isoPhase" prévues dans <listeIsoPhases>
        sous la forme de "segments" pour une LineCollection
    """
    lst = []
    for i,p in enumerate(listeIsoPhases):
        lst.append(getIsoPhase(p, i))
    return lst
#    return LineCollection(lst, colors = coul, zorder = 1)


###################################################################################################
def getIsoPhase(Phi, borne):
    """ Calcul des points de l'isoPhase PhiBF = cste 
        dans la base de la FTBO (Phi, GdB)
    """
    with errstate(invalid='ignore'): 
        dr = 180.0/pi
        Phideg = Phi/dr
        sinP = sin(Phideg)
        cosP = cos(Phideg)
        
        pts = []
        i = 0
        continuer = True
        while continuer:
            GdB = float(listePtsIsoGains[i])
            if GdB >= listeBorneInfIsoPhases[borne]:
                G = 10**(GdB/20)
                p = arctan2((sinP/G), (cosP/G-1))*dr
                if Phi < -180:
                    p = -360 + p
                g = -10*log10((cosP/G-1)**2+(sinP/G)**2)
                pts.append((p,g))#, GdB)) 
            i +=1 
            if GdB >= listeBorneSupIsoPhases[borne] or i >= len(listePtsIsoGains):
                continuer = False
                
        return pts

###################################################################################################
def getIsoPhasePlot(Phi, borne):
    """ Renvoie les "data" pour tracer une ligne d'isoPhase
        sous la forme d'un array 2D: x, y
    """
    with errstate(invalid='ignore'): 
        return array(getIsoPhase(Phi, borne)).transpose()



###################################################################################################


###################################################################################################
def removeArtist(a, ax = None):
    if ax == None:
#        ax = a.get_axes()
        ax = a.axes
    if isinstance(a, matplotlib.lines.Line2D):
        if a in ax.lines:
            ax.lines.remove(a)
    else:
        try:
            a.remove()
        except:# NotImplementedError:
            for c in a.get_children():
                removeArtist(c, ax)
    
###########################################################################################################
#
#  Pour modifier une courbe
#
############################################################################################################
class PlotInteractor:
    """
    An polygon editor.

    Key-bindings

      't' toggle vertex markers on and off.  When vertex markers are on,
          you can move them, delete them

      'd' delete the vertex under point

      'i' insert a vertex at point.  You must be within epsilon of the
          line connecting two existing vertices

    """

    showverts = True
    epsilon = 5  # max pixel distance to count as a vertex hit

    def __init__(self, parent, ax, poly, action_redess, action_efface, is_activ):
#        print "Init PlotInteractor"
        self.parent = parent
        
        if poly.figure is None:
            raise RuntimeError('You must first add the polygon to a figure or canvas before defining the interactor')
        self.ax = ax
        self.action_redess = action_redess
        self.action_efface = action_efface
        self.is_activ = is_activ
        canvas = poly.figure.canvas
        
        self.poly = poly
#        getp(self.poly)
        
        # Le point de contrôle actif
        self._ind = None 

        canvas.mpl_connect('draw_event', self.draw_callback)
        canvas.mpl_connect('button_press_event', self.button_press_callback)
#        canvas.mpl_connect('key_press_event', self.key_press_callback)
        canvas.mpl_connect('button_release_event', self.button_release_callback)
        self.m_connect = canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        
        self.canvas = canvas
        
        
#    #########################################################################################################
#    def is_activ(self):
#        return self.parent.fctConsigne == None
        
        
    #########################################################################################################
    def get_nbPt(self):
        return len(self.poly.get_xdata())
    

    #########################################################################################################
    def draw_callback(self, event):
        if not self.is_activ():
            return
        self.parent.background = self.canvas.copy_from_bbox(self.ax.bbox) 
        self.ax.draw_artist(self.poly)
        self.canvas.blit(self.ax.bbox)


    #########################################################################################################
    def get_ind_under_point(self, event):
        'get the index of the vertex under point if within epsilon tolerance'
        with errstate(invalid='ignore'): 
            xy = asarray(self.poly.get_data()).transpose()
            xyt = self.poly.get_transform().transform(xy)
            xt, yt = xyt[:, 0], xyt[:, 1]
            d = sqrt((xt-event.x)**2 + (yt-event.y)**2)
            indseq = nonzero(equal(d, amin(d)))[0]
            ind = indseq[0]
    
            if d[ind]>=self.epsilon or ind == 0:
                if self.poly.contains(event)[0] and self.get_part(event.xdata) == self.get_nbPt()-2:
                    ind = -1
                    event.u = True
                else:
                    ind = None
            else:
                event.u = True
            
            if ind == self.get_nbPt() - 1:
                ind = -1
                
            return ind


    #########################################################################################################
    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        if not self.is_activ():
            return
        if not self.showverts: return
        if event.inaxes==None: return
        
        self.parent.disconnectAllEvents()
        # On reconnecte ici pour être sûr que cette connexion a lieu en dernier
#        self.canvas.mpl_disconnect(self.m_connect)
#        self.m_connect = self.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        
        #
        # Bouton gauche
        #
        if event.button == 1:
            self._ind = self.get_ind_under_point(event)
            # Click sur un point de contrôle
#            if self._ind != None:
#                print "Click :",self._ind
                
                
        #
        # Bouton Droit
        #
        elif event.button == 3:
            self._ind = self.get_ind_under_point(event)
            
            # RClick sur un point de contrôle --> Suppression du point
            if self._ind != None and self._ind != -1:

                if self.get_nbPt() > 1:
#                    _x, _y = self.poly.get_data()
#                    _x, _y = _x.tolist(), _y.tolist()
                    del self.x[self._ind]
                    del self.y[self._ind]
                    self.set_data_redess()
                    
                    
            # RClick sur un segment --> Ajout d'un nouveau point
            elif self.poly.contains(event)[0]:
                x = event.xdata
                i = self.get_part(x)
                if i != -1:
                    self.action_efface()
                    
                    self.y.insert(i+1, self.get_y(x))
                    self.x.insert(i+1, x)
                    self.set_data_redess()

                
                
    
    #########################################################################################################
    def button_release_callback(self, event):
        'whenever a mouse button is released'
        if not self.is_activ():
            return
        if not self.showverts: return
#        if event.button != 1: return
        self._ind = None
        self.action_redess()
        self.parent.connectAllEvents()
        return

#    def key_press_callback(self, event):
#        'whenever a key is pressed'
#        if not self.is_activ():
#            return
#        if not event.inaxes: return
#        if event.key=='t':
#            self.showverts = not self.showverts
###            self.line.set_visible(self.showverts)
#            if not self.showverts: self._ind = None
#        elif event.key=='d':
#            ind = self.get_ind_under_point(event)
#            if ind is not None:
#                self.poly.xy = [tup for i,tup in enumerate(self.poly.xy) if i!=ind]
###                self.line.set_data(zip(*self.poly.xy))
#        elif event.key=='i':
#            xys = self.poly.get_transform().transform(self.poly.xy)
#            p = event.x, event.y # display coords
#            for i in range(len(xys)-1):
#                s0 = xys[i]
#                s1 = xys[i+1]
#                d = dist_point_to_segment(p, s0, s1)
#                if d<=self.epsilon:
#                    self.poly.xy = array(
#                        list(self.poly.xy[:i]) +
#                        [(event.xdata, event.ydata)] +
#                        list(self.poly.xy[i:]))
###                    self.line.set_data(zip(*self.poly.xy))
#                    break
#
#
#        self.canvas.draw()

    
    #########################################################################################################
    def motion_notify_callback(self, event):
        'on mouse movement'
        with errstate(invalid='ignore'): 
            if not self.is_activ():
                return
            
            if not self.showverts: return
            if event.inaxes is None: return
            
            #
            # Si on n'a pas cliqué sur un truc interessant (point de contrôle ou segment)
            #
            if self._ind is None: 
                ind = self.get_ind_under_point(event)
                if ind == -1:
                    self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_HAUT_BAS))
                    self.action_efface()
    #                event.u = True
                elif ind != None:
                    self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_CROIX))
                    self.action_efface()
    #                event.u = True
    #            else:
    #                return
    #                self.canvas.SetCursor(wx.StockCursor(globdef.CURSEUR_DEFAUT))
                return
            
            if event.button != 1: return
            
            # Pour dire qu'il ne faut pas faire autre chose avec cet event
    #        event.u = True
            
            x,y = event.xdata, event.ydata
            
            # On fait glisser le dernier segment
            if self._ind == -1 or self._ind == self.get_nbPt() - 1:
                i = self.get_nbPt()-1
                x0, y0 = self.x[i-1], self.y[i-1]
                if x-x0 != 0:
                    a = (y-y0)/(x-x0)
                    b = y0 - a*x0
                    self.y[i] = a*self.x[i] + b
                    self.set_data_redess()
                    
            # On fait glisser le point de contrôle <self._ind>
            else:
                if x < self.x[self._ind-1]:
                    x = self.x[self._ind-1]
                elif x > self.x[self._ind+1]:
                    x = self.x[self._ind+1]
                    
                self.x[self._ind], self.y[self._ind] = x, y
                self.set_data_redess()
        
        
        
        
    #########################################################################################################
    def set_data_redess(self, _x = None, _y = None):
        if _x != None:
            self.x = _x
        if _y != None:
            self.y = _y
        self.poly.set_data(self.x, self.y)
        self.redess()
    
    
    #########################################################################################################   
    def set_xMax(self, xMax):
        n = self.get_nbPt()
#        a = (self.y[n-2] - self.y[n-1])/(self.x[n-2] - self.x[n-1])
#        b = self.y[n-2] - a * self.x[n-2]
#        yMax = a * xMax +b
        self.y[n-1] = self.get_y(xMax)
        self.x[n-1] = xMax
        
        self.set_data_redess()
        
        
    #########################################################################################################
    def redess(self):
        try:
            self.canvas.restore_region(self.parent.background)
        except:
            pass
        self.ax.draw_artist(self.poly)
        self.canvas.blit(self.ax.bbox)
        
        
    #########################################################################################################
    def getPlot(self):
        return self.poly.get_xdata(), self.poly.get_ydata()


    #########################################################################################################
    def get_part(self, x):
        """ Renvoie l'index du 1er point du segment contenant <x>
        """
        _x = self.poly.get_xdata()
        i = 0
        continuer = True
        while continuer:
            if _x[i] > x or i >= self.get_nbPt()-1:
                continuer = False
            else:
                i += 1
        return i - 1

    
    #########################################################################################################
    def get_y(self, x):
        """ Renvoie l'ordonnée correspondant à l'abscisse <x>
        """
        with errstate(invalid='ignore'): 
            i = self.get_part(x)
            
            _x = self.poly.get_xdata()
            _y = self.poly.get_ydata()
    
            y0 = _y[i]
            y1 = _y[i+1]
            x0 = _x[i]
            x1 = _x[i+1]
            
            if x1-x0 > 0:
                a = (y1-y0)/(x1-x0)
                b = y0 - a*x0
                return a*x+b
            else:
                return None
        
        
        
    #########################################################################################################
    def getRegularPlot(self, rangeT):
        consigne = self.getPlot()
        if rangeT == None: # Echelle auto
            rangeT = [consigne[0][0], consigne[0][-1]]
        dt = (rangeT[1] - rangeT[0])/globdef.NBR_PTS_REPONSE
        
        T = []
        Y = []
        t = 0.0
        continuer = True
        while continuer:
            if t > rangeT[1]:
                continuer = False
            else: 
                T.append(t)
                Y.append(self.get_y(t))
                t += dt
     
        return Y, T
    
    #########################################################################################################
    def getRegularPlot2(self, rangeT):
        consigne = self.getPlot()
        if rangeT == None: # Echelle auto
            rangeT = [consigne[0][0], consigne[0][-1]]
        dt = (rangeT[1] - rangeT[0])/globdef.NBR_PTS_REPONSE
        T = []
        Y = []
        t = 0.0
        for i, t0 in enumerate(consigne[0][:-1]):
            y0 = consigne[1][i]
            y1 = consigne[1][i+1]
            t1 = consigne[0][i+1]
            T.append(t0)
            Y.append(y0)
            if t1-t0 > 0:
                a = (y1-y0)/(t1-t0)
                b = y0 - a*t0
                continuer = True
                while continuer:
                    if t > t1:
                        continuer = False
                    else:
                        T.append(t)
                        Y.append(a*t+b)
                        t += dt
        return Y, T
        
class DegreeFormatter(Formatter):
    def __call__(self, x, pos=None):
        # \u00b0 : degree symbol
        return "%d\u00b0" % x


###########################################################################""
def getFileBitmap(ft, i):
    """ Renvoie le nom d'un fichier temporaire 
        d'une image de l'expression de la ft
        ainsi que sa hauteur
    """
    dir = tempfile.mkdtemp("exportExcel")
    file = os.path.join(dir, str(i)+'.bmp')
    bmp = ft.getBitmap(taille = 200)
    
    b=wx.EmptyBitmap(bmp.GetWidth(), bmp.GetHeight())
    mdc=wx.MemoryDC()
    mdc.SelectObject(b)
    mdc.SetBackground(wx.WHITE_BRUSH)
    mdc.Clear() 
    mdc.DrawBitmap(bmp, 0, 0, True)
    mdc.SelectObject(wx.NullBitmap) 
    bmp = b
    img = bmp.ConvertToImage()
    img.SaveFile(file, wx.BITMAP_TYPE_BMP )
    h = img.GetHeight()
    return file, h


############################################################################################
#
#
# Fonction renvoyant un échantillon de ligne au format wxBitmap
#
#
############################################################################################ 
CANVAS_PARENT = None

def EchantillonLigne(size, style, marker, color, width):
    global CANVAS_PARENT
    fig = Figure()#, dpi = 1)
    
    fig.set_figheight(1.0*size[1]/fig.dpi)
    fig.set_figwidth(1.0*size[0]/fig.dpi)
    fig.set_facecolor('#FFFFFF')
    if CANVAS_PARENT == None:
#        print "CANVAS_PARENT"
        CANVAS_PARENT = wx.Frame(None, -1, size = size, style= wx.BORDER_NONE)
#        CANVAS_PARENT.Show()
    canvas = FigureCanvas(CANVAS_PARENT, -1, fig)
    l1 = matplotlib.lines.Line2D([0, 0.5, 1], [0.5, 0.5, 0.5],
                                 transform=fig.transFigure, figure=fig,
                                 color = color, 
                                 linewidth = width,
                                 marker = marker, 
                                 linestyle = style)
    fig.lines.extend([l1])
    fig.canvas.draw()
    return fig.canvas.bitmap


