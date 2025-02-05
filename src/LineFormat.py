#!/usr/bin/env python
# -*- coding: utf-8 -*-

##This file is part of pySylic
#############################################################################
#############################################################################
##                                                                         ##
##                               LineFormat                                ##
##                                                                         ##
#############################################################################
#############################################################################

## Copyright (C) 2009-2025 Cédrick FAURY

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

import wx, json
import xml.etree.ElementTree as ET


###################################################################################################
#
#  Conteneur du format de ligne
#
###################################################################################################
class LineFormat():
    """ Format de ligne pour MatPlotLib
        Arguments :
        coul  : couleur (format wx)
        styl  : style de ligne (format mpl)
        epais : épaisseur
        
    """
    
    def __init__(self, coul = wx.Colour(0,0,0), styl = "-", epais = 2, format = None):
        if isinstance(coul, wx.Colour):
            self.coul = coul
        elif type(coul) == str:
            self.coul = self.str2coul(coul)
        self.styl = styl
        self.epais = epais
    

    ###############################################################################################
    def toJSON(self):
        d = self.__dict__
        d['coul'] = self.get_coul_str()
        return d


    ###############################################################################################
    def __repr__(self):
        return f"{self.coul}-{self.epais}-{self.styl}"
    
    
    ###############################################################################################
    def get_coul_str(self):
        return self.coul.GetAsString(wx.C2S_HTML_SYNTAX)
    

    ###############################################################################################
    def str2coul(self, str):
        return wx.NamedColour(str)

    # ###############################################################################################
    # def getBranche(self, nom):
    #     root = ET.Element(nom)
    #     root.set("couleur", self.get_coul_str())
    #     root.set("style", self.styl)
    #     root.set("epaisseur", str(self.epais))
    #     return root
        
    # ###############################################################################################
    # def ouvrir(self, nom, brancheFormat):
    #     branche = brancheFormat.find(nom)
    #     if branche != None:
    #         self.coul = self.str2coul(branche.get("couleur"))
    #         self.styl = branche.get("style")
    #         self.epais = eval(branche.get("epaisseur"))
    #         return True
    #     return False
        
    ###############################################################################################
    def copie(self, format):
        self.coul = format.coul
        self.styl = format.styl
        self.epais = format.epais
        
    # ###############################################################################################
    # def writeConfig(self, config, titre, nom):
    #     config.set(titre, "coul"+nom, self.get_coul_str())
    #     config.set(titre, "epais"+nom, self.epais)
    #     config.set(titre, "styl"+nom, self.styl)
    #     return
    
#     ###############################################################################################
#     def readConfig(self, config, titre, nom):
# #        print "readConfig", 
#         coul = config.get(titre, "coul"+nom)    
# #        print coul
# #        v = eval(coul)
# #        self.coul = wx.Colour(v[0], v[1], v[2], v[3]) 
#         self.coul = self.str2coul(coul)
#         self.epais = config.getfloat(titre, "epais"+nom)
#         self.styl = config.get(titre, "styl"+nom)
# #        print self
#         return
    
##########################################################################################################
# Modification de la FT ...
#############################################################################################################
myEVT_FORMAT_MODIFIED = wx.NewEventType()
EVT_FORMAT_MODIFIED = wx.PyEventBinder(myEVT_FORMAT_MODIFIED, 1)

#----------------------------------------------------------------------

class FormatEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.Id = 0
        self.Format = None

    def SetId(self, id):
        self.Id = id

    def GetId(self):
        return self.Id

    def SetFormat(self, format):
        self.Format = format
        
    def GetFormat(self):
        return self.Format
    
        
###################################################################################################
#
#  Dialog de selection du style de ligne
#
###################################################################################################
try:
    from agw import floatspin as FS
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.floatspin as FS
    
class LineFormatSelector(wx.Dialog):
    """ Dialog de selection d'un format de ligne
        <format> = liste : [couleur, style, épaisseur]
    """
    def __init__(self, parent, format):
        wx.Dialog.__init__(self, parent, -1, _("Format de ligne"))
        
        self.format = format
        
        self.lineStyle = [_("ligne continue"), #solid line style
                          _("pointillés"), #dashed line style
                          _("mixte"), #dash-dot line style
                          _("points"), #dotted line style
                          ]
        
        self.lineStyleMpl = ['-', '--', '-.', ':']
        
        #
        # Style
        #
        txtStyle = wx.StaticText(self, -1, _("Style de ligne :"))
        selStyle = PenStyleComboBox(self, choices=self.lineStyle, style=wx.CB_READONLY,
                                pos=(20,40), size=(100, -1))
        selStyle.SetToolTipString(_("Modifier le style de la ligne"))
        selStyle.SetValue(self.lineStyle[self.lineStyleMpl.index(format.styl)])
        
        #
        # Epaisseur
        #
        txtWidth = wx.StaticText(self, -1, _("Epaisseur :"))
#        selWidth = wx.SpinCtrl(self, -1, "", size=(100, -1))
        selWidth = FS.FloatSpin(self, -1, min_val=0.01, max_val=10.0,
                                       increment=0.1, value=1.0, 
                                       size = (80, -1),
                                       agwStyle=FS.FS_LEFT)
        selWidth.SetFormat("%f")
        selWidth.SetDigits(2)
        
        selWidth.SetToolTipString(_("Modifier l'épaisseur de la ligne"))
#        selWidth.SetRange(1,6)
        selWidth.SetValue(format.epais)
        
        #
        # Couleur
        #
        txtColor = wx.StaticText(self, -1, _("Couleur :"))
        selColor = wx.Button(self, -1, "", size = (100,22))
        selColor.SetToolTipString(_("Modifier la couleur de la ligne"))
        selColor.SetBackgroundColour(format.coul)
        
        #
        # Les boutons standards
        #
        btnsizer = wx.StdDialogButtonSizer()
        
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            btnsizer.AddButton(btn)
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("The OK button completes the dialog")
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("The Cancel button cancels the dialog. (Cool, huh?)")
        btnsizer.AddButton(btn)
        btnsizer.Realize()     
        
        #
        # Mise en place
        #
        sizer = wx.GridBagSizer()
        sizer.Add(txtStyle, (0,0), flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizer.Add(txtWidth, (1,0), flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizer.Add(txtColor, (2,0), flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizer.Add(selStyle, (0,1), flag = wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizer.Add(selWidth, (1,1), flag = wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizer.Add(selColor, (2,1), flag = wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, border = 5)
        sizer.Add(btnsizer, (3,0), (1,2),flag = wx.ALIGN_CENTER|wx.ALL, border = 5)
        self.SetSizerAndFit(sizer)
        
        #
        # Les évenements
        # 
        self.Bind(wx.EVT_BUTTON, self.OnClick, selColor)
        self.Bind(wx.EVT_COMBOBOX, self.OnCombo, selStyle)
        self.Bind(wx.EVT_SPINCTRL, self.OnSpin, selWidth)
        self.selColor = selColor
        self.selStyle = selStyle
        
    ###############################################################################################
    def OnClick(self, event = None):      
    
        dlg = wx.ColourDialog(self)

        # Ensure the full colour dialog is displayed, 
        # not the abbreviated version.
        dlg.GetColourData().SetChooseFull(True)

        if dlg.ShowModal() == wx.ID_OK:

            # If the user selected OK, then the dialog's wx.ColourData will
            # contain valid information. Fetch the data ...

            self.format.coul = dlg.GetColourData().GetColour()
            self.selColor.SetBackgroundColour(self.format.coul)
            self.selStyle.Refresh()
            
        # Once the dialog is destroyed, Mr. wx.ColourData is no longer your
        # friend. Don't use it again!
        #dlg.Destroy()
        return
    
    ###############################################################################################
    def OnCombo(self, event = None):
        self.format.styl = self.lineStyleMpl[self.lineStyle.index(event.GetEventObject().GetValue())]
        return
    
    ###############################################################################################
    def OnSpin(self, event = None):
        self.format.epais = event.GetEventObject().GetValue()
        self.selStyle.Refresh()
        return
     
     
    
import wx.adv
class PenStyleComboBox(wx.adv.OwnerDrawnComboBox):

    # Overridden from OwnerDrawnComboBox, called to draw each
    # item in the list
    def OnDrawItem(self, dc, rect, item, flags):
        if item == None:
            # painting the control, but there is no valid item selected yet
            return

        r = wx.Rect(*rect)  # make a copy
        r.Deflate(3, 5)

        wxLineStyle = [wx.SOLID, #solid line style
                       wx.SHORT_DASH, #dashed line style
                       wx.DOT_DASH, #dash-dot line style
                       wx.DOT, #dotted line style
                       ]
        
#        pen = wx.Pen(dc.GetTextForeground(), 3, wxLineStyle[item])
#        print type(self.Parent.format.epais)
        pen = wx.Pen(self.Parent.format.coul, max(1,int(self.Parent.format.epais)), wxLineStyle[item])
        dc.SetPen(pen)

        if flags & wx.adv.ODCB_PAINTING_CONTROL:
            # for painting the control itself
            dc.DrawLine( r.x+5, 
                        int(r.y+r.height/2), 
                        r.x+r.width - 5, 
                        int(r.y+r.height/2)
                        )

        else:
            # for painting the items in the popup
            dc.DrawText(self.GetString( item ),
                        r.x + 3,
                        int((r.y + 0) + ( (r.height/2) - dc.GetCharHeight() )/2)
                        )
            dc.DrawLine( r.x+5, 
                         int(r.y+((r.height/4)*3)+1), 
                         r.x+r.width - 5, 
                         int(r.y+((r.height/4)*3)+1)
                         )

           
    # Overridden from OwnerDrawnComboBox, called for drawing the
    # background area of each item.
    def OnDrawBackground(self, dc, rect, item, flags):
        # If the item is selected, or its item # iseven, or we are painting the
        # combo control itself, then use the default rendering.
        if (item & 1 == 0 or flags & (wx.adv.ODCB_PAINTING_CONTROL |
                                      wx.adv.ODCB_PAINTING_SELECTED)):
            wx.adv.OwnerDrawnComboBox.OnDrawBackground(self, dc, rect, item, flags)
            return

        # Otherwise, draw every other background with different colour.
        bgCol = wx.Colour(240,240,250)
        dc.SetBrush(wx.Brush(bgCol))
        dc.SetPen(wx.Pen(bgCol))
        dc.DrawRectangleRect(rect)



    # Overridden from OwnerDrawnComboBox, should return the height
    # needed to display an item in the popup, or -1 for default
    def OnMeasureItem(self, item):
        # Simply demonstrate the ability to have variable-height items
        if item & 1:
            return 36
        else:
            return 24

    # Overridden from OwnerDrawnComboBox.  Callback for item width, or
    # -1 for default/undetermined
    def OnMeasureItemWidth(self, item):
        return -1; # default - will be measured from text width
    
    
    
    
    
#############################################################################################################
class SelecteurFormatLigne(wx.Panel):
    
    def __init__(self, parent, id, format, tooltip, size = (20, 10)):
        wx.Panel.__init__(self, parent, -1)#, style = wx.BORDER_SIMPLE)
        from graphmpl import EchantillonLigne
        self.fctEchantillon = EchantillonLigne
#        print format
        self.format = format
        self.id = id
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.size = size[0]-8, size[1]-8
        self.btn = wx.BitmapButton(self, -1, wx.EmptyBitmap(self.size[0], self.size[1]))
#                                   size = (20,10), style = wx.BORDER_SUNKEN)
        self.btn.SetToolTipString(tooltip)
        self.btn.SetBackgroundColour(wx.WHITE)
        self.SetFormatBouton()
        sizer.Add(self.btn, flag = wx.ALIGN_CENTER_VERTICAL)
        
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btn)
        
        self.SetSizerAndFit(sizer)
        
    def OnClick(self, event = None):
        
        dlg = LineFormatSelector(self, self.format)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.SetFormatBouton()
            evt = FormatEvent(myEVT_FORMAT_MODIFIED, self.GetId())
            evt.SetId(self.id)
            evt.SetFormat(self.format)
            self.GetEventHandler().ProcessEvent(evt)
            
        #dlg.Destroy()
        return
    
    
    def MiseAJour(self, format):
        self.format = format
        self.SetFormatBouton()
        
        
    def SetFormatBouton(self):
        wxLineStyle = {"-": wx.SOLID, #solid line style
                       "--": wx.SHORT_DASH, #dashed line style
                       "-.": wx.DOT_DASH, #dash-dot line style
                       ":": wx.DOT, #dotted line style
                       }
        bmp = self.fctEchantillon(self.size, self.format.styl, 'None', self.format.get_coul_str(), self.format.epais)
#        bmp = wx.EmptyBitmap(self.size[0], self.size[1])
#        dc = wx.MemoryDC(bmp)
#        dc.Clear()
#        dc.SetBackground(wx.Brush(self.btn.GetBackgroundColour()))
#        dc.SetPen(wx.Pen(self.format.coul, min(1,self.format.epais), wxLineStyle[self.format.styl]))
#        
#        l, h = bmp.GetWidth(), bmp.GetHeight()
#        dc.DrawLine(0, h/2, l, h/2)
        
        self.btn.SetBitmapLabel(bmp)
        self.btn.SetBitmapDisabled(bmp.ConvertToImage().AdjustChannels(1,1,1,0.3).ConvertToBitmap())
       
#        dc.SelectObject(wx.NullBitmap)
            
#        dlg = wx.ColourDialog(self)
#
#        # Ensure the full colour dialog is displayed, 
#        # not the abbreviated version.
#        dlg.GetColourData().SetChooseFull(True)
#
#        if dlg.ShowModal() == wx.ID_OK:
#
#            # If the user selected OK, then the dialog's wx.ColourData will
#            # contain valid information. Fetch the data ...
#
#            self.format[0] = dlg.GetColourData().GetColour()
#            self.btn.SetBackgroundColour(self.format[0])
#            
#            evt = FormatEvent(myEVT_FORMAT_MODIFIED, self.GetId())
#            evt.SetId(self.id)
#            evt.SetFormat(self.format)
#            self.GetEventHandler().ProcessEvent(evt)
#            
#
#        # Once the dialog is destroyed, Mr. wx.ColourData is no longer your
#        # friend. Don't use it again!
#        dlg.Destroy()
#        return
    
    def Activer(self, etat):
        self.btn.Enable(etat)

