#!/usr/bin/env python
# -*- coding: utf-8 -*-

##This file is part of pySequence
#############################################################################
#############################################################################
##                                                                         ##
##                                  version                                ##
##                                                                         ##
#############################################################################
#############################################################################

## Copyright (C) 2015 Cédrick FAURY

#    pySyLiC is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
    
#    pySyLiC is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with pySyLiC; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
version.py

Copyright (C) 2015-2025
@author: Cedrick FAURY

"""


__appname__= "pySyLiC"
__author__ = "Cédrick FAURY"
__version__ = "1.0"
print(__version__)


###############################################################################################
def GetVersion_cxFreeze():
    return __version__.replace("-beta", ".0")

###############################################################################################
def GetVersion_short():
    return __version__.split('.')[0]

###############################################################################################
def GetAppnameVersion():
    return __appname__+" "+GetVersion_short()


    

    

    
    
    
    