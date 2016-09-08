#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of pySyLiC.
# 
#  Copyright (C) 2001-2012 Cédrick FAURY and Thomas PAVIOT
# 
# pySyLiC is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# pySyLiC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with pySyLiC; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import sys
import globdef
import traceback
import wx

def _exceptionhook(typ, value, traceb):
    """ On catch une exception """
    frame=traceb.tb_frame
    print >>sys.stderr,"\n"
    traceback.print_tb(traceb)
    print >>sys.stderr,"\nType : ",typ,"\n"
    print >>sys.stderr,"ValueError : ",value
    sys.exit()

sys.excepthook = _exceptionhook

class RedirectErr:
    #
    # Redirige la sortie des erreurs pour envoyer l'erreur par mail
    #
    def __init__(self,stderr):
        self.stderr=stderr
        self.content=""
        self.error_occured=False
        self.file_error=None

    def write(self,text):
        #
        # A la premiere erreur, on enregistrer la fonction de sortie
        #
        if not self.error_occured:
            #
            # Première erreur
            # D'abord on enregistre la fonction atexit
            import atexit
            atexit.register(SendBugReport)
            # puis on ouvre le fichier qui contient les erreurs
            self.file_error=open(globdef.ERROR_FILE,'w')
            print globdef.ERROR_FILE
            self.error_occured=True
        if self.file_error is not None:
            self.file_error.write(text)
            self.file_error.flush()

sys.stderr=RedirectErr(sys.stderr)


def SendBugReport():
    """
    Fonction qui envoie le rapport de bug par mail.
    """
    #
    # On ouvre le fichier qui contient les erreurs
    #
    import webbrowser, datetime

    message=_(u"pySyLiC a rencontré une erreur et doit être fermé.\nVoulez-vous envoyer un rapport de bug ?")
    dlg=wx.MessageDialog(None,message,_("Erreur"), wx.YES_NO| wx.ICON_ERROR).ShowModal()
    if dlg==5103:#YES, on envoie le mail
        #
        # Définition du mail
        #
        e_mail="cedrick.faury@freesbee.fr"
        now = str(datetime.datetime.now())
        subject=_(u"pySyLiC ") + globdef.VERSION
        subject+= _(u" : rapport de bug") + now
#        body="<HTML><BODY><P>"
        body =_(u"Le bug suivant s'est produit le ") + now
        body+= "%0A"
#        body+=("""
#        """)
        body+=_(u"Merci de décrire ci-dessous l'opération ayant provoqué le bug :")
        body+="%0A%0A%0A%0A%0A=================TraceBack===================="
        #
        # Parcours du fichier
        #
        file_error=open(globdef.ERROR_FILE,'r')
        for line in file_error.readlines():
            body+=line+"%0A"
        file_error.close()
        body+="==============================================%0A%0A"
        body+=_(u"L'équipe de développement de pySyLiC vous remercie pour votre participation.")
#        body+="</P></BODY></HTML>"
        file_error.close()
        to_send="""mailto:%s?subject=%s&body=%s"""%(e_mail,subject,body)
        #
        # On vérifie si l'utilisateur travaille avec Outlook
        #
#        try:
#            outlook_app = Dispatch("Outlook.application")
#            msg = outlook.CreateItem(0)
#            msg.To = e_mail
#            msg.Subject = subject
#            msg.Body = body
#            msg.Send()
#        #
#        # Sinon on ouvre son client de messagerie normal
#        #
#        except:
        print "Envoi ...",to_send
        print webbrowser.open("""mailto:%s?subject=%s&body=%s"""%(e_mail,subject,body))


if __name__=='__main__':
    sys.stderr = RedirectErr(sys.stderr)
#    print r
    