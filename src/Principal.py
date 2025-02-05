#!/usr/bin/env python
# -*- coding: utf-8 -*-

##This file is part of PySylic
#############################################################################
#############################################################################
##                                                                         ##
##                              Principal                                  ##
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
#    along with PySylic; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


from CedWidgets import *
import version

try:
    from agw import aui
except ImportError:
    import wx.lib.agw.aui as aui
    
import sys
import Images

#import wx.lib.hyperlink as hl
import wx.adv
#import wx.lib.agw.foldpanelbar as fpb

#import wx.lib.agw.floatspin as fs
#import wx.lib.agw.labelbook as lb
#from wx.lib.agw.fmresources import *
from wx.lib.wordwrap import wordwrap



#import os#, sys,  traceback, xml

# modules propres de PySyLiC
#import globdef
import calcul
#import fonctions
import Options

import graphmpl as graph

from LineFormat import LineFormat, SelecteurFormatLigne, EVT_FORMAT_MODIFIED

#if globdef.USE_MATPLOTLIB:
#    import graphmpl as graph
#else:
#    import graph
#    import export
    
from fonctions import FonctionTransfertFact, FonctionTransfertDev, SelFTEvent, \
                      SelecteurFTFact, FonctionTransfertCorrec, myEVT_FT_MODIFIED, \
                      SelecteurFTDev, SelecteurFTFit, EVT_FT_MODIFIED
from scipy.signal import residue

import xml.etree.ElementTree as ET

#if globdef.USE_THREAD:
#    import threading

#import NotebookCtrl as NB
#try:
#    import agw.flatnotebook as NB
#except ImportError: # if it's not there locally, try the wxPython lib.
#    import wx.lib.agw.flatnotebook as NB

class WindowUpdateLocker(object):
    """
    Python translation of wxWindowUpdateLocker.
    Usage:
    with WindowUpdateLocker(window):
        do this, do that...
    thawn again
    """
    def __init__(self, window):
        self.window = window
    
    def __enter__(self):
        if self.window is not None:
            self.window.Freeze()
       
        return self.window
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.window is not None:
            self.window.Thaw()
#---------------------------------------------------------------------------
class wxPySylic(wx.Frame, PrintHandler):

    def __init__(self, parent, title ="" , nomFichier = None):
        wx.Frame.__init__(self, parent, -1, title, 
                          style= wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
#        wx.DEFAULT_FRAME_STYLE |
#        self.Freeze()
        WindowUpdateLocker(self)
        self.version = version.__version__
        
        self.DossierSauvegarde = globdef.DOSSIER_EXEMPLES
        
        # Indique si le tracé à l'écran est à jour (option : MAJ_AUTO = False)
        self.traceAJour = True
        
        #
        # Selection des Tracés
        #
        # Page H
        self.TracerH = True
        self.additionner = True
        self.lstTracerSsFT = []
        
        # Page C
        self.CorTracerH = True
        self.CorTracerC = True
        self.CorTracerCH = True
        
        # Page FT
        self.tracerFTBO = True
        self.tracerFTBF = True
        
        #
        # Tracés annexes (autres fenetres)
        #
        self.TracerReponse = False
        self.TracerMarges = False
        self.TracerPoles = False
        self.TracerDecomp = False
        
        #
        # Les formats de ligne des diagrammes
        #
        self.formats = {}
        self.initFormats()
           
        #
        # Les positions des expressions
        #
        self.positionsExpr = {}
        self.initPositionsExpr()
        
        #
        # Taille et position de la fenêtre
        #
#        self.SetMinSize((800,570)) # Taille mini d'écran : 800x600
        self.SetSize((1024,738)) # Taille pour écran 1024x768
        # On centre la fenêtre dans l'écran ...
        self.CentreOnScreen(wx.BOTH)
        # On applique l'icone
#        ico = wx.Icon(os.path.join(globdef.DOSSIER_IMAGES,'icone.ico'), wx.BITMAP_TYPE_ICO)
        ico = Images.Icone.GetIcon()
        self.SetIcon(ico)

        # Use a panel under the AUI panes in order to work around a
        # bug on PPC Macs
        pnl = wx.Panel(self)
        self.pnl = pnl
        
        self.mgr = aui.AuiManager()
        self.mgr.SetManagedWindow(pnl)

        #
        # Barre de status ... à faire
        #
#        self.statusBar = PyVotStatusBar(self)
#        self.SetStatusBar(self.statusBar)
#        self.statusBar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)
#        self.statusBar.SetFieldsCount(2)
#        self.statusBar.SetStatusWidths([-1,100])
#        self.statusBar.SetStatusStyles(1, wx.SB_RAISED)
        
        #############################################################################################
        # Instanciation et chargement des options
        #############################################################################################
        options = Options.Options()
        if options.fichierExiste():
#            options.ouvrir()
            try :
                options.ouvrir()
            except:
                print("Fichier d'options corrompus ou inexistant !! Initialisation ...")
                options.defaut()

        
        # On applique les options ...
        self.DefinirOptions(options)
        # Option à n'appliquer qu'au démarrage de pySyLiC
        globdef.NBR_MAXI_PLOT = options.optGenerales["NBR_MAXI_PLOT"]
        
        
        #############################################################################################
        # On lance l'internationalisation
        #############################################################################################
        globdef.SetInternationalization()
        self.change_langue = False
        
        #############################################################################################
        # Initialisation des FT
        #############################################################################################
        self.FT_H = None
        self.FT_C = None
        self.FTBF = []
        self.FTBFnc = []
        self.FTBO = []
        self.num = 0
        
        ################################################################################################
        # NoteBook de gauche
        #################################################################################################
        self.nbGauche = NbGauche(pnl, self.getNum, self.setNum, self.getFT_H, self.setFT_H,
                                 self.getFT_C, self.setFT_C,
                                 self.getFTBO, self.getFTBF, app = self)
        
        
        ###############################################################################################
        # Fenetres de tracé
        ###############################################################################################
        
#        tps1 = time.clock()
        self.zoneGraph = graph.ZoneGraph(pnl, self, self.tracer)
#        tps2 = time.clock()    
#        print "Création zoneGraph :", tps2 - tps1
        
#        tps1 = time.clock()
        self.winReponse = WinReponse(self, self.getNum, self.setNum, self.getFTBF, self.getFTBFnc)
        self.winMarge = WinMarge(self, self.getNum, self.getFTBO)
        self.winPoles = WinPoles(self, self.getNum, self.getFTBF)
        self.winDecompose = WinDecompose(self, self.getNum, self.getFTBF, self.getFTBO)
#        tps2 = time.clock()    
#        print "Création Fenêtres :", tps2 - tps1


        #############################################################################################
        # Mise en place des morceaux
        #############################################################################################
        self.mgr.AddPane(self.zoneGraph, 
                         aui.AuiPaneInfo().
                         CenterPane().
#                         Caption("Bode").
                         PaneBorder(False).
                         Floatable(False).
                         CloseButton(False)
#                         Name("Bode")
#                         Layer(2).BestSize(self.zoneGraph.GetMaxSize()).
#                         MaxSize(self.zoneGraph.GetMaxSize())
                        )

   
        
        #############################################################################################
        # Barre d'outils
        #############################################################################################
        self.tb = BarreOutils(pnl, self)
        self.mgr.AddPane(self.tb, 
                         aui.AuiPaneInfo().
#                         Name("tb1").
#                         ToolbarPane().
                         Top().Layer(3).
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
        
        self.mgr.AddPane(self.nbGauche,
                         aui.AuiPaneInfo().
                         Left().Layer(2).BestSize((264, -1)).
                         MinSize((262, -1)).
                         Caption(_("Définition du Systéme")).
#                         CaptionVisible(False).
                         GripperTop().
                         Floatable(True).FloatingSize((264, 700)).
                         TopDockable(False).BottomDockable(False).
                         CloseButton(False).
                         PaneBorder(False)
#                         Name("Action")
                         )
        
        self.mgr.Update()
#        self.mgr.SetFlags(self.mgr.GetFlags() ^ wx.aui.AUI_MGR_TRANSPARENT_DRAG)
      
        
        
        
        
        #
        # On ouvre le fichier .syl passé en argument
        #
        if nomFichier is not None:
            self.ouvrir(nomFichier)
        else :
            nomFichier = ''
#        wx.CallAfter(self.definirNomFichierCourant, nomFichier)
        
        self.definirNomFichierCourant(nomFichier = '', modif = False)
        
        ###############################################
        ###############################################
        # Tout ce qu'il faut pour imprimer ...
        ###############################################
        ###############################################
        self.initPrintHandler(PrintoutWx, self, globdef.PRINT_PAPIER_DEFAUT, globdef.PRINT_MODE_DEFAUT)
        
        ###############################################
        ###############################################
        # Gestion des Evenements ...
        ###############################################
        ###############################################
        self.Bind(EVT_FT_MODIFIED, self.OnFTModified)
        self.nbGauche.Bind(EVT_FORMAT_MODIFIED, self.OnFormatModified)
        
        # Interception de la demande de fermeture
        self.Bind(wx.EVT_CLOSE, self.quitterPySyLiC )
        
        self.nbGauche.initialiser()
        
        # Synchronisation des scrolledBitmaps
        lstScrolledBitmap = self.getLstScrolledBitmap()
#        print lstScrolledBitmap
        lstScrolledBitmap[0].synchroniserAvec(lstScrolledBitmap[1:])


        # Maintenant que tout est en place, on applique les options
        
        wx.CallAfter(self.AppliquerOptions, tracer = False)
        if globdef.DEBUG: print("Appliquer options : fini")
#        self.OnFTModified(forcerMaJ = True)
        wx.CallAfter(self.OnFTModified, forcerMaJ = True)
        if globdef.DEBUG: print("Premier tracé : fini")
        

        #print("Init pySyLiC : fini")
#        wx.CallAfter(self.Thaw)
        
        
    ######################################################################################################
    def getLstScrolledBitmap(self):
        """ Renvoie toutes les ScrolledBitmap contenues dans la fenêtre
            (pour synchronisation)
        """
        return    self.nbGauche.getLstScrolledBitmap() \
                + self.winMarge.getLstScrolledBitmap() \
                + self.winPoles.getLstScrolledBitmap() \
                + self.winReponse.getLstScrolledBitmap() \
                + self.winDecompose.getLstScrolledBitmap()
        
    #########################################################################################################
    def OnBitmapChanged(self, event):
        print("OnBitmapChanged")
        self.num = event.GetNum()
        
    #########################################################################################################
    def getNum(self):
        return self.num
    
    #########################################################################################################
    def setNum(self, num):
        self.num = num
        if self.nbGauche.book.GetSelection() == 2:            # Page TF
            lstFTNum, lstCoul, lstPosE, marges, HC = self.getFTaTracer_FT()
            poles = self.getFTBF()[0].getPoles()
            self.zoneGraph.mettreAJourEtRedessiner(lstFTNum, lstCoul, lstPosE, marges, HC, poles)
        elif self.nbGauche.book.GetSelection() == 1:            # Page C
            lstFTNum, lstCoul, lstPosE, marges, HC = self.getFTaTracer_C()
            poles = self.getFTBF()[0].getPoles()
            self.zoneGraph.mettreAJourEtRedessiner(lstFTNum, lstCoul, lstPosE, marges, HC, poles)
            
        if self.TracerReponse:
            self.winReponse.MiseAJour()
            
        if self.TracerPoles:
            self.winPoles.tracer()
            
        if self.TracerDecomp:
            self.winDecompose.MiseAJour()
            
        if self.TracerMarges and self.tracerFTBO:
#            self.winMarge.calculerMarges()
            self.winMarge.MiseAJour()
    
    #########################################################################################################
    def OnFormatModified(self, event):
#        print "OnFormatModified"
        self.nbGauche.PageH.MiseAJourFormats()
        self.nbGauche.PageC.MiseAJourFormats()
        self.nbGauche.PageFT.MiseAJourFormats()
        self.tracer()
        
    #########################################################################################################
    def getLstFormat(self):
        """ Génère un dictionnaire de couleurs ...
        """
        lst = {}
        r,v,b = 255, 0, 0
        d = 40
        for f in range(globdef.MAXI_NBR_MAXI_PLOT):
            lst["H"+str(f)] = LineFormat(wx.Colour(r,v,b), "-", 2)
            r,v,b = abs(b - d) % 256, abs(r - d) % 256, abs(v - d) % 256
        return lst
 
    #########################################################################################################
    def getLstPositionsExpr(self):
        """ Génère un dictionnaire de positions par défaut pour les expressions ...
        """
        lst = {}
        for f in range(globdef.MAXI_NBR_MAXI_PLOT):
            for d in ["Bode", "Black", "Nyquist"]:
                lst["H"+str(f)+"_"+d] = PositionExpression()
        return lst
    
    #########################################################################################################
    def getZonesGraph(self):
        return self.zoneGraph.getZonesGraph()
        
        
    #########################################################################################################
    def activerZoomAuto(self, etat = None):
#        print "activerZoomAuto", etat

        # Pour savoir dans quel état est chaque zone
        if etat == None:
            lst = []
            for z in self.getZonesGraph():
                lst.append(z.zoomAuto)
            return lst
        
        # Pour mettre chaque zone dans un état différent
        elif type(etat) == list:
            for i,z in enumerate(self.getZonesGraph()):
                z.setZoomAuto(etat[i])
                
        # Pour mettre toutes les zone dans même état
        else:
            for z in self.getZonesGraph():
                z.setZoomAuto(etat)
        
        
    #########################################################################################################
    def getTypeSysteme(self):
        return self.nbGauche.schemaBloc.GetSelection()
    
    
    #########################################################################################################
    def setTypeSysteme(self, typ):
#        print "setTypeSysteme", typ
        self.nbGauche.schemaBloc.ChangeSelection(typ)
        return self.nbGauche.schemaBloc.OnPageChanged()
    
    def OnSystemeChange(self):
        if self.getTypeSysteme() == 0:
            self.tb.activerMarges(False)
            
        self.FTBF = []
        self.FTBO = []
        self.FTBFnc = []    
            
        # Utile pour la page sinus  : changement du tooltip
        self.winReponse.OnSystemeChange()
        
        
#        self.winReponse.setFTBF(self.getFTBF(), self.getFTBFnc())
        
        # Utile pour activer/désactiver le bouton "pôles"
        self.zoneGraph.OnSystemeChange()
        
        # On change le titre de la fenêtre "pôles"*
        self.winPoles.miseAJourTitre(self.getTypeSysteme() != 0)
        
        
    #########################################################################################################
    def OnFTModified(self, event = None, forcerMaJ = False):
#        print "OnFTModified"
        if event != None:
            self.MarquerFichierCourantModifie()
        
#        # RaZ des FTBO et FTBF (à priori, il faut les recalculer ...)
        self.FTBO = []
        self.FTBF = []
        self.FTBFnc = []
        
        if not (globdef.MAJ_AUTO or forcerMaJ):
            self.tb.activerMiseAJour(True)
            self.traceAJour = False
            return
        
        self.tb.activerMiseAJour(False)
        self.traceAJour = True
        
#        self.Freeze()
        wx.BeginBusyCursor(wx.HOURGLASS_CURSOR)
        
        self.zoneGraph.setCurseur(False)
#        tps1 = time.clock()    
        
#        if self.thread != None:
#            print "Stop Thread !!"
#            self.thread._Thread__stop() 
#        self.thread = threading.Thread(None, self.tracer)
#        self.thread.start()
        
        #
        # Mise à jour des FT des diverses fenêtres
        #
#        self.winMarge.setFTNum(self.getFTBO())
#        self.winReponse.setFTBF(self.getFTBF(), self.getFTBFnc())
#        self.winPoles.setFTBF(self.getFTBF())
#        self.nbGauche.PageFT.MiseAJourBmpFT()
        
        #
        # Tracé dans les diverses fenêtres
        #
        self.tracer(forcerMaJ = forcerMaJ)

#        if globdef.MAJ_AUTO or forcerMaJ:
#        
##        tps2 = time.clock()    
##        print "tracé", (tps2 - tps1)
#           
#                
#            if self.TracerReponse:
#                self.winReponse.setFTBF(self.getFTBF(), self.getFTBFnc())
#                self.winReponse.MiseAJour()
#                
#            if self.TracerPoles:
#                self.winPoles.calculerEtTracer(self.getFTBF())
#                
#            if self.TracerDecomp:
#                self.winDecompose.MiseAJour(self.getFTBO(), self.getFTBF())
        
#        self.winMarge.setFTNum(self.FT_H.FTNum * self.FT_C.FTNum)
            
        wx.EndBusyCursor()
        
        
        
#        self.Thaw()
        
#        event.Skip()
        
#    def setNumEtTracer(self, num):
#        self.winReponse.setNum(num)
#        self.winMarge.setNum(num)
#        self.winMarge.calculerMarges()
#        self.tracer()
        
    
    def tracer(self, event = None, forcerMaJ = False):
        """ Selectionne le type de tracé :
                - H (et ses sous FT)
                - HxC (et H et/ou C)
                - FTBO et/ou FTBF
        """
        
#        print "tracer"
            
        # RaZ des FTBO et FTBF (à priori, il faut les recalculer ...)
#        self.FTBO = None
#        self.FTBF = None
#        self.FTBFnc = None
        
        if not (globdef.MAJ_AUTO or forcerMaJ):
            return

        self.zoneGraph.setEstFTBF(False)
        
        if self.nbGauche.book.GetSelection() == 0:              # Page H
            HC = None
            marges = None
            lstFTNum, lstCoul, lstPos = self.getFTaTracer_H()
            
        elif self.nbGauche.book.GetSelection() == 1:            # Page C
            lstFTNum, lstCoul, lstPos, marges, HC = self.getFTaTracer_C()
            
        elif self.nbGauche.book.GetSelection() == 2:            # Page TF
            lstFTNum, lstCoul, lstPos, marges, HC = self.getFTaTracer_FT()
            
        if lstFTNum != []: # Pour eviter une erreur lors de l'initialisation de NbSysteme
            poles = self.getFTBF()[0].getPoles()
            zeros = self.getFTBF()[0].getZeros()
            self.zoneGraph.mettreAJourEtRedessiner(lstFTNum, lstCoul, lstPos, marges, HC, poles, zeros)
        
        if globdef.MAJ_AUTO or forcerMaJ:
            if self.TracerReponse:
                self.winReponse.MiseAJourBmp()
                self.winReponse.MiseAJour()
                
            if self.TracerPoles:
                self.winPoles.tracer()
                
            if self.TracerDecomp:
                self.winDecompose.MiseAJour()#self.getFTBO(), self.getFTBF())
                
            if self.TracerMarges and self.tracerFTBO:
                self.winMarge.MiseAJour()
        


##########################################################################################################
#
# Obtention des FT à tracer
#
##########################################################################################################
    def getListFTNum(self, tous = True):
        lst = []
        col = []
        pos = {"Bode" :[],
               "Black" :[],
               "Nyquist" :[]}
        
        for i, ft in enumerate(self.FT_H.lstFTNum):
            if tous or self.lstTracerSsFT[i]:
                lst.append(ft)
                col.append(self.formats["H"+str(i)])
                for d in pos:
                    pos[d].append(self.positionsExpr["H"+str(i)+"_"+d])
        return lst, col, pos
        
    ######################################################################################################
    def getProduitFTNum(self, lst):
        som = calcul.FonctionTransfertNum()
        for ft in lst:
            som = som * ft
        return som
    
    ######################################################################################################
    def getFT_H(self):
        return self.FT_H
    
    ######################################################################################################
    def getFT_C(self):
        return self.FT_C
    
    ######################################################################################################
    def setFT_H(self, FT):
        self.FT_H = FT 
    
    ######################################################################################################
    def setFT_C(self, FT):
        self.FT_C = FT
    
    ######################################################################################################
    def getFTBO(self):
        """ Renvoie la FBTO du systeme"""
#        print "getFTBO", self.FTBO
        if self.FTBO == []:
            
#            print self.FT_H
            if self.getTypeSysteme() == 0:                      # Système Simple
                self.FTBO = self.FT_H.FTNum
#                print self.FTBO
                if self.FTBO != []:
                    self.FTBO[0].nom = "H"
                else:
                    self.FTBO = []
                
            else:   
                self.FTBO = []                                           # Système Bouclé      
                for i, FT_C in enumerate(self.FT_C.FTNum):
                    self.FTBO.append(self.FT_H.FTNum[0] * FT_C)
#                    if not self.FTBO != None:
                if len(self.FTBO) == 1:
                    self.FTBO[0].nom = _("FTBO")
                else:
                    for i,FTBO in enumerate(self.FTBO):
                        FTBO.nom = r""+_("FTBO")+"_{"+str(i+1)+r"}"
                
#            print self.FTBO
        return self.FTBO


    ######################################################################################################
    def getFTBF(self):
        
        """ Renvoie la FBTF du systeme"""
        if self.FTBF == []:
            if self.getTypeSysteme() == 0:    # Système Simple
                self.FTBF = self.getFTBO()
            else:
                self.FTBF = []
                for i,FTBO in enumerate(self.getFTBO()):
                    if len(self.getFTBO()) == 1:
                        nom = _("FTBF")
                    else:
                        nom = r""+_("FTBF")+r"_{"+str(i+1)+r"}"
                    if FTBO.retard == 0:
                        self.FTBF.append(calcul.FonctionTransfertNum(FTBO.polyN, 
                                                                FTBO.polyN + FTBO.polyD, 
                                                                nom = nom))
                    else:
    #                    num, den = calcul.pade(self.getFTBO().retard, 3)
                        self.FTBF.append(calcul.FonctionTransfertNum(FTBO.polyN, 
                                                                [FTBO.polyD, FTBO.polyN], 
                                                                nom = nom, retard = FTBO.retard))
        return self.FTBF
    

    ######################################################################################################
    def getFTBFnc(self):
        """ Renvoie la FBTF du systeme non corrigé"""
        if self.FTBFnc == []:
            if self.getTypeSysteme() == 0:    # Système Simple
                self.FTBFnc = []#self.FT_H.FTNum
            else:
                self.FTBFnc = []
                for i, FT_H in enumerate(self.FT_H.FTNum):
                    nom = r""+_("FTBF_{nc}")
                    if FT_H.retard == 0:
                        self.FTBFnc.append(calcul.FonctionTransfertNum(FT_H.polyN, 
                                                                  FT_H.polyN + FT_H.polyD, 
                                                                  nom = nom))
                    else:
    #                    num, den = calcul.pade(self.getFTBO().retard, 3)
                        self.FTBFnc.append(calcul.FonctionTransfertNum(FT_H.polyN, 
                                                                [FT_H.polyD, FT_H.polyN], 
                                                                nom = nom, retard = FT_H.retard))
        
        if self.FTBFnc == []:
            return None
        else:
            return self.FTBFnc[0]
    
    ######################################################################################################
    def getFTaTracer_H(self):
        """ Etabli la liste des FTNum à tracer
                (pour H et ses sous FT)
            et ce qui va avec :
             - formats de ligne
             - positions des expressions des FT
        """
        
        lstFTNum = []
        lstCoul = []
        lstPosE = {"Bode" :[],
                   "Black" :[],
                   "Nyquist" :[]}
        
        if self.TracerH:
            lstFTNum.extend(self.FT_H.FTNum)
            lstCoul.extend([self.formats["H"]] * len(lstFTNum))
            for d in lstPosE:
                lstPosE[d].extend([self.positionsExpr["H_"+d]] * len(lstFTNum))
            if self.getTypeSysteme() == 0:
                self.zoneGraph.setEstFTBF(True)
            
        else:
            lstFT, lstCol, lstPos = self.getListFTNum(tous = False)
            for i,ft in enumerate(lstFT):
                lstCoul.append(lstCol[i])
                for d in lstPosE:
                    lstPosE[d].append(lstPos[d][i])
                lstFTNum.append(ft)
            
            if self.additionner and len(lstFT) > 0:
                lstCoul.append(self.formats["SomH"])
                for d in lstPosE:
                    lstPosE[d].append(self.positionsExpr["SomH_"+d])
                lstFTNum.append(self.getProduitFTNum(lstFT))
        
        return lstFTNum, lstCoul, lstPosE
    

    ######################################################################################################
    def getFTaTracer_C(self):
        """ Etabli la liste des FTNum à tracer
                (pour H, C et HC)
        """
        
        lstFTNum = []
        lstCoul = []
        lstPosE = {"Bode" :[],
                   "Black" :[],
                   "Nyquist" :[]}
        marges = None
        HC = None
        
        if self.CorTracerCH:
            somme = self.getFTBO()
            lstCoul.extend([self.formats["HC"]] * len(somme))
            for d in lstPosE:
                lstPosE[d].extend([self.positionsExpr["HC_"+d]] * len(somme))
            lstFTNum.extend(somme)
            # On prévoi le tracé des isos pour HxC seulement
            HC = 0
        
        if self.CorTracerH:
            lstCoul.append(self.formats["H"])
            for d in lstPosE:
                lstPosE[d].append(self.positionsExpr["H_"+d])
            self.FT_H.FTNum[0].nom = "H"
            lstFTNum.extend(self.FT_H.FTNum)
        
        if self.CorTracerC:
            lstCoul.extend([self.formats["C"]] * len(self.FT_C.FTNum))
            for d in lstPosE:
                lstPosE[d].extend([self.positionsExpr["C_"+d]] * len(self.FT_C.FTNum))
#            self.FT_C.FTNum.nom = "C"
            lstFTNum.extend(self.FT_C.FTNum)
            
        if self.TracerMarges and self.CorTracerCH:
#            self.winMarge.setFTNum(somme)
#            marges = self.winMarge.calculerMarges()
#        if self.TracerMarges and self.tracerFTBO:
            marges = self.winMarge.calculerMarges()
            
            
        return lstFTNum, lstCoul, lstPosE, marges, HC
    
    ######################################################################################################
    def getFTaTracer_FT(self):
        """ Etabli la liste des FTNum à tracer
                (pour FTBO et/ou FTBF)
        """
        
        lstFTNum = []
        lstCoul = []
        lstPosE = {"Bode" :[],
                   "Black" :[],
                   "Nyquist" :[]}
        marges = None
        HC = None
        
        if self.tracerFTBO:
            somme = self.getFTBO()
            lstCoul.extend([self.formats["HC"]] * len(somme))
            for d in lstPosE:
                lstPosE[d].extend([self.positionsExpr["HC_"+d]] * len(somme))
            lstFTNum.extend(somme)
            # On prévoi le tracé des isos pour la FTBO seulement
            HC = 0
        
        if self.tracerFTBF:
            somme = self.getFTBF()
            lstCoul.extend([self.formats["FTBF"]] * len(somme))
            for d in lstPosE:
                lstPosE[d].extend([self.positionsExpr["FTBF_"+d]] * len(somme))
            lstFTNum.extend(self.getFTBF())
            self.zoneGraph.setEstFTBF(True)
        
        if self.TracerMarges and self.tracerFTBO:
            marges = self.winMarge.calculerMarges()
         
        return lstFTNum, lstCoul, lstPosE, marges, HC

        
#    #########################################################################################################
#    def OnSize(self, event):
#        event.Skip()
        
    #########################################################################################################
    def OnFocus(self, event):
        pass
    
    def getNomFichierCourantCourt(self):
        return os.path.splitext(os.path.split(self.fichierCourant)[-1])[0]
        
    #############################################################################
    def definirNomFichierCourant(self, nomFichier = '', modif = False):
#        if modif : print "Fichier courant modifié !"
        self.fichierCourant = nomFichier
        self.fichierCourantModifie = modif
        if self.fichierCourant == '':
            t = ''
        else:
            t = ' - ' + self.fichierCourant
        if modif : 
            t += " **"
        self.SetTitle(version.__appname__+" " + str(self.version) + t )

    def MarquerFichierCourantModifie(self):
        self.definirNomFichierCourant(self.fichierCourant, True)
        

#     #############################################################################            
#    def Escape(self, event):
#        "Op. à effectuer quand la touche <Echap> est pressée"
##        print "Escape"
#        if not self.suppression:
#            if self.elemProv.num is not None:
#                self.elemProv.num = None
#                self.mtg.effacerElem(self.elemProv)
###                self.mtg.frame.afficherIconeElem(self.elemProv)
###                self.mtg.frame.delete("Icone")
###        else:
###            self.desactiverModeSuppr()
#        
#        self.elemProv.num = None
#
#        # Remise à la normale du curseur
#        self.mtg.frame.effaceCurseur()
###        self.master["cursor"] = 'arrow'
###        self.mtg.frame["cursor"] = 'arrow'
#
#        # Remise à la normale des boutons
#        if not self.mtg.deuxrlt():
#            self.barreElements.activer_desactiverBoutonPG(1)
#        if self.elemProv.num is not None:
#            self.barreElements.deverouille(self.elemProv.num)
###            self.barreElements.listeBouton[self.elemProv.num].configure(relief = RAISED)
#            
###        for c in self.barreElements.listeBouton.keys():
###            self.barreElements.listeBouton[c].configure(relief = RAISED)
#
#        self.zoneMessage.afficher('SelectElem')
#        #self.elemProv.num = None

    
                                      
    #########################################################################################################
    def OnOpenClick(self, event):    
        self.dialogOuvrir()
    
    def OnSaveClick(self, event):
        id = event.GetId()
        self.commandeEnregistrer()
#        if self.fichierCourant == '':
#            self.dialogEnregistrer()
#        else:
#            self.enregistrer(self.fichierCourant)

    def OnNewClick(self, event):
        raz = False
        
        if self.fichierCourantModifie:
            dlg = DialogInitProjet(self)
            raz = dlg.ShowModal()
            dlg.Destroy()
        else:
            raz = wx.ID_OK
        
        if raz == wx.ID_OK:
            self.reinitialiser()
    
#    def OnImprimClick(self, event):
#
#        self.zoneGraph.PrintPreview()
#        return 
#        
#        bmp = self.zoneGraph.getBitmap()
#        print bmp.GetWidth(), bmp.GetHeight()
#        data = wx.PrintDialogData(self.printData)
#        printout = MyPrintout(bmp)
#        printout2 = MyPrintout(bmp)
#        self.preview = wx.PrintPreview(printout, printout2, data)
#
#        if not self.preview.Ok():
#            print "Houston, we have a problem..."
#            return
#
#        pfrm = wx.PreviewFrame(self.preview, self, _("Aperçu avant impression"))
#
#        print dir(pfrm)
#        pfrm.Initialize()
#        pfrm.SetPosition(self.GetPosition())
#        pfrm.SetSize(self.GetSize())
#        pfrm.Show(True)


        
#        self.nbGauche.SetSelectionId(2)
    
#    def OnPrintClick(self, event):
#        """ Impression d'un rapport d'analyse
#        """
#        self.Freeze()
#        
#        # On lance l'analyse si ce n'est pas déja fait ...
#        if self.analyse.estPerimee:
#            self.analyse.lancerAnalyse(self.mtgComplet, self.zMont)
#            self.nbGauche.tbAnalys = Analyse.TBAnalyse(self.nbGauche, self.mtgComplet, self.zMont, self.analyse, self.nbCdCF)
#        
#        if self.options.optImpression["DemanderImpr"]:
#            optionImpr = self.optionsImprProv.copy()
#            dlg = Options.FenOptionsImpression(self, optionImpr)
#            dlg.CenterOnScreen()
#            val = dlg.ShowModal()
#            if val == wx.ID_OK:
#                self.optionsImprProv = optionImpr
#                afficherRapport = True
#            else:
#                afficherRapport = False
#            dlg.Destroy()
#            optImpr = self.optionsImprProv
#        else:
#            afficherRapport = True
#            optImpr = self.options.optImpression
#        
#        # Frame contenant le rapport   
#        if afficherRapport:   
#            win = Imprime.FrameRapport(self, optImpr, 
#                                       self.fichierCourant,
#                                       self.analyse, 
#                                       self.zMont,
#                                       self.mtgComplet.CdCF,
#                                       self.nbCdCF.CdCF_Charges, 
#                                       self.nbGauche.tbAnalys.GetPage(3),
#                                       self.nbGauche.tbAnalys.GetPage(4), 
#                                       self.nbGauche.tbAnalys.GetPage(1))
#            
#            self.analyse.reinitialiserAffichage(self.zMont)
#            win.Show(True)
#        
#        self.Thaw()
#        
#        
#   
#    def OnRetourneClick(self,event):
#        wx.BeginBusyCursor(wx.HOURGLASS_CURSOR)
##        self.zMont.analyse.initTraceResultats()
#        if self.analyse is not None:
#            self.analyse.reinitialiserAffichage(self.zMont)
#        self.analyse == None
##        self.mtgComplet.mtg.rafraichirAffichage(self.zMont)
#        
#        self.mtgComplet.mtg.retourner()
##        self.tree._tree._treeStruct['Composants'] = [2,self.mtgComplet.mtg._tree]
#        self.tree.RecreateTree()
#        self.mtgComplet.mtg.rafraichirAffichage(self.zMont)
#        self.OnCdCFModified()
#        wx.EndBusyCursor()
        
    def OnAboutClick(self, event):
        win = A_propos(self)
        win.ShowModal()
  
    def OnTracerMarges(self, tracer):
        self.TracerMarges = tracer
        self.winMarge.Show(tracer)
        if True:#tracer:
            self.tracer()
            
    def OnTracerPoles(self, tracer):
        self.TracerPoles = tracer
        self.winPoles.Show(tracer) 
        if tracer:
            self.winPoles.tracer()
    
    def OnTracerReponse(self, tracer):
        self.TracerReponse = tracer
        self.winReponse.Show(tracer)
        if tracer:
            self.winReponse.MiseAJourBmp()
            self.winReponse.initTB()
            self.winReponse.ReTracer()
            self.winReponse.SetFocus()
            
        
    def OnTracerDecomp(self, tracer):
        self.TracerDecomp = tracer
        if tracer:
            self.winDecompose.MiseAJour()
        self.winDecompose.Show(tracer)
            
#    def OnHelpClick(self, event):
#        lienAide = {"index"   : "index.html",
#                    "cdcf"    : "cdcf.html",
#                    "analyse" : "analyse.html"}
#        
#        fichierAideChm = os.path.join(globdef.HELPPATH,'PyvotAide.chm')
#        fichierAideHtml = os.path.join(globdef.HELPPATH,"html","index.html")
#        
#        def aideAbsente():
#            dlg = wx.MessageDialog(self, "Le fichier d'aide est absent !",
#                                       'Fichier absent',
#                                       wx.OK | wx.ICON_ERROR
#                                       #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
#                                       )
#            dlg.ShowModal()
#            dlg.Destroy()
###    webbrowser.open(lienAide[clef])
###    print "Affichage de l'aide :",lienAide[clef]
#        if self.options.optGenerales["TypeAide"] == 0 and sys.platform == 'win32':
#            if os.path.isfile(fichierAideChm):
#                os.startfile(fichierAideChm)
#            else:
#                aideAbsente()                
#        else:
#            if os.path.isfile(fichierAideHtml):
#                os.chdir(os.path.join(globdef.HELPPATH,"html"))
#                webbrowser.open('index.html')
#                os.chdir(globdef.PATH)
#            else:
#                aideAbsente()
#
#        
##        dlg = wx.MessageDialog(self, "Cette fonctionnalité n'est pas encore disponible ...",
##                               'Aide de PyVot',
##                               wx.OK | wx.ICON_INFORMATION
##                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
##                               )
##        dlg.ShowModal()
##        dlg.Destroy()
#  

    def DefinirOptions(self, options):
        self.options = options.copie()
        #
        # Options Générales
        #
            # Dossier d'enregistrement
        self.DossierSauvegarde = self.options.optGenerales["RepCourant"]
            
            # Variable complexe
        globdef.VAR_COMPLEXE = self.options.optGenerales["VAR_COMPLEXE"]
        
            # Temps de réponse
        globdef.TEMPS_REPONSE = self.options.optCalcul["TEMPS_REPONSE"]
        
            # Antialiasing
        globdef.ANTIALIASED = self.options.optAffichage["ANTIALIASED"]
        
            # Mise à Jour Auto
        globdef.MAJ_AUTO = self.options.optGenerales["MAJ_AUTO"]
        
            # Nombre de périodes affichées en cas d'echelle automatique
        globdef.NB_PERIODES_REP_TEMPO = self.options.optCalcul["NB_PERIODES_REP_TEMPO"]
  
        globdef.TRACER_FLECHE = self.options.optAffichage["TRACER_FLECHE"]
        
        
        
#        globdef.NBR_MAXI_PLOT = options.optGenerales["NBR_MAXI_PLOT"]
        globdef.TYPE_SELECTEUR_TF = options.optGenerales["TypeSelecteur"]
        globdef.NBR_PTS_REPONSE = options.optCalcul["NBR_PTS_REPONSE"]
#        print "NBR_PTS_REPONSE", globdef.NBR_PTS_REPONSE

        #
        # Couleurs
        #
        
        globdef.COUL_MARGE_GAIN_OK = options.optCouleurs["COUL_MARGE_OK"]
        globdef.COUL_MARGE_GAIN_NO = options.optCouleurs["COUL_MARGE_NO"]
        globdef.FORM_GRILLE = options.optCouleurs["FORM_GRILLE"]
        globdef.FORM_ISOGAIN = options.optCouleurs["FORM_ISOGAIN"]
        globdef.FORM_ISOPHASE = options.optCouleurs["FORM_ISOPHASE" ]
#        globdef.COUL_LAMBDA = options.optCouleurs["COUL_LAMBDA"]
        globdef.COUL_POLES = options.optCouleurs["COUL_POLES"]
        globdef.COUL_PT_CRITIQUE = options.optCouleurs["COUL_PT_CRITIQUE" ]

        #
        # Impression
        #
        globdef.PRINT_PROPORTION = options.optImpression["PRINT_PROPORTION"]
        
        globdef.IMPRIMER_NOM = options.optImpression["IMPRIMER_NOM"]
        globdef.POSITION_NOM = options.optImpression["POSITION_NOM"]
        globdef.TEXTE_NOM = options.optImpression["TEXTE_NOM"]
#        globdef.IMPRIMER_TEXTE = options.optImpression["IMPRIMER_TEXTE"]
        globdef.IMPRIMER_TITRE = options.optImpression["IMPRIMER_TITRE"]
        globdef.POSITION_TITRE = options.optImpression["POSITION_TITRE"]
        globdef.TEXTE_TITRE = options.optImpression["TEXTE_TITRE"]
        
        globdef.MAX_PRINTER_DPI = options.optImpression["MAX_PRINTER_DPI"]
        
        #
        # Affichage
        #
        globdef.FONT_TYPE = options.optAffichage["FONT_TYPE"]
        
        self.change_langue = globdef.LANG != options.optGenerales["LANG"]
        globdef.LANG = options.optGenerales["LANG"]
        
        globdef.DEPHASAGE = options.optGenerales["DEPHASAGE"]
        
        globdef.NBR_MAXI_PLOT = options.optGenerales["NBR_MAXI_PLOT"]
        
        
    #########################################################################################################
    def AppliquerOptions(self, tracer = True):
        """ Procédure mettant en application toutes les options sauvegardées
        """

        #
        # Type de selecteur de FT_H
        #
        self.nbGauche.PageH.AppliquerSelecteur()
        
        #
        # Déphasage
        #
        self.nbGauche.PageH.SelFT_H.MiseAJourBmp()
        if self.FT_H.retard != 0 and not globdef.DEPHASAGE:
            self.FT_H.retard = 0
        #
        # Recalcul des variables et des sous FT
        #
        self.FT_H.detDictVari()
        self.FT_H.detLstFTNum()
        
        if hasattr(self.nbGauche.PageH, "panelVariables"):
            self.nbGauche.PageH.panelVariables.OnListeVariableModified(self.FT_H.variables)
            
        
        #
        # Variable Complexe
        #
        self.nbGauche.schemaBloc.SetImg()
        self.nbGauche.schemaBloc.OnSize()
        self.nbGauche.PageH.selAffichFT.OnSelModified(self.FT_H)
        wx.CallAfter(self.nbGauche.PageH.FitInside)

        #
        # Antialiasing
        #
        self.zoneGraph.modifierAntialiased()
        self.winReponse.modifierAntialiased()
        self.winDecompose.modifierAntialiased()
        
        #
        # Couleurs
        #
#        print "   Couleurs"
        self.zoneGraph.setCouleurs()
        if self.TracerPoles:
            self.winPoles.setCouleurs()
                
        #
        # Mise à Jour Automatique
        #
#        if not self.traceAJour:
        if tracer :
            self.OnFTModified()
        # Présence du bouton dans la barre d'outils
        if globdef.MAJ_AUTO:
            self.tb.enleverMiseAJour()
        else:
            self.tb.mettreMiseAJour()
        
        #
        # Nombre de points réponse temporelle et nombre de périodes
        #
        if self.TracerReponse:
#            self.winReponse.setFTBF(self.getFTBF(), self.getFTBFnc())
            self.winReponse.MiseAJour()
        
        #
        # Type de police
        #
        graph.AppliquerTypeFont()
            
            
        #
        # Langage (uniquement pour le message de changement de langue)
        #  
        def info():
            dlg = wx.MessageDialog(self, _('Merci de redémarrer PySyLiC pour que le changement de langue opére'),
                                   _('Changement de langue'),
                                   wx.OK | wx.ICON_INFORMATION
                                   )
            dlg.ShowModal()
            dlg.Destroy()
            
        if self.change_langue:
            globdef.SetInternationalization()
            wx.CallAfter(info)
                
        
            
#        print "Fin AppliquerOptions"
        
        
#   #########################################################################################################         
    def OnOptionsClick(self, event = None, page = 0):
        options = self.options.copie()
#        print options
        dlg = Options.FenOptions(self, options)
        dlg.CenterOnScreen()
        dlg.nb.SetSelection(page)

        # this does not return until the dialog is closed.
        val = dlg.ShowModal()
    
        if val == wx.ID_OK:
#            print options
            self.DefinirOptions(options)
            self.AppliquerOptions()
            
        else:
            pass
#            print "You pressed Cancel"

        dlg.Destroy()
        

    #---------------------------------------------------------------------------             
    def dialogOuvrir(self,nomFichier=None):
        mesFormats = _("Système pySyLiC (.syl)|*.syl|" \
                       "Tous les fichiers|*.*'")
  
        if nomFichier == None:
            dlg = wx.FileDialog(
                                self, message=_("Ouvrir un système"),
                                defaultDir = self.DossierSauvegarde, 
                                defaultFile = "",
                                wildcard = mesFormats,
                                style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                                )
                
            # Show the dialog and retrieve the user response. If it is the OK response, 
            # process the data.
            if dlg.ShowModal() == wx.ID_OK:
                # This returns a Python list of files that were selected.
                paths = dlg.GetPaths()
                nomFichier = paths[0]
            else:
                nomFichier = ''
            
            dlg.Destroy()
            
        self.Refresh()
                
        if nomFichier != '':
#            print "Ouverture de",nomFichier
#            self.options.extraireRepertoire(nomFichier)
##            print self.options.repertoireCourant.get()
            if self.fichierCourantModifie:
                raz = False
#                self.fenR = FenReinitialiser(self,self,self.raz)
                dlg = DialogInitProjet(self)
                raz = dlg.ShowModal()
                dlg.Destroy()
            else:
                raz = True
                
            if raz:
                wx.BeginBusyCursor(wx.HOURGLASS_CURSOR)
                self.ouvrir(nomFichier)
                wx.EndBusyCursor()
                  
                  
    ########################################################################################################       
    def ouvrir(self, nomFichier):
        """ Ouvre un fichier .syl """
        
        
        def ouvrirFich():  
#            print "Ouverture", fichier, "..."
#            try:
            root = ET.parse(fichier).getroot()
            
            #
            # branche "H"
            #
            brancheH = root.find("FT_H")
            typ = brancheH.get("type_FT", "0")
            if typ == "1":
                FT_H = FonctionTransfertDev()
            else:
                FT_H = FonctionTransfertFact()
#            print "...type :",typ,"..."
            FT_H.ouvrir(brancheH)
#            print FT_H
            
            #
            # branche "C"
            #
            brancheC = root.find("FT_C")
            if brancheC != None:
                typ = brancheC.get("type_FT", "1")
                if typ == "1":
                    FT_C = FonctionTransfertCorrec()
                else:
                    FT_C = FonctionTransfertFact()
                FT_C.ouvrir(brancheC)
            else:
                FT_C = None
                
            #
            # branche "Format"
            #   
            brancheFormat = root.find("Format")
            if brancheFormat != None:
                formats = {}
                for k in ["H", "C", "HC", "FTBF", "SomH", "Cons", "Rep", "RepNc"]:
                    formats[k] = LineFormat()
                    formats[k].ouvrir(k, brancheFormat)
#                    try:
#                        formats[k] = getFormat(k)
#                    except:
#                        pass #Pas de clef k ==> on mettra la valeur par défaut dans initFormats
                
                continuer = True
                i = 0
                while continuer:
                    f = LineFormat()
                    ok = f.ouvrir("H"+str(i), brancheFormat)
#                    f = getFormat("H"+str(i))
                    if ok:
                        formats["H"+str(i)] = f
                    else:
                        continuer = False
                    i += 1
            else:
                formats = {}
                
            #
            # branche "PositionExpressions"
            #   
            branchePosExpr = root.find("PositionExpressions")
            if branchePosExpr != None:
                positionsExpr = {}
                for k in ["H", "C", "HC", "FTBF", "SomH"]:
                    for d in ["_Bode", "_Black", "_Nyquist"]:
                        positionsExpr[k+d] = PositionExpression()
                        positionsExpr[k+d].ouvrir(k+d, branchePosExpr)
                
                continuer = True
                i = 0
                while continuer:
                    for d in ["_Bode", "_Black", "_Nyquist"]:
                        f = PositionExpression()
                        ok = f.ouvrir("H"+str(i)+d, branchePosExpr)
                        if ok:
                            positionsExpr["H"+str(i)+d] = f
                        else:
                            continuer = False
                    i += 1
            else:
                positionsExpr = {}
                
            return 0, FT_H, FT_C, formats, positionsExpr
        
        
        
#            except xml.parsers.expat.ExpatError:
#                return 1
#            except : 
#                return sys.exc_info()[2]
        
        def AfficheErreur(Erreur):
            mess = _('Impossible de lire le fichier')+' %s!\n\n' %nomFichier
#            for m in traceback.format_tb(Erreur):
#                mess += "\n" + m
            dlg = wx.MessageDialog(self, mess,
                                   _('Erreur ouverture'),
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            
        fichier = open(nomFichier,'r')

        Erreur, FT_H, FT_C, formats, positionsExpr = ouvrirFich()
        
        if Erreur == 0:
            self.initialiser(FT_H, FT_C, formats, positionsExpr,
                             os.path.basename(nomFichier))
            self.DossierSauvegarde = os.path.dirname(nomFichier)
        else:
            AfficheErreur(Erreur)

        fichier.close()
            
    #########################################################################################################
    def reinitialiser(self):
        """ Fait une RAZ ...
        """
        self.Freeze()
        wx.BeginBusyCursor(wx.HOURGLASS_CURSOR)
        
        self.initFormats()
        
        if globdef.TYPE_SELECTEUR_TF == 0:
            self.FT_H.__init__(K = 1.0, classe = 0, lstPolyN = [], lstPolyD = [])
        else:
            self.FT_H.__init__()
        self.FT_H.detDictVari()
        self.FT_H.detLstFTNum()
        
        self.FT_C.__init__()
#        print self.FT_H    

        if self.TracerMarges:
            self.tb.DesactiverMarges()
#            self.OnTracerMarges(False)
            
        if self.TracerPoles:
            self.tb.DesactiverPoles()
#            self.OnTracerPoles(False)

        if self.TracerReponse:
            self.tb.DesactiverReponse()
#            self.OnTracerReponse(False)
            
        if self.TracerDecomp:
            self.tb.DesactiverDecomp()
#            self.OnTracerDecomp(False)
        
        
        self.nbGauche.initialiser()
        self.definirNomFichierCourant('')
        self.OnFTModified()
        
        wx.EndBusyCursor()
        self.Thaw()
    
    
    #########################################################################################################
    def initFormats(self, formats = {}):
        """ Donne à self.format les faleurs de <formats>
            (valeurs par défaut si format == {})
        """
        #
        # Valeurs par défaut
        #
        self.formats["H"] = LineFormat(wx.Colour(0,0,0), "-", 2)          # Couleur de H
        self.formats["C"] = LineFormat(wx.Colour(255,0,0), "-", 2)          # Couleur de C
        self.formats["HC"] = LineFormat(wx.Colour(0,0,255), "-", 2)        # Couleur de HC = FTBO
        self.formats["FTBF"] = LineFormat(wx.Colour(0,255,0), "-", 2)    # Couleur de FTBF
        self.formats["SomH"] = LineFormat(wx.Colour(40,40,40), "-", 2)    # Couleur de la somme des ss FT de H sélectionnée    
                        
        self.formats["Cons"] = LineFormat(globdef.COUL_CONSIGNE, "-", 2)
        self.formats["Rep"] = LineFormat(globdef.COUL_REPONSE, "-", 2)
        self.formats["RepNc"] = LineFormat(globdef.COUL_REPONSENC, "-", 2)

        self.formats.update(self.getLstFormat())# Couleur des sous FT de H
            
        #
        # Nouvelles valeurs
        #
        self.formats.update(formats)
        
    #########################################################################################################
    def initPositionsExpr(self, positions = {}):
        """ Donne à self.format les faleurs de <formats>
            (valeurs par défaut si format == {})
        """
#        print "initPositionsExpr", positions
        #
        # Valeurs par défaut
        #
        for d in ["Bode", "Black", "Nyquist"]:
            self.positionsExpr["H_"+d] = PositionExpression()        
            self.positionsExpr["C_"+d] = PositionExpression()        
            self.positionsExpr["HC_"+d] = PositionExpression()        
            self.positionsExpr["FTBF_"+d] = PositionExpression()    
            self.positionsExpr["SomH_"+d] = PositionExpression()    

        self.positionsExpr.update(self.getLstPositionsExpr())
            
        #
        # Nouvelles valeurs
        #
        self.positionsExpr.update(positions)
        
#        print self.positionsExpr
        
        
    #########################################################################################################
    def initialiser(self, FT_H, FT_C, formats, positionsExpr,
                    nomFichier = ''):
#        print "Initialisation système ..."
        
        # RaZ des FTBO et FTBF (à priori, il faut les recalculer ...)
        self.FTBO = []
        self.FTBF = []
        self.FTBFnc = []
        
        self.Refresh()
        self.Freeze()
        
        wx.BeginBusyCursor(wx.HOURGLASS_CURSOR)
        
        #
        # Accorde le selecteur de FT au type de FT_H
        #    et modifie l'option en conséquence ...
        #
        if isinstance(FT_H, FonctionTransfertDev):
            sel = 1
        else:
            sel = 0
            
        if sel != globdef.TYPE_SELECTEUR_TF:
            globdef.TYPE_SELECTEUR_TF = sel
            self.options.optGenerales["TypeSelecteur"] = sel
            self.AppliquerOptions()
        
        #
        # Mise à jour des formats et des positions des expressions
        #
        self.initFormats(formats)
        self.initPositionsExpr(positionsExpr)

         
        #
        # Mise à jour de la page H
        #
        self.FT_H = FT_H
        if FT_H.retard != 0:
            globdef.DEPHASAGE = True
        self.FT_H.detDictVari()
        self.FT_H.detLstFTNum()
        self.nbGauche.PageH.initialiser()

        
        #
        # Mise à jour de la page C
        #
        if FT_C != None:
            self.FT_C = FT_C
        else:
            self.FT_C = FonctionTransfertCorrec("P")
        self.FT_C.detDictVari()
        self.FT_C.detLstFTNum()
        self.nbGauche.PageC.initialiser()


        #
        # Mise à jour de la page FT
        #
        self.nbGauche.PageFT.initialiser()
        
        #
        # Réinitialisation des boutons des zone graphiques
        #
        self.zoneGraph.reinitialiserBoutons()
        
        #
        # Régle le type de système
        #
        if FT_C != None:
            self.setTypeSysteme(1)
        else:
            self.setTypeSysteme(0)
        
        #
        # On affiche tout
        #
        self.OnFTModified()
        
        
        self.definirNomFichierCourant(nomFichier)
        
        wx.EndBusyCursor()
        self.Thaw()
        
    #----------------------------------------------------------------------------------------------
    def dialogEnregistrer(self):
        mesFormats = _("Système (.syl)|*.syl|" \
                     "Tous les fichiers|*.*'")
        dlg = wx.FileDialog(
            self, message=_("Enregistrer le système sous ..."), defaultDir=self.DossierSauvegarde , 
            defaultFile="", wildcard=mesFormats, style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR
            )
        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
            self.enregistrer(path)
            self.DossierSauvegarde = os.path.split(path)[0]
#            print "Nouveau dossier de sauvegarde", self.DossierSauvegarde
        else:
            dlg.Destroy()
            
    def commandeEnregistrer(self):
#        print "fichier courant :",self.fichierCourant
        if self.fichierCourant != '':
            s = _("'Oui' pour enregistrer le système dans le fichier\n")
            s += self.fichierCourant
            s += ".\n\n"
            s += _("'Non' pour enregistrer le système dans un autre fichier.")
            
            dlg = wx.MessageDialog(self, s,
                                   _('Enregistrement'),
                                     wx.ICON_INFORMATION | wx.YES_NO | wx.CANCEL
                                     )
            res = dlg.ShowModal()
            dlg.Destroy() 
            if res == wx.ID_YES:
                self.enregistrer(self.fichierCourant)
            elif res == wx.ID_NO:
                self.dialogEnregistrer()
            
            
        else:
            self.dialogEnregistrer()

    ###############################################################################################
    def enregistrer(self, nomFichier):
        self.Freeze()
        wx.BeginBusyCursor(wx.HOURGLASS_CURSOR)
        fichier = file(nomFichier, 'w')
        
        # Création de la racine
        systeme = ET.Element("Systeme")
        
        # Ajout de la branche H
        systeme.append(self.FT_H.getBranche())
        
        # Ajout de la branche C
        if self.getTypeSysteme() == 1:
            systeme.append(self.FT_C.getBranche("FT_C"))
        
        # Ajout de la branche "Format"
        systeme.append(self.getBrancheFormat())
        
        # Ajout de la branche "Position des Expressions"
        systeme.append(self.getBranchePosExpr())
        
        indent(systeme)
        ET.ElementTree(systeme).write(fichier)
        fichier.close()
        self.definirNomFichierCourant(nomFichier)
        wx.EndBusyCursor()
        self.Thaw()

    ###############################################################################################
    def getBrancheFormat(self):
        root = ET.Element("Format")
        for k in ["H", "C", "HC", "FTBF", "SomH", "Cons", "Rep", "RepNc"]:
#            root.append(getBrancheSimple(k, self.formats[k]))
            root.append(self.formats[k].getBranche(k))
        
        for i, ft in enumerate(self.FT_H.lstFTNum):
#            root.append(getBrancheSimple("H"+str(i), self.formats["H"+str(i)]))
            root.append(self.formats["H"+str(i)].getBranche("H"+str(i)))
        
        return root
    
    ###############################################################################################
    def getBranchePosExpr(self):
        root = ET.Element("PositionExpressions")
        for k in ["H", "C", "HC", "FTBF", "SomH"]:
            for d in ["_Bode", "_Black", "_Nyquist"]:
                root.append(self.positionsExpr[k+d].getBranche(k+d))
        
        for i, ft in enumerate(self.FT_H.lstFTNum):
            for d in ["_Bode", "_Black", "_Nyquist"]:
                root.append(self.positionsExpr["H"+str(i)+d].getBranche("H"+str(i)+d))
        
        return root
    
#    def changerCurseur(self, curs = wx.CURSOR_ARROW, elem = None):    
#        if elem is not None:
#            image = Images.Img_Elem(elem).ConvertToImage()
#
#            # since this image didn't come from a .cur file, tell it where the hotspot is
#            image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, 1)
#            image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, 1)
#
#            # make the image into a cursor
#            cursor = wx.CursorFromImage(image)
#            texte = "Choisir un emplacement pour cet élément sur le montage ..."
#            
#        else:
#            cursor = wx.StockCursor(curs)
#            if curs == globdef.CURSEUR_DEFAUT:
#                texte = ""
#            elif curs == globdef.CURSEUR_INTERDIT:
#                texte = "Impossible de placer l'élément sélectionné ici ..."
#            elif curs == globdef.CURSEUR_ORIENTATION:
#                texte = "Déplacer la souris pour choisir l'orientation du roulement ... puis cliquer ..."
#            elif curs == globdef.CURSEUR_OK:
#                texte = "Cliquer pour placer l'élément sélectionné ici ..."      
#        
#        self.SetCursor(cursor)
#        self.statusBar.SetStatusText(texte, 0)
        
    
            
        
    #############################################################################
    def quitterPySyLiC(self, event = None):
        if globdef.DEBUG: print("Quitter...",)
        self.options.enregistrer()
        try:
            self.options.enregistrer()
        except IOError:
            print("   Permission d'enregistrer les options refusée...",)
        except:
            print("   Erreur enregistrement options...",)
            
#        event.Skip()
        if not self.fichierCourantModifie:
            self.fermerPySyLic()
            return
        
        texte = _("Le Système a été modifié.\nVoulez vous enregistrer les changements ?")
        if self.fichierCourant != '':
            texte += "\n\n\t"+self.fichierCourant+"\n"
            
        dialog = wx.MessageDialog(self, texte, 
                                  _("Confirmation"), wx.YES_NO | wx.CANCEL | wx.ICON_WARNING)
        retCode = dialog.ShowModal()
        if retCode == wx.ID_YES:
            self.commandeEnregistrer()
            self.fermerPySyLic()
        elif retCode == wx.ID_NO:
            self.fermerPySyLic()
#        else:
#            print 'skipping quit'

    def fermerPySyLic(self):
#        try:
#            self.options.enregistrer()
#        except:
#            print "Erreur enregistrement options"
        if globdef.DEBUG: print("Ok")
        self.Destroy()
        sys.exit()



##########################################################################################################
##########################################################################################################
#
#  Sélection du type ,de système (représenté par SchemeBloc)
#
##########################################################################################################
##########################################################################################################
class NbSysteme(wx.Toolbook):
    def __init__(self, parent):
        wx.Toolbook.__init__(self, parent, -1, style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                            )

        # make an image list using the LBXX images
        il = wx.ImageList(110, 40)
        for i in [Images.Bouton_SystemeSimple, Images.Bouton_SystemeBoucle]:
            bmp = i.GetBitmap()
            il.Add(bmp)
        self.AssignImageList(il)
        
        lstToolTip = [_("Système composé d'une simple transmittance : H(p)"),
                      _("Système bouclé composé :\n"\
                        " - d'un processus de fonction de transfert H(p)\n"\
                        " - d'un correcteur de fonction de transfert C(p)")]
        
        # Now make a bunch of panels for the list book
        first = True
        for i, bmp in enumerate([(Images.Schema_SystemeSimple_p, Images.Schema_SystemeSimple_s),
                                 (Images.Schema_SystemeFerme_p, Images.Schema_SystemeFerme_s)]
                                 ):
            bmp_p = bmp[0].GetBitmap()
            bmp_s = bmp[1].GetBitmap()
            win = SchemaBloc(self, bmp_p, bmp_s)
            self.AddPage(win, '', imageId = i)
            self.GetToolBar().SetToolShortHelp(i+1, lstToolTip[i])
            
        self.ChangeSelection(0)
        
        self.Bind(wx.EVT_TOOLBOOK_PAGE_CHANGED, self.OnPageChanged)
        
        

    def OnSize(self, size = None):
        self.GetCurrentPage().OnSize(size)
        self.Fit()
        
    def SetImg(self):
        self.GetCurrentPage().SetImg()
   
    def OnPageChanged(self, event = None):
#        print "Page changed NbSystem"
#        sel = event.GetSelection()
#        print "PageChanged Systeme", sel
            
        self.Parent.OnSystemeChange()
        
        # On remet le NoteBook sur la page H (peut-être la seule qui reste !)
        self.Parent.book.SetSelection(0)
        
        # On Ajoute ou supprimes les pages du NoteBook qui doivent l'être
        self.Parent.gererPages()
        
        # On met à jour l'image du schéma-bloc
        self.SetImg()
        self.OnSize()
        self.Parent.Layout()
        
#        # On retrace tout ...
#        self.Parent.app.tracer(forcerMaJ = True)



class SchemaBloc(wx.Panel):
    def __init__(self, parent, bmp_p, bmp_s):
        wx.Panel.__init__(self, parent, -1)#, style = wx.BORDER_SIMPLE)
        self.SetToolTipString(_("Représentation du système sous forme de schéma-bloc."
                                ))
        self.bmp = {'p' : bmp_p,
                    's' : bmp_s}
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetImg()
        self.HsL = 1.0*self.img.GetHeight() / self.img.GetWidth()
        self.schema = wx.StaticBitmap(self, -1, self.GetBmp())
        sizer.Add(self.schema, flag = wx.EXPAND, border = 4)
        self.SetSizerAndFit(sizer)

        
    def OnSize(self, size = None):
        if size != None:
            self.SetClientSize(size)
        
        self.schema.SetBitmap(self.GetBmp())
        
#        print "CompSize", self.schema.GetSize()
        self.Fit()
#        print "  -->", self.GetSize()
        self.SetMinSize(self.GetSize())
       
       
    def SetImg(self):
        self.img = self.bmp[globdef.VAR_COMPLEXE].ConvertToImage()
        
        
    def GetBmp(self):
        l, h = self.GetClientSize()
        if l > 1:
            return wx.BitmapFromImage(self.img.Scale(l-2, int(l*self.HsL), 
                                                     wx.IMAGE_QUALITY_HIGH))
        else:
            return wx.BitmapFromImage(self.img)

##########################################################################################################
##########################################################################################################
#
#  Classe contenant le NoteBook de C(p) et de H(p)
#
##########################################################################################################
#########################################################################################################
class NbGauche(wx.Panel):
    def __init__(self, parent, getNum, setNum, getFT_H, setFT_H, getFT_C, setFT_C,
                 getFTBO, getFTBF, app):
        wx.Panel.__init__(self, parent, -1)#, style = wx.BORDER_SIMPLE)
        
        self.app = app
        
        self.SetAutoLayout(True)
        
        size = (32,32)
        self.imageList = wx.ImageList(size[0], size[1])
        
        lstBmp = [mathtext_to_wxbitmap(r'H', 200),
                  mathtext_to_wxbitmap(r'C', 200),
                  mathtext_to_wxbitmap(r'\frac{S}{E}', 200)]
        
        for i in lstBmp:
            self.imageList.Add(wx.BitmapFromImage(wx.ImageFromBitmap(i).Scale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)))

        lstToolTip = [_("Saisie et paramêtres d'affichage\n"\
                        "de la Fonction de Transfert H"),
                      _("Saisie et paramêtres d'affichage\n"\
                        "de la Fonction de Transfert du correcteur C"),
                      _("Paramètres d'affichage de la réponse harmonique du système\n"\
                        "en boucles ouverte et fermée"),]
        
        # Schéma bloc
        #----------------
        self.schemaBloc = NbSysteme(self)
        
        # Book des  FT
        #-----------------
        if True:#sys.platform == 'darwin':
            self.book = wx.Notebook(self, -1, size = (20,20))
        else:
#            self.book = NB.FlatNotebook(self, -1, size = (20,20))#, style=wx.CLIP_CHILDREN|wx.BORDER_NONE)
            self.book = NB.NotebookCtrl(self, -1, size = (20,20))#, style=wx.CLIP_CHILDREN|wx.BORDER_NONE)
        self.book.AssignImageList(self.imageList)
        self.pasEventBook = False
        
        # Selecteur de H
        #----------------
        self.PageH = PageH(self.book, getFT_H, setFT_H, app)
        self.book.AddPage(self.PageH, 'H')
        
        
        # Selecteur de C
        #----------------
        self.PageC = PageC(self.book, getNum, setNum, getFT_C, setFT_C, app)
        self.book.AddPage(self.PageC, 'HxC')
        self.toolC = None
        
        # Selecteur de FT
        #----------------
        self.PageFT = PageFT(self.book, getNum, setNum, getFTBF, getFTBO, getFT_C, app)
        self.book.AddPage(self.PageFT, 'S/E')
        self.toolFT = None
        
        # Pour indiquer qu'une seule page est présente
        self.unePage = False
        
        if hasattr(self.book, 'EnableToolTip'):
            self.book.EnableToolTip(True)
    #        self.book.EnableHiding(True)
            self.book.nb._enablehiding = True
            self.book.SetUseFocusIndicator(False)
            self.book.SetHighlightSelection(True)
            for i in range(3):
    #            self.book.SetPageImage(i, i)
                self.book.SetPageToolTip(i,lstToolTip[i])
#        print dir(self.book)
#        print self.book.GetChildren()
#        self.book.SetToolTipString(lstToolTip[0])
#        self.book.SetPageToolTip(1,lstToolTip[1])
#        self.book.SetPageToolTip(0,lstToolTip[0])
#        self.book.SetPageToolTip(2,lstToolTip[2])
#        self.book.GetToolBar().SetToolShortHelp(2, lstToolTip[1])
#        self.book.GetToolBar().SetToolShortHelp(3, lstToolTip[2])
        
        # Mise en place ...
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.schemaBloc, 0, flag = wx.EXPAND)
        self.sizer.Add(self.book, 1, flag = wx.EXPAND)
        self.SetSizer(self.sizer)
        
        self.book.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
#        self.book.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        #self.Bind(wx.EVT_CALCULATE_LAYOUT, self.OnPaint)
        
    ######################################################################################################
    def getLstScrolledBitmap(self):
        """ Renvoie toutes les ScrolledBitmap contenues dans la fenêtre
            (pour synchronisation)
        """
        return self.PageC.getLstScrolledBitmap() + self.PageFT.getLstScrolledBitmap()
    
    #########################################################################################################
    def ChangeSelection(self, num):
        self.pasEventBook = True
        self.book.ChangeSelection(num)
       
        self.pasEventBook = False
        
        
    #########################################################################################################
    def initialiser(self):
#        print "Initialisation nbGauche"
        self.ChangeSelection(0)
#        self.book.SetSelection(0)
        if self.schemaBloc.GetSelection() == 0:
            self.PageH.initialiser()
        elif self.schemaBloc.GetSelection() == 1:
            self.PageH.initialiser()
            self.PageC.initialiser()
            self.PageFT.initialiser()
        
        
    #########################################################################################################
    def gererPages(self):
        """ Ajoute ou enlève des onglet au NoteBook
            selon le type de système selectionné
        """
        
        if self.schemaBloc.GetSelection() == 0:     # Système Simple
            if not self.unePage:
                if hasattr(self.book, 'HideTab'):
                    self.book.HideTab(1)
                    self.book.HideTab(2)
#                self.book.RemovePage(1)
#                self.book.RemovePage(1)
#                self.toolFT = self.book.GetToolBar().RemoveTool(1)
#                self.toolC = self.book.GetToolBar().RemoveTool(1)
                self.unePage = True
                
        elif self.schemaBloc.GetSelection() == 1:   # Système Bouclé
            if self.unePage:
                if hasattr(self.book, 'HideTab'):
                    self.book.HideTab(1, False)
                    self.book.HideTab(2, False)
#                tb = self.book.GetToolBar()
#                tb.InsertToolItem(1, self.toolFT)
#                tb.InsertToolItem(1, self.toolC)
#                self.book.AddPage(self.PageC, '', imageId = 1)
#                self.book.AddPage(self.PageFT, '', imageId = 2)
                self.unePage = False
        
        
    #########################################################################################################
    def OnSize(self, event = None):
#        print "OnSize nbGauche"
#        self.SetVirtualSize((self.GetSize()[0]-17, -1))
        self.schemaBloc.OnSize(self.GetVirtualSize())
        if event != None:
            event.Skip()
            
        
#    #########################################################################################################
#    def SetVirtualSizeVertical(self):
#        self.FitInside()
#        sizeV = 0
#        for c in self.GetChildren():
#            sizeV += c.GetSize()[1]
#        self.SetVirtualSize((-1, sizeV))
        
        
    #########################################################################################################
    def OnPaint(self, event = None):
#        print "OnPaint nbGauche"
        self.OnSize(event)
        
        
    #########################################################################################################
    def OnPageChanged(self, event = None, page = 0):
        print("OnPageChanged")
        if self.pasEventBook:
            return
        
        
        self.book.ChangeSelection(event.GetSelection())
        if event.GetSelection() == 0:           # Page H
            self.app.tb.activerMarges(False)
            self.app.winMarge.Show(False)
            
        elif event.GetSelection() == 1:         # Page C
            self.PageC.initialiserCorrecteur()       # à cause des paramêtres du correcteur ...
            self.app.tb.activerMarges(True)
            self.app.winMarge.Show(self.app.tb.estActiveMarges())
            
        elif event.GetSelection() == 2:         # Page FT
            self.PageFT.MiseAJourParamCorrec()       # à cause des paramêtres du correcteur ...
            self.PageFT.MiseAJourBmpFT()
            self.app.tb.activerMarges(True)
            self.app.winMarge.Show(self.app.tb.estActiveMarges())
        
        self.OnSystemeChange()
        self.app.tracer()
#        event.Skip()

    def OnSystemeChange(self):
#        self.PageH.SetVirtualSizeVertical()
#        self.PageC.SetVirtualSizeVertical()
        self.app.OnSystemeChange()
        
    def getPage(self):
        return self.book.GetSelection()
    
##########################################################################################################
#
#  Page de gestion de la Fonction de Transfert H
#
##########################################################################################################
class PageH(VerticalScrolledPanel):
    def __init__(self, parent, getFT_H, setFT_H, app):
        VerticalScrolledPanel.__init__(self, parent, -1)#, style = wx.BORDER_SIMPLE)
        
#        self.SetScrollRate(0,20)
#        self.EnableScrolling(False, True)
        self.SetAutoLayout(True)    
    
#        self.parent = parent
        self.app = app

        # Les fonctions pour obtenir les FT
        self.getFT_H = getFT_H
        self.setFT_H = setFT_H
        
        self.FT_sauv = None
        
        self.Freeze()
        
        #
        # Le selecteur de FT
        #
        self.SelFT_H = self.getSelecteur()
        
        #
        # ... Variables ...
        #
        self.labelVari = [_("Paramètres"), _("Variables"), _("Paramètres")]
        sbVari = wx.StaticBox(self, -1, self.labelVari[globdef.TYPE_SELECTEUR_TF])
        self.sbVari = sbVari
        sbsVari = wx.StaticBoxSizer(sbVari, wx.VERTICAL)
        self.panelVariables = VariablesPanel(self, self, app)
        
        sbsVari.Add(self.panelVariables, 1, flag = wx.EXPAND)

        #
        # Decomposition en sous FT
        #
        sbDecomp = wx.StaticBox(self, -1, _("Décomposition"))
        sbsDecomp = wx.StaticBoxSizer(sbDecomp, wx.VERTICAL)
        self.selAffichFT = SelecteurAffichFT(self, app)
        sbsDecomp.Add(self.selAffichFT, 1, flag = wx.EXPAND)

        
        
        #
        # Mise en place
        #
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.SelFT_H, 0, flag = wx.EXPAND|wx.ALIGN_TOP)
        sizer.Add(sbsVari,      0, flag = wx.EXPAND|wx.ALIGN_TOP)
        sizer.Add(sbsDecomp,    0, flag = wx.EXPAND|wx.ALIGN_TOP)
        self.SetSizer(sizer)
        self.sizer = sizer
        
        self.FitInside()
#        wx.CallAfter(self.Layout)
        self.Layout()
#        self.initialiser()
        self.Thaw()
        
#        self.SetupScrolling()#scroll_x = False)
#        
#        self.Bind(wx.EVT_SIZE, self.OnSize)
#    
#    def OnSize(self, event = None):
#        self.SetVirtualSizeHints(self.GetClientSize()[0],-1, self.GetClientSize()[0],-1)

    ##############################################################################################
    def MiseAJourFormats(self):
#        print "MiseAJourFormats page H"
        self.selAffichFT.MiseAJourFormats()
        
    #########################################################################################################
    def initialiser(self):
#        print "initialiser PageH"
        FT_H = self.getFT_H()
        self.SelFT_H.initFTSimple(FT_H)
        self.panelVariables.OnListeVariableModified(FT_H.variables)
        self.selAffichFT.Initialiser()
        self.selAffichFT.OnSelModified(FT_H)
        self.MiseAJourFormats()
        self.Layout()
#        wx.CallAfter(
        wx.CallAfter(self.FitInside)
#        wx.CallAfter(self.Layout)


    #########################################################################################################
    def AppliquerSelecteur(self):
        """ Fonction appelée quand il faut modifier le type de selecteur de FT
            (après une modification des options)
        """
#        print "AppliquerSelecteur", globdef.TYPE_SELECTEUR_TF
        
        if isinstance(self.SelFT_H, SelecteurFTFact) and globdef.TYPE_SELECTEUR_TF == 0:
            return
        if isinstance(self.SelFT_H, SelecteurFTDev) and globdef.TYPE_SELECTEUR_TF == 1:
            return
        if isinstance(self.SelFT_H, SelecteurFTFit) and globdef.TYPE_SELECTEUR_TF == 2:
            return
        
        oldSel = self.SelFT_H    
        self.SelFT_H = self.getSelecteur()
        
#        if oldSel != self.SelFT_H:
        self.Freeze()
        self.sizer.Replace(oldSel, self.SelFT_H, recursive = True)
        oldSel.Destroy()
        self.sbVari.SetLabel(self.labelVari[globdef.TYPE_SELECTEUR_TF])
        self.Refresh()
        self.Thaw()
     
        wx.CallAfter(self.Layout)
#        self.SetVirtualSizeVertical()
        
    #########################################################################################################
    def getSelecteur(self):
        """ Instancie puis renvoie un selecteur de FT
            en fonction du type de FT <FT_H>
        """
        FT_H = self.getFT_H()
        
        if globdef.TYPE_SELECTEUR_TF == 0:
            #
            # Le selecteur de FT sous forme factorisée
            #
            if hasattr(self, 'SelFT_H'):
                # On vient du selecteur polynôme développés
                if isinstance(FT_H, FonctionTransfertDev):
                    FT = FT_H.factoriser()
                    if FT != None:
                        self.setFT_H(FT)
                    else:
                        text = _("La fonction H(p) n'est pas factorisable\n" \
                                 "de manière satisfaisante !\n" \
                                 "Elle sera réinitialisée...")
                        dlg = wx.MessageDialog(self, text,
                               _('Factorisation impossible'),
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
                        dlg.ShowModal()
                        dlg.Destroy()
                        self.setFT_H(FonctionTransfertFact())
                    
                
                # On vient du selecteur Ajustement de courbe
                else: 
                    # La FT n'a pas été changée : on restaure l'ancienne
                    if FT_H.getOrdre() == 0: 
                        print("La FT a été changée")
                        if self.FT_sauv == None:
                            self.setFT_H(self.getFT_H())
                        else:
                            self.setFT_H(self.FT_sauv)
                        FT_H = self.getFT_H()
                        FT_H.detDictVari()
                        FT_H.detLstFTNum()
                        self.OnFTModified()
                    # La FT n'a pas été changée
                    else:
                        FT_H.restoreIncidesVariables()
                        FT_H.classeNulle = False
            else:
                self.setFT_H(FonctionTransfertFact())
#            print self.app.FT_H
            sel = SelecteurFTFact(self, self.getFT_H())    
    
        elif globdef.TYPE_SELECTEUR_TF == 1:
            #
            # Le selecteur de FT sous forme développée
            #
            if hasattr(self, 'SelFT_H'):
                if isinstance(FT_H, FonctionTransfertFact):
                    self.setFT_H(FT_H.developper())
            else:
                self.setFT_H(FonctionTransfertDev())
            sel = SelecteurFTDev(self, self.getFT_H())
            
        else:
            #
            # Le selecteur de FT par identification de paramêtres
            #
            if FT_H != None:
                self.FT_sauv = FT_H.copie()
                self.setFT_H(FonctionTransfertFact(classeNulle = True))
            else:
                self.setFT_H(FonctionTransfertFact(classeNulle = True))
            FT_H = self.getFT_H()
            FT_H.detDictVari()
            FT_H.detLstFTNum()
            sel = SelecteurFTFit(self, FT_H)
            if hasattr(self, 'SelFT_H'):
                self.OnFTModified()
       
        return sel
    
    
    #########################################################################################################
    def OnFTModified(self, sendEvent = True):
        """ Mise à jour du panel quand la FT à été modifiée
        """
#        print "FT_H modifiée :", 
#        print self.app.FT_H
#        print self.app.FT_C
        self.Freeze()
        FT_H = self.getFT_H()
        self.panelVariables.OnListeVariableModified(FT_H.variables)
        self.selAffichFT.OnSelModified(FT_H)
#        self.Layout()
        wx.CallAfter(self.FitInside)
#        self.Fit()
#        wx.CallAfter(self.Layout)
#        self.OnSize()
#        print self.Parent.Parent.GetVirtualSize()
#        self.SetVirtualSizeVertical()
#        self.FitInside()
        
        wx.CallAfter(self.Thaw)
        
        if sendEvent:
            self.sendEventFTModified()

#    #########################################################################################################
#    def SetVirtualSizeVertical(self):
#        print "SetVirtualSizeVertical H",
#        self.FitInside()
##        sizeV = 0
##        for c in self.GetChildren():
##            print ".",c.GetSize()[1],
##            sizeV += c.GetSize()[1]
#        self.SetVirtualSize((-1, -1))
##        print sizeV
        
    #########################################################################################################
    def OnVariableModified(self):
        """ Mise à jour du panel quand la valeur d'une variable à été modifiée
        """
#        print "OnVariableModified pageH"
#        print "Variable modifiée :", self.app.FT_H.variables
#        print "additionner 2 :", self.app.additionner
        FT_H = self.getFT_H()
        n = len(FT_H.lstFTNum)
        FT_H.detLstFTNum()
#        print self.app.FT_H.lstFTNum
        if len(FT_H.lstFTNum) != n:
            self.selAffichFT.OnSelModified(FT_H)
        else:
            self.selAffichFT.OnFTModified(FT_H)
        self.SelFT_H.MiseAJourBmp()
        wx.CallAfter(self.Layout)
#        self.FitInside()
        self.sendEventFTModified()


    #########################################################################################################
    def sendEventFTModified(self):
        evt = SelFTEvent(myEVT_FT_MODIFIED, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)
        
        
    #########################################################################################################
    def OnNomVariableModified(self):
        """ Mise à jour du panel quand le nom d'une variable à été modifié
        """
        self.panelVariables.OnListeVariableModified(self.getFT_H().variables)
        
        wx.CallAfter(self.Layout)
#        self.MettreEnPlace()
        



########################################################################################################
class VariablesPanel(wx.Panel):
    def __init__(self, parent, maitre, app, exclure = []):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.maitre = maitre
        self.app = app
        self.exclure = exclure
#        self.OnListeVariableModified(self.maitre.FT.variables)
        
    def OnListeVariableModified(self, variables):
#        print "OnListeVariableModified",
#        self.Freeze()
        self.DestroyChildren()
        sizer = wx.BoxSizer(wx.VERTICAL)

        if globdef.TYPE_SELECTEUR_TF == 0:
            l = self.getListeTriee(variables)
        else:
            l = list(variables.keys())
        for nom in l:
#        for nom, val in variables.items():
            val = variables[nom]
            if not nom in self.exclure:
                if val.t in [VAR_REEL, VAR_REEL_POS, VAR_REEL_SUPP1, VAR_REEL_POS_STRICT]:
                    slider = True
                    fct = self.app.activerZoomAuto
                else:
                    slider = False
                    fct = None
                vctrl = VariableCtrl(self, val, slider = slider, fct = fct)
                sizer.Add(vctrl, flag = wx.ALIGN_RIGHT | wx.ALL, border = 1)
        
        self.Bind(EVT_VAR_CTRL, self.OnVariableModified)
        
        self.SetSizerAndFit(sizer)
#        à voir s'il faut le rétablir ...
        self.Layout()

#        self.Thaw()
        
    def getListeTriee(self, variables):
        horsTri = [r'\alpha', r'K', r'a', r'T', r'\tau']
        lst = []
        for n in horsTri:
            if n in variables:
                lst.append(n)
            
        def getId(nom):
            i = nom.split('}')[0].split('{')[1]
            return eval(i)
            
        lstPoly = {}
        
        for nom in variables:
            if not nom in lst:
                i = getId(nom)
                if i in lstPoly:
                    lstPoly[i].append(nom)
                else:
                    lstPoly[i] = [nom]
            
        # On trie les noms de variable par Id
        for l in lstPoly.values():
            l.sort()
            
        # On met les Id dans l'ordre
        listId = list(lstPoly.keys())
        listId.sort()
        
        # On rajout tout ça à la liste
        for i in listId:
            lst.extend(lstPoly[i])
                    
        return lst
    
    
    def OnVariableModified(self, event):
#        print self.parent
#        print "Variable modifiée",event.GetVar()
        self.maitre.OnVariableModified()
    
##########################################################################################################
#
#  Page de gestion de la Fonction de Transfert C
#
##########################################################################################################
class PageC(VerticalScrolledPanel):
    def __init__(self, parent, getNum, setNum, getFT_C, setFT_C, app):
        VerticalScrolledPanel.__init__(self, parent, -1)
#        print "Init Page C"
        self.Freeze()
#        self.app = app
        
        # Les fonctions pour obtenir les FT
        self.getFT_C = getFT_C
        self.setFT_C = setFT_C
        
        # La fonction pour obtenir le numéro de FT
        self.getNum = getNum
        self.setNum = setNum
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.lstCorrecteurs = [FonctionTransfertCorrec("P"),
                               FonctionTransfertCorrec("PI"),
                               FonctionTransfertCorrec("PI2"),
                               FonctionTransfertCorrec("PD"),
                               FonctionTransfertCorrec("PD2"),
                               FonctionTransfertFact(multiple = True)]
        
        self.lstNomCorr = ["P",
                           "PI",
                           "PI2",
                           "PD", 
                           "PD2",
                           "Perso"]
        
        self.lstHelp = [_("Correcteur à action Proportionnelle\n"\
                          "sous la forme :\n"\
                          "  C(p) = K"),
                          
                        _("Correcteur à action Proportionnelle et Intégrale\n"\
                          "sous la forme :\n"\
                          "              1 + Tp\n"\
                          "  C(p) = K --------\n"\
                          "              1 + aTp\n"\
                          "avec a>=1"),
                          
                        _("Correcteur à action Proportionnelle et Intégrale\n"\
                          "sous la forme :\n"\
                          "              1 + Tp\n"\
                          "  C(p) = K --------\n"\
                          "                Tp"),
                          
                        _("Correcteur à action Proportionnelle et Dérivée\n"\
                          "sous la forme :\n"\
                          "              1 + aTp\n"\
                          "  C(p) = K --------\n"\
                          "              1 + Tp\n"\
                          "avec a>=1"),
                          
                        _("Correcteur à action Proportionnelle et Dérivée\n"\
                          "sous la forme :\n"\
                          "  C(p) = K (1 + Tp)\n"),
                          
                        _("Correcteur personnalisé")]
        
        
        
        imageList = wx.ImageList(32, 32)
        imageList.Add(Images.Boutons_CorrecP.GetBitmap())
        imageList.Add(Images.Boutons_CorrecPI.GetBitmap())
        imageList.Add(Images.Boutons_CorrecPI.GetBitmap())
        imageList.Add(Images.Boutons_CorrecPD.GetBitmap())
        imageList.Add(Images.Boutons_CorrecPD.GetBitmap())
        imageList.Add(Images.Boutons_CorrecPerso.GetBitmap())
        
#        style = INB_FIT_BUTTON | INB_LEFT | INB_SHOW_ONLY_IMAGES #| INB_SHOW_ONLY_TEXT
        self.book = wx.Toolbook(self, -1, style=wx.BK_LEFT)
#        self.book = lb.FlatImageBook(self, -1, style=style)
        self.book.AssignImageList(imageList)
        
        self.SelCorr = []
        for indx, txts in enumerate(self.lstNomCorr):
            if indx == len(self.lstNomCorr)-1:
                selCorr = SelecteurCorrecteurPerso(self.book, self.lstCorrecteurs[indx], app, self)
                
            else:
                selCorr = SelecteurCorrecteur(self.book, self.lstCorrecteurs[indx], app, self)
            self.book.AddPage(selCorr, "", imageId = indx)
            self.book.GetToolBar().SetToolShortHelp(indx+1, self.lstHelp[indx])
            self.SelCorr.append(selCorr)

#        print self.lstCorrecteurs[4]

        self.setFT_C(self.lstCorrecteurs[0])
        
        sizer.Add(self.book, 1, wx.EXPAND)

        self.SetSizerAndFit(sizer)
        self.sizer = sizer
        
        self.Bind(wx.EVT_TOOLBOOK_PAGE_CHANGED, self.OnPageChanged)
        
        self.Layout()
        self.SendSizeEvent()
        self.Thaw()
        
        self.SetAutoLayout(1)
        
        self.Bind(EVT_BITMAP_CHANGED, self.OnBitmapChanged)
        
    ######################################################################################################
    def getLstScrolledBitmap(self):
        """ Renvoie toutes les ScrolledBitmap contenues dans la fenêtre
            (pour synchronisation)
        """
        lst = []
        for selCorr in self.SelCorr:
            lst.extend(selCorr.getLstScrolledBitmap())
        return lst
    
    #########################################################################################################
    def OnBitmapChanged(self, event):
#        print "OnBitmapChanged C"
        num = event.GetNum()
        self.setNum(num)
        self.sizer.Layout()
        
    ##############################################################################################
    def MiseAJourFormats(self):
#        print "MiseAJourFormats page C"
        sel = self.book.GetSelection()
        self.SelCorr[sel].panelAffiche.MiseAJourFormats()
        

    ##############################################################################################
    def initialiser(self):
#        print "initialiser pageC"
        FT_C = self.getFT_C()
        if hasattr(FT_C, 't'):
            self.ChangeSelection(FT_C.t)
        else:
            self.ChangeSelection("Perso")
        sel = self.book.GetSelection()
        self.lstCorrecteurs = [FonctionTransfertCorrec("P"),
                               FonctionTransfertCorrec("PI"),
                               FonctionTransfertCorrec("PI2"),
                               FonctionTransfertCorrec("PD"),
                               FonctionTransfertCorrec("PD2"),
                               FonctionTransfertFact(multiple = True)]
        self.lstCorrecteurs[sel] = FT_C
        for n, s in enumerate(self.lstCorrecteurs):
#            print n, s
            self.SelCorr[n].initialiser(s, redessiner = False)
#        self.SelCorr[sel].initialiser(self.app.FT_C)
        self.MiseAJourFormats()
        
#    #########################################################################################################
#    def SetVirtualSizeVertical(self):
#        print "SetVirtualSizeVertical C"
#        self.FitInside()
#        sizeV = 0
#        for c in self.GetChildren():
#            sizeV += c.GetSize()[1]
#        self.SetVirtualSize((-1, sizeV))
        
        
    #########################################################################################################
    def initialiserCorrecteur(self):
        sel = self.book.GetSelection()
#        print "Initialisation correcteur"
#        print self.lstCorrecteurs[4]
        self.SelCorr[sel].initialiser(self.getFT_C())
#        print self.lstCorrecteurs[4]
        
    #########################################################################################################
    def OnVariableModified(self):
        """ Mise à jour du panel quand la valeur d'une variable à été modifiée
        """
        wx.CallAfter(self.Layout)
        wx.CallAfter(self.FitInside)
        self.sendEventFTModified()
        
    #########################################################################################################
    def sendEventFTModified(self):
        evt = SelFTEvent(myEVT_FT_MODIFIED, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)
        
    #########################################################################################################
    def OnPageChanged(self, event):
        indx = event.GetSelection()
#        corr = self.lstCorrecteurs[indx]
#        print "Page corr :", indx

        #
        # On met à jour la FT_C de l'application
        #
        self.setFT_C(self.lstCorrecteurs[indx])
        FT_C = self.getFT_C()
        if isinstance(FT_C, FonctionTransfertFact):
            FT_C.detFTNum()
            
        #
        # On met à jour le selecteurAffich
        #
        self.SelCorr[indx].panelAffiche.GererSelections()
        
        
        #
        # On signal le changement de FT_C
        #
        self.sendEventFTModified()
        
#    def GererSelections(self):
#        for c in self.SelCorr:
#            c.GererSelections()
            
    def ChangeSelection(self, type):
        self.book.ChangeSelection(self.lstNomCorr.index(type))
            
            
##########################################################################################################    
class SelecteurCorrecteur(wx.Panel):
    def __init__(self, parent, FT_C, app, maitre):
        wx.Panel.__init__(self, parent, -1)
        self.SetAutoLayout(True)
        self.FT = FT_C
        FT_C.detDictVari()
        FT_C.detLstFTNum()
        
#        print "Selecteur Correcteur :",self.FT_C.lstFTNum 
        self.maitre = maitre
        self.getNum = app.getNum
        
        #
        # L'équation de FT_C
        #
#        print "ScrolledBitmap : FT_C"
        self.ft = ScrolledBitmap(self, -1, wx.NullBitmap)
        self.MiseAJourBmpFT()
        
        
#        #
#        # Les réglages de FT_C
#        #
#        Images = wx.ImageList(16,16)
#        Images.Add(GetExpandedIconBitmap())
#        Images.Add(GetCollapsedIconBitmap())
        
#        self._pnl = fpb.FoldPanelBar(self, -1, wx.DefaultPosition,
#                                     wx.Size(-1,-1), fpb.FPB_DEFAULT_STYLE)#, fpb.FPB_COLLAPSE_TO_BOTTOM)
        
        #
        # ... paramêtres ...
        #
        sbVari = wx.StaticBox(self, -1, _("Paramètres"))
        self.sbVari = sbVari
        sbsVari = wx.StaticBoxSizer(sbVari, wx.VERTICAL)
        self.panelVariables = VariablesPanel(self, self, app)
        self.panelVariables.OnListeVariableModified(self.FT.variables)
        sbsVari.Add(self.panelVariables, 1, flag = wx.EXPAND)
        
##        print "Variables correcteur :",FT_C.variables
#        item = self._pnl.AddFoldPanel(_("Paramètres"), collapsed=True,
#                                      foldIcons=Images)
#        self.panelVariables = VariablesPanel(item, self)
#        self.panelVariables.OnListeVariableModified(self.FT.variables)
#        self._pnl.AddFoldPanelWindow(item, self.panelVariables,
#                                     fpb.FPB_ALIGN_WIDTH, 5, 20)
#        self._pnl.Expand(item)
#        self.itemVariables = item
        
        #
        # ... selection affichage ...
        #
        sbDecomp = wx.StaticBox(self, -1, _("Décomposition"))
        sbsDecomp = wx.StaticBoxSizer(sbDecomp, wx.VERTICAL)
        self.panelAffiche = SelecteurAffichCor(self, app, maitre)
        sbsDecomp.Add(self.panelAffiche, 1, flag = wx.EXPAND)
        
#        item = self._pnl.AddFoldPanel(_("Affichage"), collapsed=True,
#                                      foldIcons=Images)
#        self.panelAffiche = SelecteurAffichCor(item, app, maitre)
#        self._pnl.AddFoldPanelWindow(item, self.panelAffiche,
#                                     fpb.FPB_ALIGN_WIDTH, 5, 20)
#        self._pnl.Expand(item)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ft, 0, wx.EXPAND)
        sizer.Add(sbsVari, 0, wx.EXPAND)
        sizer.Add(sbsDecomp, 0, wx.EXPAND)
        self.SetSizer(sizer)
  
        wx.CallAfter(self.Layout)
        
    ######################################################################################################
    def getLstScrolledBitmap(self):
        """ Renvoie toutes les ScrolledBitmap contenues dans la fenêtre
            (pour synchronisation)
        """
        return [self.ft]
        
    ######################################################################################################
    def initialiser(self, FT, redessiner = True):
        self.Freeze()
        
#        self._pnl.Collapse(self.itemVariables)
        self.FT = FT
        self.panelVariables.FT = FT
        self.panelVariables.OnListeVariableModified(FT.variables)
        self.FT.detLstFTNum()
#        print "Variable C modifiée :", self.FT_C.variables
        self.MiseAJourBmpFT()
#        self.OnVariableModified()
#        self._pnl.Expand(self.itemVariables)
        self.panelAffiche.BilanFT()
        self.Thaw()
        
        
    def MiseAJourBmpFT(self):
        """ Mise à jour de l'image de la FT sous forme Num
        """
        lstBmp = []
        for n in self.GetNom():
            lstBmp.append(mathtext_to_wxbitmap(n, globdef.FONT_SIZE_FT_SELECT))
            
        self.ft.SetBitmap(lstBmp, self.GetBmpHD, self.GetTeX)
#        self.Fit()
     
        wx.CallAfter(self.Layout)
        self.Refresh()
    
    
        
    def GetNom(self):
        lstNom = []
        for i,FTNum in enumerate(self.FT.FTNum):
            if len(self.FT.FTNum) == 1:
                n = r""
            else:
                n = r"_{"+str(i+1)+"}"
            lstNom.append(r"C"+n+"("+globdef.VAR_COMPLEXE+")="+self.FT.getMathText()+"="+FTNum.getMathText())
        return lstNom
    
    
    def GetBmpHD(self):
        return mathtext_to_wxbitmap(self.GetNom()[self.getNum()], globdef.FONT_SIZE_FT_HD)
    
    def GetTeX(self):
        return self.GetNom()[self.getNum()]
    
    def OnVariableModified(self):
        """ Mise à jour du panel quand la valeur d'une variable à été modifiée
        """
        self.FT.detLstFTNum()
#        print "Variable C modifiée :", self.FT_C.variables
        self.MiseAJourBmpFT()
        self.maitre.OnVariableModified()
    
    
    
##########################################################################################################    
class SelecteurCorrecteurPerso(wx.Panel):
    def __init__(self, parent, FT_C, app, maitre):
        wx.Panel.__init__(self, parent, -1)
        self.SetAutoLayout(True)
        self.FT = FT_C
        self.FT.detDictVari(retard = False)
#        print "variables correcteur",self.FT.t, ":",self.FT.variables
#        FT_C.variables['a']
        self.FT.detLstFTNum()
#        print "Selecteur Correcteur :",self.FT_C.lstFTNum 
        self.maitre = maitre
        self.getNum = app.getNum
        
        #
        # Le selecteur de FT Factorisée
        #
        self.sel = SelecteurFTFact(self, self.FT, nom = "C", retard = False)
        
        
        #
        # L'équation de FT_C
        #
#        print "ScrolledBitmap : FT_C perso"
        self.ft = ScrolledBitmap(self, -1, wx.NullBitmap)
        self.MiseAJourBmpFT()
        
        
#        #
#        # Les réglages de FT_C
#        #
#        Images = wx.ImageList(16,16)
#        Images.Add(GetExpandedIconBitmap())
#        Images.Add(GetCollapsedIconBitmap())
        
#        self._pnl = fpb.FoldPanelBar(self, -1, wx.DefaultPosition,
#                                     wx.Size(-1,-1), fpb.FPB_DEFAULT_STYLE)#, fpb.FPB_COLLAPSE_TO_BOTTOM)
        
        #
        # ... paramêtres ...
        #
        sbVari = wx.StaticBox(self, -1, _("Paramètres"))
        self.sbVari = sbVari
        sbsVari = wx.StaticBoxSizer(sbVari, wx.VERTICAL)
        self.panelVariables = VariablesPanel(self, self, app)
        self.panelVariables.OnListeVariableModified(self.FT.variables)
        sbsVari.Add(self.panelVariables, 1, flag = wx.EXPAND)
        
        
        #
        # ... selection affichage ...
        #
        sbDecomp = wx.StaticBox(self, -1, _("Décomposition"))
        sbsDecomp = wx.StaticBoxSizer(sbDecomp, wx.VERTICAL)
        self.panelAffiche = SelecteurAffichCor(self, app, maitre)
        sbsDecomp.Add(self.panelAffiche, 1, flag = wx.EXPAND)
##        print "Variables correcteur :",FT_C.variables
#        item = self._pnl.AddFoldPanel(_("Paramètres"), collapsed=True,
#                                      foldIcons=Images)
#        self.panelVariables = VariablesPanel(item, self)
#        self.panelVariables.OnListeVariableModified(self.FT.variables)
#        self._pnl.AddFoldPanelWindow(item, self.panelVariables,
#                                     fpb.FPB_ALIGN_WIDTH, 5, 20)
#        self._pnl.Expand(item)
#        self.itemVariables = item
        
#        #
#        # ... selection affichage ...
#        #
#        sbDecomp = wx.StaticBox(self, -1, _("Décomposition"))
#        sbsDecomp = wx.StaticBoxSizer(sbDecomp, wx.VERTICAL)
#        self.panelAffiche = SelecteurAffichCor(self, app, maitre)
#        sbsDecomp.Add(self.panelAffiche, 1, flag = wx.EXPAND)
        
#        item = self._pnl.AddFoldPanel(_("Affichage"), collapsed=True,
#                                      foldIcons=Images)
#        self.panelAffiche = SelecteurAffichCor(item, app, maitre)
#        self._pnl.AddFoldPanelWindow(item, self.panelAffiche,
#                                     fpb.FPB_ALIGN_WIDTH, 5, 20)
#        self._pnl.Expand(item)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sel, 0, wx.EXPAND)
        sizer.Add(self.ft, 0, wx.EXPAND)
        sizer.Add(sbsVari, 0, wx.EXPAND)
        sizer.Add(sbsDecomp, 0, wx.EXPAND)
        self.SetSizer(sizer)
     
        wx.CallAfter(self.Layout)
        
    ######################################################################################################
    def getLstScrolledBitmap(self):
        """ Renvoie toutes les ScrolledBitmap contenues dans la fenêtre
            (pour synchronisation)
        """
        return [self.ft]
    
    
    ######################################################################################################
    def initialiser(self, FT, redessiner = True):
        self.Freeze()
#        print "initialisation selecteur corecteur perso"
#        self._pnl.Collapse(self.itemVariables)
        self.FT = FT
        self.panelVariables.FT = FT
        self.sel.initFT(FT, redessiner)
        self.FT.detDictVari(retard = False)
        self.FT.detLstFTNum()
        self.panelVariables.OnListeVariableModified(FT.variables)
        
#        print "Variable C modifiée :", self.FT_C.variables
        self.MiseAJourBmpFT()
#        self.OnVariableModified()
#        self._pnl.Expand(self.itemVariables)
        self.panelAffiche.BilanFT()
        
        self.Thaw()
        
        
    def MiseAJourBmpFT(self):
        """ Mise à jour de l'image de la FT sous forme Num
        """
        lstBmp = []
        for n in self.GetNom():
            lstBmp.append(mathtext_to_wxbitmap(n, globdef.FONT_SIZE_FT_SELECT))
        self.ft.SetBitmap(lstBmp, self.GetBmpHD, self.GetTeX)
   
        wx.CallAfter(self.Layout)
        self.Refresh()
        
        
    def GetNom(self):
        lstNom = []
        for i,FTNum in enumerate(self.FT.FTNum):
            lstNom.append(r"C_{"+str(i+1)+"}("+globdef.VAR_COMPLEXE+")="+FTNum.getMathText())
        return lstNom
    
    
    def GetBmpHD(self):
        return mathtext_to_wxbitmap(self.GetNom()[self.getNum()], globdef.FONT_SIZE_FT_HD)
    
    def GetTeX(self):
        return self.GetNom()[self.getNum()]
    
    def OnVariableModified(self):
        """ Mise à jour du panel quand la valeur d'une variable à été modifiée
        """
        self.FT.detLstFTNum()
#        print "Variable C modifiée :", self.FT_C.variables
        self.MiseAJourBmpFT()
        self.maitre.OnVariableModified()
    
    
    def OnFTModified(self):
        self.Freeze()
        self.panelVariables.OnListeVariableModified(self.FT.variables)
        self.FT.detLstFTNum()
        self.MiseAJourBmpFT()
      
        wx.CallAfter(self.Layout)
        
        self.Thaw()

        self.maitre.OnVariableModified()
        
##########################################################################################################
#
#  Page de gestion de la Fonction de Transfert
#
##########################################################################################################
class PageFT(VerticalScrolledPanel):
    def __init__(self, parent, getNum, setNum, getFTBF, getFTBO, getFT_C, app):
        VerticalScrolledPanel.__init__(self, parent, -1)
#        print "Init Page C"
        self.Freeze()
        self.app = app

        # Les fonctions pour obtenir les FT
        self.getFTBF = getFTBF
        self.getFTBO = getFTBO
        self.getFT_C = getFT_C
        
        # La fonction pour obtenir le numéro de FT
        self.getNum = getNum
        self.setNum = setNum
        
        #
        # ... paramêtres ...
        #
        sbParam = wx.StaticBox(self, -1, _("Paramètres du Correcteur"))
        sbsParam = wx.StaticBoxSizer(sbParam, wx.VERTICAL)

        self.panelVariables = VariablesPanel(self, self, app)
        self.panelVariables.OnListeVariableModified(self.app.FT_C.variables)

        sbsParam.Add(self.panelVariables, 0, wx.EXPAND)

        
        #
        # ... selection affichage ...
        #
        sbAffich = wx.StaticBox(self, -1,_("Affichage"))
        sbsAffich = wx.StaticBoxSizer(sbAffich, wx.VERTICAL)
        
        self.panelAffiche = wx.Panel(self, -1)#, style = wx.BORDER_SIMPLE)
        
        # 
        # Selection de FTBO
        gbSizer = wx.GridBagSizer()
        
        self.ftbo = ScrolledBitmap(self.panelAffiche, -1, wx.NullBitmap)
        self.cbftbo = wx.CheckBox(self.panelAffiche, -1, "", style = wx.ALIGN_RIGHT)
        selFormat = SelecteurFormatLigne(self.panelAffiche, 0, self.app.formats["HC"], _("Modifier le format du tracé de cette FT"))
        
        self.selFormatHC = selFormat
        self.cbftbo.SetValue(self.app.tracerFTBO)
        self.cbftbo.SetToolTipString(_("Si coché, trace le lieu de la Fonction de Transfert\n"\
                                   " du système en Boucle Ouverte"))
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox_O, self.cbftbo)
        
        #       
        # Selection de FTBF
        self.ftbf = ScrolledBitmap(self.panelAffiche, -1, wx.NullBitmap)
        self.cbftbf = wx.CheckBox(self.panelAffiche, -1, "", style = wx.ALIGN_RIGHT)
        selFormat = SelecteurFormatLigne(self.panelAffiche, 0, self.app.formats["FTBF"], _("Modifier le format du tracé de cette FT"))
        
        self.selFormatFTBF = selFormat
        self.cbftbf.SetValue(self.app.tracerFTBF)
        self.cbftbf.SetToolTipString(_("Si coché, trace le lieu de la Fonction de Transfert\n"\
                                   " du système en Boucle Fermée"))
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox_F, self.cbftbf)
        
        #
        # Mise en place
        gbSizer.Add(self.ftbo, (0,0), (1,1), wx.ALIGN_CENTER_VERTICAL| wx.ALL|wx.EXPAND, border = 5)
        gbSizer.Add(self.ftbf, (1,0), (1,1), wx.ALIGN_CENTER_VERTICAL| wx.ALL|wx.EXPAND, border = 5)
        
        gbSizer.Add(self.cbftbo, (0,1), (1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT| wx.ALL|wx.EXPAND, border = 5)
        gbSizer.Add(self.cbftbf, (1,1), (1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT| wx.ALL|wx.EXPAND, border = 5)
        
        gbSizer.Add(self.selFormatHC, (0,2), (1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT| wx.ALL|wx.EXPAND, border = 5)
        gbSizer.Add(self.selFormatFTBF, (1,2), (1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT| wx.ALL|wx.EXPAND, border = 5)
        
        gbSizer.AddGrowableCol(0)
        
        self.panelAffiche.SetSizer(gbSizer)
        sbsAffich.Add(self.panelAffiche, 1, wx.EXPAND)
#        self.gbSizer = gbSizer
        
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sbsParam, 0, wx.EXPAND)
        sizer.Add(sbsAffich, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.sizer = sizer
        

        self.Layout()

        self.Thaw()
        
        self.SetAutoLayout(1)
        
        self.Bind(EVT_BITMAP_CHANGED, self.OnBitmapChanged)
        
#        # Synchronisation des scrolledBitmaps
#        lstBmp = [self.ftbo]
#        for selCorr in self.Parent.Parent.PageC.SelCorr:
#            lstBmp.append(selCorr.ft)
#        self.ftbf.synchroniserAvec(lstBmp)
        
    ######################################################################################################
    def getLstScrolledBitmap(self):
        """ Renvoie toutes les ScrolledBitmap contenues dans la fenêtre
            (pour synchronisation)
        """
        return [self.ftbo, self.ftbf]
    
    
    ##############################################################################################
    def MiseAJourFormats(self):
#        print "MiseAJourFormats page FT"
        WindowUpdateLocker(self)
        self.selFormatHC.MiseAJour(self.app.formats["HC"])
        self.selFormatFTBF.MiseAJour(self.app.formats["FTBF"])
        self.Layout()
#        self.FitInside()
    
    
    #########################################################################################################
    def OnBitmapChanged(self, event):
#        print "OnBitmapChanged FT"
        num = event.GetNum()
        self.setNum(num)
        self.sizer.Layout()
        
        
    #########################################################################################################
    def MiseAJourBmpFT(self, n = 0):
        """ Mise à jour de l'image de la FT sous forme Num
        """
        WindowUpdateLocker(self)
#        self._pnl.Collapse(self.itemAffich)
#        print "gbSizer",self.gbSizer.GetSize()
        lstBmp = []
        for n in self.getFTBO():
            lstBmp.append(mathtext_to_wxbitmap(n.getMathTextNom(), globdef.FONT_SIZE_FT_SELECT))    
        self.ftbo.SetBitmap(lstBmp, self.GetBmpHDFTBO, self.GetTeXFTBO, self.getNum())
      
                            
        lstBmp = []
        for n in self.getFTBF():
            lstBmp.append(mathtext_to_wxbitmap(n.getMathTextNom(), globdef.FONT_SIZE_FT_SELECT))
        self.ftbf.SetBitmap(lstBmp, self.GetBmpHDFTBF, self.GetTeXFTBF, self.getNum())
        
#        self.ftbo.FitInside()
        wx.CallAfter(self.panelAffiche.Layout)
        self.Layout()
#        self.gbSizer.Layout()
#        self.gbSizer.SetMinSize(self.panelAffiche.GetSize())
#        self.gbSizer.FitInside(self.panelAffiche)
#        print "gbSizer",self.gbSizer.GetSize()
#        self.gbSizer.Layout()
        
#        self.panelAffiche.Layout()
#        self.panelAffiche.Fit()
#        self.Fit()
#        self.Thaw()
#        print "FTBO", self.ftbo.GetSize(), self.panelAffiche.GetSize()
#        print self.itemParam.GetSize()
    
    def GetBmpHDFTBO(self):
        return mathtext_to_wxbitmap(self.getFTBO()[self.getNum()].getMathTextNom(), globdef.FONT_SIZE_FT_HD)
    
    def GetBmpHDFTBF(self):
        return mathtext_to_wxbitmap(self.getFTBF()[self.getNum()].getMathTextNom(), globdef.FONT_SIZE_FT_HD)
    
    def GetTeXFTBO(self):
        return self.getFTBO()[self.getNum()].getMathTextNom()
    
    def GetTeXFTBF(self):
        return self.getFTBF()[self.getNum()].getMathTextNom()
    
    #########################################################################################################
    def MiseAJourParamCorrec(self):
        WindowUpdateLocker(self)
        self.panelVariables.OnListeVariableModified(self.getFT_C().variables)
        self.Layout()
#        self.Thaw()
    
    #########################################################################################################
    def initialiser(self):
#        print "initialiser pageFT"
        WindowUpdateLocker(self)
        self.panelVariables.OnListeVariableModified(self.getFT_C().variables)
        self.MiseAJourBmpFT()
        self.MiseAJourFormats()
        self.BilanFT()
        
#        self._pnl.RedisplayFoldPanelItems() # Pas sûr que ce soit utile ...
        self.Layout()
#        self._pnl.Expand(self.itemParam)
#        self.Thaw()
        
#        self.app.FT_C.detLstFTNum()
#        self.OnVariableModified()
        
    #########################################################################################################
    def OnVariableModified(self):
        """ Mise à jour du panel quand la valeur d'une variable à été modifiée
        """
#        print "OnVariableModified pageFT"
        self.app.FT_C.detLstFTNum()
        self.sendEventFTModified()
        self.MiseAJourBmpFT()
        
    #########################################################################################################
    def sendEventFTModified(self):
        evt = SelFTEvent(myEVT_FT_MODIFIED, self.GetId())
        self.GetEventHandler().ProcessEvent(evt)
        
    #########################################################################################################
    def EvtCheckBox_O(self, event):
#        print "TracerH :", event.IsChecked()
        self.app.tracerFTBO = event.IsChecked()
        self.app.tracer()
        
    #########################################################################################################
    def EvtCheckBox_F(self, event):
#        print "TracerH :", event.IsChecked()
        self.app.tracerFTBF = event.IsChecked()
        self.app.tracer()
        
    #########################################################################################################
    def BilanFT(self):
        self.app.lstFTTracees = []
        for c, f in [(self.cbftbo, self.selFormatHC), (self.cbftbf, self.selFormatFTBF)]:
            if c.IsChecked():
                self.app.lstFTTracees.append((c, f))



##########################################################################################################
#
# Le selecteur des FT à afficher
#     H - C - HxC
#
#
##########################################################################################################
class SelecteurAffichCor(wx.Panel):
    def __init__(self, parent, app, maitre):
        wx.Panel.__init__(self, parent, -1)
        self.maitre = maitre
        self.app = app
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        #       
        # Selection de H
        #
        sizerH = wx.BoxSizer(wx.HORIZONTAL)
        
        self.cb = wx.CheckBox(self, -1, "H("+globdef.VAR_COMPLEXE+")", style = wx.ALIGN_RIGHT)
        self.cb.SetToolTipString(_("Si coché, trace le lieu de la Fonction de Transfert ")+"H("+globdef.VAR_COMPLEXE+")")
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.cb)
        
        sizerH.Add(self.cb, flag = wx.ALL, border = 5)
        
        selFormat = SelecteurFormatLigne(self, 0, self.app.formats["H"], _("Modifier le format du tracé de cette FT"))
        self.selFormatH = selFormat
        sizerH.Add(selFormat, flag = wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border = 5)
        
        sizer.Add(sizerH, flag = wx.ALIGN_RIGHT | wx.ALL, border = 5)
        
        #       
        # Selection de C
        #
        sizerH2 = wx.BoxSizer(wx.HORIZONTAL)

        self.cbc = wx.CheckBox(self, -1, "C("+globdef.VAR_COMPLEXE+")", style = wx.ALIGN_RIGHT)
        self.cbc.SetToolTipString(_("Si coché, trace le lieu de la Fonction de Transfert du correcteur ")+"C("+globdef.VAR_COMPLEXE+")")
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.cbc)
        
        sizerH2.Add(self.cbc, flag = wx.ALL, border = 5)
        
        selFormat = SelecteurFormatLigne(self, 0, self.app.formats["C"], _("Modifier le format du tracé de cette FT"))
        self.selFormatC = selFormat
        sizerH2.Add(selFormat, flag = wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border = 5)
        
        sizer.Add(sizerH2, flag = wx.ALIGN_RIGHT | wx.ALL, border = 5)
        
        #       
        # Selection de HC
        #
        sizerH3 = wx.BoxSizer(wx.HORIZONTAL)

        self.cbo = wx.CheckBox(self, -1, "H("+globdef.VAR_COMPLEXE+") x C("+globdef.VAR_COMPLEXE+")", style = wx.ALIGN_RIGHT)
        self.cbo.SetToolTipString(_("Si coché, trace le lieu de la Fonction de Transfert\n"
                                    " du système en Boucle Ouverte"))
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.cbo)
        
        sizerH3.Add(self.cbo, flag = wx.ALL, border = 5)
        
        selFormat = SelecteurFormatLigne(self, 0, self.app.formats["HC"], _("Modifier le format du tracé de cette FT"))
        self.selFormatHC = selFormat
        sizerH3.Add(selFormat, flag = wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border = 5)
        
        sizer.Add(sizerH3, flag = wx.ALIGN_RIGHT | wx.ALL, border = 5)
        
        self.GererSelections()
        
        self.SetSizerAndFit(sizer)
        
        
    #########################################################################################################
    def MiseAJourFormats(self):
#        print "MiseAJourFormats cor"
        self.selFormatH.MiseAJour(self.app.formats["H"])
        self.selFormatC.MiseAJour(self.app.formats["C"])
        self.selFormatHC.MiseAJour(self.app.formats["HC"])
    
            
    ###############################################################################################
    def EvtCheckBox(self, event):
        id = event.GetId()
        value = event.IsChecked()
#        print "Selection modifiée", id, value, self.cb.GetId(), self.cbc.GetId(), self.cbo.GetId()
        if id == self.cb.GetId():
            self.app.CorTracerH = value
        elif id == self.cbc.GetId():
            self.app.CorTracerC = value
        elif id == self.cbo.GetId():
            self.app.CorTracerCH = value
        
#        self.maitre.GererSelections()
        
        self.app.tracer()
        
        
    #########################################################################################################
    def GererSelections(self):
        self.cbo.SetValue(self.app.CorTracerCH)
        self.cbc.SetValue(self.app.CorTracerC)
        self.cb.SetValue(self.app.CorTracerH)
        self.BilanFT()
        
    #########################################################################################################
    def BilanFT(self):
        self.app.lstFTTracees = []
        for c, f in [(self.cbo, self.selFormatHC), (self.cb, self.selFormatH), (self.cbc, self.selFormatC)]:
            if c.IsChecked():
                self.app.lstFTTracees.append((c, f))
            
        
#    def OnVariableModified(self):
#        """ Mise à jour du panel quand la valeur d'une variable à été modifiée
#        """
#        self.parent.OnVariableModified()
        
        
        
##########################################################################################################
#
#  Controle de gestion des sous Fonctions de Transfert
#
##########################################################################################################
class SelecteurAffichFT(wx.Panel):
    """ Panel gérant l'affichage des sous fonctions de Transert, comprenant :
        - H
        - Les sous-FT de H
        - Le produit partiel des sous-FT
        
        Valable pour pageH
    """
    def __init__(self, parent, app):
        wx.Panel.__init__(self, parent, -1)#, style = wx.BORDER_SIMPLE)
        self.FT = None
        self.app = app

        self.Freeze()
        
        self.SetAutoLayout(True)
        
        #
        # La décomposition : H = H1 x H2 x ...
        #
        sizerH1 = wx.BoxSizer(wx.HORIZONTAL)

        self.bmp0 = wx.StaticBitmap(self, -1, wx.NullBitmap)
        self.MiseAJourSommeTotale()
        
        self.cb = wx.CheckBox(self, -1, "", style = wx.ALIGN_RIGHT)
        self.cb.SetValue(self.app.TracerH)
        self.cb.SetToolTipString(_("Si coché, trace le lieu de la Fonction de Transfert ")+"H("+globdef.VAR_COMPLEXE+")")
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.cb)
        
        selFormat= SelecteurFormatLigne(self, 0, self.app.formats["H"], _("Modifier le format du tracé de cette FT"))
        self.selFormatH = selFormat
        
        sizerH1.Add(self.bmp0, 1, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizerH1.Add(self.cb, 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizerH1.Add(selFormat, 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border = 5)
        
        #
        # La somme partielle
        #
        sizerH2 = wx.BoxSizer(wx.HORIZONTAL)
        self.bmp = wx.StaticBitmap(self, -1, wx.NullBitmap)
        self.MiseAJourSomme()
        
        self.cbs = wx.CheckBox(self, -1, "", style = wx.ALIGN_RIGHT)
        self.cbs.SetValue(self.app.additionner)
        self.cbs.SetToolTipString(_("Si coché, trace le lieu de ce produit de Fonctions de Transfert"))
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBoxS, self.cbs)
        
        selFormat = SelecteurFormatLigne(self, 0, self.app.formats["SomH"], _("Modifier le format du tracé de cette FT"))
        self.selFormatS = selFormat
        
        sizerH2.Add(self.bmp, 1, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizerH2.Add(self.cbs, 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizerH2.Add(selFormat, 0, flag = wx.ALIGN_CENTER| wx.ALIGN_CENTER_VERTICAL | wx.LEFT , border = 5)
        
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(sizerH1, flag = wx.ALIGN_RIGHT | wx.ALL, border = 5)
        self.sizer.Add(wx.StaticLine(self, -1, style = wx.LI_HORIZONTAL), flag = wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self, -1, style = wx.LI_HORIZONTAL), flag = wx.EXPAND)
        self.sizer.Add(sizerH2, flag = wx.ALIGN_RIGHT | wx.ALL, border = 5)
        
        #
        # Les sous fonctions
        #
        self.lstSelFTCtrl = []
        self.InsererAffichFT()
        
        #
        # Gestion des activations des CheckBox (Somme totale OU BIEN le reste)
        #
        self.GererActivation()
        
        self.Layout()
        self.SetSizerAndFit(self.sizer)
        
        
        self.Thaw()

#        self.Construire()
#        
#    def DoGetBestSize(self):
#        print "GetBestSize"
#        return   wx.Size(self.GetSize()[0], self.GetVirtualSize()[1]+2)
#

    #########################################################################################################
    def Initialiser(self):
        """ Initialisation complète du selecteur
            (en cas de RàZ système)
        """
        self.app.TracerH = True
        self.GererActivation()
        self.cb.Enable(True)
        self.cb.SetValue(True)
        self.selFormatH.Activer(True)
        self.MiseAJourFormats()
        self.BilanFT()


    #########################################################################################################
    def MiseAJourFormats(self):
        self.selFormatH.MiseAJour(self.app.formats["H"])
        self.selFormatS.MiseAJour(self.app.formats["SomH"])
        for i, f in enumerate(self.lstSelFTCtrl):
            f.selFormat.MiseAJour(self.app.formats["H"+str(i)])
        

    #########################################################################################################
    def OnFTModified(self, FT):
#        print "OnFTModified selecteur multi FT"
        self.FT = FT
        self.Refresh()
        self.Freeze()
        
        for i, s in enumerate(self.lstSelFTCtrl):
            s.MiseAJourBmp(self.FT.lstFTNum[i])
        self.Layout()
        
        self.BilanFT()
        
        self.Refresh()
        self.Thaw()
        
    #########################################################################################################
    def OnSelModified(self, FT):
#        print "Reconstruction selecteur multi FT"
        self.FT = FT
        self.Refresh()
        self.Freeze()
        
        self.MiseAJourSommeTotale()
        self.InsererAffichFT()
        self.MiseAJourSomme()
        self.GererActivation()

        self.SetSizerAndFit(self.sizer)
        self.Layout()
        self.Refresh()
        self.Thaw()
        
#        self.SetSizerAndFit(self.sizer)
        
    #########################################################################################################
    def InsererAffichFT(self):
        """ Reconstruction complete de la partie sousFT du Selecteur
            (quand le nombre de sousFT a changé)
        """
#        print "... contruction selecteur multi FT..."
        if self.FT == None:
            return
        
        #
        # RAZ (si besoin)
        #
        self.app.lstTracerSsFT = []
        for a in self.lstSelFTCtrl:
            a.Destroy()
        self.lstSelFTCtrl = []
        
        #
        # On insert les nouveaux AffichFT ....
        #
        i = 2
        for n in range(len(self.FT.lstFTNum)):
            ft = self.FT.lstFTNum[n]
            self.app.lstTracerSsFT.append(True)
            af = AffichFT(self, n, ft, self.app.lstTracerSsFT, self.app.formats["H"+str(n)])
            self.sizer.Insert(i, af, flag = wx.ALIGN_RIGHT)
            self.lstSelFTCtrl.append(af)
            i += 1
            
#        self.SetSizerAndFit(self.sizer)
#        self.sizer.Layout()
#        self.Layout()
#        self.Fit()
        

#    #########################################################################################################
#    def MiseAJourFT(self):
#        """ Modifie les expressions des sous FT (bitmap)
#            quand on a modifié une variable
#        """
##        print self.lstSelFTCtrl
#        for n in range(len(self.FT.lstFTNum)):
#            self.lstSelFTCtrl[n].MiseAJourFT(self.FT.lstFTNum[n])
#            
#        self.Layout()

    #########################################################################################################
    def OnModif(self, num, val):
        """ Fonction appelée quand on a modifié la selection de FT à tracer
        """
        self.app.lstTracerSsFT[num] = val
        self.MiseAJourSomme()
        self.app.tracer()
        
    #########################################################################################################
    def EvtCheckBox(self, event):
#        print "EvtCheckBox", event.IsChecked()
        self.app.TracerH = event.IsChecked()
        self.GererActivation()
        self.app.tracer()
        
    #########################################################################################################
    def EvtCheckBoxS(self, event):
#        print "EvtCheckBoxS", event.IsChecked()
        self.app.additionner = event.IsChecked()
        self.app.tracer()
        
    #########################################################################################################
    def GererActivation(self):
        
#        # On desactive la derniére sous fonction
#        n = 0
#        ct = None
#        for c in self.lstSelFTCtrl:
#            if c.cbA.IsChecked():
#                n += 1
#                ct = c
#        if n == 1:
#            c.cbA.Enable(False)
#            c.selFormat.Activer(False)
#        else:
#            for c in self.lstSelFTCtrl:
#                c.cbA.Enable(True)
#                c.selFormat.Activer(True)
        
        if self.app.TracerH:
            self.cbs.Enable(False)
            self.selFormatS.Activer(False)
            for c in self.lstSelFTCtrl:
                c.cbA.Enable(False)
                c.selFormat.Activer(False)
            
        else:
            self.cbs.Enable(True)
            self.selFormatS.Activer(True)
            for c in self.lstSelFTCtrl:
                c.cbA.Enable(True)
                c.selFormat.Activer(True)
            
        
            
            
        self.BilanFT()
        
        
    #########################################################################################################
    def BilanFT(self):
        self.app.lstFTTracees = []
        if self.cb.IsChecked():
            self.app.lstFTTracees.append((self.cb, self.selFormatH))
            
        for c in self.lstSelFTCtrl:
            if c.cbA.IsChecked():
                self.app.lstFTTracees.append((c.cbA, c.selFormat))
            
        if self.cbs.IsChecked():
            self.app.lstFTTracees.append((self.cbs, self.selFormatS))
        
    #########################################################################################################
    def MiseAJourSomme(self):
        """ Mise à jour de la somme PARTIELLE
            quand on a modifié la selection des sous FT à afficher
        """
        if self.FT == None:
            return
        self.Freeze()
#        print "Mise à jour Somme :", s
        self.bmp.SetBitmap(mathtext_to_wxbitmap(self.GetNom(), taille = globdef.FONT_SIZE_SSFT))
        self.Layout()
        self.Refresh()
        self.Thaw()
        
    def GetNom(self):
        s = ""
        for n in range(len(self.FT.lstFTNum)):
            if self.app.lstTracerSsFT[n]:
                s += r"H_{" + str(n+1) + "}("+globdef.VAR_COMPLEXE+")"
                if n < len(self.FT.lstFTNum)-1:
                    s += globdef.SYMBOLE_MULT
        return s
    
    
#    def GetBmpHD(self):
#        return mathtext_to_wxbitmap(self.GetNom(), globdef.FONT_SIZE_FT_HD)
    
    #########################################################################################################
    def MiseAJourSommeTotale(self):
        if self.FT == None:
            return
        self.Freeze()
        self.bmp0.SetBitmap(mathtext_to_wxbitmap(self.GetNomT(), taille = globdef.FONT_SIZE_SSFT))
        self.Layout()
        self.Refresh()
        self.Thaw()
        
    def GetNomT(self):
        s = r"H("+globdef.VAR_COMPLEXE+")="
        for n in range(len(self.FT.lstFTNum)):
            s += "H_{" + str(n+1) + "}("+globdef.VAR_COMPLEXE+")"
            if n < len(self.FT.lstFTNum)-1:
                    s += globdef.SYMBOLE_MULT
        return s
    
#    def GetBmpHDT(self):
#        return mathtext_to_wxbitmap(self.GetNomT(), globdef.FONT_SIZE_FT_HD)
    
#    #########################################################################################################
#    def changerVarComplexe(self):
#        self.MiseAJourSommeTotale()
#        self.MiseAJourSomme()
#        for s in self.lstSelFTCtrl:
#            s.changerVarComplexe()
        
        
        
##########################################################################################################
class AffichFT(wx.PyPanel):
    """ Panel contenant :
        - une sous FT (sous forme de ScrolledBitmap)
        - une CheckBox pour la "sélectionner"
        - un SelecteurFormatFT
    """
    def __init__(self, parent, id, FTNum, lstAction, format):
        wx.PyPanel.__init__(self, parent, id)#, style = wx.BORDER_SIMPLE)
        self.parent = parent
        
        
        self.nom = r"H_{"+str(id+1)+"}"
        
        self.ft = wx.StaticBitmap(self, -1, wx.NullBitmap)
        
        
        self.cbA = wx.CheckBox(self, 0, "")
        self.cbA.SetValue(lstAction[id])
        self.cbA.SetToolTipString(_("Si coché, trace le lieu de cette sous Fonction de Transfert"\
                                    " de ")+"H("+globdef.VAR_COMPLEXE+")")
        
        self.selFormat = SelecteurFormatLigne(self, id, format, _("Modifier le format du tracé de cette FT"))
        
        #
        # Mise en place
        #
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.ft, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizer.Add(self.cbA, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        sizer.Add(self.selFormat, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.SetSizerAndFit(sizer)
        self.sizer = sizer
        self.MiseAJourBmp(FTNum)
        #
        # Gestion des évenements
        #
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.cbA)    
        
        
    def EvtCheckBox(self, event):
        self.parent.OnModif(self.GetId(), event.IsChecked())
        
    def changerVarComplexe(self):
        self.MiseAJourBmp(self.FTNum)
        
    def MiseAJourBmp(self, FTNum):
        self.FTNum = FTNum
        FTNum.nom = self.nom
        self.ft.SetBitmap(self.FTNum.getBitmap(taille = globdef.FONT_SIZE_SSFT))
        self.SetSizerAndFit(self.sizer)
        self.Layout()
        
#    def GetBmpHD(self):
#        return self.FTNum.getBitmap(taille = globdef.FONT_SIZE_FT_HD)
    
        
        
        

    

    
#####################################################################################################
#####################################################################################################
class BarreOutils(aui.AuiToolBar):
    def __init__(self, parent, app):
        aui.AuiToolBar.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize,
                                   aui.AUI_TB_DEFAULT_STYLE)
#                       wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)# | wx.TB_RIGHT)
        
        self.app = app
        
        tsize = (32,32)
        self.lstImg = {'BAbout' : Images.Bouton_About.GetBitmap(),
                      'BRepons' : Images.Bouton_Reponse.GetBitmap(),
                      'BMarges' : Images.Bouton_Marges.GetBitmap(),
                      'BOuvrir' : Images.Bouton_Ouvrir.GetBitmap(),
                      'BEnreg'  : Images.Bouton_Enregistrer.GetBitmap(),
                      'BNouve' : Images.Bouton_Nouveau.GetBitmap(),
                      'BDecmp' : Images.Bouton_Decomposition.GetBitmap(),
                      'BOptio' : Images.Bouton_Options.GetBitmap(),
                      'BTravx' : Images.Bouton_Travaux.GetBitmap(),
                      'BPoles' : Images.Bouton_Poles.GetBitmap(),
                      'BImpri' : Images.Bouton_Imprimer.GetBitmap(),
                      }
        self.SetToolBitmapSize(tsize)

        self.lstToolTip = {'BAbout'  : _('Afficher des informations (Version, Licence, Auteurs)\n'\
                                        'à propos de pySyLiC'),
                          'BRepons' : _('Afficher la réponse temporelle du système'),
                          'BMarges' : _('Afficher les marges de stabilité du système\n'\
                                        '  Remarque :\n'\
                                        "  Cet outil n'est disponible que pour les systèmes bouclés\n"\
                                        "  et en mode d'édition du correcteur"),
    #                      'BFTBF'   : _('Bouton FTBF.png'),
                          'BOuvrir' : _('Ouvrir un fichier "système" (.syl)'),
                          'BEnreg'  : _('Enregistrer les paramêtres du système (fonctions de transfert, ...)\n'\
                                        'dans un fichier "système" (.syl)'),
                          'BNouve'  : _('Créer un nouveau système\n'\
                                        '  ATTENTION :\n'\
                                        '  Le système courant sera ecrasé !'),
                          'BDecmp'  : _('Afficher une décomposition en éléments simples\n'\
                                        'des Fonctions de Transfert du système'),
                          'BOptio'  : _('Permet de régler les différents options de pySyLiC'),
                          'BTravx'  : _('Mettre à jour le tracé'),
                          'BImpri'  : _("Afficher le panneau de gestion de l'impression"),
                          'BPoles'  : _("Afficher les pôles de la FTBF dans le plan complexe")
                          }
        
        self.lstLabel = {'BAbout'  : _("À propos de " + version.__appname__),
                         'BRepons' : _('réponse temporelle du système'),
                         'BMarges' : _('Marges de stabilité du système'),
                         'BOuvrir' : _('Ouvrir un système'),
                         'BEnreg'  : _('Enregistrer le système'),
                         'BNouve'  : _('Créer un nouveau système'),
                         'BDecmp'  : _('Décomposition en éléments simples des FT'),
                         'BOptio'  : _('Réglage des options de pySyLiC'),
                         'BTravx'  : _('Mettre à jour le tracé'),
                         'BImpri'  : _("Imprimer les tracés"),
                         'BPoles'  : _("Pôles de la FT"),
                         }
        
        self.menu = wx.Menu()
        id = 101
        for i in [_("Imprimer"), _("Aperç"), _("Mise en page"), _("Options")]:
            self.menu.Append(id, i)
            self.Bind(wx.EVT_MENU, self.OnMenu, id = id)
            id += 1
            
        self.lstToggle = {'BAbout'  : None,
                          'BRepons' : self.app.TracerReponse,
                          'BMarges' : self.app.TracerMarges,
                          'BOuvrir' : None,
                          'BEnreg'  : None,
                          'BNouve'  : None,
                          'BDecmp'  : self.app.TracerDecomp,
                          'BOptio'  : None,
                          'BTravx'  : None,
                          'BImpri'  : self.menu,
                          'BPoles'  : self.app.TracerPoles,
                          }
        
        self.lstEnable = {'BAbout'  : True,
                          'BRepons' : True,
                          'BMarges' : False,
                          'BOuvrir' : None,
                          'BEnreg'  : None,
                          'BNouve'  : None,
                          'BDecmp'  : True,
                          'BOptio'  : None,
                          'BTravx'  : self.app.traceAJour,
                          'BImpri'  : True,
                          'BPoles'  : True,
                          }
        
        self.lstImg0 = {'BMarges' : setAlpha(self.lstImg['BMarges']),
                        'BTravx'  : setAlpha(self.lstImg['BTravx']),
                       }
                      
        self.lstId = {'BAbout'  : 13,
                      'BRepons' : 14,
                      'BMarges' : 15,
                      'BOuvrir' : 1,
                      'BEnreg'  : 2,
                      'BNouve'  : 3,
                      'BDecmp'  : 17,
                      'BOptio'  : 20,
                      'BTravx'  : 19,
                      'BImpri'  : 16,
                      'BPoles'  : 18,
                      }
        
        self.lstNomItem = ['BNouve', 'BOuvrir', 'BEnreg', 'BImpri', '', 
                           'BRepons', 'BPoles', 'BDecmp', 'BMarges', '', 
                           'BTravx', 'BOptio', 'BAbout']

        self.SetGripperVisible(False)
        
        
        self.reCreateBar()
        
        

            
            
    def reCreateBar(self):

        self.ClearTools()
        
#        print "recréer", self.lstNomItem
        for nom in self.lstNomItem:
            if nom != '':
                id = self.lstId[nom]
                kind = self.lstToggle[nom]
                bmp = self.lstImg[nom]
                label = self.lstLabel[nom]
                help = self.lstToolTip[nom]
    
                if type(kind) == bool:
                    self.AddSimpleTool(id, label, bmp, help, aui.ITEM_CHECK)
                    self.ToggleTool(id, kind)
                    
                elif isinstance(kind, wx.Menu):
                    self.AddSimpleTool(id, label, bmp, help)
                    self.SetToolDropDown(id, True)
                    self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnMenuClick, id=id)
                    
                else:
                    self.AddSimpleTool(id, label, bmp, help)
                    
                if nom in self.lstImg0:
                    self.SetToolDisabledBitmap(id, self.lstImg0[nom])
                    self.EnableTool(id, self.lstEnable[nom])
                
                self.Bind(wx.EVT_TOOL, self.OnClick, id=id)  
            
            else:
                self.AddSeparator()
        
        self.Realize()
            
            

    def OnMenuClick(self, event):
        if event.IsDropDownClicked():
            self.PopupMenu(self.menu)


    def OnMenu(self, event):
        id = event.GetId()
        if id == 101:
#            self.app.OnDoPrint(self.app.zoneGraph.getZonesGraphVisiblesNoteBook())
            self.app.OnDoPrint(self.app.zoneGraph, titre = self.app.getNomFichierCourantCourt())
            
        elif id == 102:
#            self.app.OnPrintPreview(self.app.zoneGraph.getZonesGraphVisiblesNoteBook())
            self.app.OnPrintPreview(self.app.zoneGraph, titre = self.app.getNomFichierCourantCourt())
            
        elif id == 103:
            self.app.OnPageSetup()
            
        elif id == 104:
            self.app.OnOptionsClick(page = 3)
         
    def getPrintCanvas(self):
        return 

    def OnClick(self, event):
        id = event.GetId()

        if id == 14:
            tracer = self.GetToolToggled(id)
            self.app.OnTracerReponse(tracer)
            
        elif id == 13:
            self.app.OnAboutClick(event)
            
        elif id == 15:
            tracer = self.GetToolToggled(id)
            self.app.OnTracerMarges(tracer)
            
        elif id == 18:
            tracer = self.GetToolToggled(id)
            self.app.OnTracerPoles(tracer)
               
        elif id == 16:
            event.SetId(101)
            self.OnMenu(event)

        elif id == 17:
            tracer = self.GetToolToggled(id)
            self.app.OnTracerDecomp(tracer)
            
        elif id == 19:
            self.app.OnFTModified(forcerMaJ = True)
        
#        elif id == 4:    
#            self.parent.OnImprimClick(event)   
            
        elif id == 3:    
            self.app.OnNewClick(event)    
        
        elif id == 2:
            self.app.OnSaveClick(event)
            
        elif id == 1:    
            self.app.OnOpenClick(event)
            
        elif id == 20:
            self.app.OnOptionsClick(event)
           
    ######################################################################################################
    def enleverMiseAJour(self):
        if 'BTravx' in self.lstNomItem:
            self.DeleteTool(self.lstId['BTravx'])
            self.lstNomItem.remove('BTravx')
#            self.reCreateBar()
            self.GetAuiManager().Update()
#            self.GetAuiManager().Refresh()
            
        
    def mettreMiseAJour(self):
        if not 'BTravx' in self.lstNomItem:
            self.lstNomItem.insert(10, 'BTravx')
            self.reCreateBar()
#            self.GetAuiManager().Refresh()
            self.GetAuiManager().Update()
        
    def activerMiseAJour(self, active):
        self.EnableTool(19, active)
        self.lstEnable['BTravx'] = active
        self.Refresh()
    
    
    ######################################################################################################
    def activerMarges(self, active):
#        print "activerMarges", active
        self.EnableTool(15, active)
        self.lstEnable['BMarges'] = active
        self.Refresh()

        
    def estActiveMarges(self):
        return self.GetToolToggled(15)
    
    
    ######################################################################################################
    def DesactiverDecomp(self):
        self.Desactiver('BDecmp')
        
    def DesactiverMarges(self):
        self.Desactiver('BMarges')
        
    def DesactiverReponse(self):
        self.Desactiver('BRepons')
        
    def DesactiverPoles(self):
        self.Desactiver('BPoles')
        
    def Desactiver(self, nom):
#        print "Desactiver", nom
        id = self.lstId[nom]
        evt = wx.CommandEvent(wx.EVT_TOOL.typeId, id)
        self.ToggleTool(id, False)
        self.GetEventHandler().ProcessEvent(evt)
        self.Refresh()







#########################################################################################################
class DialogInitProjet(wx.MessageDialog):
    def __init__(self, parent):
        wx.MessageDialog.__init__(self, parent, _("Voulez-vous vraiment effacer le système en cours d'étude ?"),
                                       _('Confirmation effacement'),
                                       wx.OK | wx.ICON_QUESTION  | wx.CANCEL
                                       #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                       )




##########################################################################################################
class WinMarge(wx.MiniFrame):
    def __init__(self, parent, getNum, getFTBO, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style = wx.DEFAULT_FRAME_STYLE 
                 ):
        
#        self.nbChiffres = int(abs(calcul.decade(globdef.PRECISION)))
#        self.parent = parent
        
        # Les fonctions pour obtenir les FT
        self.getFTBO = getFTBO
        
        # La fonction pour obtenir le numéro de FT
        self.getNum = getNum
        
#        self.FTNum = FTNum
#        self.num = 0
        
        wx.MiniFrame.__init__(self, parent, -1, _("Marges de stabilité"), pos, (300,200), style)
        
        self.SetMinSize((100,100))
        self.SetBackgroundColour(wx.WHITE)
        self.SetToolTip(wx.ToolTip(_("Marges de stabilité selon la règle du revers.")))
        self.SetAutoLayout(True)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        #
        boxP = wx.StaticBox(self, -1, _("Marge de phase"))
        sP = wx.StaticBoxSizer(boxP, wx.VERTICAL)
        self.stOm = wx.StaticBitmap(self, -1, wx.NullBitmap)
        sP.Add(self.stOm, flag = wx.ALL,  border = 8)
        
        self.stMp = wx.StaticBitmap(self, -1, wx.NullBitmap)
        sP.Add(self.stMp, flag = wx.ALL,  border = 8)
        
        sizer.Add(sP, flag = wx.EXPAND|wx.ALL, border = 4)
        
        #
        boxG = wx.StaticBox(self, -1, _("Marge de gain"))
        sG = wx.StaticBoxSizer(boxG, wx.VERTICAL)
        self.stOm180 = wx.StaticBitmap(self, -1, wx.NullBitmap)
        sG.Add(self.stOm180, flag = wx.ALL,  border = 8)
        
        self.stMg = wx.StaticBitmap(self, -1, wx.NullBitmap)
        sG.Add(self.stMg, flag = wx.ALL,  border = 8)
        
        sizer.Add(sG, flag = wx.EXPAND|wx.ALL, border = 4)
        
        self.SetSizerAndFit(sizer)
        
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        #
        boxS = wx.StaticBox(self, -1, _("Surtension"))
        sS = wx.StaticBoxSizer(boxS, wx.VERTICAL)
        self.stOmS = wx.StaticBitmap(self, -1, wx.NullBitmap)
        sS.Add(self.stOmS, flag = wx.ALL,  border = 8)
        
#        self.stMs = wx.StaticText(self, -1, "")
#        sS.Add(self.stMs, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL,  border = 8)
        
        self.isoG = wx.StaticBitmap(self, -1, wx.NullBitmap)
        sS.Add(self.isoG, flag = wx.ALL,  border = 8)
        
        panelbtn = wx.Panel(self, -1)
        button = wx.Button(panelbtn, -1, _("Fermer"))
        sizer.Add(sS, flag = wx.EXPAND|wx.ALL, border = 4)
        sizer.Add(panelbtn, flag = wx.EXPAND|wx.ALL, border = 4)
        
        self.SetSizerAndFit(sizer)
        
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        self.Bind(wx.EVT_BUTTON, self.OnCloseMe, button)


    ######################################################################################################
    def getLstScrolledBitmap(self):
        """ Renvoie toutes les ScrolledBitmap contenues dans la fenêtre
            (pour synchronisation)
        """
        return []
    
    
    ######################################################################################################
    def OnCloseMe(self, event):
        self.Close(True)

    def OnCloseWindow(self, event):
        self.Parent.tb.DesactiverMarges()
#        evt = wx.CommandEvent(wx.EVT_TOOL.typeId, 15)
#        self.parent.tb.ToggleTool(15, False)
#        self.parent.tb.GetEventHandler().ProcessEvent(evt)
#        self.pop.Show(False)
#        self.pop.Destroy()
#        self.Destroy()

#    def setFTNum(self, FTNum):
#        self.num = 0
#        self.FTNum = FTNum
    
#    def setNum(self, num):
#        self.num = num
        
    def calculerMarges(self):  
        self.marges = self.getFTBO()[self.getNum()].getMarges()
        return self.marges
        
    def MiseAJour(self):
        if self.marges.Om0 != None and self.marges.getMargeP() < 0:
            coul = globdef.COUL_MARGE_GAIN_NO
        else:
            coul = globdef.COUL_MARGE_GAIN_OK
        self.stOm.SetBitmap(mathtext_to_wxbitmap(self.marges.getMathTexteOm0()))
        self.stMp.SetBitmap(mathtext_to_wxbitmap(self.marges.getMathTexteMp(), color = coul))

        if self.marges.Om180 != None and self.marges.getMargeG() < 0:
            coul = globdef.COUL_MARGE_GAIN_NO
        else:
            coul = globdef.COUL_MARGE_GAIN_OK
        self.stOm180.SetBitmap(mathtext_to_wxbitmap(self.marges.getMathTexteOm180()))#\u2081\u2088\u2080
        self.stMg.SetBitmap(mathtext_to_wxbitmap(self.marges.getMathTexteMg(), color = coul))

        if self.marges.OmS != None and ((self.marges.getMargeP() < 0 and self.marges.getMargeP() != None) or (self.marges.getMargeG() < 0 and self.marges.getMargeG() != None)):
            coul = globdef.COUL_MARGE_GAIN_NO
        else:
            coul = globdef.COUL_MARGE_GAIN_OK
                
        self.stOmS.SetBitmap(mathtext_to_wxbitmap(self.marges.getMathTexteOmS()))
        self.isoG.SetBitmap(mathtext_to_wxbitmap(self.marges.getMathTexteQ(), color = coul))
        
        self.Fit()
        self.Refresh()
        

##########################################################################################################    
##########################################################################################################
#
#  Gestion des reponses temporelles
#
##########################################################################################################
##########################################################################################################
class WinReponse(wx.MiniFrame, PrintHandler):
    def __init__(self, parent, getNum, setNum, getFTBF, getFTBFnc, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style = globdef.STYLE_FENETRE):
        self.parent = parent
        self.synchroniserPuls = False
        
        # Variable de l'état d'affichage : complet = tous les widgets
        self.AffComplet = True
        
        # Les fonctions pour obtenir les FT
        self.getFTBF = getFTBF
        self.getFTBFnc = getFTBFnc
        
        # La fonction pour obtenir le numéro de FT
        self.getNum = getNum
        self.setNum = setNum

        size = (414,550)
        wx.MiniFrame.__init__(self, parent, -1, _("réponse Temporelle du Système"),
                              pos, size, style)

        self.SetAutoLayout(True)
        
        self.tb = TBReponse(self)

        self.initPrintHandler(PrintoutWx, self.parent, globdef.PRINT_PAPIER_DEFAUT, globdef.PRINT_MODE_DEFAUT)
        
        #
        # Zone de tracé de la réponse
        #
        outils = ["BGrille", "", "BZoomA", "BZoomP", "BDepla", "BEchel", "", "BCurse", 'BImpri', "", "BExpor",'BParam']
        self.ZoneReponse = graph.ZoneGraphOutils(self, parent, 3, outils, tempo = True)
        self.ZoneReponse.Add(graph.ZoneGraphReponse(self.ZoneReponse, self.ZoneReponse, _("réponse temporelle")))

        #
        # Zone d'affichage de la FTBO
        #        
        self.pop = wx.Panel(self, -1)
        
        sizer0 = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
#        st = wx.StaticText(self.pop, -1, "FTBF("+globdef.VAR_COMPLEXE+") = ")
#        sizer.Add(st, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 5)
        
        self.BmpFTBF = ScrolledBitmap(self.pop, -1, wx.NullBitmap)
        self.BmpFTBFnc = ScrolledBitmap(self.pop, -1, wx.NullBitmap, event = False)
        self.cb1 = wx.CheckBox(self.pop, -1, "")
        self.cb1.SetValue(True)
        self.cb2 = wx.CheckBox(self.pop, -1, "")
        self.cb2.SetValue(False)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.cb1)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.cb2)
        sizer.Add(self.cb1, 0, flag = wx.EXPAND)
        sizer.Add(self.BmpFTBF, 1, flag = wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, border = 5)
        sizer.Add(self.cb2, 0, flag = wx.EXPAND)
        sizer.Add(self.BmpFTBFnc, 1, flag = wx.EXPAND|wx.ALL, border = 5)
        
        self.pop.SetSizerAndFit(sizer)
       
        panelbtn = wx.Panel(self, -1)
        button = wx.Button(panelbtn, -1, _("Fermer"))
        self.panelbtn = panelbtn
        
        #
        # Mise en place
        #
        sizer0.Add(self.pop, 0, flag = wx.EXPAND)
        sizer0.Add(self.ZoneReponse,1, flag = wx.EXPAND)
        sizer0.Add(self.tb, flag = wx.EXPAND)
        sizer0.Add(panelbtn, flag = wx.EXPAND)
        self.SetSizer(sizer0)
        self.sizer = sizer0
        
        self.signal = 0
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_BUTTON, self.OnCloseMe, button)
        self.Bind(EVT_BITMAP_CHANGED, self.OnBitmapChanged)
#        self.SetInitialSize(size)
        self.SetAutoLayout(False)

    ######################################################################################################
    def getLstScrolledBitmap(self):
        """ Renvoie toutes les ScrolledBitmap contenues dans la fenêtre
            (pour synchronisation)
        """
        return [self.BmpFTBF, self.BmpFTBFnc]


    ######################################################################################################
    def initTB(self):
        self.signal = 0
        self.tb.ChangeSelection(self.signal)
        
        
    ######################################################################################################
    def EvtCheckBox( self, event ):
       self.MiseAJour()
            
                
    ######################################################################################################
    def OnBitmapChanged(self, event):
        num = event.GetNum()
        self.setNum(num)
        self.MiseAJour(signal = self.signal)
    
    
    ######################################################################################################
    def SetAffComplet(self):
#        print "SetAffComplet"
        self.AffComplet = not self.AffComplet
        
        if self.AffComplet:
            self.TailleOrigZg = self.GetClientSize()
            posZg = self.ZoneReponse.GetScreenPosition()
            self.pop.Show(True)
            self.sizer.Insert(0, self.pop, 0, flag = wx.EXPAND)
            self.tb.Show(True)
            self.sizer.Insert(2, self.tb, 0, flag = wx.EXPAND)
            self.panelbtn.Show(True)
            self.sizer.Insert(3, self.panelbtn, 0, flag = wx.EXPAND)
            
            self.SetClientSize(self.TailleOrig)
            
            PosOrig = self.GetPosition()
            self.SetPosition((PosOrig[0], posZg[1]+self.dph))
            
        else:
            self.TailleOrig = self.GetClientSize()
            
            PosOrig = self.GetPosition()
            posZg = self.ZoneReponse.GetScreenPosition()
            posBmp = self.pop.GetScreenPosition()
            dph = PosOrig[1] - posBmp[1]
            
            self.dph = PosOrig[1] - posZg[1]
            
            self.pop.Show(False)
            self.sizer.Detach(self.pop)
            self.tb.Show(False)
            self.sizer.Detach(self.tb)
            self.panelbtn.Show(False)
            self.sizer.Detach(self.panelbtn)
            if hasattr(self, 'TailleOrigZg'):
                self.SetClientSize(self.TailleOrigZg)
            else:
                self.SetClientSize(self.ZoneReponse.GetSize())
            self.SetPosition((PosOrig[0], posZg[1]+dph))
        self.Layout()
        
    def OnCloseMe(self, event):
        self.Close(True)
        
#        self.MiseAJour()

#    ######################################################################################################
#    def OnToolClick(self, event):
#        id = event.GetId()
#        if id != self.signal:
#            self.tb.ToggleTool(self.signal, False)
#        self.signal = id
#        self.MiseAJour()
        
#    ######################################################################################################
#    def ChangerZoneParam(self, code):
#        self.ZoneParam = self.ZonesParam[code]
#        self.Fit()
#        self.Layout()
        
    ######################################################################################################    
    def MiseAJour(self, signal = None):
#        print "MiseAJour winReponse"
        
        
        if self.cb1.IsChecked() and len(self.getFTBF()) > 0:
            FTBF = self.getFTBF()[self.getNum()]
        else:
            FTBF = None
            
        if FTBF == []:
            return
        
        if self.cb2.IsChecked():
            FTBFnc = self.getFTBFnc()
        else:
            FTBFnc = None
            
        if signal != None:
            self.signal = signal
            
        def evaluer(s):
            try:
                v = eval(s)
                return v
            except:
                return
        
        fctReponsenc = None
        fctReponse = None
        
        if self.signal == 0: # Impulsion
            if FTBF != None:
                fctReponse = FTBF.getReponseImpulsionnelle
            if FTBFnc != None:
                fctReponsenc = FTBFnc.getReponseImpulsionnelle
            fctConsigne = calcul.impulsion
            param = {}
            
        elif self.signal == 1: # Echelon
            if FTBF != None:
                fctReponse = FTBF.getReponseIndicielle
            if FTBFnc != None:
                fctReponsenc = FTBFnc.getReponseIndicielle
            fctConsigne = calcul.echelon
            param = {'amplitude' : self.tb.GetCurrentPage().amplitude.v[0]}
            
        elif self.signal == 2: # Rampe
            if FTBF != None:
                fctReponse = FTBF.getReponseRampe
            if FTBFnc != None:
                fctReponsenc = FTBFnc.getReponseRampe
            fctConsigne = calcul.rampe
            param = {'pente' : self.tb.GetCurrentPage().pente.v[0]}
            
        elif self.signal == 3: # serie d'impulsions
            if FTBF != None:
                fctReponse = FTBF.getReponseSerieImpulsions
            if FTBFnc != None:
                fctReponsenc = FTBFnc.getReponseSerieImpulsions
            fctConsigne = calcul.serieImpulsions
            param = {'periode' : self.tb.GetCurrentPage().periode.v[0]}    
            
        elif self.signal == 4: # Carré
            if FTBF != None:    
                fctReponse = FTBF.getReponseCarre
            if FTBFnc != None:
                fctReponsenc = FTBFnc.getReponseCarre
            fctConsigne = calcul.carre
            param = {}
            param['amplitude'] = self.tb.GetCurrentPage().amplitude.v[0]
            param['periode'] = self.tb.GetCurrentPage().periode.v[0]
            param['decalage'] = self.tb.GetCurrentPage().decalage.v[0]
            
        elif self.signal == 5: # Triangle   
            if FTBF != None:   
                fctReponse = FTBF.getReponseTriangle
            if FTBFnc != None:
                fctReponsenc = FTBFnc.getReponseTriangle
            fctConsigne = calcul.triangle
            param = {}
            param['pente'] = self.tb.GetCurrentPage().pente.v[0]
            param['periode'] = self.tb.GetCurrentPage().periode.v[0]
            param['decalage'] = self.tb.GetCurrentPage().decalage.v[0]
            
        elif self.signal == 6: # Sinus   
            if FTBF != None:   
                fctReponse = FTBF.getReponseSinus
            if FTBFnc != None:
                fctReponsenc = FTBFnc.getReponseSinus
            fctConsigne = calcul.sinus
            param = {}
            param['amplitude'] = self.tb.GetCurrentPage().amplitude.v[0]
            param['pulsation'] = self.tb.GetCurrentPage().pulsation.v[0]
            param['decalage'] = self.tb.GetCurrentPage().decalage.v[0]
            
        elif self.signal == 7:
            if FTBF != None:
                fctReponse = FTBF.getReponsePerso
            if FTBFnc != None:
                fctReponsenc = FTBFnc.getReponsePerso
            fctConsigne = None
            param = {}
            param['T'] = self.tb.GetCurrentPage().T
            param['U'] = self.tb.GetCurrentPage().U
            self.ZoneReponse.child[0].plotInteractor.set_data_redess(self.tb.GetCurrentPage().T, self.tb.GetCurrentPage().U)
        else:
            return
        
        # On s'occupe de faire disparaitre ou apparaitre le bouton "temps de réponse"
        self.ZoneReponse.gererBoutonTR(self.signal == 1)
        self.ZoneReponse.child[0].tracerTR = False
        self.ZoneReponse.mettreAJourEtRedessiner(fctConsigne, fctReponse, fctReponsenc, **param)

    
    
    def ReTracer(self):
#        if hasattr(self.ZoneReponse.child[0], 'consigne'):
#            self.ZoneReponse.child[0].TracerTout()
#        else:
        self.MiseAJour(0)

    def SynchroniserPulsationSinus(self, pulsation):
        if self.signal == 6 and self.synchroniserPuls:
#            print "Synchroniser Pulsation"
            FTBFnc = self.getFTBFnc()
            FTBF = self.getFTBF()[self.getNum()]
            param = {}
            fctReponse = FTBF.getReponseSinus
            if FTBFnc != None:
                fctReponsenc = FTBFnc.getReponseSinus
            else:
                fctReponsenc = None
            fctConsigne = calcul.sinus
            param['pulsation'] = pulsation
            self.tb.GetCurrentPage().pulsation.v[0] = pulsation
            self.tb.zoneParamSinus.varPuls.mofifierValeursSsEvt()
            param['amplitude'] = self.tb.GetCurrentPage().amplitude.v[0]
            param['decalage'] = self.tb.GetCurrentPage().decalage.v[0]
            self.ZoneReponse.mettreAJourEtRedessiner(fctConsigne, fctReponse, fctReponsenc, **param)

#    ######################################################################################################
#    def OnToolRClick(self, event):
#        print "tool %s right-clicked\n" % event.GetId()
        
    
    ######################################################################################################
    def OnSize(self, event):
#        print self.GetSize()
        self.sizer.SetDimension(0,0,self.GetClientSize()[0],self.GetClientSize()[1])
#        self.pop.RendreVisible()
#        self.zoneReponse.Lower()
#        wx.CallAfter(self.Refresh)
#        event.Skip()

    ######################################################################################################
    def OnCloseWindow(self, event):
        self.parent.tb.DesactiverReponse()

        
    ######################################################################################################
    def MiseAJourBmp(self):
        FTBF = self.getFTBF()
        
#        print FTBF
        
        if FTBF == []:
            return
        
        FTBFnc = self.getFTBFnc()
        lstBmp = []
        for FT in FTBF:
            lstBmp.append(FT.getBitmap(color = self.parent.formats["Rep"].coul))
        self.BmpFTBF.SetBitmap(lstBmp, self.GetBmpHD, self.GetTeX, self.getNum())
        
        if FTBFnc != None:
            self.BmpFTBFnc.SetBitmap(FTBFnc.getBitmap(color = self.parent.formats["RepNc"].coul), 
                                     self.GetBmpHDnc, self.GetTeXnc)
            self.cb2.Show()
        else:
            self.BmpFTBFnc.SetBitmap(wx.NullBitmap)
            self.cb2.Show(False)
#        self.MiseAJour()
        self.pop.Fit()
        self.pop.FitInside()
        self.pop.Refresh()
#        self.sizer.Fit()
#        self.sizer.Fit(self)
        self.sizer.SetItemMinSize(self.pop, self.pop.GetSize()[0], self.pop.GetSize()[1])
        self.sizer.Layout()
        
    def GetBmpHD(self):
        FTBF = self.getFTBF()[self.getNum()]
        return FTBF.getBitmap(color = self.parent.formats["Rep"].coul, 
                                   taille = globdef.FONT_SIZE_FT_HD)
    
    def GetTeX(self):
        FTBF = self.getFTBF()[self.getNum()]
        return FTBF.getMathTextNom()
        
    def GetBmpHDnc(self):
        FTBFnc = self.getFTBFnc()
        return FTBFnc.getBitmap(color = self.parent.formats["RepNc"].coul, 
                                     taille = globdef.FONT_SIZE_FT_HD)
    
    def GetTeXnc(self):
        FTBFnc = self.getFTBFnc()
        return FTBFnc.getMathTextNom()
    
#    def detFTBF(self, FTBO):
#        self.FTBF = calcul.FonctionTransfertNum(FTBO.polyN, FTBO.polyN + FTBO.polyD, 
#                                                nom = _("FTBF"))
#        self.BmpFTBF.SetBitmap(self.FTBF.getBitmap())
#        self.MiseAJour()
#        self.pop.Fit()
#        self.pop.FitInside()
#        self.pop.Refresh()
##        self.sizer.Fit()
##        self.sizer.Fit(self)
#        self.sizer.SetItemMinSize(self.pop, self.pop.GetSize()[0], self.pop.GetSize()[1])
#        self.sizer.Layout()
        
        
#    def detReponse(self):
#        self.reponse = self.FTBF.getReponseIndicielle()
        
        
    def modifierAntialiased(self):
        self.ZoneReponse.child[0].modifierAntialiased()
        
    def OnSystemeChange(self):
#        print "OnSystemeChange"
        self.tb.OnSystemeChange()
        
        self.MiseAJour()
        self.MiseAJourBmp()
        
        
        
##########################################################################################################
class TBReponse(wx.Toolbook):
    def __init__(self, parent):
        wx.Toolbook.__init__(self, parent, -1, 
                             style = wx.BK_DEFAULT
                            )
        self.parent = parent
        
        listeSignaux = [_("Impulsion"), _("Echelon"), _("Rampe"),
                        _("Série d'Impulsions"), 
                        _("Carré"), _("Triangle"), _("Sinusoïdal"),
                        _("Personnalisé")
                        ]
        
        listeBoutons = [Images.Bouton_Signal_Impuls,
                        Images.Bouton_Signal_Echel,
                        Images.Bouton_Signal_Rampe,
                        Images.Bouton_Signal_Impulsions,
                        Images.Bouton_Signal_Carre,
                        Images.Bouton_Signal_Triangle,
                        Images.Bouton_Signal_Sinus,
                        Images.Bouton_Signal_Perso
                        ]
        
        listeZoneParam = [ParamImpuls(self),
                          ParamEchelon(self),
                          ParamRampe(self),
                          ParamImpulsions(self),
                          ParamCarre(self),
                          ParamTriangle(self),
                          ParamSinus(self),
                          ParamPerso(self)
                          ]
        
        il = wx.ImageList(32, 32)
        for f in listeBoutons:
            il.Add(f.GetBitmap())
        self.AssignImageList(il)
#        imageIdGenerator = getNextImageID(il.GetImageCount())
        
        # Now make a bunch of panels for the list book
        first = True
        for i,win in enumerate(listeZoneParam):
            self.AddPage(win, "", imageId=i)
            self.GetToolBar().SetToolShortHelp(i+1, listeSignaux[i])
#            self.GetToolBar().SetToolLongHelp(i, "Afficher la réponse temporelle du système soumis à un signal de type"+listeSignaux[i])
 
        self.Bind(wx.EVT_TOOLBOOK_PAGE_CHANGED, self.OnPageChanged)
#        self.Bind(wx.EVT_TOOLBOOK_PAGE_CHANGING, self.OnPageChanging)

        self.zoneParamSinus = listeZoneParam[6]


    def OnPageChanged(self, event):
#        print "pagechanged"
        new = event.GetSelection()
        self.Parent.MiseAJour(signal = new) 
        event.Skip()


    def MiseAJour(self):
        self.parent.MiseAJour()
        
    
    def OnSystemeChange(self):
        for p in range(self.GetPageCount()):
            self.GetPage(p).OnSystemeChange()
        
##########################################################################################################
class ParamImpuls(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(self, -1, _("Signal impulsion"))
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        box.SetHelpText(_("Paramètres de l'impulsion"))
        
        sizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(sizer)
        self.Bind(EVT_VAR_CTRL, self.OnVariableModified)
        
        
    def OnVariableModified(self, event):
        self.Parent.MiseAJour()
        
    def OnSystemeChange(self):
        return
    

##########################################################################################################
class ParamEchelon(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(self, -1, _("Signal échelon"))
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        box.SetHelpText(_("Paramètres de l'échelon"))
        
        self.amplitude = Variable(_("Amplitude"), lstVal = [1.0], typ = VAR_REEL)
        var1 = VariableCtrl(self, self.amplitude, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
        
        sizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(sizer)
        self.Bind(EVT_VAR_CTRL, self.OnVariableModified)
        
        
    def OnVariableModified(self, event):
        self.Parent.MiseAJour()
    
    def OnSystemeChange(self):
        return
    
        
##########################################################################################################
class ParamRampe(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(self, -1, _("Signal échelon"))
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        box.SetHelpText(_("Paramètres de l'échelon"))
        
        self.pente = Variable(_("Pente"), lstVal = [1.0], typ = VAR_REEL)
        var1 = VariableCtrl(self, self.pente, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
        
        sizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(sizer)
        self.Bind(EVT_VAR_CTRL, self.OnVariableModified)
        
        
    def OnVariableModified(self, event):
        self.Parent.MiseAJour()
    
    def OnSystemeChange(self):
        return
    
        
##########################################################################################################
class ParamImpulsions(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(self, -1, _("Signal série d'impulsions"))
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        box.SetHelpText(_("Paramètres du signal série d'impulsions"))
        
#        label = wx.StaticText(self, -1, "Indisponible pour l'instant ...")
#        bsizer.Add(label, 0, wx.ALIGN_RIGHT|wx.ALL, 3)

        self.periode = Variable(_("Période (s)"), lstVal = [1.0], typ = VAR_REEL_POS)
        var1 = VariableCtrl(self, self.periode, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
        
        sizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(sizer)
        self.Bind(EVT_VAR_CTRL, self.OnVariableModified)
        
        
    def OnVariableModified(self, event):
        self.Parent.MiseAJour()
        
    def OnSystemeChange(self):
        return
        
    
##########################################################################################################
class ParamCarre(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(self, -1, _("Signal carré"))
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        box.SetHelpText(_("Paramètres du signal carré"))
#        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        self.amplitude = Variable(_("Amplitude"), lstVal = [1.0], typ = VAR_REEL)
        var1 = VariableCtrl(self, self.amplitude, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
        
        self.periode = Variable(_("Période (s)"), lstVal = [1.0], typ = VAR_REEL_POS)
        var1 = VariableCtrl(self, self.periode, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
        
        self.decalage = Variable(_("Décalage"), lstVal = [0.0], typ = VAR_REEL, modeLog = False)
        var1 = VariableCtrl(self, self.decalage, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
        
        sizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(sizer)
        self.Bind(EVT_VAR_CTRL, self.OnVariableModified)
        
        
    def OnVariableModified(self, event):
        self.Parent.MiseAJour() 
        
    def OnSystemeChange(self):
        return
        
##########################################################################################################
class ParamTriangle(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(self, -1, _("Signal triangulaire"))
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        box.SetHelpText(_("Paramètres du signal triangulaire"))
#        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        self.pente = Variable(_("Pente"), lstVal = [1.0], typ = VAR_REEL)
        var1 = VariableCtrl(self, self.pente, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
        
        self.periode = Variable(_("Période (s)"), lstVal = [1.0], typ = VAR_REEL_POS)
        var1 = VariableCtrl(self, self.periode, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
        
        self.decalage = Variable(_("Décalage"), lstVal = [0.0], typ = VAR_REEL, modeLog = False)
        var1 = VariableCtrl(self, self.decalage, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
        
        sizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(sizer)
        self.Bind(EVT_VAR_CTRL, self.OnVariableModified)
        
        
    def OnVariableModified(self, event):
        self.Parent.MiseAJour()     
         
    def OnSystemeChange(self):
        return
        
##########################################################################################################
class ParamSinus(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(self, -1, _("Signal sinusoïdal"))
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        box.SetHelpText(_("Paramètres du signal sinusoïdal"))
#        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        self.amplitude = Variable(_("Amplitude"), lstVal = [1.0], typ = VAR_REEL)
        var1 = VariableCtrl(self, self.amplitude, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
        
        
        self.pulsation = Variable(_("Pulsation (rad/s)"), lstVal = [1.0], typ = VAR_REEL_POS)
        
        radio1 = wx.RadioButton( self, -1, "", style = wx.RB_GROUP )
        var1 = VariableCtrl(self, self.pulsation, labelMPL = False)
        hs = wx.BoxSizer(wx.HORIZONTAL)
        hs.Add(radio1, flag = wx.EXPAND)
        hs.Add(var1, flag = wx.ALIGN_LEFT|wx.EXPAND)
        
        radio2 = wx.RadioButton( self, -1, _("Synchroniser sur le curseur de la réponse harmonique" ))

        ss = wx.BoxSizer(wx.VERTICAL)
        ss.Add(hs, flag = wx.EXPAND)
        ss.Add(radio2, flag = wx.EXPAND)
        
        bsizer.Add(ss, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
        self.varPuls = var1
        self.radioPuls = radio2
        self.OnSystemeChange()
        
        self.decalage = Variable(_("Décalage"), lstVal = [0.0], typ = VAR_REEL, modeLog = False)
        var1 = VariableCtrl(self, self.decalage, labelMPL = False)
        bsizer.Add(var1, 0, wx.ALIGN_RIGHT|wx.ALL, 3)
        
        sizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(sizer)
        self.Bind(EVT_VAR_CTRL, self.OnVariableModified)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio)
        
        
    def OnVariableModified(self, event):
        self.Parent.MiseAJour() 
        
    def OnRadio(self, event):
        radio_selected = event.GetEventObject()
        if self.radioPuls is not radio_selected:
            self.varPuls.Enable(True)
            self.parent.parent.synchroniserPuls = False
        else:
            self.varPuls.Enable(False)
            self.parent.parent.synchroniserPuls = True
                 
    def OnSystemeChange(self):
        if self.parent.parent.parent.getTypeSysteme() == 0:
            s = "H"
        else:
            s = _("du système en boucle fermée")
        self.radioPuls.SetToolTipString(_("En choisissant cette option, la valeur de la pulsation sera la même\n" \
                                         "que celle du curseur de la fonction de transfert ")+s+".")
    
    
##########################################################################################################
class ParamPerso(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.StaticBox(self, -1, _("Signal personnalisé"))
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        box.SetHelpText(_("Paramètres du signal personnalisé"))
        
        font1 = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        label0 = wx.StaticText(self, -1, _("Personnalisation de la consigne :" ))
        label1 = wx.StaticText(self, -1, _("  Déplacer un point de contrôle :"))
        label2 = wx.StaticText(self, -1, _("bouton gauche + déplacer" ))
        label3 = wx.StaticText(self, -1, _("  Ajouter un point de contrôle :"))
        label4 = wx.StaticText(self, -1, _("bouton droit sur un segment" ))
        label5 = wx.StaticText(self, -1, _("  Supprimer un point de contrôle :"))
        label6 = wx.StaticText(self, -1, _("bouton droit sur un point" ))
        label7 = wx.StaticText(self, -1, _("  Modifier la pente du dernier segment :"))
        label8 = wx.StaticText(self, -1, _("bouton gauche sur le segment + déplacer" ))
                                        
        label0.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, underline = True))
        label1.SetFont(font1)
        label3.SetFont(font1)
        label5.SetFont(font1)
        label7.SetFont(font1)
        
        bsizer.Add(label0, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        bsizer.Add(label1, 0, wx.ALIGN_LEFT)
        bsizer.Add(label2, 0, wx.ALIGN_RIGHT|wx.BOTTOM, 2)
        bsizer.Add(label3, 0, wx.ALIGN_LEFT)
        bsizer.Add(label4, 0, wx.ALIGN_RIGHT|wx.BOTTOM, 2)
        bsizer.Add(label5, 0, wx.ALIGN_LEFT)
        bsizer.Add(label6, 0, wx.ALIGN_RIGHT|wx.BOTTOM, 2)
        bsizer.Add(label7, 0, wx.ALIGN_LEFT)
        bsizer.Add(label8, 0, wx.ALIGN_RIGHT|wx.BOTTOM, 2)
        
        sizer.Add(bsizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(sizer)
        self.Bind(EVT_VAR_CTRL, self.OnVariableModified)
        
        self.T, self.U = [0.0, 1.0, 2.0], [0.0, 1.0, 0.0]
        
    def OnVariableModified(self, event):
        self.Parent.MiseAJour()
        
    def OnSystemeChange(self):
        return
        
##########################################################################################################    
##########################################################################################################
#
#  Tracé des Poles de la FTBF dans le plan complexe
#
##########################################################################################################
##########################################################################################################
class WinPoles(wx.MiniFrame, PrintHandler):
    def __init__(self, parent, getNum, getFTBF, pos=wx.DefaultPosition,
                 style = globdef.STYLE_FENETRE):

        # Les fonctions pour obtenir les FT
        self.getFTBF = getFTBF
        self.getNum = getNum
        
        size = (300,300)
        wx.MiniFrame.__init__(self, parent, -1, "", pos, size, style)
        self.miseAJourTitre()
        
        self.Freeze()
        
        self.initPrintHandler(PrintoutWx, self.Parent, globdef.PRINT_PAPIER_DEFAUT, globdef.PRINT_MODE_DEFAUT)
        
        self.SetMinSize(size)
        self.SetSize(self.GetMinSize())
        self.SetAutoLayout(True)

        self.BmpFTBF = ScrolledBitmap(self, -1, wx.NullBitmap)

        self.zonePoles = graph.ZoneGraphOutils(self, parent, 4, ["BGrille", "", "BExpor", "BImpri", 'BParam'])
        self.zonePoles.Add(graph.ZoneGraphPoles(self.zonePoles, self.zonePoles, "Pôles"))
        
        panelbtn = wx.Panel(self, -1)
        button = wx.Button(panelbtn, -1, _("Fermer"))
        
        #
        # Mise en place
        #
        sizer0 = wx.BoxSizer(wx.VERTICAL)
        sizer0.Add(self.BmpFTBF, 0, flag = wx.EXPAND)
        sizer0.Add(self.zonePoles, 1, flag = wx.EXPAND)
        sizer0.Add(panelbtn, flag = wx.EXPAND)
        self.SetSizer(sizer0)
        self.sizer = sizer0
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_BUTTON, self.OnCloseMe, button)
        self.Bind(EVT_BITMAP_CHANGED, self.OnBitmapChanged)
#        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        
        self.Thaw()
        
    ######################################################################################################
    def getLstScrolledBitmap(self):
        """ Renvoie toutes les ScrolledBitmap contenues dans la fenêtre
            (pour synchronisation)
        """
        return [self.BmpFTBF]
    
    
    ######################################################################################################
    def OnBitmapChanged(self, event):
        num = event.GetNum()
        self.app.setNumEtTracer(num)
        
        
    #########################################################################################################
    def OnCloseMe(self, event):
        self.Close(True)
    
    
    #########################################################################################################
    def setCouleurs(self):
        self.zonePoles.child[0].setCouleurs()
    
    
    #########################################################################################################
    def MiseAJourBmp(self):#, FTBF):
#        self.FTBF = FTBF
        lstBmp = []
        for F in self.getFTBF():
            lstBmp.append(F.getBitmap(color = self.app.formats["FTBF"].coul))
        self.BmpFTBF.SetBitmap(lstBmp, self.GetBmpHD, self.GetTeX)
        
        
#    #########################################################################################################
#    def calculerEtTracer(self):
#        self.tracer()
    
    
    #########################################################################################################
    def GetBmpHD(self):
        return self.getFTBF()[self.getNum()].getBitmap(color = self.app.formats["FTBF"].coul, 
                                             taille = globdef.FONT_SIZE_FT_HD)
        
    def GetTeX(self):
        return self.getFTBF()[self.getNum()].getMathTextNom()
        
    #########################################################################################################
    def miseAJourTitre(self, estFTBF = False):
        if estFTBF:
            self.SetTitle(_("Pôles/Zéros de la FTBF"))
        else:
            self.SetTitle(_("Pôles/Zéros de la Fonction de Transfert"))
        
        
    #########################################################################################################
    def tracer(self, num = 0):
        self.Freeze()
        self.zonePoles.mettreAJourEtRedessiner(self.getFTBF()[num].getPoles(), self.getFTBF()[num].getZeros())
        self.Thaw()

        
    #########################################################################################################
    def OnSize(self, event):
#        event.Skip()
#        return
#        print self.GetSize()
        self.sizer.SetDimension(0,0,self.GetClientSize()[0],self.GetClientSize()[1])
#        self.pop.RendreVisible()
#        self.zoneReponse.Lower()
#        wx.CallAfter(self.Refresh)
#        event.Skip()

    def OnCloseWindow(self, event):
        self.Parent.tb.DesactiverPoles()
        
        
    def modifierAntialiased(self):
        self.zoneFTBF.modifierAntialiased()
        
        
##########################################################################################################    
##########################################################################################################
#
#  Décomposition en éléments simples de la FTBF
#
##########################################################################################################
##########################################################################################################
class WinDecompose(wx.MiniFrame):
    def __init__(self, parent, getNum, getFTBF, getFTBO, pos = wx.DefaultPosition, size = wx.DefaultSize,
                 style = wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP  
                 ):
#        self.parent = parent

        # Variable pour savoir s'il s'agit d'un système bouclé ou pas
        self.typeTF = "FTBF"
        
        # Les fonctions pour obtenir les FT
        self.getFTBF = getFTBF
        self.getFTBO = getFTBO
        
        self.getNum = getNum
        
        size = (300,200)
        wx.MiniFrame.__init__(self, parent, -1, _("Décomposition en éléments simples"), pos, size, style)
        self.SetBackgroundColour(wx.WHITE)
        tb = self.CreateToolBar( wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT )
        
        bmp = mathtext_to_wxbitmap(_(r"FTBF"))
        tb.SetToolBitmapSize(bmp.GetSize())
        tb.AddLabelTool(10, _("FTBF"), bmp, 
                        shortHelp= _("Affiche la décomposition en éléments simples de la FTBF"), 
                        longHelp = _("Affiche la décomposition en éléments simples de la FTBF"))
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=10)
        
        bmp = mathtext_to_wxbitmap(_(r"FTBO"))
        tb.AddLabelTool(11, _("FTBO"), bmp, 
                        shortHelp = _("Affiche la décomposition en éléments simples de la FTBO"), 
                        longHelp = _("Affiche la décomposition en éléments simples de la FTBO"))
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=11)
        
#        self.SetMinSize(size)
#        self.SetSize(self.GetMinSize())
#        self.SetAutoLayout(True)
        
        sizer0 = wx.BoxSizer(wx.VERTICAL)
        self.zoneFTBF = wx.StaticBitmap(self, -1, wx.NullBitmap)
        self.zoneDecomp = wx.StaticBitmap(self, -1, wx.NullBitmap)
        
        panelbtn = wx.Panel(self, -1)
        button = wx.Button(panelbtn, -1, _("Fermer"))
        
        sizer0.Add(self.zoneFTBF, flag = wx.EXPAND|wx.ALL, border = 5)
        sizer0.Add(self.zoneDecomp, flag = wx.EXPAND|wx.ALL, border = 5)
        sizer0.Add(panelbtn, flag = wx.EXPAND|wx.ALL, border = 5)
        self.SetSizer(sizer0)
        self.sizer = sizer0
        
        tb.Realize()
        self.tb = tb
        
        self.Bind(wx.EVT_BUTTON, self.OnCloseMe, button)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_SIZE, self.OnSize)
#        self.Bind(EVT_BITMAP_CHANGED, self.OnBitmapChanged)

    ######################################################################################################
    def getLstScrolledBitmap(self):
        """ Renvoie toutes les ScrolledBitmap contenues dans la fenêtre
            (pour synchronisation)
        """
        return []
    
    
        
#    ######################################################################################################
#    def OnBitmapChanged(self, event):
#        num = event.GetNum()
#        self.app.setNumEtTracer(num)
        
        
    def OnCloseMe(self, event):
        self.Close(True)
        
    def OnSize(self, event):
        self.Refresh()
        event.Skip()
        
    def OnToolClick(self, event):
        id = event.GetId()
        if id == 10:
            self.typeTF = "FTBF"
        elif id == 11:
            self.typeTF = "FTBO"
        self.MiseAJour()
        
    def OnCloseWindow(self, event):
        self.Parent.tb.DesactiverDecomp()
#        evt = wx.CommandEvent(wx.EVT_TOOL.typeId, 17)
#        .tb.ToggleTool(17, False)
#        .tb.GetEventHandler().ProcessEvent(evt)
        
    def MiseAJour(self):#, FTBO = None, FTBF = None):
#        if FTBO != None:
#            self.FTBO = FTBO
#        else:
#            FTBO = self.FTBO
#            
#        if FTBF != None:
#            self.FTBF = FTBF
#        else:
#            FTBF = self.FTBF
            
        FTBO = self.getFTBO()[self.getNum()]
        FTBF = self.getFTBF()[self.getNum()]
        
        if FTBO == FTBF:
            self.tb.Show(False)     
        else:
            self.tb.Show(True)
            
        if self.typeTF == "FTBF" or not self.tb.IsShown():
            FT = FTBF
        else:
            FT = FTBO
        
#        FT.nom = self.typeTF
        self.zoneFTBF.SetBitmap(FT.getBitmap(taille = globdef.FONT_SIZE_FT_DECOMP))
        
        #
        #  Décomposition en éléments simples
        #
        som = []
        try:
            r, p, k = residue(FT.polyN, FT.polyD)
        except:
            r, p, k = FT.polyN, FT.polyD, []
        
        n = 0
        i = 0
        _p = None
        continuer = True
        while continuer:
            if i >= len(r):
                continuer = False
            else:
                if _p == p[i]:
                    n += 1
                else:
                    n = 0
                    
                _p = p[i]
                
                if r[i] != 0:
                    if r[i].imag != 0:
                        sn = getMathTextList([r[i]+r[i+1], -r[i]*p[i+1]-p[i]*r[i+1]], globdef.VAR_COMPLEXE)
                        sd = getMathTextList([1, -p[i]-p[i+1], p[i]*p[i+1]], globdef.VAR_COMPLEXE)
                        i += 2
                    else:
                        sn = getMathTextList([r[i]], globdef.VAR_COMPLEXE)
                        sd = getMathTextList([1.0, -p[i]], globdef.VAR_COMPLEXE)
                        i += 1
                    
                    som.append((sn, sd, n+1))
                else:
                    i += 1
            
        s = FT.nom+r"("+globdef.VAR_COMPLEXE+") = "
        for e in som:
            sn = e[0]
            sd = e[1]
            n = e[2]
            
            if n > 1:
                sd = r'\left(' + sd + r'\right)^' + str(n)
            s += r'\frac{'+sn+'}{'+sd+'}'   
            s += r'+'
            
        s = s.rstrip(r'+')
        
        s = mathText(s)
#        print " --> ",s
        self.zoneDecomp.SetBitmap(mathtext_to_wxbitmap(s, taille = globdef.FONT_SIZE_FT_DECOMP))
        
        self.Layout()
        self.Fit()
        self.Refresh()
#        self.SetMinSize(self.GetSize())
#        self.SetMaxSize(self.GetSize())
#        print self.zoneDecomp.texte.get_bbox()

    #########################################################################################################
    def modifierAntialiased(self):
        return
    
    
    

        
        

        
        


        
            
#############################################################################################################
#
# A propos ...
# 
#############################################################################################################
class A_propos(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, _("A propos de ")+version.__appname__)
        
        self.app = parent
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        titre = wx.StaticText(self, -1, version.__appname__)
        titre.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, False))
        titre.SetForegroundColour(wx.NamedColour("BROWN"))
        sizer.Add(titre, border = 10)
        sizer.Add(wx.StaticText(self, -1, _("Version : ")+str(wx.GetApp().version)), 
                  flag=wx.ALIGN_RIGHT)
        sizer.Add(wx.StaticBitmap(self, -1, Images.Logo.GetBitmap()),
                  flag=wx.ALIGN_CENTER)
        
#        sizer.Add(20)
        nb = wx.Notebook(self, -1, style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
                             )
        
        
        # Auteurs
        #---------
        auteurs = wx.Panel(nb, -1)
        fgs1 = wx.FlexGridSizer(cols=2, vgap=4, hgap=4)
        
        lstActeurs = ((_("Développement : "),("Cédrick FAURY",)),#,
                      (_("Remerciements : "),(_("Marc BATTILANA\n    pour la définitions des IsoGains et IsoPhases,\n    ainsi que pour son soutien ..."),
                                               _("Bruno CAUSSE\n    pour ses rapports de bug\n    et ses suggestions pertinentes ..."),
                                               _("Vincent CRESPEL\n    pour son aide\n    lors de l'ajout du déphasage"),
                                               _("Philippe TRENTY\n    remarquable chasseur de bugs"),
                                               _("Et tous ceux qui m'ont encouragé !"))))#, 


        
        for ac in lstActeurs:
            t = wx.StaticText(auteurs, -1, ac[0])
            fgs1.Add(t, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=4)
            for l in ac[1]:
                t = wx.StaticText(auteurs, -1, l)
                fgs1.Add(t , flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL| wx.ALL, border=4)
                t = wx.StaticText(auteurs, -1, "")
                fgs1.Add(t, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=0)
            t = wx.StaticText(auteurs, -1, "")
            fgs1.Add(t, flag=wx.ALL, border=0)
            
        auteurs.SetSizer(fgs1)
        
        # licence
        #---------
        licence = wx.Panel(nb, -1)
        s = wx.BoxSizer(wx.VERTICAL)
        try:
            f = os.path.join(globdef.PATH, "LICENSE.txt")
            txt = open(f)
            lictext = txt.read()
            txt.close()
        except:
            lictext = _("Le fichier licence est introuvable !\n\n" \
                        "%s\n"
                        "Veuillez réinstaller pySyLiC !" %f)
            dlg = wx.MessageDialog(self, lictext,
                               _('Licence introuvable'),
                               wx.OK | wx.ICON_ERROR
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
            dlg.ShowModal()
            dlg.Destroy()
            
            
        
        
        s.Add(wx.TextCtrl(licence, -1, lictext, size = (400, -1), 
                    style = wx.TE_READONLY|wx.TE_MULTILINE|wx.BORDER_NONE ),
              1, flag = wx.EXPAND)
        licence.SetSizer(s)
        
        # Description
        #-------------
        descrip = wx.Panel(nb, -1)
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(wx.TextCtrl(descrip, -1, wordwrap(_("pySyLiC (py pour python - Systèmes Linéaires Continus) \n"
                                            "permet d'analyser graphiquement les réponses harmoniques et temporelles de Systèmes Linéaires Continus et Invariants.\n\n"
                                            "Il propose :\n"
                                            " - un tracé des lieux de Bode, de Black et de Nyquist des Fonctions de Transfert caractéristiques du système (décomposition en 'sous fonctions' de transfert, tracé des asymptotes, ...)\n"
                                            " - d'utiliser des variables dans les définitions des FT : les tracés sont automatiquement modifiés\n"
                                            " - de placer un correcteur dans la chaine directe et d'observer ses effets sur la FTBO\n"
                                            " - de tracer les réponses temporelles et harmoniques du système en boucle fermée\n"
                                            "\n"
                                            "pySyLic relève de l'Automatique et s'adresse principalement aux élèves et aux professeurs travaillant sur cette discipline.\n"
                                            "Il a été conçu de telle sorte que son utilisation soit la plus intuitive possible."),
                                            500, wx.ClientDC(self)),
                        size = (400, -1),
                        style = wx.TE_READONLY|wx.TE_MULTILINE|wx.BORDER_NONE),
              1,  flag = wx.EXPAND)
        descrip.SetSizer(s)
        
        
        
        
        
        nb.AddPage(descrip, _("Description"))
        nb.AddPage(auteurs, _("Auteurs"))
        nb.AddPage(licence, _("Licence"))
        
        sizer.Add(wx.adv.HyperlinkCtrl(self, #wx.ID_ANY, 
                                        label = _("Informations et téléchargement : https://github.com/cedrick-f/pySyLiC"),
                                        url = "https://github.com/cedrick-f/pySyLiC"),  
                  flag = wx.ALIGN_RIGHT|wx.ALL, border = 5)
        sizer.Add(nb)
        
        self.SetSizerAndFit(sizer)

#        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

#    def OnCloseWindow(self, event):
##        evt = wx.CommandEvent(wx.EVT_TOOL.typeId, 16)
#        self.app.tb.ToggleTool(13, False)
##        self.app.tb.GetEventHandler().ProcessEvent(evt)
#        event.Skip()
        
        
        
        
###########################################################################################################
def GetCollapsedIconData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\x8eIDAT8\x8d\xa5\x93-n\xe4@\x10\x85?g\x03\n6lh)\xc4\xd2\x12\xc3\x81\
\xd6\xa2I\x90\x154\xb9\x81\x8f1G\xc8\x11\x16\x86\xcd\xa0\x99F\xb3A\x91\xa1\
\xc9J&\x96L"5lX\xcc\x0bl\xf7v\xb2\x7fZ\xa5\x98\xebU\xbdz\xf5\\\x9deW\x9f\xf8\
H\\\xbfO|{y\x9dT\x15P\x04\x01\x01UPUD\x84\xdb/7YZ\x9f\xa5\n\xce\x97aRU\x8a\
\xdc`\xacA\x00\x04P\xf0!0\xf6\x81\xa0\xf0p\xff9\xfb\x85\xe0|\x19&T)K\x8b\x18\
\xf9\xa3\xe4\xbe\xf3\x8c^#\xc9\xd5\n\xa8*\xc5?\x9a\x01\x8a\xd2b\r\x1cN\xc3\
\x14\t\xce\x97a\xb2F0Ks\xd58\xaa\xc6\xc5\xa6\xf7\xdfya\xe7\xbdR\x13M2\xf9\
\xf9qKQ\x1fi\xf6-\x00~T\xfac\x1dq#\x82,\xe5q\x05\x91D\xba@\xefj\xba1\xf0\xdc\
zzW\xcff&\xb8,\x89\xa8@Q\xd6\xaaf\xdfRm,\xee\xb1BDxr#\xae\xf5|\xddo\xd6\xe2H\
\x18\x15\x84\xa0q@]\xe54\x8d\xa3\xedf\x05M\xe3\xd8Uy\xc4\x15\x8d\xf5\xd7\x8b\
~\x82\x0fh\x0e"\xb0\xad,\xee\xb8c\xbb\x18\xe7\x8e;6\xa5\x89\x04\xde\xff\x1c\
\x16\xef\xe0p\xfa>\x19\x11\xca\x8d\x8d\xe0\x93\x1b\x01\xd8m\xf3(;x\xa5\xef=\
\xb7w\xf3\x1d$\x7f\xc1\xe0\xbd\xa7\xeb\xa0(,"Kc\x12\xc1+\xfd\xe8\tI\xee\xed)\
\xbf\xbcN\xc1{D\x04k\x05#\x12\xfd\xf2a\xde[\x81\x87\xbb\xdf\x9cr\x1a\x87\xd3\
0)\xba>\x83\xd5\xb97o\xe0\xaf\x04\xff\x13?\x00\xd2\xfb\xa9`z\xac\x80w\x00\
\x00\x00\x00IEND\xaeB`\x82' 

def GetCollapsedIconBitmap():
    return wx.BitmapFromImage(GetCollapsedIconImage())

def GetCollapsedIconImage():
    import cStringIO
    stream = cStringIO.StringIO(GetCollapsedIconData())
    return wx.ImageFromStream(stream)

#----------------------------------------------------------------------
def GetExpandedIconData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x01\x9fIDAT8\x8d\x95\x93\xa1\x8e\xdc0\x14EO\xb2\xc4\xd0\xd2\x12\xb7(mI\
\xa4%V\xd1lQT4[4-\x9a\xfe\xc1\xc2|\xc6\xc2~BY\x83:A3E\xd3\xa0*\xa4\xd2\x90H!\
\x95\x0c\r\r\x1fK\x81g\xb2\x99\x84\xb4\x0fY\xd6\xbb\xc7\xf7>=\'Iz\xc3\xbcv\
\xfbn\xb8\x9c\x15 \xe7\xf3\xc7\x0fw\xc9\xbc7\x99\x03\x0e\xfbn0\x99F+\x85R\
\x80RH\x10\x82\x08\xde\x05\x1ef\x90+\xc0\xe1\xd8\ryn\xd0Z-\\A\xb4\xd2\xf7\
\x9e\xfbwoF\xc8\x088\x1c\xbbae\xb3\xe8y&\x9a\xdf\xf5\xbd\xe7\xfem\x84\xa4\
\x97\xccYf\x16\x8d\xdb\xb2a]\xfeX\x18\xc9s\xc3\xe1\x18\xe7\x94\x12cb\xcc\xb5\
\xfa\xb1l8\xf5\x01\xe7\x84\xc7\xb2Y@\xb2\xcc0\x02\xb4\x9a\x88%\xbe\xdc\xb4\
\x9e\xb6Zs\xaa74\xadg[6\x88<\xb7]\xc6\x14\x1dL\x86\xe6\x83\xa0\x81\xba\xda\
\x10\x02x/\xd4\xd5\x06\r\x840!\x9c\x1fM\x92\xf4\x86\x9f\xbf\xfe\x0c\xd6\x9ae\
\xd6u\x8d \xf4\xf5\x165\x9b\x8f\x04\xe1\xc5\xcb\xdb$\x05\x90\xa97@\x04lQas\
\xcd*7\x14\xdb\x9aY\xcb\xb8\\\xe9E\x10|\xbc\xf2^\xb0E\x85\xc95_\x9f\n\xaa/\
\x05\x10\x81\xce\xc9\xa8\xf6><G\xd8\xed\xbbA)X\xd9\x0c\x01\x9a\xc6Q\x14\xd9h\
[\x04\xda\xd6c\xadFkE\xf0\xc2\xab\xd7\xb7\xc9\x08\x00\xf8\xf6\xbd\x1b\x8cQ\
\xd8|\xb9\x0f\xd3\x9a\x8a\xc7\x08\x00\x9f?\xdd%\xde\x07\xda\x93\xc3{\x19C\
\x8a\x9c\x03\x0b8\x17\xe8\x9d\xbf\x02.>\x13\xc0n\xff{PJ\xc5\xfdP\x11""<\xbc\
\xff\x87\xdf\xf8\xbf\xf5\x17FF\xaf\x8f\x8b\xd3\xe6K\x00\x00\x00\x00IEND\xaeB\
`\x82' 

def GetExpandedIconBitmap():
    return wx.BitmapFromImage(GetExpandedIconImage())

def GetExpandedIconImage():
    import cStringIO
    stream = cStringIO.StringIO(GetExpandedIconData())
    return wx.ImageFromStream(stream)

class PositionExpression():
    """ Classe contenant la position d'un expression de FT sur la figure
        x, y : coordonnées de l'expression entre 0 et 1
    """

    def __init__(self, x = 0.5, y = 0.5):
        self.x = x
        self.y = y
        
    def __repr__(self):
        return "x = "+str(self.x)+" y = "+str(self.y)
    
    ###############################################################################################
    def getBranche(self, nom):
        root = ET.Element(nom)
        root.set("x", str(self.x))
        root.set("y", str(self.y))
        
        return root
        
    ###############################################################################################
    def ouvrir(self, nom, branchePos):
        branche = branchePos.find(nom)
        if branche != None:
            self.x = eval(branche.get("x"))
            self.y = eval(branche.get("y"))
            return True
        return False
        
        
    ###############################################################################################
    def setPos(self, x, y):
        self.x = x
        self.y = y
        
        
    ###############################################################################################
    def copie(self, pos):
        self.x = pos.x
        self.y = pos.y

#
# Fonction pour indenter les XML générés par ElementTree
#
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + "  "
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
