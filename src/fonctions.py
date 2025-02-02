#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

##This file is part of PySylic
#############################################################################
#############################################################################
##                                                                         ##
##                                Fonctions                                ##
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


#import  wx.lib.fancytext as fancytext
#import  wx.lib.scrolledpanel as scrolled
from CedWidgets import *
from numpy import poly1d, imag, real
#import scipy
#import wx
#from scipy import poly1d, float64 

import calcul 
import globdef
import os
import Images
import xml.etree.ElementTree as ET

#########################################################################################################
#
#  Les evenements perso
#
#########################################################################################################  

# Modification d'un polynôme ...
#############################################################################################################
myEVT_POLY_MODIFIED = wx.NewEventType()
EVT_POLY_MODIFIED = wx.PyEventBinder(myEVT_POLY_MODIFIED, 1)

#----------------------------------------------------------------------

msgFTtropComplexe =  _("Niveau de complexité de la fonction de transfert trop élevé !!") + "\n\n" \
                   + _("   Il est possible de tracer des fonctions aussi complexes\n"\
                       "   en modifiant l'option \"Général/Niveau de complexité\"")
                                     
class SelPolyEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.poly = []
        self.diff = 0

    def SetPoly(self, val):
        self.poly = val

    def GetPoly(self):
        return self.poly
    
    def SetDiff(self, diff):
        """ Type de modification apportée à self.poly
            0 : aucune différence
            1 : nom(s) de variable modifié ou variable ajoutée/enlevée
            2 : valeur(s) modifiée(s)
            4 : ordre modifié
        """
        self.diff = diff
    
    def GetDiff(self):
        return self.diff
    
    
    
# Modification de la FT ...
#############################################################################################################
myEVT_FT_MODIFIED = wx.NewEventType()
EVT_FT_MODIFIED = wx.PyEventBinder(myEVT_FT_MODIFIED, 1)

#----------------------------------------------------------------------

class SelFTEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.panel = None
#        self.TypeModif = 0

    def SetPanel(self, panel):
        self.panel = panel

    def GetPanel(self):
        return self.panel

    def SetTypeModif(self, tm):
        self.TypeModif = tm
        
    def GetTypeModif(self):
        return self.TypeModif



#########################################################################################################
#
#  Fonction de Transfert (sous forme développée)
#
#########################################################################################################  
class FonctionTransfertDev:
    def __init__(self, polyN = None, polyD = None, retard = 0):
        # Les deux polynomes
        if polyN == None: polyN = [1.0]
        self.polyN = polyN
        if polyD == None: polyD = [1.0]
        self.polyD = polyD
        self.retard = retard
        
        # Les variables
        self.variables = {}
        
        # La fonction de transfert sous forme numérique (type calcul.FonctionTransfertNum)
        self.FTNum = []
        
        # La liste de sous fonctions de transfert (type calcul.FonctionTransfertNum)
        self.lstFTNum = []
        
    #########################################################################################################
    def __repr__(self):
        print (self.polyN)
        print("------------------ r =", self.retard)
        print (self.polyD)
        return ""

    ######################################################################################  
    def copie(self, FT = None):
        if FT == None:
            polyN, polyD = [], []
            for p in self.polyN:
                polyN.append(p)
            for p in self.polyD:
                polyD.append(p)
            return FonctionTransfertDev(polyN, polyD, retard = self.retard)
        else:
            polyN, polyD = [], []
            for p in FT.polyN:
                polyN.append(p)
            for p in FT.polyD:
                polyD.append(p)
            self.__init__(polyN, polyD, retard = FT.retard)

    #########################################################################################################
    def getBranche(self):
        """ Enregistre la FT 
            sous forme de branche ElementTree
        """
        root = ET.Element("FT_H")
        root.set("type_FT", "1")
        root.set("PolyNum", polyToTxt(self.polyN, num = False))
        root.set("PolyDen", polyToTxt(self.polyD, num = False))
        
        variables = ET.SubElement(root, "Variables")
        variables.set("retard", str(self.retard))
        for var in self.variables.values():
            variables.set(var.n.lstrip('\\'), strList(var.v))
        
        return root
    
    #########################################################################################################
    def ouvrir(self, branche):
        validN, self.polyN, erreur = textToPoly(branche.get("PolyNum"))
        validD, self.polyD, erreur = textToPoly(branche.get("PolyDen"))
        
        variables = branche.find("Variables")
        
        try:
            self.retard = eval(variables.get("retard"))
        except:
            self.retard = 0
        if self.retard == None:
            self.retard = 0
        
        self.detDictVari()
#        print self.variables
        for k,var in self.variables.items():
#            print "  ", variables.get(k, "")
            var.v = listStr(variables.get(k, ""))
#        print self.variables
           
        return validN * validD
            
    #########################################################################################################
    def detFTNum(self):
        """ Renvoie la version numérique de la FT
                (avec les valeurs actuelles des variables)
        """
#        print "Determination de FTNum"
#        print self.variables
        
        def getPolyNum(poly):
            polyNum = []
            for c in poly:
                
                if type(c) == str or type(c) == unicode:
                    polyNum.append(self.variables[c].v[0])
                    
                elif isinstance(c, Expression):
                    v = c.evaluer()
                    if v == None:
                        return None
                    else:
                        polyNum.append(v)
                    
                else:
                    polyNum.append(c)
                    
            return polyNum
        
        pN = getPolyNum(self.polyN)
        pD = getPolyNum(self.polyD)
        
#        print pN, pD
        
        self.FTNum = [calcul.FonctionTransfertNum(pN, pD, retard = self.retard)]
    
    
#    def detLstFTNum(self):
#        """ Détermine la liste des sous FT 
#        """
#        self.detFTNum()
#        self.lstFTNum = self.FTNum.decomposition()
    
    #########################################################################################################
    def detLstFTNum(self):
        """ Détermine la liste des sous FT 
        """
#        print "detLstFtNum :"
        self.miseAJourCoef()
        
        self.detFTNum()
        K, lstFT = self.FTNum[0].getFormeCanonique()
#        print K
#        print lstFT
        lstFT[0] = lstFT[0] * K
        self.lstFTNum = lstFT
        
        if self.retard != 0:
            self.lstFTNum.append(calcul.FonctionTransfertNum(retard = self.retard))
        
    
    #########################################################################################################
    def detDictVari(self):
        """ Etabli la liste des variables de la FT
          --> self.variables
        """
#        print "Determination des variables"
        def getDictVariPoly(poly):
#            polyNum = self.separerConstVari(poly)
#            print "  ",poly
            for c in poly:
                if type(c) == str or type(c) == unicode and c != u'' and c !='':
                    if c in GREEK:
                        cc = r""+"\\"+c
                    else:
                        cc = c
                    self.variables[c] = Variable(cc, lstVal = [1.0], typ = VAR_REEL) # valeur par défaut de la variable
                
                elif isinstance(c, Expression):
#                    print c.vari
#                    self.variables.update(c.vari)
                    for k,v in c.vari.items():
                        self.variables[k] = v
                        
        self.variables = {}  
        getDictVariPoly(self.polyN)
        getDictVariPoly(self.polyD)
        
        if globdef.DEPHASAGE:
            self.variables['tau'] = Variable(r'\tau', nomNorm = _("du retard"),
                                               lstVal = [self.retard], typ = VAR_REEL_POS,
                                               modeLog = False)
        
        
#        print "-->",self.variables
#        return self.variables

    #########################################################################################################
    def miseAJourCoef(self):
        if 'tau' in self.variables.keys():
            self.retard = self.variables['tau'].v[0]
        else:
            self.retard = 0
        return
#        self.K = self.variables[u'K'].v[0]
#        self.classe = self.variables[u'a'].v[0]
#        
#        for poly in self.lstPolyN + self.lstPolyD:
#            if isinstance(poly, poly1):
#                poly.T = self.variables[poly.getNomVariables()[0]].v[0]
#            elif isinstance(poly, poly2):
#                poly.Om = self.variables[poly.getNomVariables()[0]].v[0]
#                poly.z = self.variables[poly.getNomVariables()[1]].v[0]


    #########################################################################################################
    def factoriser(self):
#        print "Factorisation de :"
#        print self
        
        classe = self.FTNum[0].classe
        K = self.FTNum[0].gainStat
        
        id = 1
#        def getPolyN(poly):
#            if poly.o == 1:
#                T = -1.0/poly.r[0]
#                return poly1(id = id, T = T)
#            elif poly.o == 2:
#                O2 = poly.c[2]/poly.c[0]
#                Om = scipy.sqrt(abs(O2))
#                Z = Om*(poly.c[1]/poly.c[2])/2
#                return poly2(id = id, Om = Om, z = Z)
            
            
        lstPolyN = []
        lstPolyD = []
        for f in self.lstFTNum:
#            print f
#            print "-->",
            if f.est1erOrdre() and sum(f.getPoles()) != 0.0:
                T = -1.0/f.polyD.r[0]
                lstPolyD.append(poly1(id = id, T = T))
#                print lstPolyD[-1]
                id += 1
            elif f.estInv1erOrdre() and sum(f.getZeros()) != 0.0:
                T = -1.0/f.polyN.r[0]
                lstPolyN.append(poly1(id = id, T = T))
#                print lstPolyN[-1]
                id += 1
            elif f.est2ndOrdre() and sum(f.getPoles()) != 0.0:
                O2 = f.polyD.c[2]/f.polyD.c[0]
                Om = scipy.sqrt(abs(O2))
                Z = Om*(f.polyD.c[1]/f.polyD.c[2])/2
                lstPolyD.append(poly2(id = id, Om = Om, z = Z))
#                print lstPolyD[-1]
                id += 1
            elif f.estInv2ndOrdre() and sum(f.getZeros()) != 0.0:
                O2 = f.polyN.c[2]/f.polyN.c[0]
                Om = scipy.sqrt(abs(O2))
                Z = Om*(f.polyN.c[1]/f.polyN.c[2])/2
                lstPolyN.append(poly2(id = id, Om = Om, z = Z))
#                print lstPolyN[-1]
                id += 1
            elif f.egaleUn() or f.estIntegPur() or f.estDerivPur():
                pass
    
            else:
                print ("FT non factorisable !")
                return None
                
#            if f.polyN.o > 0 or f.polyN.c[0] <> 1.0:
#                lstPolyN.append(getPolyN(f.polyN))
#                print id, "-->", lstPolyN[-1]
#                id += 1
#            if f.polyD.o > 0 or f.polyD.c[0] <> 1.0:
#                lstPolyD.append(getPolyN(f.polyD))
#                print id, "-->", lstPolyD[-1]
#                id += 1
                
        if lstPolyN == [None]:
            lstPolyN = []
        if lstPolyD == [None]:
            lstPolyD = []
        
#        print lstPolyN, lstPolyD
        return FonctionTransfertFact([K], [classe], lstPolyN, lstPolyD, retard = self.retard)
    
    
    #########################################################################################################
    def getMathText(self, nom = None):
        if nom != None:
            n = nom+r"("+globdef.VAR_COMPLEXE+") = "
        else:
            n = r""
        
        if self.retard == 0:
            r = r""
        else:
            r = r"e^{-"+strSc(self.retard)+globdef.VAR_COMPLEXE+"}"
            
        if self.polyD == [1.0]:
            return n+r+getMathTextPoly(self.polyN, globdef.VAR_COMPLEXE)
        else:
            return n+r+r"\frac{"+getMathTextPoly(self.polyN, globdef.VAR_COMPLEXE)+"}" \
                    "{"+getMathTextPoly(self.polyD, globdef.VAR_COMPLEXE)+"}"
    
    #########################################################################################################
    def getBitmap(self, nom = None, taille = globdef.FONT_SIZE_FT_SELECT):
        return mathtext_to_wxbitmap(self.getMathText(nom), taille = taille)
#        return getBmpFT(self)
    
    #########################################################################################################
    def getComplexite(self):
        """ Renvoie le niveau de "compléxité" de la FT
            (le nombre maximum de sous fonctions de transfert 
             qu'elle est succeptible d'avoir)
        """
        n = len(self.polyD) + len(self.polyN) - 2
        n += 1 # pour la classe
        if globdef.DEPHASAGE: # Pour la fonction retard
            n += 1
        return n
    
##########################################################################################################
class SelecteurPolynome(wx.TextCtrl):
    """ Zone de saisie des polynômes
    """
    def __init__(self, parent, id, poly):
        wx.TextCtrl.__init__(self, parent, id, polyToTxt(poly))
        self.poly = poly

        self.toolTip =  _(u'Saisir ici les coefficients du polynome.\n'\
                          u'Cliquer sur le bouton "Aide à la saisie des polynomes"\n'\
                          "pour plus d'informations.")
        self.SetToolTipString(self.toolTip)                      
        
        self.Bind(wx.EVT_TEXT, self.EvtText, self)
    
    #########################################################################################################
    def MiseAJourToolTip(self, msg = ""):
        if msg == "":
            self.SetToolTipString(self.toolTip)
        else:
            self.SetToolTipString(msg)
    
    #########################################################################################################
    def EvtText(self, event = None):
        str = event.GetString()
        if str == "":
            valid, lst, erreur = True, [], ""
        else:
            valid, lst, erreur = textToPoly(str)
#        print lst, self.poly, estDifferente(lst)
        difference = self.GetDifference(lst)
        if valid and lst !=[]:
            self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            self.poly = lst
            if difference != 0:
                evt = SelPolyEvent(myEVT_POLY_MODIFIED, self.GetId())
                evt.SetPoly(self.poly)
                evt.SetDiff(difference)
                self.GetEventHandler().ProcessEvent(evt)
            self.MiseAJourToolTip()
        else:
            self.SetBackgroundColour("pink")
            self.MiseAJourToolTip(erreur)
#            print lst
        
        self.Refresh()
        event.Skip()
    
    
    #########################################################################################################
    def MiseAJour(self, poly):
        self.poly = poly
        self.ChangeValue(polyToTxt(poly, num = False))
        
    
    #########################################################################################################
    def GetDifference(self, lst):
        """ Renvoie le type de différence entre <lst> et self.poly
            0 : aucune différence
            1 : nom(s) de variable modifié ou variable ajoutée/enlevée
            2 : valeur(s) modifiée(s)
            4 : ordre modifié
        """
        if len(lst) != len(self.poly):
            return 4
        else:
            for i,c in enumerate(lst):
                if _type(self.poly[i]) != _type(c):
                    return 1
                else:
                    if self.poly[i] != c:
                        if type(c) == str or type (c) == unicode:
                            return 1
                        else:
                            return 2
        return 0
    
    
#############################################################################################################
def _type(v):
    if type(v) == str or type (v) == unicode:
        return 0
    else:
        return 1
    
#############################################################################################################
def polyToTxt(poly, num = True):
    s = ""
    for v in poly:
        if isinstance(v, Expression) and num == False:
            s += v.py_expr + ' '
        else:
            s += str(v) + ' '
    return s[:-1]
        
#############################################################################################################
def textToPoly(txt):
    """ Renvoie une liste représentant un polynôme et un booleen attestant de la validité :
        La liste peut contenir :
         - des nombres (constantes)
         - des textes (variables)
         - des 'expressions' (voir classe 'expression')
    """

    lst = txt.split()
    if lst == []:
        return False, []
    valid = True
    erreur = ""
    lst2 = []
    for c in lst:
        expr = Expression(c)
        
        if expr.IsConstante():
            v = expr.evaluer()
            
            if v == None:
                valid = False
                erreur = _("Constante non réelle")
            elif v == False and type(v) == bool:
                valid = False
                erreur = _("Impossible d'évaluer l'expression")
            else:
                lst2.append(v)
            
        else:
            if expr.vari.has_key('s') or expr.vari.has_key('p'):
                valid = False
                erreur = _("'s' et 'p' sont des noms de variable réservés à la variable complexe")
            
            else:
                vv = expr.evaluer()
                if vv == None:
                    valid = False
                    erreur = _("Résultat de l'évaluation non réel avec la(les) variable(s) à 1")
                elif vv == False:
                    valid = False
                    erreur = _("Impossible d'évaluer l'expression")
                
                lst2.append(expr)
         
    if valid:
        s = getMathTextPoly(lst2, globdef.VAR_COMPLEXE)
        valid = tester_mathtext_to_wxbitmap(s)
        erreur = _("Syntaxe de l'expression incorrecte")
    
#    print "fin textToPoly", valid, lst2, erreur
    return valid, lst2, erreur
            

##############################################################################################################
#def textToPoly2(txt):
#    """ Renvoie une liste représentant un polynôme et un booleen attestant de la validité :
#        La liste peut contenir :
#         - des nombres (constantes)
#         - des textes (variables)
#         - des 'expressions' (voir classe 'expression')
#    """
#    lst = txt.split()
#    if lst == []:
#        return False, []
#    valid = True
#    lst2 = []
#    for c in lst:
#        try:
#            v = eval(c.lstrip('0'))
#        except:
#            v = c
#        
#        # Détection d'un nombre --> CONSTANTE
#        if type(v) == int or type(v) == float:
#            pass
#            
#        # Détection d'une chaine ...
#        elif type(v) == str or type(v) == unicode:
#            vari, expr = getVariables(v)
##            print vari, expr
#            
#            # Détection d'une exression 'simple' --> VARIABLE
#            if len(vari) == 1 and vari.keys()[0] == v:
##                print "--> variable"
#                if v[0].isalpha() and not v in ['s','p']:
#                    pass
##                    v = vari[v].n
##                    for g in GREEK:
##                        v = v.replace(g, r""+"\\"+g)
#                else:
#                    valid = False
#                    
#            else:
#                if 's' in vari.keys() or 'p' in vari.keys():
#                    valid = False
#                else:
#                    v = Expression(expr, vari, v)
#                    try:
#                        vv = v.evaluer()
#                        if vv == None:
#                            valid = False
#                    except:
#                        valid = False
#                    
#        else:
#            valid = False
#                
#        lst2.append(v)
#        
#    
#    if valid:
#        s = getMathTextPoly(lst2, globdef.VAR_COMPLEXE)
#        valid = tester_mathtext_to_wxbitmap(s)
##            self.txt.SetBackgroundColour()
##        else:
##            self.txt.SetBackgroundColour("pink")
#    
#    return valid, lst2
    
    
##########################################################################################################
class SelecteurFTDev(wx.Panel):
    def __init__(self, parent, FT):
        wx.Panel.__init__(self, parent, -1)#, style = wx.BORDER_SIMPLE)
        
        self.parent = parent
        self.FT = FT
        
        self.SetAutoLayout(True)
        
#        gbsizer = wx.GridBagSizer()
        sN = SelecteurPolynome(self, 10, self.FT.polyN)
        sD = SelecteurPolynome(self, 11, self.FT.polyD)
        self.sN = sN
        self.sD = sD
        
        self.ret = wx.StaticBitmap(self, -1, wx.NullBitmap)
#        txt.SetCursor(wx.StockCursor(globdef.CURSEUR_MAIN))
#        txt.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
#        txt.Bind(wx.EVT_MOTION, self.OnMouseMove)
#        txt.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
#        self.mouseInfo = None
        
        btn = wx.BitmapButton(self, -1, Images.Bouton_Aide.GetBitmap())
        btn.SetToolTipString(_("Aide à la saisie des polynômes"))
        self.Bind(wx.EVT_BUTTON, self.OnAide)
        #
        # Mise en place
        #
        sh = wx.BoxSizer(wx.HORIZONTAL)
        sv = wx.BoxSizer(wx.VERTICAL)
        sv.Add(sN, flag = wx.EXPAND|wx.ALL, border = 2)
        sv.Add(sD, flag = wx.EXPAND|wx.ALL, border = 2)
        
        sh.Add(self.ret, 0, flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        sh.Add(sv, 1, flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        sh.Add(btn, 0, flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        self.sh = sh
#        gbsizer.Add(sN, (0,1), (1,1), flag = wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, border = 2)
#        gbsizer.Add(sD, (1,1), (1,1), flag = wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, border = 2)
#        gbsizer.Add(txt, (0,0), (2,1), flag = wx.ALIGN_CENTER)
        
#        self.bgh = gbsizer.GetSize()[1]
        
        #
        # La zone de l'équation ...
        #
#        self.scroll = wx.ScrolledWindow(self, -1)#, style = wx.BORDER_SIMPLE | wx.HSCROLL)
#        self.scroll.SetScrollRate(1,0)

#        psizer = wx.BoxSizer(wx.HORIZONTAL)
#        
        self.sb = ScrolledBitmap(self, -1, self.FT.getBitmap("H"))
#        psizer.Add(self.sb, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND)
        
#        self.scroll.SetSizerAndFit(psizer)
#        self.scroll.SetVirtualSize(self.sb.GetSize())
#        self.panel.SetAutoLayout(True)
#        self.panel.Layout()
#        self.panel.Fit()
#        self.panel.FitInside()

#        ssizer = wx.BoxSizer(wx.HORIZONTAL)
#        ssizer.Add(self.panel, flag = wx.ALIGN_CENTER)
#        self.scroll.SetSizer(ssizer)
#        self.ftp = FTFactPanel(parent, FT)


        #
        # Mise en place ...
        #
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sh, 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND)
        sizer.Add(self.sb, 1, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND)
        
        self.SetSizer(sizer)
        self.miseAJourBmpRetard()
        
        self.Bind(EVT_POLY_MODIFIED, self.OnPolyModified, sN)
        self.Bind(EVT_POLY_MODIFIED, self.OnPolyModified, sD)
    
#        self.Bind(wx.EVT_SIZE, self.OnSize)
#        
    ###############################################################################################
    def OnAide(self, event):
        dlg = AideDialog(self)
#        dlg.CenterOnScreen()
        dlg.Show()
#        dlg.Destroy()
    
#    ###############################################################################################
#    def OnMouseDown(self, event):
#        x0, y0 = self.scroll.GetViewStart()
#        x, y = self.scroll.CalcScrolledPosition(event.m_x, event.m_y)
#        self.mouseInfo = (x,y, x0, y0)
#        
#    def OnMouseUp(self, event):
#        self.mouseInfo = None
#        
#    def OnMouseMove(self, event):
#        if self.mouseInfo == None: return
#        
#        x, y = self.scroll.CalcScrolledPosition(event.m_x, event.m_y)
#        dx = x-self.mouseInfo[0]#, y-self.mouseInfo[1]
#        
#        xu, yu = self.scroll.GetScrollPixelsPerUnit()
#        x0 = self.mouseInfo[2]#, self.mouseInfo[3]
#        
#        self.scroll.Scroll(x0+dx/xu,0)
        
#    def OnSize(self, event = None):
##        print "OnSize"
##        print "  self", self.GetSize()
##        print "  sb", self.sb.GetSize()
#        
#        l, h = self.sb.GetSize()
#        
#        self.scroll.SetVirtualSize((l,h))
#        
##        ls, hs = self.scroll.GetSize()
#        if l > self.GetSize()[0]:
#            h += 17
##            print h
#            
#        self.scroll.SetSize((-1, h))
##        self.scroll.FitInside()
#        
#        
##        print "  scroll", self.scroll.GetSize()
##        self.GetSizer().Layout()
#        self.Layout()
##        self.Fit()
##        self.scroll.FitInside()
##        print self.GetSize()
##        self.Fit()
#        event.Skip()
        
        
#    #########################################################################################################
#    def AdjustSize(self, event = None):
#        print "AdjustSize", self.sb.GetSize()
#        l, h = self.sb.GetSize()
#        self.scroll.SetVirtualSize((l,h))
#        if l > self.scroll.GetSize()[0]:
#            h += 17
#        self.scroll.SetSize((-1, h))
#        
#        return
#        print "AdjustSize"
#        self.parent.Freeze()
#        self.panel.Fit()
#        l, h = self.panel.GetSize()
#        self.scroll.SetVirtualSize((l,h))
#        
#        if l > self.scroll.GetSize()[0]:
#            h += 17
            
#        print self.bgh, h
#        self.SetSize((-1, self.bgh + h))
#        self.parent.Thaw()
#        self.sb.Fit()
#        
#        
#        self.Fit()
#        self.Refresh()
#        l, h = self.GetSize()
#        
#        self.SetSize((-1, max(h, self.GetMinSize()[1])))
    
    
    
            
            
    #########################################################################################################
    def initFTSimple(self, FT):
        self.FT = FT
        self.sN.MiseAJour(self.FT.polyN)
        self.sD.MiseAJour(self.FT.polyD)
        self.MiseAJourBmp()    
        
    
    #########################################################################################################
    def miseAJourBmpRetard(self):
        if globdef.DEPHASAGE:
            r = r"e^{-\tau "+globdef.VAR_COMPLEXE+"}"
        else:
            r = r""
        self.ret.SetBitmap(mathtext_to_wxbitmap(r"H="+r+r"\frac{N}{D}"))
        self.Layout()
#        self.FitInside()
        self.Refresh()
        
        
    #########################################################################################################
    def initFT(self, FT):
        """ Initialisation du selecteur
            après une ouverture
        """
#        print "initFT..."
        self.FT = FT
        
        self.sN.MiseAJour(self.FT.polyN)
        self.sD.MiseAJour(self.FT.polyD)
        
        self.MiseAJourBmp()
        
        self.FT.detDictVari()
        self.FT.detLstFTNum()
        
#        print "... fin initFT"
        
    #########################################################################################################
    def MiseAJourBmp(self):
        """ Modifie l'expression factorisée de la FT
            quand on a ajouté/supprimé un polynôme
        """
        self.sb.SetBitmap(self.FT.getBitmap("H"), self.GetBmpHD, self.GetTeX)
        self.miseAJourBmpRetard()
        self.sb.FitInside()
#        self.sb.Fit()
        
#        self.OnSize()
#        print "AdjustSize", self.sb.GetSize()
#        l, h = self.sb.GetSize()
#        self.scroll.SetVirtualSize((l,h))
#        print self.scroll.GetSize()
#        ls, hs = self.scroll.GetSize()
#        if l > ls:
#            h += 17
#            print h
#        self.scroll.SetSize((ls, h))
#        print self.scroll.GetSize()
#        self.Fit()
#        self.scroll.FitInside()
#        print self.GetSize()
    
    def GetBmpHD(self):
        return self.FT.getBitmap("H", globdef.FONT_SIZE_FT_HD)
    
    def GetTeX(self):
        return self.FT.getMathText("H")
#    #########################################################################################################
#    def MiseAJour(self, FT):
#        self.sN.MiseAJour(FT.polyN)
#        self.sD.MiseAJour(FT.polyD)
        
        
    #########################################################################################################
    def OnPolyModified(self, event): 
#        print "OnPolyModified", event.GetPoly()
        if event != None:
            sel = event.GetId()
#            print sel
            if sel == 10:
                polyN = event.GetPoly()
            elif sel == 11:
                polyD = event.GetPoly()
        else:
            return
        
        if self.FT.getComplexite() > globdef.NBR_MAXI_PLOT:
            dlg = wx.MessageDialog(self.Parent, msgFTtropComplexe, 
                                   "FT trop complexe", 
                                   wx.OK | wx.ICON_ERROR
                                   )
            dlg.ShowModal()
            dlg.Destroy()
            return
        else:
            if sel == 10:
                self.FT.polyN = polyN
            elif sel == 11:
                self.FT.polyD = polyD
        
        self.MiseAJourBmp()
        
        self.FT.detDictVari()
        self.FT.detLstFTNum()
#        print self.FT.FTNum
        
        if event.GetDiff() == 1: # Seul le nom d'une variable a été modifié ...
            self.parent.OnNomVariableModified()
        else:
            self.parent.OnFTModified()
       
import  wx.lib.filebrowsebutton as filebrowse





import fitting

##########################################################################################################
class SelecteurFTFit(wx.Panel):
    def __init__(self, parent, FT):
        wx.Panel.__init__(self, parent, -1)#, style = wx.BORDER_SIMPLE)
        
        self.parent = parent
        self.FT = FT
        
        self.SetAutoLayout(True)
        
#        typesMesure = [_("Réponse indicielle")]
#        cb = wx.ComboBox(self, 500, _("Type de mesure"), 
#                         choices = typesMesure,
#                         style = wx.CB_DROPDOWN)
        
        
#        box = wx.StaticBox(self, -1, _("Fichier de points"))
#        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        filemask = "Fichiers CSV (.csv)|*.csv|" \
                   "Fichiers texte (.txt)|*.txt"
        self.fbbh = filebrowse.FileBrowseButtonWithHistory(self, -1, labelText =_("Fichier"),
                                                           buttonText ="...",
                                                           fileMask = filemask,
                                                           fileMode = wx.OPEN,
                                                           toolTip=_("Choisir le fichier contenant les coordonnées des points"),
                                                           changeCallback = self.fbbhCallback)
        
        self.fbbh.callCallback = False
        self.fbbh.SetHistory([], 4)

        
        typesAjust = [_("Automatique"), _(u'1er ordre'), _(u'2ème ordre')]
        sizer = wx.BoxSizer(wx.VERTICAL)
        rb = wx.RadioBox(
                self, -1, _("Ordre"), wx.DefaultPosition, wx.DefaultSize,
                typesAjust, 1, wx.RA_SPECIFY_COLS
                )
        self.mode = 0
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, rb)
        #rb.SetBackgroundColour(wx.BLUE)
        rb.SetToolTip(wx.ToolTip(_("Choisir l'ordre le la fonction de transfert\n"\
                                   "avec laquelle identifier les paramètres")))
        
        self.sb = ScrolledBitmap(self, -1, self.FT.getBitmap("H"))
        
        btn = wx.BitmapButton(self, -1, Images.Bouton_Identif.GetBitmap())
        btn.SetToolTipString(_("Afficher la courbe d'ajustement"))
        self.Bind(wx.EVT_BUTTON, self.OnAffiche)
        
        #
        # Mise en place
        #
        sh = wx.BoxSizer(wx.HORIZONTAL)
        sh.Add(self.sb, 1, flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        sh.Add(rb, 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND)
        sh.Add(btn, 0, flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
#        sizer.Add(cb, 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND)
        sizer.Add(self.fbbh, 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND)
        sizer.Add(sh, 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND)
        
        self.SetSizer(sizer)
        

#        

    ###############################################################################################
    def fbbhCallback(self, evt):
        if hasattr(self, 'fbbh'):
            value = evt.GetString()
            if not value:
                return
            history = self.fbbh.GetHistory()
            if value not in history:
                history.append(value)
                self.fbbh.SetHistory(history)
                self.fbbh.GetHistoryControl().SetStringSelection(value)
        else:
            return
        
        self.t, self.y = fitting.getPointsMesure(value)
        if self.t != None:
            self.calculer()
        
    ###############################################################################################
    def calculer(self):
        self.param , self.fct = fitting.ajuster(self.t, self.y, mode = self.mode)     
        self.OnPolyModified()
        if hasattr(self, 'win') and hasattr(self, 't'):
            self.win.MiseAJour(self.FT.FTNum, [self.t, self.y], 
                           [self.t, self.fct(self.t, *self.param)])
        
    ###############################################################################################
    def EvtRadioBox(self, event):
        self.mode = event.GetInt()
        self.calculer()
        
    ###############################################################################################
    def OnAffiche(self, event = None):
        
        if not hasattr(self, 'win'):
            self.win = fitting.WinAjustement(self.Parent.app)
        else:
            try:
                if not self.win.__nonzero__():
                    self.win = fitting.WinAjustement(self.Parent.app)
            except:
                pass
        if hasattr(self, 't'):
            self.win.MiseAJour(self.FT.FTNum, [self.t, self.y], 
                               [self.t, self.fct(self.t, *self.param)])
        self.win.Show()
    

    def initFTSimple(self, FT):
        self.FT = FT
        self.MiseAJourBmp()    
    
    #########################################################################################################
    def initFT(self, FT):
        """ Initialisation du selecteur
            après une ouverture
        """
#        print "initFT..."
        self.FT = FT
        
        
        self.MiseAJourBmp()
        
        self.FT.detDictVari()
        self.FT.detLstFTNum()
        
#        print "... fin initFT"
        
    #########################################################################################################
    def MiseAJourBmp(self):
        """ Modifie l'expression factorisée de la FT
            quand on a ajouté/supprimé un polynôme
        """
        self.sb.SetBitmap(self.FT.getBitmap("H"), self.GetBmpHD, self.GetTeX)
        self.sb.FitInside()

    
    def GetBmpHD(self):
        return self.FT.getBitmap("H", globdef.FONT_SIZE_FT_HD)
    
    def GetTeX(self):
        return self.FT.getMathText("H")
        
    #########################################################################################################
    def OnPolyModified(self): 
#        print "OnPolyModified",self.param
        self.FT.K = self.param[0]
        if len(self.param) == 2:
            self.FT.lstPolyD = [poly1(T = self.param[1])]
        elif len(self.param) == 3:
            self.FT.lstPolyD = [poly2(z = self.param[1],Om = self.param[2])]
        else:
            return
        
        self.MiseAJourBmp()
        
        self.FT.detDictVari()
        self.FT.detLstFTNum()
        
        self.parent.OnFTModified()
         
        
class AideDialog(wx.Dialog):
    def __init__(self, parent):
        
        wx.Dialog.__init__(self, None, -1, _("Format de définition d'un polynôme"), 
                           style=wx.DEFAULT_DIALOG_STYLE)
        
        font = wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL)
        
        def expr(str):
            return mathtext_to_wxbitmap(Expression(str).getMplText())
        

        label1 = wx.StaticText(self, -1, _("Saisir dans la zone de texte les coefficients du polynôme\n" 
                                           "dans l'ordre décroissant des puissances de ") + globdef.VAR_COMPLEXE + " :")
        
        label11 =  wx.TextCtrl(self, -1, "4.3 a 1", style = wx.TE_READONLY) 
        label12 =  wx.StaticText(self, -1, "--->")
        mplP = wx.StaticBitmap(self, -1, mathtext_to_wxbitmap(r"4.3" + globdef.VAR_COMPLEXE +"^2 + a"+ globdef.VAR_COMPLEXE+" + 1"))  
        
        label2 = wx.StaticText(self, -1, _("Les coefficients peuvent être de différents types :"))
        
        labelC = wx.StaticText(self, -1, _("Constante : ")) 
        labelV = wx.StaticText(self, -1, _("Variable : ")) 
        labelE = wx.StaticText(self, -1, _("Expression : "))  
              
        lstExemples = ["1.56", "",
                       "a", 
                       "beta_6", "",
                       "2/(a+1)", 
                       "3*sqrt(b)*cos(2*pi)"]
        
        exe = []
        mpl = []
        for e in lstExemples:
            if e != "":
                exe.append(wx.TextCtrl(self, -1, e, style = wx.TE_READONLY))
                mpl.append(wx.StaticBitmap(self, -1, expr(e)))
            else:
                exe.append(None)
                mpl.append(None)
        
        box = wx.StaticBox(self, -1, _("Faites des essais ici :"))
        bsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        
        label31 =  SelecteurPolynome(self, -1, []) 
        label32 =  wx.StaticText(self, -1, "--->")
        bsizer.Add(label31, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border = 5)
        bsizer.Add(label32, 0, wx.ALIGN_CENTER|wx.ALL, border = 5)
        self.mplPe = ScrolledBitmap(self, -1, expr(label31.GetValue()))  
        bsizer.Add(self.mplPe, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL|wx.EXPAND, border = 5)
        self.Bind(EVT_POLY_MODIFIED, self.EvtText, label31)
        self.bsizer = bsizer
        
        
        #
        # Le bouton pour sortir
        #
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        
        #
        # Mise en place
        #
        sizer = wx.GridBagSizer()
        sizer.Add(label1, (0,0), (1,4), wx.ALIGN_LEFT|wx.ALL, border = 5)
        
        sizer.Add(label11, (1,1), (1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border = 5)
        sizer.Add(label12, (1,2), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
        sizer.Add(mplP,  (1,3), (1,2), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, border = 5)
        
        sizer.Add(wx.StaticLine(self, -1), (3, 0), (1,5), wx.EXPAND)
        
        sizer.Add(label2, (4,0), (1,4), wx.ALIGN_LEFT|wx.ALL, border = 5)
        
        sizer.Add(labelC, (6,0), (1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border = 5)
        sizer.Add(labelV, (8,0), (1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border = 5)
        sizer.Add(labelE, (11,0), (1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border = 5)
        
        for i, exe1, mpl1 in zip(range(len(exe)),exe, mpl):
            if exe1 != None:
                sizer.Add(exe1,  (6+i,1), (1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border = 5)
                sizer.Add(wx.StaticText(self, -1, "--->"),  (6+i,2), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
                sizer.Add(mpl1,  (6+i,3), (1,2), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, border = 5)
            else:
                sizer.Add(wx.StaticLine(self, -1), (6+i, 0), (1,5), wx.EXPAND)
#        sizer.Add(exeC,  (6,1), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
#        sizer.Add(exeV1, (7,1), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
#        sizer.Add(exeV2, (8,1), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
#        sizer.Add(exeE1, (9,1), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
#        sizer.Add(exeE2, (10,1), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
#        
#        sizer.Add(mplC,  (6,2), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
#        sizer.Add(mplV1, (7,2), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
#        sizer.Add(mplV2, (8,2), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
#        sizer.Add(mplE1, (9,2), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
#        sizer.Add(mplE2, (10,2), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
        
        sizer.Add(wx.StaticLine(self, -1), (13, 0), (1,5), wx.EXPAND)
        
        sizer.Add(bsizer, (14,0), (1,4), wx.EXPAND|wx.ALL, border = 5)
        
#        sizer.Add(label31, (15,1), (1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border = 5)
#        sizer.Add(label32, (15,2), (1,1), wx.ALIGN_CENTER|wx.ALL, border = 5)
#        sizer.Add(self.mplPe, (15,3), (1,2), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, border = 5)
        
        
        sizer.Add(btn,   (16,0), (1,4), wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 5)

        self.SetSizer(sizer)
        sizer.Fit(self)   
        
        
    def EvtText(self, event):
        poly = event.GetPoly()
        bmp = mathtext_to_wxbitmap(getMathTextPoly(poly, globdef.VAR_COMPLEXE))
        self.mplPe.SetBitmap(bmp)
        
        # On ajuste la taille au contenu (verticalement)
        self.Layout()
#        h = max(self.mplPe.GetSize()[1], self.bsizer.GetSize()[1])
#        self.SetSize((-1, h))
        self.Refresh()
        
        
        
        
#########################################################################################################
#########################################################################################################
#
#  Fonction de Transfert de Correcteur
#
#########################################################################################################  
#########################################################################################################

class FonctionTransfertCorrec:
    """ Classe définissant la fonction de transfert d'un correcteur
        type :
          "P"  : C(p) = K
          "PI" : C(p) = K (1+Tp)/(1+aTp))
          "PI2" : C(p) = K(1+Tp)/Tp
          "PD" : C(p) = K (1+aTp)/(1+Tp))
          "PD2" : C(p) = K (1+Tp)
          "PID" ! C(p) = K (1+aTp)/(1+Tp))... à faire !!
    """
    def __init__(self, type = "P"):
        self.classe = 0
        self.t = type
        
        # Gain statique
        self.K = [1.0]
        
        # Constante de temps
        self.T = [1.0]
        
        # Paramètre de "position"
        self.a = [2.0]
        
        # Les variables
        self.variables = {}
        
        # La fonction de transfert sous forme numérique (type calcul.FonctionTransfertNum)
        self.FTNum = []
        
        # La liste de sous fonctions de transfert (type calcul.FonctionTransfertNum)
        self.lstFTNum = []
        
        self.detDictVari()
        self.detLstFTNum()
        
    def __repr__(self):
        print ("   1+",self.T, globdef.VAR_COMPLEXE)
        print (self.K,"------------------   ")
        print ("   1+",self.T, globdef.VAR_COMPLEXE)
        return ""

    def getBranche(self, nom = ""):
        root = ET.Element("FT_C")

        param = ET.SubElement(root, "param")
        param.set("t", self.t)
        param.set("T", str(self.T))
        param.set("K", str(self.K))
        param.set("a", str(self.a))
        param.set("classe", str(self.classe))
        
        return root

    def ouvrir(self, branche):
        param = branche.find("param")
        self.t = param.get("t")
        self.T = eval(param.get("T"))
        self.K = eval(param.get("K"))
        self.a = eval(param.get("a"))
        self.classe = eval(param.get("classe"))
        
    def getPolyND(self):
        polyNumer = []
        polyDenom = []
        if self.t == "P":
#            print self.K
            for K in self.K:
                polyNumer.append(poly1d([K]))
                polyDenom.append(poly1d([1.0]))
        elif self.t == "PI":
            for K in self.K:
                for T in self.T:
                    for a in self.a:
                        polyNumer.append([K] * poly1d([T, 1.0]))
                        polyDenom.append(poly1d([T * a, 1.0]))
        elif self.t == "PI2":
            for K in self.K:
                for T in self.T:
                    polyNumer.append([K] * poly1d([T, 1.0]))
                    polyDenom.append(poly1d([T, 0.0]))
        elif self.t == "PD":
            for K in self.K:
                for T in self.T:
                    for a in self.a:
                        polyNumer.append([K] * poly1d([T * a, 1.0]))
                        polyDenom.append(poly1d([T, 1.0]))
        elif self.t == "PD2":
            for K in self.K:
                for T in self.T:
                    polyNumer.append([K] * poly1d([T, 1.0]))
                    polyDenom.append(poly1d([1.0]))
        return polyNumer, polyDenom

#    def getPolyND2(self):
#        if self.t == "P":
#            polyNumer = poly1d([self.K])
#            polyDenom = poly1d([1.0])
#        elif self.t == "PI":
#            polyNumer = [self.K] * poly1d([self.T, 1.0])
#            polyDenom = poly1d([self.T * self.a, 1.0])
#        elif self.t == "PI2":
#            polyNumer = [self.K] * poly1d([self.T, 1.0])
#            polyDenom = poly1d([self.T, 0.0])
#        elif self.t == "PD":
#            polyNumer = [self.K] * poly1d([self.T * self.a, 1.0])
#            polyDenom = poly1d([self.T, 1.0])
#        elif self.t == "PD2":
#            polyNumer = [self.K] * poly1d([self.T, 1.0])
#            polyDenom = poly1d([1.0])
#        return polyNumer, polyDenom
        
    def detFTNum(self):
        """ Determine la version numérique de la FT
                (avec les valeurs actuelles des variables)
        """
        self.FTNum = []
        polyNumer, polyDenom = self.getPolyND()
        i = 1
        for pN, pD in zip(polyNumer, polyDenom):
            self.FTNum.append(calcul.FonctionTransfertNum(pN.c, pD.c, nom = r"C_{"+str(i)+r"}"))
            i += 1
    
    def miseAJourCoef(self):
        self.K = self.variables[u'K'].v
        
        if self.t == "PI" or self.t == "PD":
            self.a = self.variables[u'a'].v
            self.T = self.variables[u'T'].v
        elif self.t == "PI2" or self.t == "PD2":
            self.T = self.variables[u'T'].v
    
    def detLstFTNum(self):
        """ Détermine la liste des sous FT 
        """
#        print "detLstFtNum :"
        self.miseAJourCoef()
        
        self.lstFTNum = []
        
#        polyNumer, polyDenom = self.getPolyND()
        
#        print type(self.K)
#        print type(polyNumer)
#        print type(polyDenom)
#        self.lstFTNum.append(calcul.FonctionTransfertNum(polyNumer.c, [1.0]))
#        self.lstFTNum.append(calcul.FonctionTransfertNum([1.0], polyDenom.c))
        
        self.detFTNum()
#        self.lstFTNum = self.FTNum.decomposition()
    
    
    def detDictVari(self):
        """ Etabli la liste des variables de la FT
          --> self.variables
        """
#        print "Determination des variables"
        
        self.variables = {}  
        self.variables[u'K'] = Variable(u'K', lstVal = self.K, typ = VAR_REEL_POS_STRICT, multiple = True)
        if self.t == "PI" or self.t == "PD":
            self.variables[u'a'] = Variable(u'a', lstVal = self.a, typ = VAR_REEL_SUPP1, multiple = True)
            self.variables[u'T'] = Variable(u'T', lstVal = self.T, typ = VAR_REEL_POS_STRICT, multiple = True)
        elif self.t == "PI2" or self.t == "PD2":
            self.variables[u'T'] = Variable(u'T', lstVal = self.T, typ = VAR_REEL_POS_STRICT, multiple = True)

    #########################################################################################################
    def getMathText(self):
        p = globdef.VAR_COMPLEXE
        Correcteurs = {"P" : r"K",
                       "PI" : r"K\frac{1+T"+p+"}{1+aT"+p+"}",
                       "PI2" : r"K\frac{1+T"+p+"}{T"+p+"}",
                       "PD" : r"K\frac{1+aT"+p+"}{1+T"+p+"}",
                       "PD2" : r"K(1+T"+p+")",
                       "PID" : r"K\frac{1+T"+p+"}{1+aT"+p+"}",
                       }
        return Correcteurs[self.t]
    
    
    #########################################################################################################
    def getBitmap(self, nom = None, taille = globdef.FONT_SIZE_FT_SELECT):
        if nom != None:
            n = nom+"("+globdef.VAR_COMPLEXE+")="
        return mathtext_to_wxbitmap(n+self.getMathText(), taille)
        
#        bmpK = mathtext_to_wxbitmap(r'K')
#        
#        if self.t == "PI":
#            bmpN = mathtext_to_wxbitmap(r'T+1')
#            bmpD = getBmpPoly([u'aT', 1.0])
#        elif self.t == "PI2":
#            bmpN = getBmpPoly([u'T', 1.0])
#            bmpD = getBmpPoly([u'T', 0.0])
#        elif self.t == "PD":
#            bmpN = getBmpPoly([u'aT', 1.0])
#            bmpD = getBmpPoly([u'T', 1.0])
#            
#        if self.t == "P":
#            bmp = bmpK 
#        else:
#            bmpR = getBmpRapportPoly(bmpN, bmpD)
#            bmp = getBmpProduitFT(bmpK, bmpR)
#        
#        return bmp
#    
    def getBitmapNum(self):
        return self.FTNum.getBitmap(nom = "", taille = globdef.FONT_SIZE_FT_SELECT)
    
#        bmpK = getBmpPoly([self.K])
#        
#        if self.t == "PI":
#            bmpN = getBmpPoly([self.T, 1.0])
#            bmpD = getBmpPoly([self.a*self.T, 1.0])
#        elif self.t == "PI2":
#            bmpN = getBmpPoly([self.T, 1.0])
#            bmpD = getBmpPoly([self.T, 0.0])
#        elif self.t == "PD":
#            bmpN = getBmpPoly([self.a*self.T, 1.0])
#            bmpD = getBmpPoly([self.T, 1.0])
#            
#        if self.t == "P":
#            bmp = bmpK 
#        else:
#            bmpR = getBmpRapportPoly(bmpN, bmpD)
#            bmp = getBmpProduitFT(bmpK, bmpR)
#        
#        return bmp

      
#########################################################################################################
#
#  Fonction de Transfert (sous forme factorisée)
#
#########################################################################################################  
class FonctionTransfertFact:
    def __init__(self, K = None, classe = None, lstPolyN = None, lstPolyD = None, 
                 retard = 0, classeNulle = False, multiple = False):
        
        # Gain statique
        if K == None: K = [1.0]
        self.K = K
        
        # Retard
        
        self.retard = retard
        self.multiple = multiple
        
        # Classe (entier !)
        if classe == None: classe = [0]
        self.classe = classe
        self.classeNulle = classeNulle
        
        # Les deux polynomes factorises
        # On est obligé de procéder ainsi depuis py26 car [] passe sous un même id à chaque instanciation d'une FT !!
        if lstPolyN == None:
            self.lstPolyN =[]
        else:
            self.lstPolyN = lstPolyN
        
        if lstPolyD == None:
            self.lstPolyD =[]
        else:
            self.lstPolyD = lstPolyD
            
        
        # Les variables
        self.variables = {}
        
        # La fonction de transfert sous forme numérique (type calcul.FonctionTransfertNum)
        self.FTNum = []
        
        # La liste de sous fonctions de transfert (type calcul.FonctionTransfertNum)
        self.lstFTNum = []
        
    ######################################################################################  
    def __repr__(self):
        print ("    ",self.lstPolyN)#, id(self.lstPolyN))
        print (self.K,"--------------------        classe =", self.classe, "r = ", self.retard)
        print ("    ",self.lstPolyD)#, id(self.lstPolyD))
        return ""


    ######################################################################################  
    def copie(self, FT = None):
        if FT == None:
            lstPolyN, lstPolyD = [], []
            for p in self.lstPolyN:
                lstPolyN.append(p.copie())
            for p in self.lstPolyD:
                lstPolyD.append(p.copie())
            return FonctionTransfertFact(self.K, self.classe, 
                                         lstPolyN, lstPolyD, self.retard, 
                                         self.classeNulle, self.multiple)
        else:
            lstPolyN, lstPolyD = [], []
            for p in FT.lstPolyN:
                lstPolyN.append(p.copie())
            for p in FT.lstPolyD:
                lstPolyD.append(p.copie())
            self.__init__(FT.K, FT.classe, lstPolyN, lstPolyD, FT.retard, 
                          FT.classeNulle, FT.multiple)
    
    ######################################################################################  
    def getBranche(self, nom = "FT_H"):
        root = ET.Element(nom)
        root.set("type_FT", "0")

        lstPolyN = ET.SubElement(root, "lstPolyN")
        for poly in self.lstPolyN:
            lstPolyN.append(poly.getBranche())
            
        lstPolyD = ET.SubElement(root, "lstPolyD")
        for poly in self.lstPolyD:
            lstPolyD.append(poly.getBranche())
        
        Gain_Classe = ET.SubElement(root, "Gain_Classe")
        Gain_Classe.set("gain", strList(self.K))
        Gain_Classe.set("classe", strList(self.classe))
        Gain_Classe.set("retard", str(self.retard))
        
        return root


    ######################################################################################  
    def ouvrir(self, branche):
#        print "Ouverture FTFact...",
        Gain_Classe = branche.find("Gain_Classe")
        self.K = listStr(Gain_Classe.get("gain"))
        self.classe = listStr(Gain_Classe.get("classe"))
        try:
            self.retard = eval(Gain_Classe.get("retard"))
        except:
            self.retard = 0
        if self.retard == None:
            self.retard = 0
        self.lstPolyN, self.lstPolyD = [], []
        
        lstPolyN = branche.find("lstPolyN")
        for p1 in lstPolyN.findall("poly1"):
            p = poly1()
            p.ouvrir(p1)
            self.lstPolyN.append(p)
        
        for p2 in lstPolyN.findall("poly2"):
            p = poly2()
            p.ouvrir(p2)
            self.lstPolyN.append(p)
#            print "Poly2 :", p.id, p.Om, p.z
            
        lstPolyD = branche.find("lstPolyD")
        for p1 in lstPolyD.findall("poly1"):
            p = poly1()
            p.ouvrir(p1)
            self.lstPolyD.append(p)
        
        for p2 in lstPolyD.findall("poly2"):
            p = poly2()
            p.ouvrir(p2)
            self.lstPolyD.append(p)
#            print "Poly2 :", p.id, p.Om, p.z
#            print p
            
#        print "Ok"
            
        
    def __mul__(self, FT):
        if isinstance(FT, FonctionTransfertFact):
            nFT = FonctionTransfertFact(FT.K*self.K, self.classe + FT.classe, 
                                        self.lstPolyN + FT.lstPolyN,
                                        self.lstPolyD + FT.lstPolyD,
                                        retard = self.retard + FT.retard)
        elif isinstance(FT, FonctionTransfertCorrec):
            polyN, polyD = FT.getPolyND()
            nFT = FonctionTransfertFact(FT.K*self.K, self.classe + FT.classe, 
                                        self.lstPolyN + [polyN],
                                        self.lstPolyD + [polyD],
                                        retard = self.retard + FT.retard)
        return nFT
    
    def getOrdre(self):
        o = 0
#        print "getOrdre", self.lstPolyD
        for p in self.lstPolyD:
            if isinstance(p, poly1):
                o += 1
            else:
                o += 2
        return o
    
    
    def getLambda(self):
        if self.classe > 0:
            return 2.3
        else:
            return calcul.roundN(20*scipy.log10(1.3*self.K/(self.K+1)))[0]
        
    
    
    def detFTNum(self):
        """ Determine la version numérique de la FT
                (avec les valeurs actuelles des variables)
        """
        
        
#        print "Determination de FTNum"
#        print self
        
        if self.lstPolyN == []:
            lstPolyN = [None]
        else:
            lstPolyN = self.lstPolyN
            
        if self.lstPolyD == []:
            lstPolyD = [None]
        else:
            lstPolyD = self.lstPolyD
#        print "   ",self.classe
#        print "   ",self.K
#        print "   ",self.lstPolyN+[None]
#        print "   ",self.lstPolyD+[None]
        self.FTNum = []
        
        def mult(lst1, lst2):
            lst = []
            for P1 in lst1:
                for p2 in lst2:
                    P2 = poly1d(p2)
                    lst.append(P1*P2)
            return lst
        
        def getLstPoly(lstPoly):
            if lstPoly[0] == None:
                lst = [[1.0]]
            else:
                lst = lstPoly[0].getPolyNum()
            
            lstP = []
            for p1 in lst:
                P1 = poly1d(p1)
                lstP.append(P1)
                
            i = 1
            while i < len(lstPoly):
                lstP = mult(lstP, lstPoly[i].getPolyNum())
                i += 1
            
            return lstP
        
        
        
        for classe in self.classe:
            for K in self.K:
                c = int(abs(classe)+1)*[0.0]
                if classe >=0:
                    c[0] = 1.0
                    polyNum0 = poly1d([K])
                    polyDen0 = poly1d(c)
                else:
                    c[0] = K
                    polyNum0 = poly1d(c)
                    polyDen0 = poly1d([1.0])
                 
                for polyN in getLstPoly(lstPolyN):
                    for polyD in getLstPoly(lstPolyD):
                        pN = polyNum0*polyN
                        pD = polyDen0*polyD
                        self.FTNum.append(calcul.FonctionTransfertNum(pN.c, pD.c, retard = self.retard))
                 
#                for polyN in lstPolyN:
#                    if polyN == None:
#                        lstPN = [[1.0]]
#                    else:
#                        lstPN = polyN.getPolyNum()
#                        
#                    polyNumer = poly1d([1.0])
#                    for polyNNum in lstPN:
#                        polyNumer = polyNumer * poly1d(polyNNum)
#                    
#                        for polyD in lstPolyD:
#                            if polyD == None:
#                                lstPD = [[1.0]]
#                            else:
#                                lstPD = polyD.getPolyNum()
#                                
#                            polyDenom = poly1d([1.0])
#                            for polyDNum in lstPD:
#                                polyDenom = polyDenom * poly1d(polyDNum)
#            
#                                pN = polyNum0*polyNumer
#                                pD = polyDen0*polyDenom
#                                self.FTNum.append(calcul.FonctionTransfertNum(pN.c, pD.c, retard = self.retard))
#        print self.FTNum
            
            
    def miseAJourCoef(self):
        
        self.K = self.variables[r'K'].v
        if not self.classeNulle:
            self.classe = self.variables[r'\alpha'].v
        
        if r'\tau' in self.variables.keys():
            self.retard = self.variables[r'\tau'].v[0]
        else:
            self.retard = 0
        
        for poly in self.lstPolyN + self.lstPolyD:
            if isinstance(poly, poly1):
                poly.T = self.variables[poly.getNomVariables()[0]].v
            elif isinstance(poly, poly2):
                poly.Om = self.variables[poly.getNomVariables()[0]].v
                poly.z = self.variables[poly.getNomVariables()[1]].v
    
    
    def detLstFTNum(self):
        """ Détermine la liste des sous FT 
        """
#        print "detLstFtNum :"
#        print self
        self.miseAJourCoef()
        
        c = int(abs(self.classe[0])+1)*[0.0]
        
        if self.classe[0] >= 0:
            c[0] = 1.0
            if self.classe[0] == 0 and self.K[0] == 1.0:
                if len(self.lstPolyN) + len(self.lstPolyD) != 0:
                    self.lstFTNum = []
                else:
                    self.lstFTNum = [calcul.FonctionTransfertNum([1.0], [1.0])]
            else:
                self.lstFTNum = [calcul.FonctionTransfertNum([self.K[0]], c)]
        else:
            c[0] = self.K[0]
            self.lstFTNum = [calcul.FonctionTransfertNum(c, [1.0])]
        
        
#        def getPolyNum(lstPoly):
#            for poly in lstPoly:
#                p = p*poly1d(poly.getPolyNum()[0])
#            return p
        
        
        for p in self.lstPolyN:
            if isinstance(p, poly2) and globdef.DECOMP_2ND_ORDRE:
                for _p in p.getDecomposition():
                    self.lstFTNum.append(calcul.FonctionTransfertNum(_p, [1.0]))
            else:
                self.lstFTNum.append(calcul.FonctionTransfertNum(p.getPolyNum()[0], [1.0]))
        
        for p in self.lstPolyD:
            if isinstance(p, poly2) and globdef.DECOMP_2ND_ORDRE:
                for _p in p.getDecomposition(): # _p sous forme liste
                    self.lstFTNum.append(calcul.FonctionTransfertNum([1.0], _p))
            else:
                self.lstFTNum.append(calcul.FonctionTransfertNum([1.0], p.getPolyNum()[0]))
        
        if self.retard != 0:
            self.lstFTNum.append(calcul.FonctionTransfertNum(retard = self.retard))
        
        self.detFTNum()
#        self.lstFTNum = self.FTNum.decomposition()
    
    
    ######################################################################################
    def restoreIncidesVariables(self):
        for p in self.lstPolyN + self.lstPolyD:
            if isinstance(p, poly1):
                o = 1
            elif isinstance(p, poly2):
                o = 2
            p.id = self.genId(o)
        return
    
    
    ######################################################################################
    def genId(self, o):
        lstId = []

        for p in self.lstPolyN + self.lstPolyD:
            if (o == 1 and isinstance(p, poly1)) \
            or (o == 2 and isinstance(p, poly2)):
                lstId.append(p.id)
        
        id = 1
        while id in lstId:
            id += 1

        return id
    
    
    ######################################################################################
    def detDictVari(self, retard = True):
        """ Etabli la liste des variables de la FT
          --> self.variables
        """
#        print "Determination des variables"
        
        
        def getDictVariPoly(lstPoly):
#            polyNum = self.separerConstVari(poly)
            for p in lstPoly:
                self.variables.update(p.getVariables(multiple = self.multiple))
        
        self.variables = {}  
        self.variables[r'K'] = Variable(r'K', nomNorm = _("du gain statique"),
                                        lstVal = self.K, typ = VAR_REEL_POS_STRICT,
                                        multiple = self.multiple)
        if not self.classeNulle:
            self.variables[r'\alpha'] = Variable(r'\alpha', nomNorm = _("de la classe"),
                                                 lstVal = self.classe, typ = VAR_ENTIER,
                                                 multiple = self.multiple)
        
        if globdef.DEPHASAGE and retard:
            self.variables[r'\tau'] = Variable(r'\tau', nomNorm = _("du retard"),
                                               lstVal = [self.retard],  typ = VAR_REEL_POS,
                                               modeLog = False,
                                               multiple = self.multiple)
        
        getDictVariPoly(self.lstPolyN)
        getDictVariPoly(self.lstPolyD)
        
    def getDiagAsymp(self):
        return
#        print "-->",self.variables
#        return self.variables

    def developper(self):
        def getPolyDev(lstPoly):
            pn = poly1d([1.0])
            for p in lstPoly:
                pn = pn * poly1d(p.getPolyNum()[0])
            return pn
                
        polyN = getPolyDev(self.lstPolyN) * [self.K[0]]
        polyD = getPolyDev(self.lstPolyD)
#        print polyN
#        print "  ", polyD
        c = int(abs(self.classe[0])+1)*[0.0]
        c[0] = 1.0
        if self.classe[0] > 0:
            polyD = polyD * poly1d(c)
        else:
            polyN = polyN * poly1d(c)
#        print "..."
#        print polyN
#        print "  ", polyD
        return FonctionTransfertDev(polyN.c.tolist(), polyD.c.tolist(), retard = self.retard)
    
    #########################################################################################################
    def getMathText(self, nom = None, retard = True):
        """ Renvoie l'expression de la FT sous forme MathText
        """
        
        #
        # Nom de la fonction
        #
        if nom != None:
            n = nom+r"("+globdef.VAR_COMPLEXE+") = "
        else:
            n = r""
            
        
        if globdef.DEPHASAGE and retard:
            r = r"e^{-\tau "+globdef.VAR_COMPLEXE+"}"
        else:
            r = r""
            
        def getProduitPolyN(lstp):
            s = r''
            if len(lstp) > 1:
                for p in lstp:
                    s += r"\left("+p.getMathText()+r"\right)"
                return s
            elif len(lstp) == 1:
                return lstp[0].getMathText()
            else:
                return r"1"
        
        #
        # Gain statique et classe
        #
        if not self.classeNulle:
            g = r"\frac{K}{"+globdef.VAR_COMPLEXE+r"^\alpha}"
            mult = globdef.SYMBOLE_MULT
        else:
            g = r""
            mult = r""
        
        #
        # Quotien des polynômes
        #
        if self.lstPolyD == []:
            if self.lstPolyN == []:
                q = ""
            else:
                q = getProduitPolyN(self.lstPolyN)
                if len(self.lstPolyN) == 1 and len(self.lstPolyD) == 0:
                    q = r"\left(" + q + r"\right)"
                q = mult + q
        else:
            if not self.classeNulle:
                q = mult + r"\frac{"+getProduitPolyN(self.lstPolyN)+"}{"+getProduitPolyN(self.lstPolyD)+"}"
            else:
                q = mult + r"\frac{K}{"+getProduitPolyN(self.lstPolyD)+"}"
        return n + r + g + q
    
    
    #########################################################################################################
    def getBitmap(self, nom = None, taille = globdef.FONT_SIZE_FT_SELECT, retard = True):
        return mathtext_to_wxbitmap(self.getMathText(nom, retard), taille = taille)

    
    #########################################################################################################
    def getComplexite(self):
        """ Renvoie le niveau de "compléxité" de la FT
            (le nombre maximum de sous fonctions de transfert 
             qu'elle est succeptible d'avoir)
        """
        n = 0
        if self.classe != 0:
            n += 1
            
        for p in self.lstPolyN+self.lstPolyD:
            if isinstance(p, poly1):
                n += 1
            else:
                n += 2
        n += 1 # Pour la classe
        if globdef.DEPHASAGE: # Pour la fonction retard
            n += 1
        return n
    
#########################################################################################################
class SelecteurPolynomeFact(wx.Panel):
    def __init__(self, parent, id, lstPoly):
        wx.Panel.__init__(self, parent, id)
        self.lstPoly = lstPoly
        
        
        self.SetAutoLayout(True)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
#        self.txt = wx.StaticText(self, -1, self.lstPolyToTxt(lstPoly))
        if id == 10:
            nd = _("numérateur")
        else:
            nd = _("dénominateur")
            
        im1 = Images.Bouton_Select1er.GetBitmap()
        im2 = Images.Bouton_Select2nd.GetBitmap()
        imE = Images.Bouton_SelectEff.GetBitmap()
        
        b1 = wx.BitmapButton(self, 11, im1)
        b2 = wx.BitmapButton(self, 12, im2)
        bE = wx.BitmapButton(self, 13, imE)
        
#        SetSuperToolTip(b1, _("Ajouter un polynôme d'ordre 1 au ")+nd)
        b1.SetToolTipString(_("Ajouter un polynôme d'ordre 1 au ")+nd)
        b2.SetToolTipString(_("Ajouter un polynôme d'ordre 2 au ")+nd)
        bE.SetToolTipString(_("Supprimer le dernier polynôme ajouté au ")+nd)
        
        self.Bind(wx.EVT_BUTTON, self.OnSpinUp, b1)
        self.Bind(wx.EVT_BUTTON, self.OnSpinUp, b2)
        self.Bind(wx.EVT_BUTTON, self.OnSpinDown, bE)
        
#        sizer.Add(self.txt, wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
        sizer.Add(b1, flag = wx.LEFT|wx.RIGHT|wx.TOP, border = 2 )
        sizer.Add(b2, flag = wx.LEFT|wx.RIGHT|wx.TOP, border = 2 )
        sizer.Add(bE, flag = wx.LEFT|wx.RIGHT|wx.TOP, border = 2 )
        
        self.SetSizerAndFit(sizer)
        
    
    def OnSpinUp( self, event ):
        deg = event.GetId() - 10
        id = self.Parent.genId(deg)
        if deg == 1:
            self.lstPoly.append(poly1(id))
        else:
            self.lstPoly.append(poly2(id))
        self.modifier()
        
    def OnSpinDown( self, event ):
        if len(self.lstPoly) > 0:
            self.lstPoly.pop()
            self.modifier()
    
    def modifier(self):
#        print "Poly modifié :", self.lstPoly
        self.Parent.OnPolyModified(self.lstPoly)
        
##########################################################################################################
#class FTFactPanel(wx.ScrolledWindow):
#    def __init__(self, parent, FT):
#        wx.ScrolledWindow.__init__(self, parent, -1, style = wx.BORDER_SIMPLE | wx.HSCROLL)
#        
#        self.parent = parent
#        
#        sizer = wx.BoxSizer(wx.HORIZONTAL)
#        
#        txt = wx.StaticText(self, -1, "H("+globdef.VAR_COMPLEXE+") = ")
#        sizer.Add(txt, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
#        self.lH, self.hH = txt.GetSize()
#        
#        self.sb = wx.StaticBitmap(self, -1, getBmpFT(FT))#[[u'K'],[u'p*']])
#        sizer.Add(self.sb, flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND)
#        
#        self.SetSizer(sizer)
#        
#        self.AdjustSize()
#    
#    def AdjustSize(self):
#        lS, hS = self.sb.GetSize()
##        print "Size FTFactPanel :",lS+self.lH, max(hS, self.hH) ,
#        self.SetVirtualSize((lS+self.lH, max(hS, self.hH)))
##        print self.GetVirtualSize()
#        
#    def MiseAJourBmp(self, FT):
#        self.sb.SetBitmap(getBmpFT(FT))
#        self.AdjustSize()
#        self.FitInside()
#        self.Refresh()
        
        
#########################################################################################################
class SelecteurFTFact(wx.Panel):
    """ Panel contenant l'expression canonique de la FT
        (sous forme factorisée canonique)
        et les boutons pour ajouter/enveler des polynômes
    """
    def __init__(self, parent, FT, nom = "H", retard = True):
        wx.Panel.__init__(self, parent, -1)#, style = wx.BORDER_SIMPLE)
        
        self.FT = FT
        self.retard = retard
        
#        print "selecteurFT Fact"
#        print self.FT
        self.nom = nom
        
#        print "Selecteur FT Fact:",self.FT
#        print " N :",self.FT.polyN
#        print " D :",self.FT.polyD
        self.SetAutoLayout(True)
        
        
        #
        # L'image de l'expression canonique
        #
        self.sb = ScrolledBitmap(self, -1)
        self.sb.SetBitmap(FT.getBitmap(self.nom, retard = self.retard), self.GetBmpHD, self.GetTeX)
        self.sb.SetToolTipString(_("Forme canonique de la Fonction de Transfert"))
        
        
        #
        # Les boutons d'ajout/enlèvement de polynômes
        #
        sizerCtrl = wx.BoxSizer(wx.VERTICAL)
        sN = SelecteurPolynomeFact(self, 10, self.FT.lstPolyN)
        sD = SelecteurPolynomeFact(self, 11, self.FT.lstPolyD)
        sizerCtrl.Add(sN, flag = wx.ALIGN_CENTER)
        sizerCtrl.Add(sD, flag = wx.ALIGN_CENTER)
        self.sN = sN
        self.sD = sD
        self.sizerCtrl = sizerCtrl
        
        #
        # Mise en place
        #
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sb, 1, flag = wx.ALIGN_LEFT | wx.EXPAND)
        sizer.Add(sizerCtrl, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
        self.SetSizer(sizer)
        self.sizer = sizer

    ######################################################################################################    
    def MiseAJourBmp(self):
        """ Modifie l'expression factorisée de la FT
            quand on a ajouté/supprimé un polynôme
        """
        # On modifie l'image
        self.sb.SetBitmap(self.FT.getBitmap(self.nom, retard = self.retard), 
                          self.GetBmpHD, self.GetTeX)
        
        # On ajuste la taille au contenu (verticalement)
        self.Layout()
        h = max(self.sb.GetSize()[1], self.sizerCtrl.GetSize()[1])
        self.SetSize((-1, h))
        
    def GetBmpHD(self):
        return self.FT.getBitmap(self.nom, globdef.FONT_SIZE_FT_HD, retard = self.retard)

    def GetTeX(self):
        return self.FT.getMathText(self.nom)

    ######################################################################################################    
    def initFTSimple(self, FT):
        self.FT = FT
        self.sN.lstPoly = self.FT.lstPolyN
        self.sD.lstPoly = self.FT.lstPolyD
        self.MiseAJourBmp()
        self.FT.detDictVari(self.retard)
        self.FT.detLstFTNum()
    
    
    ######################################################################################################    
    def initFT(self, FT, redessiner = True):
#        print "initFT"
        self.FT = FT
        self.sN.lstPoly = self.FT.lstPolyN
        self.sD.lstPoly = self.FT.lstPolyD
        self.OnPolyModified(redessiner = redessiner)
        
        
    ######################################################################################################    
    def OnPolyModified(self, lst = None, redessiner = True):
#        print "OnPolyModified"
#        print self.FT
        if self.FT.getComplexite() > globdef.NBR_MAXI_PLOT:
            if lst != None: 
                del lst[-1]
            dlg = wx.MessageDialog(self.Parent, msgFTtropComplexe, 
                                   "FT trop complexe", 
                                   wx.OK | wx.ICON_ERROR
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        self.MiseAJourBmp()
        self.FT.detDictVari(self.retard)
        self.FT.detLstFTNum()
        
        if redessiner:
            self.Parent.OnFTModified()
        
    
    ######################################################################################################    
    def lstPolyToTxt(self, lstPoly):
        s = ""
        for p in lstPoly:
            s += p.getPolyTxt()
        return s
    
    ######################################################################################################    
    def genId(self, o):
        """ Renvoie le premier ID disponible
            (pour les indices des variables)
        """
        return self.FT.genId(o)
#        lstId = []
#
#        for p in self.FT.lstPolyN + self.FT.lstPolyD:
#            if (o == 1 and isinstance(p, poly1)) \
#            or (o == 2 and isinstance(p, poly2)):
#                lstId.append(p.id)
#                
##        print "ListeId",o,"=",lstId
#        
#        id = 1
#        while id in lstId:
#            id += 1
#
#        return id
                
                

#########################################################################################################
class poly1:
    def __init__(self, id = -1, T = None):
        self.id = id
        # Constante de temps
        if T == None:
            T = [1.0]
        self.T = T
        
    def copie(self):
        return poly1(self.id, self.T.copy())
    
    def getBranche(self):
        root = ET.Element("poly1")
        param = ET.SubElement(root, "param")
        param.set("id", str(self.id))
        param.set("T", strList(self.T))
        return root

    def ouvrir(self, branche):
        param = branche.find("param")
        self.id = eval(param.get("id"))
        self.T = listStr(param.get("T"))
    
    def getStrId(self): 
        if self.id == -1:
            return ""
        else:
            return str(self.id)
    
    def __repr__(self):
        return "("+strSc(self.getPolyNum()[0][0])+"p+1)"
    
    def getPolyTxt(self):
        return "("+self.getPoly()[0]+"+1)"
#    
    def getPoly(self):
        return [u'T'+self.getStrId(), 1.0]
    
    def getPolyNum(self):
        lst = []
        for T in self.T:
            lst.append([T, 1.0])
        return lst
    
    def getVariables(self, multiple = False):
        return {self.getNomVariables()[0] : Variable(self.getNomVariables()[0], 
                                                     lstVal = self.T, typ = VAR_REEL_POS_STRICT, 
                                                     multiple = multiple)}
    
    def getNomVariables(self):
        return [r'T_{'+self.getStrId()+'}']
    
#    def getNomVariables(self):
#        return ['T'+self.getStrId()]
        
#    def getFancy(self):
#        return "T"+FancyIndice(self.getStrId())+globdef.VAR_COMPLEXE+"+1"

    def getMathText(self):
        return r"1+T_{"+self.getStrId()+"} "+globdef.VAR_COMPLEXE
                
#    def getBmpId(self):
#        return getBmpFancy(self.getFancy())

##########################################################################################################
class poly2:
    def __init__(self, id = -1, Om = None, z = None):
        self.id = id
        # Pulsation propre
        if Om == None:
            Om = [1.0]
        self.Om = Om
        # Coefficient d'amortissement
        if z == None:
            z = [1.0]
        self.z = z
    
    def copie(self):
        return poly2(self.id, self.Om.copy(), self.z.copy())
    
    def getBranche(self):
        root = ET.Element("poly2")
        param = ET.SubElement(root, "param")
        param.set("id", str(self.id))
        param.set("Om", strList(self.Om))
        param.set("z", strList(self.z))
        return root

    def ouvrir(self, branche):
        param = branche.find("param")
        self.id = eval(param.get("id"))
        self.Om = listStr(param.get("Om"))
        self.z = listStr(param.get("z"))
#        print "Poly2 :", self.id, self.Om, self.z
        
    def getStrId(self): 
        if self.id == -1:
            return ""
        else:
            return str(self.id)
    
    def __repr__(self):
        p = self.getPolyNum()[0]
        return "("+strSc(p[0])+"p²+"+strSc(p[1])+"p+1)"
    
    def getPoly(self):
        i = self.getStrId()
        return [u'1/w'+i+u'2', u'2z'+i+u'/w'+i, 1.0]

    def getPolyNum(self):
        lst = []
        for Om in self.Om:
            for z in self.z:
                lst.append([1.0/Om**2, 2.0*z/Om, 1.0])
        return lst
    
    def getVariables(self, multiple = False):
        return {self.getNomVariables()[0] : Variable(self.getNomVariables()[0], 
                                                     lstVal = self.Om, typ = VAR_REEL_POS_STRICT, 
                                                     multiple = multiple),
                self.getNomVariables()[1] : Variable(self.getNomVariables()[1], 
                                                     lstVal = self.z, typ = VAR_REEL_POS_STRICT, 
                                                     multiple = multiple)}

    def getNomVariables(self):
        return [r'\omega_{'+self.getStrId()+'}',
                r'z_{'+self.getStrId()+'}']

#    def getNomVariables(self):
#        return ['omega'+self.getStrId(),
#                'z'+self.getStrId()]
#    def getFancy(self):
#        globdef.VAR_COMPLEXE+"<sup>2</sup>/u\u03C9"+self.id+"<sup>2</sup>+2z//u\03C9"+FancyIndice(self.id)+"+1"

    def getMathText(self):
        id = r'{'+self.getStrId()+'}'
        p = globdef.VAR_COMPLEXE
        return r"\frac{"+p+"^2}{\omega_"+id+"^2}" \
                r"+\frac{2z_"+id+"}{\omega_"+id+"}"+p+"+1"
    
    
    def getDecomposition(self):
        """ Décompose le polynôme du 2nd ordre en deux polynômes d'ordre 1
            (si possible !)
            Pas de prise en compte des variables multiples !
        """
        # Polynôme sous la forme d'une liste
        p = self.getPolyNum()[0]
        
        # Recherche des racines
        pn = poly1d(p)
        if abs(imag(pn.r[0])) < globdef.EPSILON: # Racines réelles
            return [[-1.0/real(pn.r[0]), 1.0] , [-1.0/real(pn.r[1]), 1.0]]
        else:
            return [p]



