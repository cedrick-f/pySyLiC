#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

##This file is part of PySylic
#############################################################################
#############################################################################
##                                                                         ##
##                              exportExcel                                ##
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

import xlwt, os

def createBook(nomFichier, graph): 
    book = xlwt.Workbook()
    nom = graph.__class__.__name__
#    if isinstance(graph, ZoneGraphBode):
#        nom = 'Bode'
#    elif isinstance(graph, ZoneGraphBlack):
#        nom = 'Black'
#    elif isinstance(graph, ZoneGraphNyquist):
#        nom = 'Nyquist'
#    elif isinstance(graph, ZoneGraphReponse):
#        nom = 'Réponse'
#    elif isinstance(graph, ZoneGraphPoles):
#        nom = 'Pôles'
    contenu, images = graph.getContenuExport()
    print nomFichier
    createSheet(book, nom, contenu, images)
    print nom
    print contenu
    print images
    book.save(nomFichier)



def createSheet(book, nom, contenu, images):
    ws = book.add_sheet(nom)
    
    font0 = xlwt.Font()
    font0.name = 'Arial'
    font0.bold = True
    style0 = xlwt.XFStyle()
    style0.font = font0

    for col, cont in enumerate(contenu):
        ws.write(1, col, cont[0], style0)
        for row, val in enumerate(cont[1]):
            ws.write(row+2, col, val)
    
    if images != []:
        dir = ''
        h = 0
        for img, col, tail in images:
            h = max(h, tail)
        ws.row(0).height_mismatch = 1
        ws.row(0).height = h*256/17
        dir = os.path.dirname(img)
        
        ws.write(0, 0, "1")
    #    fnt = xlwt.Font()
    #    fnt.height = 256*h/17
    #    style = xlwt.XFStyle()
    #    style.font = fnt
    #    ws.row(0).set_style(style) 
    
        for img, col, tail in images:
            ws.insert_bitmap(img, 0, col, scale_x =1, scale_y = 1)
            os.remove(img)
        os.rmdir(dir)

