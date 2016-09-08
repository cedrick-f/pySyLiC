#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

##This file is part of PySylic
#############################################################################
#############################################################################
##                                                                         ##
##                                 export                                  ##
##                                                                         ##
#############################################################################
#############################################################################

## Copyright (C) 2009 Cédrick FAURY

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import matplotlib
matplotlib.interactive(False)
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
#matplotlib.use('WX')
#from matplotlib.backends.backend_wx import FigureCanvasWx as FigureCanvas
#from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

import wx

class WinExport(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, size = (640,400))
        self.SetAutoLayout(True)
        self.parent = parent
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.pnl = wx.Panel(self, -1)
        sizer.Add(self.pnl, flag = wx.EXPAND)
        self.SetSizer(sizer)
        
    def exporterBode(self, zoneGraph):
        rangeX = zoneGraph.contenu["minmax"]
    
            
        #
        # Séparation des contenus "Gain" et "Phase"
        #
        if "diagReel" in zoneGraph.contenu.keys():
            lR = zoneGraph.contenu["diagReel"]
        else:
            lR = ([],[])
            
        if "diagAsymp" in zoneGraph.contenu.keys():
            lA = zoneGraph.contenu["diagAsymp"]
        else:
            lA = ([],[])
        
        contenuGain = {"diagA" : lA[0],
                       "diagR" : lR[0]}
        
        contenuPhas = {"diagA" : lA[1],
                       "diagR" : lR[1]}
        
        if "marges" in zoneGraph.contenu.keys():
            contenuGain["marges"] = zoneGraph.winMarges
            contenuPhas["marges"] = zoneGraph.winMarges
        else:
            contenuGain["marges"] = None
            contenuPhas["marges"] = None
            
        #
        # Tracé
        #
        
        self.figure1 = Figure()
        self.canvas1 = FigureCanvas(self.pnl, -1, self.figure1)
        
#        self.figure1.
        if zoneGraph.zoneGraphGain.tracerGrille:
            self.figure1.gca().grid(linewidth=1)
        self.figure1.gca().set_xlim(rangeX)   
        for i, diag in enumerate(contenuGain["diagR"]):
            plot = self.figure1.add_subplot(111, animated = True, cursor_props = (1.3, "red"))
            plot.semilogx(diag.reponse[0],diag.reponse[1])
#            plot.grid(True)

        self.figure2 = Figure()
        self.canvas2 = FigureCanvas(self.pnl, -1, self.figure2)
        if zoneGraph.zoneGraphGain.tracerGrille:
            self.figure2.gca().grid(linewidth=1)
        self.figure2.gca().set_xlim(rangeX)   
#        if zoneGraph.zoneGraphGain.tracerGrille:
#            self.figure2.grid(linewidth=1)
            
        for i, diag in enumerate(contenuPhas["diagR"]):
            plot = self.figure2.add_subplot(111, animated = True, cursor_props = (1.3, "red"))
    
            plot.semilogx(diag.reponse[0],diag.reponse[1])
#            plot.grid(True)

#            self.plot.append(plot)
        
#        self.canvas1.draw()
#        self.canvas2.draw()
        
        self.pnl.sizer = wx.BoxSizer(wx.VERTICAL)
        self.pnl.sizer.Add(self.canvas1, 2, wx.LEFT | wx.TOP | wx.GROW)
        self.pnl.sizer.Add(self.canvas2, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.pnl.SetSizer(self.pnl.sizer)
        self.pnl.Fit()
#        self.pnl.FitInside()
        self.Fit()

#    def exporter(zoneGraph):
#        
#        plt.xlim(rangeX)
#        if zoneGraph.zoneGraphGain.tracerGrille:
#            plt.grid(linewidth=1)
#        plt.figure(1)
#        plt.subplot(211)
#        for i, diag in enumerate(contenuGain["diagR"]):
#            plt.semilogx(diag.reponse[0], diag.reponse[1], 
#                         color = zoneGraph.lstCoul[i].GetAsString(wx.C2S_HTML_SYNTAX),
#                         )
#        plt.subplot(212)
#        for i, diag in enumerate(contenuPhas["diagR"]):
#            plt.semilogx(diag.reponse[0], diag.reponse[1], 
#                         color = zoneGraph.lstCoul[i].GetAsString(wx.C2S_HTML_SYNTAX),
#                         )
#       
#        plt.show()
#        return