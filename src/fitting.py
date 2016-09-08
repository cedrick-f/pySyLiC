#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

##This file is part of pySylic
#############################################################################
#############################################################################
##                                                                         ##
##                                 Fitting                                 ##
##                                                                         ##
#############################################################################
#############################################################################

## Copyright (C) 2009-2010 Cédrick FAURY

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#8
#    You should have received a copy of the GNU General Public License
#    along with pySylic; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import scipy.interpolate
import scipy
from scipy.optimize import curve_fit
from numpy import *
import csv

import wx

# Fonctions de référence
def rep1(t, K, T):
    return K*(1.-scipy.exp(-t/T))

def rep2(t, K, z, w):
    T1 = -1/(-z*w-w*sqrt(z*z-1))
    T2 = -1/(-z*w+w*sqrt(z*z-1))
    return K*(1-(T1*exp(-t/T1)-T2*exp(-t/T2))/(T1-T2))

#def rep2(t, K, z, w):
#    _w = w*sqrt(z*z-1)
#    p1 = -z*w + _w
#    p2 = -z*w - _w
#    B = z*z/(p1*(p1-p2))
#    C = z*z/(p2*(p2-p1))
#    return K*(1 + B*exp(p1*t) + C*exp(p2*t))

def rep4(t, K, z, w):
    a = z*w
    b = w*sqrt(1-z*z)
    return K*(1 - exp(-a*t)*cos(b*t) - a/b*exp(-a*t)*sin(b*t))

fct = [rep1, rep2, rep4]

def message(mess):
    dlg = wx.MessageDialog(None, mess,
                           _(u'Erreur'),
                           wx.OK | wx.ICON_ERROR)
    dlg.ShowModal()
    dlg.Destroy()
    
# points de mesure
def getPointsMesure(fichierCSV):
    def conv(sr):
        s = []
        for l in sr:
            la = asfarray(l)
            s.append(la)
        s = array(s)
        s = transpose(s)
        return s
    
    for sep in [';', ',', ' ']:
        try:
            spamReader = csv.reader(open(fichierCSV, 'rb'), delimiter = sep)
        except:
            message(_(u"Impossible d'ouvrir le fichier :\n") + fichierCSV) 
    
        try:
            s = conv(spamReader)
        except:
            s = []
            
        valid = True
        try:
            t = s[0]
            y_meas = s[1]
        except:
            valid = False
        
        if valid:
            return t, y_meas
        
    message(_(u"Le fichier %s \nn'a pas un format valide.") %fichierCSV)
    return None, None


# Paramètres initiaux
p0 = [[1,1],
      [1, 2, 1],
      [1, 0.5, 1]]



def ajuster(x, y, mode = 0):
    with errstate(all='ignore'): 
        var = []
        par = []
        for _fct, _p0 in zip(fct, p0):
            try:
                popt, pcov = curve_fit(_fct, x, y, _p0)
            except RuntimeError: 
                continue
            var.append(max(diag(pcov)))
            par.append(popt)
        
        if mode == 0:
            i = var.index(min(var))
        elif mode == 1:
            i = 0
        else:
            i = var.index(min(var[1:]))
       
    return [par[i], fct[i]]

##########################################################################################################    
##########################################################################################################
#
#  Gestion des reponses temporelles
#
##########################################################################################################
##########################################################################################################
from CedWidgets import *
import graphmpl as graph

class WinAjustement(wx.MiniFrame, PrintHandler):
    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style = globdef.STYLE_FENETRE):
        
    
        
        # Variable de l'état d'affichage : complet = tous les widgets
        self.AffComplet = True
        
        self.FT = None
        self.Reponse = None
        self.Mesure = None
        
        size = (414,550)
        wx.MiniFrame.__init__(self, parent, -1, _(u"Ajustement de réponse indicielle"), pos, size, style)
      
#        self.SetMinSize(size)
        

        self.SetAutoLayout(True)
        

        self.initPrintHandler(PrintoutWx, parent, globdef.PRINT_PAPIER_DEFAUT, globdef.PRINT_MODE_DEFAUT)
        
        #
        # Zone de tracé
        #
        outils = ["BGrille", "", "BZoomA", "BZoomP", "BDepla", "BEchel", "", "BCurse", 'BImpri', "", "BExpor",'BParam']
        self.ZoneAjustement = graph.ZoneGraphOutils(self, parent, 3, outils, tempo = True)
        self.ZoneAjustement.Add(graph.ZoneGraphAjustement(self.ZoneAjustement, self.ZoneAjustement, _(u"Ajustement réponse indicielle")))
#        self.zoneReponse = graph.ZoneGraphReponse(self, parent)

        #
        # Zone d'affichage de la FT
        #        
        self.pop = PopPanel(self)
        
        sizer0 = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
       
        self.BmpFT = ScrolledBitmap(self.pop, -1, wx.NullBitmap) 
        sizer.Add(self.BmpFT, 1, flag = wx.EXPAND|wx.ALL, border = 5)
        
        self.pop.SetSizerAndFit(sizer)
       
        panelbtn = wx.Panel(self, -1)
        button = wx.Button(panelbtn, -1, _(u"Fermer"))
        self.panelbtn = panelbtn
        
        #
        # Mise en place
        #
        sizer0.Add(self.pop, 0, flag = wx.EXPAND)
        sizer0.Add(self.ZoneAjustement,1, flag = wx.EXPAND)
        sizer0.Add(panelbtn, flag = wx.EXPAND|wx.ALIGN_CENTER)
        self.SetSizer(sizer0)
        self.sizer = sizer0
        
        self.signal = 0
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_BUTTON, self.OnCloseMe, button)
        
#        self.SetInitialSize(size)
        self.SetAutoLayout(False)

    def OnCloseWindow(self, event):
        print "OnCloseWindow"
        self.Parent.win = None
        self.Destroy()
        return
    
    ######################################################################################################
    def SetAffComplet(self):
#        print "SetAffComplet"
        self.AffComplet = not self.AffComplet
        
        if self.AffComplet:
            self.TailleOrigZg = self.GetClientSize()
            posZg = self.ZoneAjustement.GetScreenPosition()
            self.pop.Show(True)
            self.sizer.Insert(0, self.pop, 0, flag = wx.EXPAND)
            self.panelbtn.Show(True)
            self.sizer.Insert(2, self.panelbtn, 0, flag = wx.EXPAND)
            
            self.SetClientSize(self.TailleOrig)
            
            PosOrig = self.GetPosition()
            self.SetPosition((PosOrig[0], posZg[1]+self.dph))
            
        else:
            self.TailleOrig = self.GetClientSize()
            
            PosOrig = self.GetPosition()
            posZg = self.ZoneAjustement.GetScreenPosition()
            posBmp = self.pop.GetScreenPosition()
            dph = PosOrig[1] - posBmp[1]
            
            self.dph = PosOrig[1] - posZg[1]
            
            self.pop.Show(False)
            self.sizer.Detach(self.pop)
            self.panelbtn.Show(False)
            self.sizer.Detach(self.panelbtn)
            if hasattr(self, 'TailleOrigZg'):
                self.SetClientSize(self.TailleOrigZg)
            else:
                self.SetClientSize(self.ZoneAjustement.GetSize())
            self.SetPosition((PosOrig[0], posZg[1]+dph))
        self.Layout()
        
    
    def OnCloseMe(self, event):
        self.Close(True)
        
        
    ######################################################################################################    
    def MiseAJour(self, FT, mesures, reponse):
        self.FT = FT[0]
        self.Mesure = mesures
        self.Reponse = reponse
        self.MiseAJourBmp()
        self.ZoneAjustement.mettreAJourEtRedessiner(self.Mesure, self.Reponse)

    ######################################################################################################
    def ReTracer(self):
        if hasattr(self.ZoneAjustement.child[0], 'consigne'):
            self.ZoneAjustement.child[0].TracerTout()
        else:
            self.MiseAJour(0)
 
    
    ######################################################################################################
    def OnSize(self, event):
        self.sizer.SetDimension(0,0,self.GetClientSize()[0],self.GetClientSize()[1])

        
    ######################################################################################################
    def setFT(self, FT, mesures, reponse):
        self.FT = FT[0]
        self.Mesure = mesures
        self.Reponse = reponse
        self.MiseAJourBmp()
        
        
    ######################################################################################################
    def MiseAJourBmp(self):
        if self.FT == None:
            return
#        print "MiseAJourBmp"
        self.BmpFT.SetBitmap(self.FT.getBitmap(), self.GetBmpHD)
        
#        self.MiseAJour()
        self.pop.Fit()
        self.pop.FitInside()
        self.pop.Refresh()
#        self.sizer.Fit()
#        self.sizer.Fit(self)
        self.sizer.SetItemMinSize(self.pop, self.pop.GetSize()[0], self.pop.GetSize()[1])
        self.sizer.Layout()
        
    def GetBmpHD(self):
        return self.FT.getBitmap(taille = globdef.FONT_SIZE_FT_HD)
     
        
    def modifierAntialiased(self):
        self.ZoneAjustement.child[0].modifierAntialiased()
        

