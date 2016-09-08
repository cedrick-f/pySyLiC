#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

from distutils.core import setup
import py2exe
import os
import matplotlib
#import babel

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "0.32.2"
        self.company_name = u"Cédrick FAURY"
        self.copyright = u"copyright (c) 2009-2011 Cédrick FAURY"
        self.name = "pySyLiC"


# Remove the build folder, a bit slower but ensures that build contains the latest
import shutil
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("dist", ignore_errors=True)

from glob import glob
data_files = [("Microsoft.VC90.CRT", glob(r'msvcr90.dll')), 
              #("localedata", glob( os.path.join( os.path.dirname( babel.__file__ ), "localedata", "*.*"))),
#              ("Microsoft.VC90.CRT", glob(r'msvcp90.dll')), 
#              ("Microsoft.VC90.CRT", glob(r'msvcm90.dll')), 
              ("Microsoft.VC90.CRT", glob(r'Microsoft.VC90.CRT.manifest'))]
data_files.extend(matplotlib.get_py2exe_datafiles())

manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!-- Copyright (c) Microsoft Corporation.  All rights reserved. -->
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
    <noInheritable/>
    <assemblyIdentity
        type="win32"
        name="Microsoft.VC90.CRT"
        version="9.0.21022.8"
        processorArchitecture="x86"
        publicKeyToken="1fc8b3b9a1e18e3b"
    />
    <file name="msvcr90.dll" /> 
</assembly>
"""
RT_MANIFEST = 24

icon = "D:\\Documents\\Developpement\\PySyLic\\PySyLiC 0.31\\Images\\icone.ico"

test_wx = Target(
    # used for the versioninfo resource
    description = "PySyLic",

    # what to build
    script = "PySyLic.py",
    other_resources = [(RT_MANIFEST, 1, manifest % dict(prog="test_wx"))],
    icon_resources = [(1, icon)],
    dest_base = "PySyLic")

options = {    "py2exe" : { "compressed": 1,
                           
                            "optimize": 2,
                            
                            "bundle_files": 1,
                            
                            'packages' : ['pytz', 'win32api'],
                            
                            'excludes' : ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'pywin.debugger',
                                          'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
                                          'Tkconstants', 'Tkinter', 'pydoc', 'doctest', 'test', 'sqlite3',
                                          "PyQt4", "PyQt4.QtGui","PyQt4._qt",
                                          "matplotlib.backends.backend_qt4agg", "matplotlib.backends.backend_qt4",
                                          "matplotlib.numerix"],
                            
                            'dll_excludes' : ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', 'tcl85.dll',
                                              'tk85.dll', "UxTheme.dll", "mswsock.dll", "POWRPROF.dll",
                                              "QtCore4.dll", "QtGui4.dll" ],



#                            "dll_excludes":["wxMSW26uh_vc.dll","gdiplus.dll","libgdk-win32-2.0-0.dll","libgobject-2.0-0.dll","libgdk_pixbuf-2.0-0.dll",],
#                            "packages": ["matplotlib","pytz","matplotlib.numerix.random_array"],
                            
                            #"excludes" : ['scipy.interpolate' ],
                            #"includes": ['_scproxy'],
                            #"packages": [ 'scipy.factorial'],
                                   }     }


setup(
      #com_server=['myserver'],
      options = options,
      zipfile = None,
#      console=["PySyLic.py"],
      data_files = data_files,
      windows=[{"script" :"PySyLic.py",
                "icon_resources":[(1, icon)],
                #"other_resources": [(24,1,manifest)]
                }]
    )
