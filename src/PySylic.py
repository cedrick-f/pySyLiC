#!/usr/bin/env python
# -*- coding: utf-8 -*-

##This file is part of pySylic
#############################################################################
#############################################################################
##                                                                         ##
##                                 PySylic                                 ##
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
#8
#    You should have received a copy of the GNU General Public License
#    along with pySylic; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

SHOW_SPLASH = True
SPLASH_TIME = 5000



#
#
import globdef
import sys, os, os.path
import wx
import version


if hasattr(sys, 'setdefaultencoding'):
    sys.setdefaultencoding('utf8')
else:
    reload(sys)  # Reload does the trick!
    sys.setdefaultencoding('utf-8')
    
print sys.getdefaultencoding()

try:
    from agw import advancedsplash as AdvancedSplash 
except:    
    import wx.lib.agw.advancedsplash as AdvancedSplash

if not "beta" in version.__version__ and sys.argv[0].endswith(".exe"): #sys.platform != "win32" or 
    import Error



def pySyLiCRunning():
    #
    # Cette fonction teste si pySyLiC.exe est déjà lancé, auquel cas on arrete tout.
    #
    try:
        import wmi
        HAVE_WMI=True
    except:
        HAVE_WMI=False
        
    if not HAVE_WMI:
        return False
    else:
        nb_instances=0
        try:
            controler = wmi.WMI()
            for elem in controler.Win32_Process():
                if "PySylic.exe" == elem.Caption:
                    nb_instances=nb_instances+1
            if nb_instances>=2:
                sys.exit(0)
        except:
            pass



##########################################################################################################
#
#  Application pySyLiC
#
##########################################################################################################
class PySylicApp(wx.App):
    def OnInit(self):
        """
        Create and show the splash screen.  It will then create and show
        the main frame when it is time to do so.
        """
        self.version = version.__version__
        
        try:
            import getpass
            self.auteur = unicode(getpass.getuser(),'cp1252')
        except:
            self.auteur = ""
        
        wx.SystemOptions.SetOptionInt("mac.window-plain-transition", 1)
        self.SetAppName(version.__appname__)
        
        
        
        NomFichier = None
        if len(sys.argv)>1: # un paramètre a été passé en argument
            argv = sys.argv
            if "debug" in argv:
                globdef.DEBUG = True
                argv.remove("debug")
            if "nopsycho" in argv:
                globdef.PSYCO = False
                argv.remove("nopsycho")
            
            parametre = argv[1]
            # on verifie que le fichier passé en paramètre existe
            if os.path.isfile(parametre):
                NomFichier = parametre
        
#        if globdef.PSYCO:
#            from CedWidgets import chronometrer
#            try:
#                import psyco
#                HAVE_PSYCO=True
#            except ImportError:
#                HAVE_PSYCO=False
#            
#            if HAVE_PSYCO:
#                print "Psyco !!!!!"
#                
#                if globdef.DEBUG: 
#                    PSYCO_LOG = os.path.join(globdef.APP_DATA_PATH, sys.argv[0]+'.log-psyco')
#                    psyco.log(logfile=PSYCO_LOG)
#                    psyco.profile()
#
#                print chronometrer(psyco.full)
        
        frame = Principal.wxPySylic(None, nomFichier = NomFichier)
        frame.Show()
        return True
    
    
# Test to see if we need to show a splash screen. If the splash is enabled (and
# we're not the application fork), then show a splash screen and relaunch the
# same application except as the application fork.
if __name__ == "__main__":
    AppFN = sys.argv[0]
    if SHOW_SPLASH and (len(sys.argv) == 1) and AppFN.endswith(".exe"):
        
#        sys.stderr = open(os.path.join(globdef.APP_DATA_PATH, sys.executable + '.log'), "a")
        from Images import Logo
        pySyLiCRunning()
        App = wx.App()
#        bmp = wx.Image(os.path.join(globdef.DOSSIER_IMAGES,'Logo.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        bmp = Logo.GetBitmap()
        F = AdvancedSplash.AdvancedSplash(None, bitmap = bmp, timeout = SPLASH_TIME, 
                                          agwStyle = AdvancedSplash.AS_TIMEOUT | AdvancedSplash.AS_CENTER_ON_SCREEN | AdvancedSplash.AS_SHADOW_BITMAP,
                                          shadowcolour = wx.BLACK)
        F.SetText(version.__appname__+" "+version.__version__)
        os.spawnl(os.P_NOWAIT, AppFN, '"%s"' % AppFN.replace('"', r'\"'), "NO_SPLASH")
        App.MainLoop()
        sys.exit()

##########################################################################################################
# Imports (on les fait pendant le splash
##########################################################################################################
# On crée d'abord la variable d'environnement HOME qui peut être nécessaire à matplotlib
import user
os.environ['HOME'] = globdef.APP_DATA_PATH
print "user.home", user.home
import Principal


    
if __name__ == "__main__":
    if globdef.PSYCO:
        from CedWidgets import chronometrer
        try:
            import psyco
            HAVE_PSYCO=True
        except:
            HAVE_PSYCO=False
        
        if HAVE_PSYCO:
#            import psyco ; psyco.jit() 
#            from psyco.classes import *
            print "Psyco !!!"
            
            if globdef.DEBUG: 
                PSYCO_LOG = os.path.join(globdef.APP_DATA_PATH, sys.argv[0]+'.log-psyco')
                psyco.log(logfile=PSYCO_LOG)
                psyco.profile()

            psyco.full()
    App = PySylicApp(0)
    App.MainLoop()
    
