#!/usr/bin/python
# -*- coding: utf-8 -*-

##################################################################################################
#
#    Script pour générer un pack avec executable :
#    c:\python27\python setup.py build
#
##################################################################################################

import sys, os
if hasattr(sys, 'setdefaultencoding'):
    sys.setdefaultencoding('utf8')
else:
    reload(sys)  # Reload does the trick!
    sys.setdefaultencoding('utf-8')
print sys.getdefaultencoding()

#from glob import glob
from cx_Freeze import setup, Executable
from version import __version__, __appname__, GetVersion_cxFreeze    

import matplotlib

    
## Remove the build folder, a bit slower but ensures that build contains the latest
import shutil
shutil.rmtree("build", ignore_errors=True)

#import enchant.utils
#enchant_files = enchant.utils.win32_data_files() 
#le = []
#for d, s in enchant_files:
#    for f in s:
#        if d =='':
#            le.append((f, os.path.join(d, os.path.split(f)[1])))
#        else:
#            le.append((f, os.path.join('..',d, os.path.split(f)[1])))
#enchant_files = le
#enchant_files = [([r.replace("\\", "/") for r in a], b.replace("\\", "/")) for b, a in enchant_files]
#print enchant_files

# Inculsion des fichiers de données
#################################################################################################
includefiles = [#('D:/Developpement/Microsoft.VC90.CRT', "Microsoft.VC90.CRT"),
                ('../LICENSE.txt','../LICENSE.txt'),
                ('../locale', '../locale'), 
                ( matplotlib.get_data_path(),"mpl-data")
                                          ]

#                     ('C:\\Python27\\lib\\site-packages\\enchant\\share\\enchant\\myspell', 'share/enchant/myspell'), 
#                     ('C:\\Python27\\lib\\site-packages\\enchant\\*.dll', ''),
#                     ('C:\\Python27\\lib\\site-packages\\enchant\\share\\enchant\\ispell', 'share/enchant/ispell'),
#                     ('C:\\Python27\\lib\\site-packages\\enchant\\lib\\enchant\\*.dll', 'lib/enchant'),
            

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {'build_exe': 'build/bin',
                     "packages": ["os", 'pytz'],#, 'scipy'],
                     "includes": ["encodings.ascii",
#                                   "scipy",
                                'scipy.special._ufuncs_cxx', 
                                'scipy.integrate.vode', 
                                "scipy.integrate.lsoda",
                                "scipy.sparse.csgraph._validation",
                                  "numpy.lib.format", ],
                
                     "optimize" : 0,
#                     "path" : ["../packages/html5lib"],#, "../packages/xhtml2pdf",  "../packages/xhtml2pdf/w3c"],
#                     "zip_includes": [("../packages/html5lib/", "html5lib"),
#                                      ("../packages/xhtml2pdf/w3c/css.py", "xhtml2pdf/w3c/css.py")],
                     
                     "excludes": ["tkinter",
                                  '_gtkagg', '_tkagg', 'bsddb', 'curses', 'pywin.debugger',
                                  'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl', "tables",
                                  'Tkconstants', 'pydoc', 'doctest', 'test', 'sqlite3',
                                  "matplotlib.backends.backend_qt4agg", "matplotlib.backends.backend_qt4", "matplotlib.backends.backend_tkagg",
                                  "matplotlib.numerix",#"scipy.lib", 
                                  "PyQt4", "PyQt4.QtGui","PyQt4._qt",
                                  "PyQt5", "PyQt5.QtGui","PyQt5._qt",
                                  'PIL','_ssl', '_hashlib',
                                  'collections.abc',
                                  # Modules Matplotlib à enlever pour alléger : (à la main !!)

#                                  'scipy.lib.lapack.flapack', 
#                                  'scipy.lib.blas.fblas', 
#                                  'scipy.lib.lapack.clapack', 
#                                  'scipy.linalg._interpolative', 
#                                  'scipy.linalg._clapack', 
#                                  'scipy.linalg._flinalg',
                                  ],
                     "include_files": includefiles,
                     'bin_excludes' : ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', 'tcl85.dll',
                                              'tk85.dll', "UxTheme.dll", "mswsock.dll", "POWRPROF.dll",
                                              "QtCore4.dll", "QtGui4.dll",
                                               ]}


# pour inclure sous Windows les dll system de Windows necessaires
if sys.platform == "win32":
    build_exe_options["include_msvcr"] = True
    
# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if not "beta" in __version__:
    if sys.platform == "win32":
        base = "Win32GUI"

icon = "C:/Users/Cedrick/Documents/Developp/pySyLiC/Images/icone.ico"
cible = Executable(
    script = "PySylic.py",
    targetName="pySyLiC.exe",
    base = base,
    compress = True,
    icon = os.path.join("", icon),
    initScript = None,
    copyDependentFiles = True,
    appendScriptToExe = False,
    appendScriptToLibrary = False
    )


setup(  name = __appname__,
        version = GetVersion_cxFreeze(),
        author = "Cédrick FAURY",
        description = __appname__+" "+__version__,
        options = {"build_exe": build_exe_options},
#        include-msvcr = True,
        executables = [cible])


#
# Post-traitement
#
print 
A_enlever = ['scipy.lib.lapack.flapack.pyd', 
             'scipy.lib.blas.fblas.pyd', 
             'scipy.lib.lapack.clapack.pyd', 
             'scipy.linalg._interpolative.pyd', 
             'scipy.linalg._clapack.pyd', 
             'scipy.linalg._flinalg.pyd',]
for f in A_enlever:
    f = os.path.join("build", "bin", f)
    print "Suppression de", f
    try:
        os.remove(f)
    except:
        print "   pas trouvé"



