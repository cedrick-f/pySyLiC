#!/usr/bin/env python
# -*- coding: utf-8 -*-

##This file is part of PySyLic
#############################################################################
#############################################################################
##                                                                         ##
##                                   Options                               ##
##                                                                         ##
#############################################################################
#############################################################################

## Copyright (C) 2009-2025 Cédrick FAURY

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


import json
import configparser
import os.path
#import wx

import globdef
from CedWidgets import changeEchelle, VariableCtrl, Variable, VAR_ENTIER_POS, EVT_VAR_CTRL
from LineFormat import LineFormat, SelecteurFormatLigne, EVT_FORMAT_MODIFIED
import wx
import Images

##############################################################################
#      Options     #
##############################################################################
class OptionsEncoder(json.JSONEncoder):
        def default(self, o):
            if hasattr(o, 'toJSON'):
                return o.toJSON()
            return o.__dict__

class Options:
    """ Définit les options de PySyLic """
    def __init__(self, options = None):
        #
        # Toutes les options ...
        # Avec leurs valeurs par défaut.
        #
        # self.optAffichage = {}
        # self.optCouleurs = {}
        # self.optGenerales = {}
        # self.optImpression = {}
        # self.optCalcul = {}
        
        
          
#        self.listeOptions = ["Général", "Affichage", "Couleurs", "Impression"] 
         
        self.typesOptions = {"Général" : {},
                             "Affichage" : {},
                             "Calcul" : {},
                             "Formats de ligne" : {},
                             "Impression" : {},
                             }
        
        if options == None:
            self.defaut()


        # Le fichier où seront sauvées les options
        self.fichierOpt = os.path.join(globdef.APP_DATA_PATH, "PySyLiC.cfg")

    #########################################################################################################
    def __repr__(self):
        t = "Options :\n"
        for o in self.typesOptions['Général'].items() + self.typesOptions['Affichage'].items() + self.typesOptions['Impression'].items() + self.typesOptions['Formats de ligne'].items():
            if type(o[1]) == int or type(o[1]) == float:
                tt = str(o[1])
            elif type(o[1]) == bool:
                tt = str(o[1])
            else:
                tt = o[1]
            t += "\t" + o[0] + " = " + tt +"\n"
        return t
    
    
    #########################################################################################################
    def fichierExiste(self):
        """ Vérifie si le fichier 'options' existe
        """
#        PATH=os.path.dirname(os.path.abspath(sys.argv[0]))
#        os.chdir(globdef.PATH)
        if os.path.isfile(self.fichierOpt):
            return True
        return False


    #########################################################################################################
    def enregistrer(self):
        """" Enregistre les options dans un fichier
        """
        config = json.dumps(self.typesOptions, 
                            #default=lambda o: o.toJSON, 
                            cls = OptionsEncoder,
                            sort_keys=True, 
                            indent=4, 
                            ensure_ascii=False)
        with open(self.fichierOpt,'w', encoding="utf-8") as f:
            f.write(config)
        return




        # config = configparser.ConfigParser()

        # for titre, dicopt in self.typesOptions.items():
        #     config.add_section(titre)
        #     for opt in dicopt.items():
        #         if isinstance(opt[1], LineFormat):
        #             opt[1].writeConfig(config, titre, opt[0])
        #         else:
        #             config.set(titre, opt[0], str(opt[1]))
            
            
#        config.add_section('Options generales')
#       
#        config.add_section('Options analyse')
#        config.set('Options analyse', 'animMont', self.proposerAnimMont.get())
#        config.set('Options analyse', 'animArret', self.proposerAnimArret.get())
#        config.set('Options analyse', 'traceChaines', self.proposerChaines.get())
#
#        config.add_section('Options aide')
#        config.set('Options aide', 'type', self.typeAide.get())
#
#        config.add_section('Dossiers')
#        config.set('Dossiers', 'repcourant', self.repertoireCourant.get())
        
        # config.write(open(self.fichierOpt,'w'))



    ############################################################################
    def ouvrir(self):
        """ Ouvre un fichier d'options 
        """
        print("ouverture :",self.fichierOpt)
        with open(self.fichierOpt,'r', encoding="utf-8") as f:
            config = f.read()
        self.typesOptions = json.loads(config)

        self.typesOptions['Formats de ligne']["FORM_GRILLE"] = LineFormat(**self.typesOptions['Formats de ligne']["FORM_GRILLE"])
        self.typesOptions['Formats de ligne']["FORM_ISOGAIN"] = LineFormat(**self.typesOptions['Formats de ligne']["FORM_ISOGAIN"])
        self.typesOptions['Formats de ligne']["FORM_ISOPHASE"] = LineFormat(**self.typesOptions['Formats de ligne']["FORM_ISOPHASE"])

        return




        # config = configparser.ConfigParser()
        # config.read(self.fichierOpt)
        # print("ouverture :",self.fichierOpt)
        # for titre in self.typesOptions:
        #     titreUtf = titre.encode('utf-8')
        #     for titreopt in self.typesOptions[titre]:
        #         opt = self.typesOptions[titre][titreopt] 
                
        #         if type(opt) == int:
        #             opt = config.getint(titreUtf, titreopt)
        #         elif type(opt) == float:
        #             opt = config.getfloat(titreUtf, titreopt)
        #         elif type(opt) == bool:
        #             opt = config.getboolean(titreUtf, titreopt)
        #         elif type(opt) == str or type(opt) == unicode:
        #             opt = config.get(titreUtf, titreopt)
        #         elif isinstance(opt, wx._gdi.Colour):
        #             v = eval(config.get(titreUtf, titreopt))
        #             opt = wx.Colour(v[0], v[1], v[2], v[3])
        #         elif isinstance(opt, LineFormat):
        #             opt.readConfig(config, titreUtf, titreopt)
                    
                
        #         # pour un passage correct de la version 2.5 à 2.6
        #         try:
        #             v = eval(opt)
        #             if type(v) == tuple:
        #                 opt = wx.Colour(v[0], v[1], v[2]).GetAsString(wx.C2S_HTML_SYNTAX)

        #         except:
        #             pass
                
        #         self.typesOptions[titre][titreopt] = opt
                
                
        


    ############################################################################
    def copie(self):
        """ Retourne une copie des options """
        options = Options()
        for titre,dicopt in self.typesOptions.items():
            titre.encode('utf-8')
            nopt = {}
            for opt in dicopt.items():
                options.typesOptions[titre][opt[0]] = opt[1]
#                nopt[opt[0]] = opt[1]
#            options.typesOptions[titre] = (options.typesOptions[titre][0], nopt)
        return options


        
    ############################################################################
    def defaut(self):
        globdef.DefOptionsDefaut()
        
        self.typesOptions['Général']["TypeSelecteur"] = globdef.SELECTEUR_FT
        self.typesOptions['Général']["RepCourant"] = globdef.DOSSIER_EXEMPLES
        self.typesOptions['Général']["VAR_COMPLEXE"] = globdef.VAR_COMPLEXE
        self.typesOptions['Général']["MAJ_AUTO"] = globdef.MAJ_AUTO
        self.typesOptions['Général']["DEPHASAGE"] = globdef.DEPHASAGE
        self.typesOptions['Général']["NBR_MAXI_PLOT"] = globdef.NBR_MAXI_PLOT
        self.typesOptions['Général']["LANG"] = globdef.LANG
        
        self.typesOptions['Affichage']["ANTIALIASED"] = globdef.ANTIALIASED
        self.typesOptions['Affichage']["TRACER_FLECHE"] = globdef.TRACER_FLECHE   
        self.typesOptions['Affichage']["FONT_TYPE"] = globdef.FONT_TYPE     
        
        self.typesOptions['Calcul']["NB_PERIODES_REP_TEMPO"] = globdef.NB_PERIODES_REP_TEMPO
        self.typesOptions['Calcul']["TEMPS_REPONSE"] = globdef.TEMPS_REPONSE
        self.typesOptions['Calcul']["NBR_PTS_REPONSE"] = globdef.NBR_PTS_REPONSE
        
        self.typesOptions['Formats de ligne']["COUL_MARGE_OK"] = globdef.COUL_MARGE_GAIN_OK
        self.typesOptions['Formats de ligne']["COUL_MARGE_NO"] = globdef.COUL_MARGE_GAIN_NO
#        print globdef.FORM_GRILLE
        self.typesOptions['Formats de ligne']["FORM_GRILLE"] = globdef.FORM_GRILLE
        self.typesOptions['Formats de ligne']["FORM_ISOGAIN"] = globdef.FORM_ISOGAIN
        self.typesOptions['Formats de ligne']["FORM_ISOPHASE"] = globdef.FORM_ISOPHASE
#        self.typesOptions['Formats de ligne']["COUL_LAMBDA"] = globdef.COUL_LAMBDA
        self.typesOptions['Formats de ligne']["COUL_POLES"] = globdef.COUL_POLES
        self.typesOptions['Formats de ligne']["COUL_PT_CRITIQUE"] = globdef.COUL_PT_CRITIQUE
        self.typesOptions['Formats de ligne']["COUL_CONSIGNE"] = globdef.COUL_CONSIGNE
        self.typesOptions['Formats de ligne']["COUL_REPONSE"] = globdef.COUL_REPONSE
        self.typesOptions['Formats de ligne']["COUL_REPONSENC"] = globdef.COUL_REPONSENC                    
 
        
                            
        
        self.typesOptions['Impression']["PRINT_PROPORTION"] = globdef.PRINT_PROPORTION
        self.typesOptions['Impression']["IMPRIMER_NOM"] = globdef.IMPRIMER_NOM
        self.typesOptions['Impression']["POSITION_NOM"] = globdef.POSITION_NOM
        self.typesOptions['Impression']["TEXTE_NOM"] = globdef.TEXTE_NOM
        self.typesOptions['Impression']["IMPRIMER_TITRE"] = globdef.IMPRIMER_TITRE
        self.typesOptions['Impression']["POSITION_TITRE"] = globdef.POSITION_TITRE
        self.typesOptions['Impression']["TEXTE_TITRE"] = globdef.TEXTE_TITRE
        self.typesOptions['Impression']["MAX_PRINTER_DPI"] = globdef.MAX_PRINTER_DPI
                              
                              
                              
#        self.proposerAnimMont.set(1)
#        self.proposerAnimArret.set(1)
#        self.proposerChaines.set(1)
#        self.typeAide.set(0)
#        self.repertoireCourant.set("Exemples/")

    ###########################################################################
    def extraireRepertoire(self,chemin):
        for i in range(len(chemin)):
            if chemin[i] == "/":
                p = i
        self.repertoireCourant = chemin[:p+1]
        return chemin[:p+1]
        
        
##############################################################################
#     Fenêtre Options     #
##############################################################################
class FenOptions(wx.Dialog):
#   "Fenêtre des options"      
    def __init__(self, parent, options):
        wx.Dialog.__init__(self, parent, -1, _("Options de pySyLiC"))#, style = wx.RESIZE_BORDER)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.options = options
        self.parent = parent
        
        
        #
        # Le book ...
        #
        nb = wx.Notebook(self, -1)
        nb.AddPage(pnlGenerales(nb, options.typesOptions['Général']), _("Général"))
        nb.AddPage(pnlAffichage(nb, options.typesOptions['Affichage']), _("Affichage"))
        nb.AddPage(pnlCalcul(nb, options.typesOptions['Calcul']), _("Calcul"))
        nb.AddPage(pnlImpression(nb, options.typesOptions['Impression']), _("Impression"))
        nb.AddPage(pnlCouleurs(nb, options.typesOptions['Formats de ligne']), _("Formats de ligne"))
        nb.SetMinSize((400,-1))
        sizer.Add(nb, flag = wx.EXPAND)#|wx.ALL)
        self.nb = nb
        
        #
        # Les boutons ...
        #
        btnsizer = wx.StdDialogButtonSizer()
        
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            btnsizer.AddButton(btn)
        
        btn = wx.Button(self, wx.ID_OK)
        help = _("Valider les changements apportés aux options")
        btn.SetToolTip(wx.ToolTip(help))
        btn.SetHelpText(help)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        help = _("Annuler les changements et garder les options comme auparavant")
        btn.SetToolTip(wx.ToolTip(help))
        btn.SetHelpText(help)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        
        btn = wx.Button(self, -1, _("Défaut"))
        help = _("Rétablir les options par défaut")
        btn.SetToolTip(wx.ToolTip(help))
        btn.SetHelpText(help)
        self.Bind(wx.EVT_BUTTON, self.OnClick, btn)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        bsizer.Add(btn)
        bsizer.Add(btnsizer, flag = wx.EXPAND)
        
        sizer.Add(bsizer, flag = wx.EXPAND)#|wx.ALL)
        self.SetMinSize((400,-1))
#        print self.GetMinSize()
#        self.SetSize(self.GetMinSize())
        self.SetSizerAndFit(sizer)
        
    def OnClick(self, event):
        self.options.defaut()
        
        for np in range(self.nb.GetPageCount()):
            
            p = self.nb.GetPage(np)
#            print "   ",p
            for c in p.GetChildren():
#                print c
                c.Destroy()
#            p.DestroyChildren()
#            print p.GetSizer().GetChildren()
            p.CreatePanel()
            p.Layout()
        
        
        
#############################################################################################################
class pnlGenerales(wx.Panel):
    def __init__(self, parent, optGene):
        
        wx.Panel.__init__(self, parent, -1)
        
        self.opt = optGene
        
        self.CreatePanel()
    
        
    
    def CreatePanel(self):
        
        self.ns = wx.BoxSizer(wx.VERTICAL)
        
        #
        # Langage
        #
        sb0 = wx.StaticBox(self, -1, _("Langage"), size = (200,-1))
        sbs0 = wx.StaticBoxSizer(sb0,wx.VERTICAL)
        
        self.nom_langues = list(zip(*globdef.INSTALLED_LANG.items()))
#        print self.nom_langues
        cb = wx.ComboBox(self, -1, globdef.INSTALLED_LANG[self.opt["LANG"]], size = (40, -1), 
                         choices = self.nom_langues[1],
                         style = wx.CB_DROPDOWN|wx.CB_READONLY ,
                         name = "LANG")
        cb.SetToolTip(wx.ToolTip(_("Choisir le langage utilisé par pySyLiC\n\n" \
                                   "  Nécessite un redémarrage de pySyLiC")))
        sbs0.Add(cb, flag = wx.EXPAND|wx.ALL, border = 5)
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, cb)
        self.ns.Add(sbs0, flag = wx.EXPAND|wx.ALL)
        
        
        #
        # Choix du dossier de sauvegarde par défaut
        #
        sb1 = wx.StaticBox(self, -1, _("Dossier de sauvegarde par défaut"), size = (200,-1))
        sbs1 = wx.StaticBoxSizer(sb1,wx.VERTICAL)
        fs = DirSelectorCombo(self, -1)
        # fs.SetValueWithEvent(self.opt["RepCourant"])
        fs.SetValue(self.opt["RepCourant"])
        fs.SetToolTip(wx.ToolTip(_("Permet de selectionner le dossier\n" \
                                   "dans lequel seront sauvegardés les fichiers *.syl\n"\
                                   "après le lancement de pySyLic.\n"\
                                   "Par la suite, le dossier de sauvegarde proposé\n"\
                                   "est le dernier dossier utilisé pour un enregistrement.")))
        sbs1.Add(fs, flag = wx.EXPAND|wx.ALL, border = 5)
        fs.Bind(wx.EVT_TEXT, self.EvtComboCtrl)
        self.ns.Add(sbs1, flag = wx.EXPAND|wx.ALL)
        
        #
        # Option "Type de selecteur de fonction"
        #
        rb1 = wx.RadioBox(self, -1, _("Type de selecteur de fonction"), wx.DefaultPosition, wx.DefaultSize,
                          [_("polynômes factorisés"),_("polynômes développés"), _("identification à partir d'une courbe")], 
                          1, wx.RA_SPECIFY_COLS)
        rb1.SetSelection(self.opt["TypeSelecteur"])
        rb1.SetToolTip(wx.ToolTip(_("Choisir la forme sous laquelle vous souhaitez saisir\n"\
                                    "les polynômes des fonctions de transfert :\n"\
                                    " - \"polynômes factorisés\" : fonction de transfert sous forme canonique\n"\
                                    " - \"polynômes développés\" : saisie de chaque coefficient réel indépendamment\n"\
                                    " - \"ajustement sur courbe\" : identification des paramètres à partir d'une courbe expérimentale")))
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, rb1)
        self.ns.Add(rb1, flag = wx.EXPAND|wx.ALL)
        
        #
        # Apparence & Comportement
        #
        sb3 = wx.StaticBox(self, -1, _("Apparence et Comportement"), size = (200,-1))
        sbs3 = wx.StaticBoxSizer(sb3,wx.VERTICAL)
        
        # Option VAR_COMPLEXE
        hs = wx.BoxSizer(wx.HORIZONTAL)
        ttr = wx.StaticText(self, -1, _("Lettre pour la variable complexe :"))
        cb = wx.ComboBox(self, -1, self.opt["VAR_COMPLEXE"], size = (40, -1), 
                         choices = ['p', 's'],
                         style = wx.CB_DROPDOWN|wx.CB_READONLY ,
                         name = "VAR_COMPLEXE")
        help = _("Choisir la lettre utilisée pour désigner la variable complexe.")
        cb.SetToolTipString(help)
        ttr.SetToolTipString(help)
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, cb)
        hs.Add(ttr, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4)
        hs.Add(cb, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4)
        sbs3.Add(hs, flag = wx.EXPAND|wx.ALL, border = 5)
        
        # MAJ_AUTO
        cb2 = wx.CheckBox(self, -1, _("Mise à jour automatique des tracés"))
        cb2.SetToolTip(wx.ToolTip(_("Si cette case est cochée, les tracés sont mis à jour automatiquement\n"\
                                    "à chaque modification de la Fonction de Transfert")))
        cb2.SetValue(self.opt["MAJ_AUTO"])
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBoxM, cb2)
        
        sbs3.Add(cb2, flag = wx.EXPAND|wx.ALL, border = 5)
        
        
        # DEPHASAGE
        cb3 = wx.CheckBox(self, -1, _('Ajouter la fonction "retard"'))
        cb3.SetToolTip(wx.ToolTip(_("Si cette case est cochée, il est possible d'ajouter la fonction \"retard\"\n"\
                                    "à la Fonction de Transfert du processus")))
        cb3.SetValue(self.opt["DEPHASAGE"])
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBoxD, cb3)
        
        sbs3.Add(cb3, flag = wx.EXPAND|wx.ALL, border = 5)
        
        self.ns.Add(sbs3, flag = wx.EXPAND|wx.ALL)
        
        #
        # Nombre de SousFT maxi
        #
        sb3 = wx.StaticBox(self, -1, _("Niveau de complexité"), size = (200,-1))
        sbs3 = wx.StaticBoxSizer(sb3,wx.VERTICAL)
        self.ncp = Variable(_('Nombre maximum de\nsous Fonctions de Transfert'), 
                            lstVal = self.opt["NBR_MAXI_PLOT"], 
                            typ = VAR_ENTIER_POS, bornes = [8,globdef.MAXI_NBR_MAXI_PLOT])
        vc2 = VariableCtrl(self, self.ncp, coef = 1, labelMPL = False, signeEgal = False,
                          help = _("Nombre maximum de sous fonctions de transfert\n"\
                                   "que peut avoir la fonction de transfert H\n"\
                                   "!! Nécessite un redémarrage de pySyLiC !!"))
        self.Bind(EVT_VAR_CTRL, self.EvtVariableNpc, vc2)
        
        sbs3.Add(vc2, flag = wx.EXPAND|wx.ALL, border = 5)
        self.ns.Add(sbs3, flag = wx.EXPAND|wx.ALL)
        
        self.SetSizerAndFit(self.ns)
    
    def EvtComboBox(self, event):
        cb = event.GetEventObject()
#        data = GetClientData(event.GetSelection())
        data = cb.GetValue()
        name = cb.GetName()
        if name == "VAR_COMPLEXE":
            self.opt["VAR_COMPLEXE"] = data
        elif name == "TEMPS_REPONSE":
            self.opt["TEMPS_REPONSE"] = float(eval(data.strip("%")))/100
        else:
            num = event.GetSelection()
            self.opt["LANG"] = self.nom_langues[0][num]
            
    
    def EvtRadioBox(self, event):
        self.opt["TypeSelecteur"] = event.GetInt()
        
    def EvtComboCtrl(self, event):
        self.opt["RepCourant"] = event.GetEventObject().GetValue()
        
    def EvtCheckBoxM(self, event):
        self.opt["MAJ_AUTO"] = event.GetEventObject().GetValue()
    
    def EvtCheckBoxD(self, event):
        self.opt["DEPHASAGE"] = event.GetEventObject().GetValue()
        
    def EvtVariableNpr(self, event):
        self.opt["NB_PERIODES_REP_TEMPO"] = event.GetVar().v[0]
        
    def EvtVariableNpc(self, event):
        self.opt["NBR_MAXI_PLOT"] = event.GetVar().v[0]

#    def EvtCheckBoxOnglet(self, event):
#        dlg = wx.MessageDialog(self, "L'option ne sera effective qu'au redémarrage de l'application",
#                               'Option "Arbre de structure"',
#                               wx.OK | wx.ICON_INFORMATION
#                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
#                               )
#        dlg.ShowModal()
#        dlg.Destroy()
#        self.opt["OngletMontage"] = event.GetEventObject().GetValue()
#        
#    def EvtCheckBoxHachurer(self, event):
#        self.opt["Hachurer"] = event.GetEventObject().GetValue()

#############################################################################################################
class pnlCalcul(wx.Panel):
    def __init__(self, parent, optCalc):
        
        wx.Panel.__init__(self, parent, -1)
        
        self.opt = optCalc
        
        self.CreatePanel()
    
        
    
    def CreatePanel(self):
        
        self.ns = wx.BoxSizer(wx.VERTICAL)
        
        
        #
        # NB_PERIODES_REP_TEMPO
        #
        sb2 = wx.StaticBox(self, -1, _("Réponse temporelle"), size = (200,-1))
        sbs2 = wx.StaticBoxSizer(sb2,wx.VERTICAL)
        self.npr = Variable(_('Nombre de periodes affichées\nen mode "échelle automatique"'), 
                            lstVal = self.opt["NB_PERIODES_REP_TEMPO"], 
                            typ = VAR_ENTIER_POS, bornes = [2,20])
        vc1 = VariableCtrl(self, self.npr, coef = 1, labelMPL = False, signeEgal = False,
                          help = _("En mode \"échelle automatique\",\n"\
                                   "pour les consignes périodiques,\n"\
                                   "pySyLiC règle l'echelle du temps\n"\
                                   "sur le nombre de périodes défini ici."))
        self.Bind(EVT_VAR_CTRL, self.EvtVariableNpr, vc1)
        
        hs = wx.BoxSizer(wx.HORIZONTAL)
        txt = wx.StaticText(self, -1, _("Niveau d'évaluation du temps de réponse"))
        cb = wx.ComboBox(self, -1, str(int(self.opt["TEMPS_REPONSE"]*100))+"%", (90, 50), 
                         (60, -1), ['1%', '2%', '3%', '5%', '8%', '10%', '15%'],
                         wx.CB_DROPDOWN|wx.CB_READONLY,
                         name = "TEMPS_REPONSE")
        
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, cb)
        hs.Add(txt, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4)
        hs.Add(cb, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4)
        sbs2.Add(vc1, flag = wx.EXPAND|wx.ALL, border = 5)
        sbs2.Add(hs, flag = wx.EXPAND|wx.ALL, border = 5)
        
        
        # 
        # Performances
        #
#        sb3 = wx.StaticBox(self, -1, _("Performances"))
#        sbs3 = wx.StaticBoxSizer(sb3, wx.VERTICAL)
        
        
        # NBR_PTS_REPONSE
        self.npr = Variable(_("Nombre de points de calcul pour la réponse temporelle"), 
                            lstVal = self.opt["NBR_PTS_REPONSE"], 
                            typ = VAR_ENTIER_POS, bornes = [50,500])
        vc = VariableCtrl(self, self.npr, coef = 10, labelMPL = False, signeEgal = False,
                          help = _("Ajuster le nombre de points\n"\
                                   "pour le calcul de la réponse temporelle.\n"\
                                   "(en principe, il est inutile de modifier cette valeur)"))
        sbs2.Add(vc, flag = wx.EXPAND|wx.ALL, border = 5)
        
        self.ns.Add(sbs2, flag = wx.EXPAND|wx.ALL)
        
        self.SetSizerAndFit(self.ns)
    
    def EvtComboBox(self, event):
        cb = event.GetEventObject()
#        data = GetClientData(event.GetSelection())
        data = cb.GetValue()
        name = cb.GetName()
        if name == "VAR_COMPLEXE":
            self.opt["VAR_COMPLEXE"] = data
        elif name == "TEMPS_REPONSE":
            self.opt["TEMPS_REPONSE"] = float(eval(data.strip("%")))/100
        else:
            num = event.GetSelection()
            self.opt["LANG"] = self.nom_langues[0][num]
            
    
    def EvtRadioBox(self, event):
        self.opt["TypeSelecteur"] = event.GetInt()
        
    def EvtComboCtrl(self, event):
        self.opt["RepCourant"] = event.GetEventObject().GetValue()
        
    def EvtCheckBox(self, event):
        self.opt["MAJ_AUTO"] = event.GetEventObject().GetValue()
        
    def EvtVariableNpr(self, event):
        self.opt["NB_PERIODES_REP_TEMPO"] = event.GetVar().v[0]
        
    def EvtVariableNpc(self, event):
        self.opt["NBR_MAXI_PLOT"] = event.GetVar().v[0]

#    def EvtCheckBoxOnglet(self, event):
#        dlg = wx.MessageDialog(self, "L'option ne sera effective qu'au redémarrage de l'application",
#                               'Option "Arbre de structure"',
#                               wx.OK | wx.ICON_INFORMATION
#                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
#                               )
#        dlg.ShowModal()
#        dlg.Destroy()
#        self.opt["OngletMontage"] = event.GetEventObject().GetValue()
#        
#    def EvtCheckBoxHachurer(self, event):
#        self.opt["Hachurer"] = event.GetEventObject().GetValue()

#######################################################################################################
class pnlAffichage(wx.Panel):
    def __init__(self, parent, optAffichage):
        wx.Panel.__init__(self, parent, -1)
        self.opt = optAffichage
        self.CreatePanel()
        

    def CreatePanel(self):
        self.ns = wx.BoxSizer(wx.VERTICAL)
        # 
        # Performances
        #
        sb3 = wx.StaticBox(self, -1, _("Performances"))
        sbs3 = wx.StaticBoxSizer(sb3, wx.VERTICAL)
        
        # ANTIALIASED
        cb2 = wx.CheckBox(self, -1, _("Lisser les courbes (antialiasing)"))
        cb2.SetToolTip(wx.ToolTip(_("En décochant cette case, l'affichage devrait être plus rapide")))
        cb2.SetValue(self.opt["ANTIALIASED"])
        
        sbs3.Add(cb2, flag = wx.EXPAND|wx.ALL, border = 5)
            
        # 
        # Polices de caractère
        #
        sb2 = wx.StaticBox(self, -1, _("Type de Police de caractère"))
        sbs2 = wx.StaticBoxSizer(sb2, wx.VERTICAL)
        
        lstBmp = [Images.TypeFont0.GetBitmap(), 
                  Images.TypeFont1.GetBitmap(), 
                  Images.TypeFont2.GetBitmap()]
#        print self.opt["FONT_TYPE"],
        for i, bmp in enumerate(lstBmp):
#            print i,
            sz = wx.BoxSizer(wx.HORIZONTAL)
            rb = wx.RadioButton(self, 100+i, "")
            sz.Add(rb, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            sz.Add(wx.StaticBitmap(self, -1, bmp), 0, wx.ALL, border = 5)
            if self.opt["FONT_TYPE"] == i:
                rb.SetValue(True)
            self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, rb )
            sbs2.Add(sz)
            
        
        self.ns.Add(sbs2, flag = wx.EXPAND)
        self.ns.Add(sbs3, flag = wx.EXPAND)
        
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cb2)
        self.Bind(EVT_VAR_CTRL, self.OnVariableModified)
        
        self.SetSizerAndFit(self.ns)
        
    
    def OnRadio(self, event):
        radio = event.GetId() - 100
        self.opt["FONT_TYPE"] = radio
         
    def OnVariableModified(self, event):
#        print "NBR_PTS_REPONSE 1", self.npr.v[0]
        self.opt["NBR_PTS_REPONSE"] = self.npr.v[0]
        
    
    def EvtCheckBox(self, event):
        self.opt["ANTIALIASED"] = event.IsChecked()
        
        
#    def OnClick(self, event):
#        # Nouveau
#        if event.GetId() == 10: 
#            frame = ElementTable.ElementGridFrame(self, Elements.listeElements, Elements.listeFamilles,
#                                                  fichier = wx.GetApp().auteur)
#        
#        # Editer
#        elif event.GetId() == 11:
#            frame = ElementTable.ElementGridFrame(self, fichier = self.cb.GetValue())
#        frame.Show(True)
#        
#        
#    def SetFichier(self, fichier):
#        self.opt["FichierProprietes"] = fichier
#        self.cb.SetValue(self.opt["FichierProprietes"])
#    
#    
#        
#    
#    def EvtRadioBox(self, event = None):
#        if event != None:
##            print "Radio",event.GetId()
#            self.opt["ProprietesDefaut"] = event.GetId()
#        
#        if self.opt["ProprietesDefaut"] == 0:
#            self.sb2.Enable(False)
#            self.cb.Enable(False)
#            self.b1.Enable(False)
#            self.b2.Enable(False)
#        else:
#            self.sb2.Enable(True)
#            self.cb.Enable(True)
#            self.b1.Enable(True)
#            self.b2.Enable(True)
#        
#    def EvtComboBox(self, event):
#        self.opt["FichierProprietes"] = event.GetEventObject().GetValue()
#        

#############################################################################################################
class pnlImpression(wx.Panel):
    def __init__(self, parent, opt):
        wx.Panel.__init__(self, parent, -1)
        self.opt = opt
        self.CreatePanel()
        
        
    def CreatePanel(self):
        
        self.ns = wx.BoxSizer(wx.VERTICAL)
        #
        # Mise en page
        #
        sb1 = wx.StaticBox(self, -1, _("Mise en page"), size = (200,-1))
        sbs1 = wx.StaticBoxSizer(sb1,wx.VERTICAL)
        cb2 = wx.CheckBox(self, -1, _("Garder les proportions de l'écran"))
        cb2.SetToolTip(wx.ToolTip(_("Si cette case est cochée, les tracés imprimés\n"\
                                    "auront les mêmes proportions (largeur/hauteur) qu'à l'écran.")))
        cb2.SetValue(self.opt["PRINT_PROPORTION"])
        sbs1.Add(cb2, flag = wx.EXPAND|wx.ALL, border = 5)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cb2)
        self.ns.Add(sbs1, flag = wx.EXPAND|wx.ALL)
        
        #
        # Elements à imprimer
        #
        sb2 = wx.StaticBox(self, -1, _("Eléments à imprimer"), size = (200,-1))
        sbs2 = wx.StaticBoxSizer(sb2,wx.VERTICAL)
        sup = "\n"+_("En décochant cette case, vous pouvez choisir un texte personnalisé")
        selTitre = selecteurTexteEtPosition(self, _("Nom du fichier système"),
                                            self.Parent.Parent.Parent.fichierCourant,
                                            _("Nom de fichier sous lequel le système actuel est sauvegardé")+sup,
                                            "IMPRIMER_TITRE", "POSITION_TITRE", "TEXTE_TITRE")
        selNom = selecteurTexteEtPosition(self, _("Nom de l'utilisateur"),
                                            globdef.NOM,
                                            _("Nom de l'utilisateur de l'ordinateur")+sup,
                                            "IMPRIMER_NOM", "POSITION_NOM", "TEXTE_NOM")
        sbs2.Add(selTitre, flag = wx.EXPAND|wx.ALL, border = 5)
        sbs2.Add(selNom, flag = wx.EXPAND|wx.ALL, border = 5)
        self.ns.Add(sbs2, flag = wx.EXPAND|wx.ALL)
        
        #
        # Qualité de l'impression
        #
        sb3 = wx.StaticBox(self, -1, _("Qualité de l'impression"), size = (200,-1))
        sbs3 = wx.StaticBoxSizer(sb3,wx.VERTICAL)
        hs = wx.BoxSizer(wx.HORIZONTAL)
        ttr = wx.StaticText(self, -1, _("Résolution de l'impression :"))
        cb = wx.ComboBox(self, -1, str(self.opt["MAX_PRINTER_DPI"]), size = (80, -1), 
                         choices = ['100', '200', '300', '400', '500', '600'],
                         style = wx.CB_DROPDOWN|wx.CB_READONLY)
        help = _("Ajuster la résolution de l'impression.\n"\
                 "Attention, une résolution trop élevée peut augmenter\n"\
                 "significativement la durée de l'impression.")
        cb.SetToolTipString(help)
        ttr.SetToolTipString(help)
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox, cb)
        hs.Add(ttr, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4)
        hs.Add(cb, flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4)
        sbs3.Add(hs, flag = wx.EXPAND|wx.ALL, border = 5)
        self.ns.Add(sbs3, flag = wx.EXPAND|wx.ALL)
        
        self.SetSizerAndFit(self.ns)
    
    def EvtComboBox(self, event):
        cb = event.GetEventObject()
        data = cb.GetValue()
        self.opt["MAX_PRINTER_DPI"] = eval(data)
        
    def EvtCheckBox(self, event):
        self.opt["PRINT_PROPORTION"] = event.GetEventObject().GetValue()
        


class selecteurTexteEtPosition(wx.Panel):
    def __init__(self, parent, titre, textedefaut, tooltip, impoption, posoption, txtoption, ctrl = True):
        wx.Panel.__init__(self, parent, -1)
        
        self.impoption = impoption
        self.posoption = posoption
        self.txtoption = txtoption
        self.textedefaut = textedefaut
        
        self.lstPos = ["TL","TC","TR","BL","BC","BR"]
        tooltips = [_("En haut à gauche"), _("En haut au centre"), _("En haut à droite"),
                   _("En bas à gauche"), _("En bas au centre"), _("En bas à droite")]
        #
        # Le titre
        #
        self.titre = wx.CheckBox(self, -1, titre)
        self.titre.SetValue(self.Parent.opt[self.impoption])
        self.titre.SetToolTip(wx.ToolTip(tooltip))
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.titre)
        
        #
        # Le texte à afficher
        #
        if not self.Parent.opt[self.impoption]:
            txt = self.Parent.opt[self.txtoption]
        else:
            txt = self.textedefaut
            
        if ctrl:
#            print self.Parent.opt[self.txtoption]
            self.texte = wx.TextCtrl(self, -1, txt)
            self.Bind(wx.EVT_TEXT, self.EvtText, self.texte)
        else:
            self.texte = wx.StaticText(self, -1, txt)
        self.texte.Enable(not self.Parent.opt[self.impoption])
            
        #
        # La position
        #
        radio = []
        box1_title = wx.StaticBox(self, -1, _("position") )
        box1 = wx.StaticBoxSizer( box1_title, wx.VERTICAL )
        grid1 = wx.BoxSizer(wx.HORIZONTAL)
        radio.append(wx.RadioButton(self, 101, "", style = wx.RB_GROUP ))
        radio.append(wx.RadioButton(self, 102, "" ))
        radio.append(wx.RadioButton(self, 103, "" ))
        for r in radio:
            grid1.Add(r)
        box1.Add(grid1)
        
        img = wx.StaticBitmap(self, -1, Images.Zone_Impression.GetBitmap())
        img.SetToolTip(wx.ToolTip(_("Choisir ici la position du texte par rapport aux tracés")))
        box1.Add(img)
        
        grid2 = wx.BoxSizer(wx.HORIZONTAL)
        radio.append(wx.RadioButton(self, 104, "" ))
        radio.append(wx.RadioButton(self, 105, "" ))
        radio.append(wx.RadioButton(self, 106, "" ))
        for r in radio[3:]:
            grid2.Add(r)
        box1.Add(grid2)
        
        for i, r in enumerate(radio):
            r.SetToolTip(wx.ToolTip(tooltips[i]))
            self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio, r)
        
        self.radio = self.lstPos.index(self.Parent.opt[self.posoption])
        for i, r in enumerate(radio):
            if i == self.radio:
                r.SetValue(True)
            else:
                r.SetValue(False)
        
#        sizerV = wx.BoxSizer(wx.VERTICAL)
#        sizerV.Add(box1)
#        sizerV.Add(img)
#        sizerV.Add(box2)
        
#        posList = [" "," "," "," "," "," "]
#        rb = wx.RadioBox(self, -1, _("position"), wx.DefaultPosition, wx.DefaultSize,
#                         posList, 2, wx.RA_SPECIFY_ROWS)
#        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, rb)
#        try:
#            rb.SetSelection(self.lstPos.index(self.Parent.opt[self.posoption]))
#        except:
#            pass
#        self.rb = rb
#        self.rb.Enable(self.titre.GetValue())
        
        
        #
        # Mise en place
        #
        sizerG = wx.BoxSizer(wx.VERTICAL)
        sizerG.Add(self.titre, flag = wx.EXPAND)
        sizerG.Add(self.texte, flag = wx.EXPAND|wx.ALL, border = 15)
        
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(sizerG, 1, flag = wx.EXPAND)
        self.sizer.Add(box1, flag = wx.EXPAND|wx.ALIGN_LEFT)
        self.SetSizer(self.sizer)
        self.sizer.Fit( self )
        
    def OnRadio(self, event):
        self.radio = event.GetId()-101
        self.Parent.opt[self.posoption] = self.lstPos[self.radio]
#        print self.radio
    
#    def EvtRadioBox(self, event):
#        p = event.GetInt()
#        self.Parent.opt[self.posoption] = self.lstPos[p]
        
    def EvtText(self, event):
        txt = event.GetString()
        self.Parent.opt[self.txtoption] = txt
        
    def EvtCheckBox(self, event):
        self.Parent.opt[self.impoption] = event.GetEventObject().GetValue()
        self.texte.Enable(not self.Parent.opt[self.impoption])
        
#        self.Parent.opt[self.posoption] = self.lstPos[self.radio]
        
    
        if not self.Parent.opt[self.impoption]:
            self.Parent.opt[self.txtoption] = self.texte.GetValue()
            self.texte.SetValue(self.Parent.opt[self.txtoption])    
        else:
            self.texte.SetValue(self.textedefaut)
            self.Parent.opt[self.txtoption] = ""
            
        
#        self.rb.Enable(event.GetEventObject().GetValue())
            
#class pnlImpression(wx.Panel):
#    def __init__(self, parent, opt):
#        wx.Panel.__init__(self, parent, -1)
#        ns = wx.BoxSizer(wx.VERTICAL)
#        self.opt = opt
#        
#        sb1 = wx.StaticBox(self, -1, "Contenu du rapport", size = (200,-1))
#        sbs1 = wx.StaticBoxSizer(sb1,wx.VERTICAL)
#        tree = ChoixRapportTreeCtrl(self, self.opt)
#        sbs1.Add(tree, flag = wx.EXPAND|wx.ALL, border = 5)
#        
##        print tree.GetVirtualSize()[1], tree.GetBestSize()[1]
#        
#        cb2 = wx.CheckBox(self, -1, "Demander ce qu'il faut inclure à chaque création de rapport")
#        cb2.SetValue(self.opt["DemanderImpr"])
#        
#        sbs1.Add(cb2, flag = wx.EXPAND|wx.ALL, border = 5)
#        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cb2)
#        
#        ns.Add(sbs1, flag = wx.EXPAND|wx.ALL)
#        self.SetSizerAndFit(ns)
#        sb1.SetMinSize((-1, 130))
#        
##    def EvtComboCtrl(self, event):
##        self.opt["FichierMod"] = event.GetEventObject().GetValue()
#    
#    def EvtCheckBox(self, event):
#        self.opt["DemanderImpr"] = event.IsChecked()
#     
#class pnlAnalyse(wx.Panel):
#    def __init__(self, parent, options):
#        wx.Panel.__init__(self, parent, -1)
#        ns = wx.BoxSizer(wx.VERTICAL)
#        self.options = options
#        
#        sb1 = wx.StaticBox(self, -1, "Outils visuels d'analyse")
#        sbs1 = wx.StaticBoxSizer(sb1,wx.VERTICAL)
#        
#        label = {"AnimMontage"  : "Proposer l'animation du démontage/remontage",
#                 "AnimArrets"   : "Proposer l'animation du manque d'arrêt axial",
#                 "ChaineAction" : "Proposer le tracé des chaînes d'action"}
#
#        self.cb = {}
#        for titre, opt in options.items():
#            c = wx.CheckBox(self, -1, label[titre])
#            self.cb[c.GetId()] = titre
#            c.SetValue(opt)
#            self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, c)
#            sbs1.Add(c, flag = wx.ALL, border = 5)
#        
#        ns.Add(sbs1, flag = wx.EXPAND)
#
#        self.SetSizerAndFit(ns)
#
#    def EvtCheckBox(self, event):
#        self.options[self.cb[event.GetId()]] = event.IsChecked()
        
class pnlCouleurs(wx.Panel):
    """ Dialog de selection d'un format de ligne
        <format> = liste : [couleur, style, épaisseur]
    """
    def __init__(self, parent, opt):
        wx.Panel.__init__(self, parent, -1)
        
        self.opt = opt
        
        lstIDCoul = ["COUL_POLES", "COUL_PT_CRITIQUE", "COUL_MARGE_OK", "COUL_MARGE_NO"]
        
        lstIDForm = ["FORM_GRILLE", "FORM_ISOGAIN", "FORM_ISOPHASE"]

        self.lstIDCoul = lstIDCoul
        self.lstIDForm = lstIDForm
        
        self.CreatePanel()
        
        
        
    def CreatePanel(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        nomCouleurs = {"COUL_MARGE_OK"      : _('Marge de stabilité "valide"'),
                       "COUL_MARGE_NO"      : _('Marge de stabilité "non valide"'),
                       "COUL_POLES"         : _('Pôles'),
                       "COUL_PT_CRITIQUE"   : _('Point critique et Courbe "lambda"')
                        }
        
        nomFormatLigne  = {"FORM_GRILLE"        : _('Grille'),
                           "FORM_ISOGAIN"       : _('Courbe "isogain"'),
                           "FORM_ISOPHASE"      : _('Courbe "isophase"')
                           }
        
        self.lstButton = {}
        for i, k in enumerate(self.lstIDCoul):
            sizerH = wx.BoxSizer(wx.HORIZONTAL)
            txtColor = wx.StaticText(self, i+100, nomCouleurs[k])
            selColor = wx.Button(self, i, "", size = (80,22))
            selColor.SetToolTipString(_("Modifier la couleur de l'élément") + " :\n" + nomCouleurs[k])
            selColor.SetBackgroundColour(self.opt[k])
            
            sizerH.Add(txtColor, flag = wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 5)
            sizerH.Add(selColor, flag = wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 5)
            self.sizer.Add(sizerH, flag = wx.ALIGN_RIGHT|wx.ALL)
            
            self.lstButton[k] = selColor
            self.Bind(wx.EVT_BUTTON, self.OnClick, id = i)
    
        for i, k in enumerate(self.lstIDForm):
            sizerH = wx.BoxSizer(wx.HORIZONTAL)
            txtColor = wx.StaticText(self, i+100, nomFormatLigne[k])
            selColor = SelecteurFormatLigne(self, i+len(self.lstIDCoul), self.opt[k], 
                                            _("Modifier le format de ligne de l'élément") + " :\n" + nomFormatLigne[k],
                                            size = (80,22))
            
            sizerH.Add(txtColor, flag = wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 5)
            sizerH.Add(selColor, flag = wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 5)
            self.sizer.Add(sizerH, flag = wx.ALIGN_RIGHT|wx.ALL)
            
            self.lstButton[k] = selColor
            self.Bind(EVT_FORMAT_MODIFIED, self.OnFormatModified)
            
        self.SetSizer(self.sizer)
        
    ###############################################################################################
    def OnFormatModified(self, event = None):    
        return
        
    ###############################################################################################
    def OnClick(self, event = None):      
        id = event.GetId()
        colourData = wx.ColourData()
        colourData.SetColour(wx.NamedColour(self.opt[self.lstIDCoul[id]]))
        dlg = wx.ColourDialog(self, colourData)

        # Ensure the full colour dialog is displayed, 
        # not the abbreviated version.
        dlg.GetColourData().SetChooseFull(True)

        if dlg.ShowModal() == wx.ID_OK:

            # If the user selected OK, then the dialog's wx.ColourData will
            # contain valid information. Fetch the data ...

            self.opt[self.lstIDCoul[id]] = dlg.GetColourData().GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
            self.lstButton[self.lstIDCoul[id]].SetBackgroundColour(self.opt[self.lstIDCoul[id]])
#            print self.opt[self.lstID[id]]
            
        # Once the dialog is destroyed, Mr. wx.ColourData is no longer your
        # friend. Don't use it again!
        dlg.Destroy()
        return
    
    
#class nbOptions(wx.Notebook):
#    def __init__(self, parent, options):
#        wx.Notebook.__init__(self, parent, -1)
#        
#        self.AddPage(pnlGenerales(self, options.optGenerales), _("Général"))
#        self.AddPage(pnlAffichage(self, options.optAffichage), _("Affichage"))
##        self.AddPage(pnlImpression(self, options.optImpression), "Rapport")
##        self.AddPage(pnlAnalyse(self, options.optAnalyse), "Analyse")
#        self.SetMinSize((350,-1))
            
##########################################################################################################
#
#  DirSelectorCombo
#
##########################################################################################################
class DirSelectorCombo(wx.ComboCtrl):
    def __init__(self, *args, **kw):
        wx.ComboCtrl.__init__(self, *args, **kw)

        # make a custom bitmap showing "..."
        bw, bh = 14, 16
        bmp = wx.EmptyBitmap(bw,bh)
        dc = wx.MemoryDC(bmp)

        # clear to a specific background colour
        bgcolor = wx.Colour(255,254,255)
        dc.SetBackground(wx.Brush(bgcolor))
        dc.Clear()

        # draw the label onto the bitmap
        label = "..."
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        tw,th = dc.GetTextExtent(label)
        dc.DrawText(label, (bw-tw)//2, (bw-tw)//2)
        del dc

        # now apply a mask using the bgcolor
        bmp.SetMaskColour(bgcolor)

        # and tell the ComboCtrl to use it
        self.SetButtonBitmaps(bmp, True)
        

    # Overridden from ComboCtrl, called when the combo button is clicked
    def OnButtonClick(self):
        # In this case we include a "New directory" button. 
#        dlg = wx.FileDialog(self, "Choisir un fichier modèle", path, name,
#                            "Rich Text Format (*.rtf)|*.rtf", wx.FD_OPEN)
        dlg = wx.DirDialog(self, _("Choisir un dossier"),
                           defaultPath = globdef.DOSSIER_EXEMPLES,
                           style = wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it. 
        if dlg.ShowModal() == wx.ID_OK:
            self.SetValue(dlg.GetPath())

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()
        
        self.SetFocus()

    # Overridden from ComboCtrl to avoid assert since there is no ComboPopup
    def DoSetPopupControl(self, popup):
        pass


