#!/usr/bin/env python
# -*- coding: utf-8 -*-

##This file is part of PySylic
#############################################################################
#############################################################################
##                                                                         ##
##                                 Calcul                                 ##
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
#    along with pySylic; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


from scipy.signal import lti, lsim, step, impulse
from scipy import interpolate#, #\
                  #pi, log10, ones, sin, zeros_like, nan, inf, argmin
from scipy.optimize import fsolve, fmin#, fmin_powell
from numpy import poly1d, angle, logspace, linspace, concatenate, \
                  append, rad2deg, delete, insert, isnan, real, inf, \
                  array, arange, unwrap, seterr, sqrt, round
#import scipy.linalg as linalg
import scipy
#scipy.seterr(all = "raise")
seterr(all = 'ignore')

import globdef
import wx

from CedWidgets import *

# Pour débuggage !!
#from matplotlib.pyplot import gcf, setp, getp

try:
    import psyco
    HAVE_PSYCO=True
except ImportError:
    HAVE_PSYCO=False


import traceback
import warnings
import sys

# Pour débuggage : traceback des warning
#def warn_with_traceback(message, category, filename, lineno, file=None, line=None):
#    traceback.print_stack()
#    log = file if hasattr(file,'write') else sys.stderr
#    log.write(warnings.formatwarning(message, category, filename, lineno, line))
#
#warnings.showwarning = warn_with_traceback

warnings.filterwarnings("ignore")

class FonctionTransfertNum:
    def __init__(self, polyN = [1.0], polyD = [1.0], nom = "H", retard = 0, 
                 rapide = False, pulsRes = []):
        self.nom = nom
        self.retard = retard
        
        if not isinstance(polyN, poly1d):
#            print polyN
            self.polyN = poly1d(polyN)
        else:
            self.polyN = polyN
            
        if not isinstance(polyD, poly1d):
            if isinstance(polyD[0], poly1d): # Cas spécial en cas de FTBF avec retard dans la FTBO
                # Données pour getMathText
                self.polyNreel = polyD[1]
                self.polyDD = polyD[0]
                # Approximation de Padé
                num, den = pade(self.retard, 3)
                D = polyD[0]
                N = polyD[1]
                self.polyD = den*D+num*N
                self.polyN = den*self.polyN
            else:
                self.polyD = poly1d(polyD)
        else:
            self.polyD = polyD

        self.pulsRes = pulsRes
        
        if not rapide:
            self.classe = self.getClasse()
            self.gainStat = self.getGainStatique()
            self.cassures = self.getPulsationCassures()
            # réponse de référence (pour calcul de Phi ABSOLU)
            self.reponse0 = self.getReponseHarmoniqueBlack(50, rapide = True)
        
        
    def __repr__(self):
        nn = ' '*(len(self.nom) +4)
        N1, N2 = self.polyN.__str__().split('\n')
        D1, D2 = self.polyD.__str__().split('\n')
        bb = '-'*(max(len(N2),len(D2))+2)
        F = nn+N1+'\n'+nn+N2+'\n'+self.nom+" = "+bb+'\n'+nn+D1+'\n'+nn+D2
        return F

    
    def __mul__(self, ft):
        if isinstance(ft, FonctionTransfertNum):
            return FonctionTransfertNum(self.polyN * ft.polyN, self.polyD * ft.polyD, 
                                        retard = self.retard + ft.retard, pulsRes = self.pulsRes)
        else:
            return FonctionTransfertNum(self.polyN * ft, self.polyD, 
                                        retard = self.retard, pulsRes = self.pulsRes)
    
    
    #######################################################################################
    def egaleUn(self):
#        if self.retard == 0:
#            return False
        un = len(self.polyN) == len(self.polyD)
        for i, p in enumerate(self.polyN):
            un = un and (p == self.polyD[i])
        return un
    
    
    def getPoles(self):
        return aproxComplexes(self.polyD.r)
    
    def getZeros(self):
        return aproxComplexes(self.polyN.r)
    
    def getNbrZeroPos(self):
        i = 0
        for z in self.getZeros():
            if z.real > 0:
                i += 1
        return i
    
    def getNbrPolePos(self):
        i = 0
        for z in self.getPoles():
            if z.real > 0:
                i += 1
        return i
            
    def estStable(self):
        for p in self.getPoles():
            if p.real >= 0:
                return False
        return True
    
    
    #######################################################################################
    def getClasse(self):
        """ Renvoie la classe de la FT
            (fonction normalement appelée 1 seule fois : à l'instanciation de la FT)
        """
        pn = 0
        zn = 0
        for p in self.getPoles():
            if p == 0:
                pn += 1
        for z in self.getZeros():
            if z == 0:
                zn +=1
                
        return pn - zn
    
    
    #######################################################################################
    def getGainStatique(self):
        """ Renvoie le gain statique de la FT
            (fonction normalement appelée 1 seule fois : à l'instanciation de la FT)
        """
        
        def polyCano(poly):
            rn = poly.r.tolist().count(0.0)
            
            p = poly1d([1.0] + [0.0] * rn)
            
            return poly/p

        coefN = polyCano(self.polyN)[0](0)
        coefD = polyCano(self.polyD)[0](0)
        return coefN / coefD
    
    
    #######################################################################################
    def getPulsationsResonance(self, lstFT):
        """ Renvoie les pulsations de résonance
            (fait lors de la décomposition)
        """
        self.pulsRes = []
        for f in lstFT:
            if f.est2ndOrdre() or f.estInv2ndOrdre():
                K,Om,Z,S = f.getCoef2nd()
                if Z < 1/sqrt(2):
                    OmRes = Om*sqrt(1-2*Z*Z)
                    if not isnan(OmRes):
                        if Z != 0:
                            Res = 0 # Valeur finie
                        else:
                            if f.est2ndOrdre():
                                Res = 1 # Valeur +infini
                            else:
                                Res = -1
                        self.pulsRes.append((OmRes, Res))
                        f.pulsRes = [(OmRes, Res)]

        
    #######################################################################################
    def getPulsationCassures(self):
        """ Renvoie les pulsations de cassure de la FT
            (fonction normalement appelée 1 seule fois : à l'instanciation de la FT)
            >>> array
        """
        c = abs(array(self.getZeros()+ self.getPoles()))
        c.sort()
        return c
    
    
    #######################################################################################
    def getRangeDecade(self):
        """ Renvoie un intervalle, en décade, 
            "adapté" à la visualisation des cassures
        """

        r = abs(self.cassures).tolist()

        try:
            while True : r.remove(0.0)
        except:
            pass
        if r != []:
            mini = decade(r[0]) - 1
            maxi = decade(r[-1]) + 2
            return [mini, maxi]
        else:
            return [-1, 1]
        
    
    #######################################################################################
    def getRange(self, rng = None):
        """ Renvoie un intervalle, 
            "adapté" à la visualisation des cassures
        """
        if rng == None:
            rng = self.getRangeDecade()
        return [10**rng[0], 10**rng[1]]
    
    
    #######################################################################################
    def getLambda(self):
        with errstate(invalid='ignore'): 
            if self.classe > 0:
                return 2.3
            else:
                return roundN(20*log10(1.3*self.gainStat/(self.gainStat+1)))[0]
        
        
    #######################################################################################
    def getFormeCanonique(self):
        """ Renvoie la FT sous sa forme canonique :
                K : gain statique
                c : classe
                lstFT : liste des sous FT simples
        """

        # pour factoriser un polynôme
        def decompose(racines, mult):
            morceaux = []
            n = 0
            while n < len(racines):
                z = racines[n]
                if estReel(z): # Racines réelles
                    if z.real == 0.0:
                        mult = 1
                    morceaux.append(poly1d([1.0,-z.real])*mult)
                    mult = 1
                    n += 1
                else:
                    morceaux.append(poly1d([1.0,-2*z.real, z.real**2+z.imag**2])*mult)
                    mult = 1
                    n += 2
            return morceaux
        
        zeros = self.getZeros()
        poles = self.getPoles()

#        print "zéros", zeros
        
        numerateur = decompose(zeros, self.polyN.c[0])
        denominateur = decompose(poles, self.polyD.c[0])
        
        lstFT = []
        if numerateur == [] and denominateur == []:
            ft = FonctionTransfertNum()
            lstFT.append(ft)
        
#        for m in numerateur+denominateur:
#            if m.c[-1] == 0.0:
#                N = m
#                D = poly1d(1.0)
#            else:
#                N = m/m.c[-1]
#                D = poly1d(1.0)
#            lstFT.append(FonctionTransfertNum(N,D))  
            
        for m in numerateur:
            if m.c[-1:][0] == 0.0:
                N = m
                D = poly1d(1.0)
            else:
                N = m/m.c[-1:][0]
                D = poly1d(1.0)#(1/m.c[-1:][0])
            lstFT.append(FonctionTransfertNum(N,D))
        
        for m in denominateur:
#            print "Denom :", m
            if m.c[-1:][0] == 0.0:
                D = m
                N = poly1d(1.0)
            else:
                D = m/m.c[-1:][0]
                N = poly1d(1.0)#1/m.c[-1:][0])
            lstFT.append(FonctionTransfertNum(N,D))
            
#        lstFT[0].polyN = lstFT[0].polyN*[self.polyN.c[0]/self.polyD.c[0]]
#        print self.gainStat, lstFT
        self.getPulsationsResonance(lstFT)
#        print self.pulsRes
#        for f in lstFT:
#            print "  ", f.pulsRes
        return self.gainStat, lstFT
        
        
    #######################################################################################
    def getOrdre(self):
        return self.polyD.o
    
    
#    #######################################################################################
#    def getGain(self):
#        if self.estDerivPur() or self.estIntegPur():  
#            return self.polyN[0]
#        else:
#            return 1.0
    
    #######################################################################################
    def est2ndOrdre(self):
        return self.getOrdre() == 2 and self.polyN.o == 0 and self.polyD.c[2] != 0.0
    
    #######################################################################################
    def est1erOrdre(self):
        return self.getOrdre() == 1 and self.polyN.o == 0
    
    #######################################################################################
    def estInv2ndOrdre(self):
        return self.getOrdre() == 0 and self.polyN.o == 2 and self.polyN.c[2] != 0.0
    
    #######################################################################################
    def estInv1erOrdre(self):
        return self.getOrdre() == 0 and self.polyN.o == 1
    
    #######################################################################################
    def estDerivPur(self):
        return self.polyD.o == 0 and sum(self.getZeros()) == 0.0
    
    #######################################################################################
    def estIntegPur(self):
        return self.polyN.o == 0 and sum(self.getPoles()) == 0.0
    
    #######################################################################################
    def getCoef2nd(self):
        with errstate(invalid='ignore'): 
            if self.est2ndOrdre():
                polyCar = self.polyD
    #            poly0 = self.polyN
                K = self.gainStat
            elif self.estInv2ndOrdre():
                polyCar = self.polyN
    #            poly0 = self.polyD
                K = 1.0/self.gainStat
            else: return 0,0,0,0
            
    #        K = poly0.c[0]
            
            O2 = polyCar.c[2]/polyCar.c[0]
            S = sign(O2)
            Om = sqrt(abs(O2))
            Z = Om*(polyCar.c[1]/polyCar.c[2])/2
            
            return K,Om,Z,S
    
    #######################################################################################
    def getCoef1er(self):
        with errstate(invalid='ignore'): 
            if self.est1erOrdre():
                polyCar = self.polyD
                K = self.gainStat
            elif self.estInv1erOrdre():
                polyCar = self.polyN
                K = 1/self.gainStat
            else: 
                return 0, 0, 0
            
            T = -1.0/polyCar.r[0]#c[0]/K
            S = sign(T)
            T = abs(T)
            return K, T, S
    
    
    ######################################################################################################
    def getDiagAsympGainPhase(self):
#        if globdef.DEBUG:
#            print "getDiagAsymp Gain Phase..."
            
        with errstate(invalid='ignore'): 
            if self.estDerivPur():
                ordre = self.polyN.o
                K = self.gainStat
    #            print "Dérivateur : ordre =", ordre, "gain =", K
                diagG = DiagAsympGain(0.0, [AsympGain(0.0, ordre*20.0)], KdB = 20*log10(K))
                diagP = DiagAsympPhase(0.0, [AsympPhase(0.0, ordre*90.0)])
                return diagG, diagP
            
            elif self.estIntegPur():
                ordre = self.polyD.o
                K = self.gainStat
    #            print "Intégrateur : ordre =", ordre, "gain =", K
                diagG = DiagAsympGain(0.0, [AsympGain(0.0, -ordre*20.0)],  KdB = 20*log10(K))
                diagP = DiagAsympPhase(0.0, [AsympPhase(0.0, -ordre*90.0)])
                return diagG, diagP
            
            elif self.est1erOrdre() or self.estInv1erOrdre():   
                if self.est1erOrdre():
                    s = 1
                else:
                    s = -1
                    
                K,T,S = self.getCoef1er()
#                print "K =", K, ", T =", T, ", S =", S
                omegaC = 1/T
                a1 = AsympGain(0.0, 0.0)
                a2 = AsympGain(omegaC, -s*20.0)
                diagG = DiagAsympGain(0.0, [a1,a2], KdB = s*20*log10(K))
    #            print diagG
                a1 = AsympPhase(0.0, 0.0)
                a2 = AsympPhase(omegaC, -s*S*90.0)
                diagP = DiagAsympPhase(0.0, [a1,a2])
                
                return diagG, diagP
        
            elif self.est2ndOrdre() or self.estInv2ndOrdre():
    #            if globdef.DEBUG: print "  2nd Ordre"
                
                if self.est2ndOrdre():
                    s = 1
                else:
                    s = -1
                
                K, Om, Z, S = self.getCoef2nd()
              
#                if globdef.DEBUG: print "  Coefs :", K, Om, Z, S
                
                if globdef.DECOMP_2ND_ORDRE and Z >= 1:
                    diagG, diagP = None, None
    
                    K, lstFT = self.getFormeCanonique()
                    
                    # Ca évite de grosss problèmes de recursion infinie...
                    if len(lstFT) == 1:
                        d = globdef.DECOMP_2ND_ORDRE
                        globdef.DECOMP_2ND_ORDRE = False
                        diagG, diagP = lstFT[0].getDiagAsympGainPhase()
                        globdef.DECOMP_2ND_ORDRE = d
                        return diagG, diagP
                    
#                    print "  Decomp :", K, lstFT
                    lstFT[0] = FonctionTransfertNum(lstFT[0].polyN * K, lstFT[0].polyD)
                    for ft in lstFT:
                        dG, dP = ft.getDiagAsympGainPhase()
                        diagG = dG + diagG
                        diagP = dP + diagP
    
                    return diagG, diagP
                        
                else:
                    
    #                print "K =", K, ", Om =", Om, ", Z =", Z, ", S =", S
                    a1 = AsympGain(0.0, 0.0)
                    a2 = AsympGain(Om, -s*40.0)
                    diagG = DiagAsympGain(0.0, [a1,a2], KdB = s*20*log10(K))
                    
                    a1 = AsympPhase(0.0, 0.0)
                    a2 = AsympPhase(Om, -s*sign(Z)*180.0)
                    diagP = DiagAsympPhase(0.0, [a1,a2])
                    return diagG, diagP
            
            else:
                diagG, diagP = None, None
    
                K, lstFT = self.getFormeCanonique()

                lstFT[0] = FonctionTransfertNum(lstFT[0].polyN * K, lstFT[0].polyD)
                for ft in lstFT:
                    dG, dP = ft.getDiagAsympGainPhase()
                    diagG = dG + diagG
                    diagP = dP + diagP

                return diagG, diagP
    
        
    #######################################################################################
    def getDiagNyquist(self, pulsas, rapide):
#        self.reponse = self.getReponseHarmoniqueNyquist(pulsas)
        self.reponseN = self.getReponseHarmoniqueNyquist(pulsas, rapide)
        return DiagNyquist(self.reponseN)
    
    #######################################################################################
    def getDiagBlack(self, pulsas, rapide):
#        self.reponse = self.getReponseHarmoniqueBlack(pulsas)
        self.reponseB = self.getReponseHarmoniqueBlack(pulsas, rapide)
        return DiagBlack(self.reponseB)
    
    #######################################################################################
    def getDiagBode(self, pulsas):
        self.reponseP, self.reponseG = self.getReponseHarmoniqueBode(pulsas)
        return DiagBode(self.reponseP), DiagBode(self.reponseG)
        
#    ######################################################################################################
#    def getReponseImpulsionnelle(self, rangeT = None):
#        if self.polyD.o == 0 and self.polyN.o == 0:
#            return None
#        
#        if rangeT == None:
#            N = NBR_PTS_REPONSE
#            _T = None
#        else:
#            _T = arange(0, rangeT[1], (rangeT[1]-rangeT[0])/NBR_PTS_REPONSE)
#            N = None
#            
#        x = scipy.zeros(NBR_PTS_REPONSE)
#        x[0] = PINF
#        h = scipy.signal.lfilter(self.polyN, self.polyD, x) 
#        
#        return Tp, yout
    
    #######################################################################################
    def getSystem(self):
        with errstate(invalid='ignore'): 
            try:
                return lti(self.polyN,self.polyD)
            except ValueError:
                pass
                print ("Improper transfer function")
            
    ###################################################################################################
    def getAutoRange(self, N = 100):
        with errstate(invalid='ignore'): 
#            vals = linalg.eigvals(sys.A)
            vals = self.getPoles()
            c = min(abs(real(vals)))
            if c != 0.0:
                tc = 1.0/c
            else:
                tc = 1.0
            return linspace(0, 7*tc, N)
         
         
    ######################################################################################################
    def getReponseTempoRetard(self, T, Y):
        """ Renvoie la réponse temporelle T,Y retardée de self.retard
        """
        if self.retard != 0:
            T = concatenate(([0, self.retard], T + self.retard))[:-2]
            Y = concatenate(([0, 0], Y))[:-2]
            return T, Y
        else:
            return T, Y
    
    
    ######################################################################################################
    def getReponseImpulsionnelle(self, rangeT = None):
        if self.polyD.o == 0 and self.polyN.o == 0:
            gain = self.polyN.c[0]/self.polyD.c[0]
            return None, gain, rangeT
        
        if rangeT == None: # Intervalle des temps "Automatique"
            N = globdef.NBR_PTS_REPONSE
            if self.estStable():
                _T = None
            else:
                # On estime "é la louche le temps de réponse"
                _T = self.getAutoRange(N)*3
        else:
            _T = arange(0, rangeT[1], (rangeT[1]-rangeT[0])/globdef.NBR_PTS_REPONSE)
            N = None
        
        sys = self.getSystem()
        if sys == None:
            return None, None
        else:
            res = impulse(sys, T = _T, N = N)#, full_output = True)
            Tp, yout = res[0], res[1]
            Tp, yout = self.getReponseTempoRetard(Tp, yout)
            return Tp, yout
    
    ######################################################################################################
    def getReponseIndicielle(self, amplitude, rangeT = None):
        if self.polyD.o == 0 and self.polyN.o == 0:
            gain = self.polyN.c[0]/self.polyD.c[0]
            return None, gain, rangeT
        
        if rangeT == None:
            N = globdef.NBR_PTS_REPONSE
            if self.estStable():
                _T = None
            else:
                # On estime "à la louche le temps de réponse"
                _T = self.getAutoRange(N)*3
        else:
            _T = arange(0, rangeT[1], (rangeT[1]-rangeT[0])/globdef.NBR_PTS_REPONSE)
            N = None
            
        sys = self.getSystem()
        if sys == None:
            return None, None, None
        else:
            Tp, yout = step(sys, T = _T, N = N)
            Tp, yout = self.getReponseTempoRetard(Tp, yout*amplitude)
            return Tp, yout, self.gainStat
        
    
      
    ######################################################################################################
    def getReponseRampe(self, pente, rangeT = None):
        if self.polyD.o == 0 and self.polyN.o == 0:
            gain = self.polyN.c[0]/self.polyD.c[0]
            return None, gain, rangeT
                
        if rangeT == None:
            sys = self.getSystem()
            if sys == None:
                return None, None
            _T = self.getAutoRange(globdef.NBR_PTS_REPONSE)

        else:
            _T = arange(0, rangeT[1], (rangeT[1]-rangeT[0])/globdef.NBR_PTS_REPONSE)
            
        _U = pente * _T

        return self.getReponse(_U, _T)


    ######################################################################################################
    def getReponseSerieImpulsions(self, periode, rangeT = None):
        if rangeT == None:
            rangeT = [0.0, globdef.NB_PERIODES_REP_TEMPO*periode] 
        
        sys = self.getSystem()
        if sys == None:
            return None, None
        
        np = (rangeT[1]-rangeT[0]) // periode # nombre de périodes entières dans rangeT
        
        if np == 0:
            ppp = globdef.NBR_PTS_REPONSE
        else:
            ppp = int(globdef.NBR_PTS_REPONSE/np) # points par période
        
        Tref = linspace(0, periode, ppp)
        _U = []

        ntp = int(rangeT[1]/periode) 
        if ntp != rangeT[1]/periode:
            ntp += 1        # Nombre total de périodes  
        
        t1 = ntp * periode # instant final multiple de <periode>

        T = arange(0, t1, t1/ppp/ntp).tolist()
        
        if self.polyD.o == 0 and self.polyN.o == 0:
            gain = self.polyN.c[0]/self.polyD.c[0]
            return None, gain, T
        
        continuer = True
        c = 0
        R = array([0.0] * ppp * ntp)

        while continuer:
            if c >= ntp:
                continuer = False
            else:
                t0 = c*periode

                Tref = arange(0, t1-t0, periode/ppp)[0:len(R)-c*ppp]
                
                h = impulse(sys, T = Tref)[1]
                z = [0.0] * c * ppp
                
                h  = array(z+h.tolist())
                R = R + h
                c += 1
                
        R = R.tolist()
        
        _T = []
        _R = []
        for i in range(min(len(T), len(R))):
            if T[i] > rangeT[0] and T[i] < rangeT[1]:
                _T.append(T[i])
                _R.append(R[i])
                
        Tp, Yout = self.getReponseTempoRetard(array(_T), array(_R))
        return Tp, Yout
    
    
    
    
    ######################################################################################################
    def getReponseCarre(self, amplitude, periode, decalage, rangeT = None):
#        print "getReponseCarre", rangeT
        if rangeT == None:
            rangeT = [0.0, globdef.NB_PERIODES_REP_TEMPO*periode]
            
        if self.polyD.o == 0 and self.polyN.o == 0:
            gain = self.polyN.c[0]/self.polyD.c[0]
            return None, gain, rangeT
        
        _T = arange(0, rangeT[1], (rangeT[1]-rangeT[0])/globdef.NBR_PTS_REPONSE)
        _U = []
        for t in _T:
            _U.append(carre(t, amplitude, periode, decalage))
            
        return self.getReponse(_U, _T)
    
    
    ######################################################################################################
    def getReponseTriangle(self, pente, periode, decalage, rangeT = None):
#        print "getReponseTriangle", rangeT
        if rangeT == None:
            rangeT = [0.0, globdef.NB_PERIODES_REP_TEMPO*periode]
        
        if self.polyD.o == 0 and self.polyN.o == 0:
            gain = self.polyN.c[0]/self.polyD.c[0]
            return None, gain, rangeT

        _T = arange(0, rangeT[1], (rangeT[1]-rangeT[0])/globdef.NBR_PTS_REPONSE)
        _U = []
        for t in _T:
            _U.append(triangle(t, pente, periode, decalage))
            
        return self.getReponse(_U, _T)
    
    
    ######################################################################################################
#    def getReponseSinus(self, amplitude, pulsation, decalage, rangeT = None):
#        temps, result = chronometrer(self.getReponseSinus2, amplitude, pulsation, decalage, rangeT = None)
#        print "Calcul réponse Sinus:",temps
#        return result
    
    ######################################################################################################
    def getReponseSinus(self, amplitude, pulsation, decalage, rangeT = None, nbPts = None):
#        print "getReponseSinus", rangeT
        if nbPts == None:
            nbPts = globdef.NBR_PTS_REPONSE
      
        if rangeT == None:
            rangeT = [0.0, globdef.NB_PERIODES_REP_TEMPO*2*pi/pulsation]
            
        if self.polyD.o == 0 and self.polyN.o == 0:
            gain = self.polyN.c[0]/self.polyD.c[0]
            return None, gain, rangeT

        _T = arange(0.0, rangeT[1], (rangeT[1]-rangeT[0])/nbPts)
        _U = sinus(_T, amplitude, pulsation, decalage)
        
#        _U = []       
#        for t in _T:
#            _U.append(sinus(t, amplitude, pulsation, decalage))
        dt, rep = chronometrer(self.getReponse,_U, _T)
#        print "Rep Sinus :", dt
#        rep = self.getReponse(_U, _T)
        
        return rep
    
    ######################################################################################################
    def getReponsePerso(self, U, T, rangeT = None):
#        print "getReponsePerso", U, T
        return self.getReponse(U, T)
        
        
    ######################################################################################################
    def getReponse(self, U, T):
        with errstate(invalid='ignore'): 
            if self.polyD.o == 0 and self.polyN.o == 0:
                gain = self.polyN.c[0]/self.polyD.c[0]
                return None, gain, None
            
            sys = self.getSystem()
            if sys == None:
                return None, None
            
            if globdef.LSIM_SOLVER == 0: # à éviter ...
                Tp, Yout = scipy.signal.lsim(sys, U, T, interp = globdef.INTERPOLATION)
            else:
                
                Tp, Yout, xout = lsim(sys, U, T)#, atol = globdef.LSIM_TOLERANCE)
    
            Tp, Yout = self.getReponseTempoRetard(Tp, Yout)
            return Tp, Yout
    
    
    #########################################################################################################
    def getPhiRetard(self, w, Phi):
        return Phi - self.retard * w
        
        
    #########################################################################################################
    def getReponseHarmoniquePhi(self, pulsas):
#        print "getReponseHarmoniquePhi"#, pulsas
        with errstate(invalid='ignore'): 
            w, h = self.getReponseHarmonique(pulsas)
            Phi = rad2deg(unwrap(angle(h)))
            #
            # Correction en fonction de Phi(0)
            #    par rapport à Phi(0) lors du calcul de reponse0 !!
            #    par rapport à Phi(min) sinon
            #

            if type(pulsas) == int:
                Phi = Phi -180* (round((Phi[0]-self.Phi0())/180))
            else:
                Phi = Phi -180* (round((Phi[0]-self.Phi(pulsas[0]))/180))
    
            return w, self.getPhiRetard(w, Phi)
    
    
#    #########################################################################################################
#    def getPulsResonance(self):
#        if self.getOrdre() < 2:
#            return None, None
#        
#        # fonction à minimiser
#        def freq(w):
#            w, h = scipy.signal.freqs(self.polyN, self.polyD, [w])
#            H = abs(h[0][0])
#            return -H
#        
#        #
#        # On cherche les maxi à proximité des cassures
#        #
#        c = self.cassures[:]
#        c = list(set(c))
#        if len(c) > 0:
#            res = fmin_powell(freq, c[0], full_output = True, disp = False)
#            w = res[0]
#            h = -res[1]
#            warnflag = res[4]
#        
#            if isnan(h):
#                HdB = inf
#            else:
#                HdB = 20.0*log10(h)
#
#        return w, HdB
        
        
    #########################################################################################################
    def lisserReponse(self, pulsas = None, reponsePhi = None, coef = 1.0):
        """ Renvoie une série de pulsation mieux adaptée pour éviter les irrégularité de tracé.
            Principe : variations de Phi limitées ...
            <coef> > 1 pour affiner encore le lissage (utile pour Nyquist)
        """
        with errstate(invalid='ignore'): 
            if reponsePhi == None:
                reponsePhi = self.getReponseHarmoniquePhi(pulsas)
            
            w, Phi = reponsePhi

            #
            # On insert des points (w) si intervalle de Phi trop grand
            #
            continuer = True
            i = 0
            c = 0 # compteur anti plantage !!! ((:::
            while continuer:
                if i<len(w)-1 and i < 3000:
                    if abs(Phi[i+1] - Phi[i]) > globdef.DELTA_PHI_MAXI/coef and c < 20:
                        w = insert(w, [i+1], (w[i] + w[i+1])/2 )
                        Phi = insert(Phi, [i+1], self.Phi(w[i+1]))
                        c += 1
                    else:
                        if c >= 20: print ("! PLANTAGE LisserReponse !")
                        i += 1
                        c = 0
                else:
                    continuer = False
            
            return w
            
    
        
    #########################################################################################################
    def getReponseHarmonique(self, pulsas):
        """ Renvoie la réponse harmonique
            --> forme complexe "brute"
            sans tenir compte du retard
        """
#        print "getReponseHarmonique"#, pulsas
        with errstate(invalid='ignore'): 
            # On évite les problèmes de précision de calcul 
            # en remplaçant les FT au numérateur égal au dénominateur
            # par 1/1.
            if self.egaleUn():
                w, h = scipy.signal.freqs(array([1.0]), array([1.0]), pulsas)
                
            else:
                w, h = scipy.signal.freqs(self.polyN, self.polyD, pulsas)
            
            return w, h
        
        
    #########################################################################################################
    def getReponseHarmoniqueNyquist(self, pulsas, rapide = False):
        if not rapide:
            w = self.lisserReponse(pulsas, coef = 4.0)
        else:
            w = pulsas
        w, h = self.getReponseHarmonique(w)
        if self.retard != 0:
            h = h * exp(-self.retard * 1j * w)
        reponse = w, h.real, h.imag
        return reponse
    
    
    #########################################################################################################
    def getReponseHarmoniqueBlack(self, pulsas, rapide = False):
#        print "getReponseHarmoniqueBlack", self
        with errstate(invalid='ignore'): 
            if not rapide:
                w = self.lisserReponse(pulsas)
                
                #            
                # On ajoute les pulsations de résonance le cas échéant
                #
                for wr,r in self.pulsRes:
                    if r == 0: # résonance "finie"
                        w = append(w, wr)
                    else: # résonance "infinie" (il faut éviter un calcul à la pulsation de résonance)
                        # Calcul d'une fraction de l'intervalle de l'axe log(w)
                        I = (w[-1]/w[0])**(0.000001)
                        wa = wr/I
                        wb = wr*I
                        w = append(w, [wa, wb]) 
                        # On vérifie que wr n'est pas déja dans la liste !
                        continuer = True
                        i = 0
                        l = []
                        while continuer:
                            if i < len(w):
                                if w[i] > wa and w[i] < wb:
                                    l.append(i)
                                i += 1
                            else:
                                continuer = False  
                        w = delete(w,l)
#                        a = argmin(abs(w-wr))
#                        if w[a] == wr:
#                            w = delete(w, [a])
                w.sort()
            else:
                w = pulsas
            
            #
            # On calcul la réponse ... pour de bon
            #
            w, h = self.getReponseHarmonique(w)
           
            HdB = 20.0 * log10(abs(h))
            Phi = rad2deg(unwrap(angle(h)))
            
            #
            # On corrige le "unwrap" en cas de résonance infinie
            #
            for wr,r in self.pulsRes:
                if r != 0:
                    continuer = True
                    i = 0
                    if w[i] < wr:
                        while continuer:
                            if i < len(w)-1:
                                if w[i+1] > wr:
                                    if sign(Phi[i+1] - Phi[i]) == r:
                                        Phi = concatenate((Phi[:i+1], Phi[i+1:]-r*360))
                                i += 1
                            else:
                                continuer = False  
            
            #
            # Correction globale en fonction de Phi(0)
            #    par rapport à Phi(0) lors du calcul de reponse0 !!
            #    par rapport à Phi(min) sinon
            #
            if type(pulsas) == int: # lors du calcul de reponse0
#                print "   ", Phi[0], self.Phi0(),
                Phi = Phi -180* (round((Phi[0]-self.Phi0())/180))
#                print "-->", Phi[0]
            else:
                Phi = Phi -180* (round((Phi[0]-self.Phi(pulsas[0]))/180))
    
            if globdef.INTERPOLER:
                tckw = interpolate.splrep(w, HdB, s=0)
                tckp = interpolate.splrep(w, Phi, s=0)
                w = logspace(log10(w[0]), log10(w[-1]), num = globdef.NBR_PTS_COURBES*2)
                HdB = interpolate.splev(w, tckw, der=0)
                Phi = interpolate.splev(w, tckp, der=0)

            reponse = w, self.getPhiRetard(w, Phi), HdB
            return reponse
        
        
    #########################################################################################################
    def getReponseHarmoniqueBode(self, pulsas):
        rep = self.getReponseHarmoniqueBlack(pulsas)
        return (rep[0], rep[1]), (rep[0], rep[2])
        
    
    #########################################################################################################
    def Phi0(self):
        # A revoir !!!
        
        
        return -self.classe * 90 - self.getNbrPolePos() * 180# + self.getNbrZeroPos() * 180
    
    
    #########################################################################################################
    def Phi180(self, Om):
        """ Renvoie la phase comprise entre -180° et 180°
            !! sans tenir compte du retard !!
        """
        with errstate(invalid='ignore'): 
            c = self.polyN(1j*Om)/self.polyD(1j*Om)
            a = angle(c, True)
            return a
    
    
    #########################################################################################################
    def Phi(self, Om):
        """ Renvoie la phase ABSOLUE
        """
        with errstate(invalid='ignore'): 
            #
            # valeur "brute" de l'angle
            #
            if Om is None: return None
            
            a = self.Phi180(Om)
    
            #
            # Correction de l'angle à l'aide de réponse0
            #
            
            # On cherche la valeur de Phi(Om) dans reponse0 (approx)
            w = self.reponse0[0] # La liste des pulsations
#            n = len(w)-1
#            i = -1
            if Om <= w[0]:
                PhiA = self.reponse0[1][0]
                OmA = w[0]
            elif Om >= w[-1]:
                PhiA = self.reponse0[1][-1]
                OmA = w[-1]
            else:
                continuer = True
                i = 0
                while continuer:
                    if i < len(w)-1:
                        if w[i+1] > Om:
                            continuer = False
                        else:
                            i += 1
            
                PhiA = (self.reponse0[1][i] + self.reponse0[1][i+1])/2
                OmA = (self.reponse0[0][i] + self.reponse0[0][i+1])/2
            
            # On enlève l'effet du déphasage
            PhiA = PhiA + OmA * self.retard
            
#            print "PhiA(",w[i],") =", PhiA , "(",i,")"
            
#            # On cherche la position la plus proche de Om dans self.reponse0[0]
#            n = len(self.reponse0[0])-1
#            if Om <= self.reponse0[0][0]:
#                i = 0
#            elif Om >= self.reponse0[0][-1]:
#                i = n
#            else:
#                i = 0
#                s0 = sign(self.reponse0[0][0] - Om)
#                continuer = True
#                while continuer:
#                    Om0 = self.reponse0[0][i]
#                    s = sign(Om0 - Om)
#                    i += 1
#                    if s != s0 or i >= n:
#                        i += -1
#                        continuer = False
#                    
#    #        print "  i =",i,self.reponse0[1][i-1]
#            
#    #        print len(self.reponse0[0])
#    #        if i < len(self.reponse0[0]):
#            # Phi "aproximatif"
#            PhiA = self.reponse0[1][i]
#            print "  ", a, "<-->", PhiA
            
            a = a + sign(PhiA)*round(abs(PhiA-a) / 180) * 180
            
            # On remet l'effet du déphasage
            a = self.getPhiRetard(Om, a)

            return a
        
    def derivee(self, fct, Om):
        with errstate(invalid='ignore'): 
            dd = 0.001
            return  (fct(Om*(1+dd)) - fct(Om*(1-dd))) / log10((1+dd)/(1-dd))
    
    
    def deriveedHdP(self, fct1, fct2, Om):
        with errstate(invalid='ignore'): 
            dd = 0.001
            return  (fct1(Om*(1+dd)) - fct1(Om*(1-dd))) / (fct2(Om*(1+dd)) - fct2(Om*(1-dd)))


    def deriveeNyquist(self, Om):
        """ Renvoie la pente de la courbe de Nyquist
            à la pulsation Om
            (utilisé dans ZoneGraphNyquist)
        """
        dd = 0.001
        r1, i1 = self.H_real_imag(Om*(1-dd))
        r2, i2 = self.H_real_imag(Om*(1+dd))
        return  (r2 - r1) / (i2 - i1)
        
        
    def OmegaFctPhi(self, p, Om0):
        with errstate(invalid='ignore'): 
               
            def phi(Om):
                return self.Phi(Om) - p
            e = scipy.special.geterr()
            scipy.special.seterr(all = 'ignore')
            Om = fsolve(phi, Om0)
            scipy.special.seterr(**e)

            return Om
    
#    def dPhi(self, Om):
#        dd = 0.001
#        return  (self.Phi(Om*(1-dd)) - self.Phi(Om*(1+dd)))/log10((1+dd)/(1-dd))
#        
#    def dHdB(self, Om):
#        dd = 0.001
#        return  (self.HdB(Om*(1-dd)) - self.HdB(Om*(1+dd)))/log10((1+dd)/(1-dd))
        
    def FTBF(self):
        return FonctionTransfertNum(self.polyN, self.polyN + self.polyD, retard = self.retard)
    
    def HdB(self, Om):
        with errstate(invalid='ignore'): 
            if Om <= 0:
                h = None
                # print (Om, "!")
            else:
                h = 20 * log10(abs(self.polyN(1j*Om)/self.polyD(1j*Om)))
            return h
    
    def HdB_logOm(self, logOm):
        Om = 10**logOm
        return self.HdB(Om)
        
        
    def H(self, Om):
        with errstate(invalid='ignore'): 
            h = abs(self.polyN(1j*Om)/self.polyD(1j*Om))
            return h
    
    def H_real_imag(self, Om):
        p = self.polyN(1j*Om)/self.polyD(1j*Om)
        return p.real, p.imag
    
    def derivH(self, Om):
        ecart = 1.1
        continuer = True
        lderivh = 0.0
        while continuer:
            dh = self.H(Om*ecart) - self.H(Om/ecart)
            dw = Om*ecart - Om/ecart
            derivh = dh/dw
            if lderivh - derivh < globdef.PRECISION:
                continuer = False
            lderivh = derivh
            ecart = ecart/2
        return derivh
        
    def SurtensionFTBF(self, Om):
        with errstate(invalid='ignore'): 
    #        j = complex(0,1)
            FTBF = self.FTBF()
            h = abs(FTBF.polyN(1j*Om)/FTBF.polyD(1j*Om))
            K = self.gainStat
            h0 = K/(K+1)
            return h/h0
    
    def getPulsationSurtension(self):

        precision = globdef.PRECISION
       
        FTBF = self.FTBF()
        
        Om0 = FTBF.getPulsationCassures()[-1:][0]/10
        
        Om1 = FTBF.getPulsationCassures()[-2:][0]*10
        
        def maximum(o):
            m = FTBF.HdB(o)
            if m is not None:
                return -m
        
        # print(Om0, Om1)
        # print(FTBF.derivH(Om0) , FTBF.derivH(Om1))
        if Om1 > Om0 and FTBF.derivH(Om0) * FTBF.derivH(Om1) < 0.0:
            try:
                Om = fmin(maximum, Om1, maxfun=5000, maxiter=5000, disp = False)[0]
                return Om, self.HdB(Om), self.Phi180(Om), FTBF.HdB(Om), FTBF.Phi180(Om)
            except:
                return None, None, None, None, None
        else:
#            print "Pas Trouvé !"
            return None, None, None, None, None
        
        
    
    
        def racine(Om0, Om1):
            Om = (Om0 + Om1)/2
            dH = FTBF.derivH(Om)
            if abs(dH) < precision:
                return Om
            elif dH < 0:
                return racine(Om0, Om)
            else:
                return racine(Om, Om1)
        
        Om0 = FTBF.getPulsationCassures()[-1:][0]/10
        
        Om1 = FTBF.getPulsationCassures()[-2:][0]*10
        
        if Om1 > Om0 and FTBF.derivH(Om0) * FTBF.derivH(Om1) < 0.0:
            Om = racine(Om0, Om1)
            return Om, self.HdB(Om), self.Phi180(Om), FTBF.HdB(Om), FTBF.Phi180(Om)
        else:
#            print "Pas Trouvé !"
            return None, None, None, None, None
        
        return
    
    ########################################################################################
    def getPulsationCoupure(self):
        """ Renvoie la pulsation de coupure (H = 0dB)
            et la phase correspondante
            (principe : racines de HdB(w) recherchées à proximité des cassures
             en partant de la "dernière" x2)
        """
#        print "getPulsationCoupure"
        precision = globdef.PRECISION
        
        #
        # On cherche les racines à proximité des cassures
        # ... y compris une décade avant la première ...
        #
        c = self.cassures[:]
        c = list(set(c))
        
        # On terminera avant la première cassure si la classe est >=1
        if c[0] == 0 and len(c)>1:
            c[0] = c[1]/10.0
            
        # On commencera après la dernière cassure
        c.append(c[-1]*2)
        c.sort()
#        print "   ", c
        
        Om = None
        continuer = True
        i = len(c)-1
        while continuer:
            if i < 0:
                continuer = False
            else:
                e = scipy.special.geterr()
                scipy.special.seterr(all = 'ignore')
                O, ii, r, m = fsolve(self.HdB_logOm, c[i], full_output = 1)
                scipy.special.seterr(**e)
                Om = 10**O[0]
#                print "    ", Om, r
                if r == 1 and Om/c[i] > precision :

                    continuer = False
                i += -1
        
        #
        # On vérifie que Om est bien une vraie racine (et pas sur une asymptote)
        #
        if Om != None and (Om > 1000*max(self.cassures) or Om < min(self.cassures)/1000):
            Om = None
            
        return Om, self.Phi(Om)
    
        
        
#    def getPulsationCoupure2(self):
##        print "Calcul Om0"
#
#        precision = globdef.PRECISION
#        
#        def racine(Om0, Om1):
#            Om = (Om0 + Om1)/2
#            H = self.HdB(Om)
##            print "  ",Om, H
##            return
#            if abs(H) < precision:
#                return Om
#            elif H < 0:
#                return racine(Om0, Om)
#            else:
#                return racine(Om, Om1)
#        
#        Om0 = self.cassures[-1:][0]/10
#        Om1 = self.cassures[-2:][0]*10
##        print Om0, Om1
#        
#        if Om1 > Om0 and self.HdB(Om0) * self.HdB(Om1) < 0.0:
#            Om = racine(Om0, Om1)
#            return Om, self.Phi(Om)
#        else:
##            print "Pas Trouvé !"
#            return None, None
    
    #########################################################################################################
    def getPulsation180(self, Om0):
#        print "getPulsation180", self.cassures
        
        def P(om):
            return self.Phi(10**om) + 180
        
        Om = []
        continuer = True
        i = len(self.cassures)-1
        
        for cass in self.cassures:
            if cass > 0:
                e = scipy.special.geterr()
                scipy.special.seterr(all = 'ignore')
                logO, ii, r, m = fsolve(P, log10(cass), full_output = 1)
                scipy.special.seterr(**e)
                if r == 1:
                    Om.append(10**(logO[0]))
            
            
#        while continuer:
#            if i < 0:
#                continuer = False
#            else:
#                print "   ", self.cassures[i]
#                if self.cassures[i] > 0:
##                    e = scipy.geterr()
##                    scipy.seterr(all = 'ignore')
#                    logO, ii, r, m = fsolve(P, log10(self.cassures[i]), full_output = 1)
#                    print "  r=", r
##                    scipy.seterr(**e)
#                    if r == 1:
#                        Om.append(10**(logO[0]))
#    #                    continuer = False
##                    else:
##                        print m
#                i -= 1
        i = 1
        while i < len(Om):
            if isclose(Om[i], Om[i-1]):
                del Om[i]
            else:
                i += 1
        
        Om = list(set(Om))
        
        
        
#        print "Om =",Om
        if Om == []:
            Om = None
        elif len(Om) == 1:
            Om = Om[0]
        else:
            OOm = []
            for o in Om:
                h = self.HdB(o)
                if h < 0:
                    OOm.append(o)
            if OOm != []:
                Om = min(OOm)
            else:
                Om = None
            
            
        #
        # On vérifie que Om est bien une vraie racine (et pas sur une asymptote)
        #
        if Om != None and (Om > 1000*max(self.cassures) or Om < min(self.cassures)/1000):
            Om = None
            
        # Je ne sais plus pourquoi j'ai ajouté ça à partir de la 0.34
#        if Om0 != None and Om != None and Om < Om0:
#            Om = None
            
        # 
        # On détermine le sens
        #
#        print self.Phi(Om*(1-0.001)), self.Phi(Om*(1+0.001))
#        if Om != None:
#            if self.Phi(Om*(1-0.001)) < self.Phi(Om*(1+0.001)):
#                sens = -1
#            else:
#                sens = 1
#        else:
#            sens = 0
            
#        if Om != None and self.Phi(Om+Om/10) >= -180:
#            Om = None
#        print "Om =", Om
        if Om is None:
            return None, None
        return Om, self.HdB(Om)
    

        
#    #########################################################################################################
#    def getPulsation180(self):
##        print "Calcul Om180"
#        v = -180
#        precision = globdef.PRECISION
#        
##        self.c=0 # compteur pour debuggage
#        def racine(Om0, Om1):
#            Om = (Om0 + Om1)/2
#            P = self.Phi180(Om)
#            
##            print "  ",Om, P
#            
##            self.c+=1
##            if seloomf.c >10:
##                return 
#            
#            if abs(-abs(P)-v) < precision:
#                return Om
#            elif P > 0:
#                return racine(Om0, Om)
#            else:
#                return racine(Om, Om1)
#        
##        Om0 = self.getPulsationCassures()[-1:][0]/10
##        Om1 = self.getPulsationCassures()[-2:][0]*10
#
#        # On choisi un intervalle proche de la solution
#        Om0, Om1 = self.getIntervalle(2, v)
##        print Om0, Om1
#        
#        if Om1 > Om0 and (self.Phi(Om0)-v) * (self.Phi(Om1)-v) < 0.0:
#            Om = racine(Om0, Om1)
#            return Om, self.HdB(Om)
#        else:
##            print "Pas Trouvé !"
#            return None, None
    
#    ######################################################################################################
#    def getIntervallePuls(self, grad):
#        """ Renvoie l'intervalle de puslations
#            pour lequel la FT est visible 
#            dans le plan défini par <grad>
#        """
#        
#        if not hasattr(self, 'reponse'):
#            pulsas = getPulsationsD(self.getRangeDecade())
#            self.reponse = self.getReponseHarmoniqueGainPhase(pulsas)
#            return self.getIntervallePuls(grad)
#        
#        minOm, maxOm = None, None
#        
#        continuer = True
#        i = 0
#        while continuer:
#            if i >= len(self.reponse[0]):
#                continuer = False
#            elif grad.estDansPlan(self.reponse[2][i], self.reponse[1][i]):
#                minOm = self.reponse[0][max(0, i-1)]
#                continuer = False
#            i += 1
#            
#        continuer = True
#        i = len(self.reponse[0])-1
#        while continuer:
#            if i < 0:
#                continuer = False
#            elif grad.estDansPlan(self.reponse[2][i], self.reponse[1][i]):
#                maxOm = self.reponse[0][min(len(self.reponse[0])-1, i+1)]
#                continuer = False
#            i += -1
#            
#        rangeOm = [minOm, maxOm]
#        rangeOm.sort()
#        
#        return rangeOm
    
    ######################################################################################################
    def traverse(self, ax, reponse):
        """ Renvoie l'intervalle de puslations
            pour lequel la FT est visible dans le plan défini par ax (MPL)
            
        """
#        print "getIntervallePulsMpl" , 
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        xc, yc = (xmin + xmax)/2, (ymin + ymax)/2
        
        def fct(i):
            i = int(round(i))
#            print i
            if i > 0 and i < len(reponse[1])-1:
                x, y = reponse[1][i], reponse[2][i]
                return (xc-x)**2 + (yc-y)**2
            else:
                return None
        
        iOm = int(round(fmin(fct, len(reponse[0])/2, disp = 0)))
        
#        print iOm
        traverse = False
        signe = 0
        for dr in [(iOm-1, iOm), (iOm, iOm+1) ]:
            pt0 = reponse[1][dr[0]], reponse[2][dr[0]]
            pt1 = reponse[1][dr[1]], reponse[2][dr[1]]
            for pt in [(xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax)]:
                u = (pt[0]-pt0[0], pt[1]-pt0[1])
                v = (pt1[0]-pt0[0], pt1[1]-pt0[1])
                s = u[0]*v[1] - u[1]*v[0]
                if signe == 0:
                    signe = s
                else:
                    traverse = (signe*s <= 0)
                if traverse:
                    break
        
        return traverse, iOm
    
    
    
    
    ######################################################################################################
    def getIntervallePulsMpl(self, ax, reponse):
        """ Renvoie l'intervalle de puslations
            pour lequel la FT est visible dans le plan défini par ax (MPL)
            
        """
#        print "getIntervallePulsMpl" , 
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
#        print xmin, xmax, ymin, ymax
        
        def estDansPlan(x,y):
#            return ax.contains_point((x,y))
            return x <= xmax and x >= xmin and y <= ymax and y >= ymin
        
        
            
        minOm, maxOm = None, None
        
#        print reponse[0][0], reponse[0][-1]
        # valeur mini de Omega
        continuer = True
        i = 0
        while continuer:
            if i >= len(reponse[0]):
                continuer = False
            elif estDansPlan(reponse[1][i], reponse[2][i]):
                minOm = reponse[0][max(0, i-1)]
                continuer = False
            i += 1
        # Si déja dans le plan (zoom out...) il faut élargir !!    
        if i == 1:# or minOm == None:
            minOm = self.getRange()[0]
            
#        print "minOm", minOm
        
        if minOm == None: # aucun point de la réponse n'est dans le plan ...
            tr, i = self.traverse(ax, reponse)
            if tr:
#                print "traverse!!"
                minOm = reponse[0][i-1]
                maxOm = reponse[0][i+1]
            else:
                maxOm = None
            
        else:
            # valeur maxi de Omega
            continuer = True
            j = len(reponse[0])-1
            while continuer:
                if j < 0:
                    continuer = False
                elif estDansPlan(reponse[1][j], reponse[2][j]):
                    maxOm = reponse[0][min(len(reponse[0])-1, j+1)]
                    continuer = False
                j += -1
            if j == len(reponse[0])-2:# or maxOm == None:
                
                maxOm = self.getRange()[1]
        
#        print "min-maxOm", minOm, maxOm
        
        rangeOm = [minOm, maxOm]
        try:
            rangeOm.sort()
        except:
            pass
        
        return rangeOm
    
    def getIntervalle(self, axe, v):
        """ Renvoie l'intervalle de pulsation
            dans lequel se trouve la valeur <v>
            sur l'axe <axe> : 
                0 : pulsation
                1 : gain
                2 : phase
        """

        i = len(self.reponse0[0]) - 2
        continuer = True

        s = sign(self.reponse0[axe][i+1] - v)

        while continuer: 
            Om = self.reponse0[0][i]
            V = self.reponse0[axe][i]
            i += -1
            if i < 0:
                inter = [None, None]
                continuer = False
            if (V-v) * s < 0 : # changement de signe !
                inter = [Om, self.reponse0[0][i+2]]
                continuer = False
        return inter
    
#    def getIntervalle2(self, axe, v):
#        """ Renvoie l'intervalle de pulsation
#            dans lequel se trouve la valeur <v>
#            sur l'axe <axe> : 
#                0 : pulsation
#                1 : gain
#                2 : phase
#        """
##        print "getIntervalle",v,
#        if not hasattr(self, 'reponse'):
#            return []
#        i = len(self.reponse[0]) - 2
#        continuer = True
##        print i,
#        s = scipy.sign(self.reponse[axe][i+1] - v)
##        print s
#        while continuer: 
##            print "  "
#            Om = self.reponse[0][i]
#            V = self.reponse[axe][i]
#            i += -1
##            print "  "
#            if i < 0:
#                inter = [None, None]
#                continuer = False
#            if (V-v) * s < 0 : # changement de signe !
##                print "   trouvé : ", i, Om, V
#                inter = [Om, self.reponse[0][i+2]]
#                continuer = False
#        return inter
    
    
    #########################################################################################################
    def getMarges(self):
        Om, Phi = self.getPulsationCoupure()
        Om180, HdB = self.getPulsation180(Om)
        OmS, HdBS, PhiS, HdBF, PhiF = self.getPulsationSurtension()
        return Marges(Om, Phi, Om180, HdB, 1, OmS, HdBS, PhiS, HdBF, PhiF)
    
    
    #########################################################################################################
    def getMathText(self):
        if self.retard == 0:
            r = r""
        else:
            r = r"e^{-"+strSc(self.retard)+globdef.VAR_COMPLEXE+"}"
            
        if hasattr(self, 'polyNreel'): # Cas d'une FTBF avec retard dans FTBO
            
            if self.polyNreel.o == 0 and self.polyNreel.c[0] == 1.0:
                t2 = r"" + r
            elif self.polyNreel.o == 0:
                t2 = getMathTextPoly(self.polyNreel, globdef.VAR_COMPLEXE) + r
            else:
                t2 = r + r"\left(" +getMathTextPoly(self.polyNreel, globdef.VAR_COMPLEXE)+r"\right)"
            
            f = r + r"\frac{"+getMathTextPoly(self.polyNreel, globdef.VAR_COMPLEXE)+"}" \
                         r"{"+getMathTextPoly(self.polyDD, globdef.VAR_COMPLEXE)+r"+"\
                         + t2 + r"}"
            
        else:
            if self.polyD.o == 0 and self.polyD.c[0] == 1.0:
                if self.polyN.o == 0:
                    if self.polyN.c[0] == 1.0:
                        if r == r"":
                            f = r"1"
                        else:
                            f = r
                    else:
                        f = getMathTextPoly(self.polyN, globdef.VAR_COMPLEXE) + r
                else:
                    f = r + getMathTextPoly(self.polyN, globdef.VAR_COMPLEXE)
            else:
                f = r + r"\frac{"+getMathTextPoly(self.polyN, globdef.VAR_COMPLEXE)+"}" \
                             r"{"+getMathTextPoly(self.polyD, globdef.VAR_COMPLEXE)+"}"
        return f
    
    #########################################################################################################
    def getBitmap(self, nom = None, taille = 100, color = wx.BLACK):
        if nom == None:
            n = self.nom+"("+globdef.VAR_COMPLEXE+")="
        elif nom == "":
            n = ""
        else:
            n = nom+"("+globdef.VAR_COMPLEXE+")="
        return mathtext_to_wxbitmap(n+self.getMathText(), taille = taille, color = color)
    
    
    #########################################################################################################
    def getMathTextNom(self, nom = None):
        if nom == None:
            s = self.nom+'('+globdef.VAR_COMPLEXE+') = '
        else:
            s = nom
        
        s += self.getMathText()
       
        return s
    
if HAVE_PSYCO:
    print ("Psyco !!!!!")
    psyco.bind(FonctionTransfertNum.getReponse)
    psyco.bind(lsim)
    
#########################################################################################################
class Marges():
    def __init__(self, Om, Phi, Om180, HdB, sens180, OmS, HdBS, PhiS, HdBF, PhiF):
        self.Om0 = Om
        self.Phi0 = Phi
        
        self.Om180 = Om180
        self.HdB180 = HdB
        self.sens180 = sens180
        
        self.OmS = OmS
        self.HdBS = HdBS
        self.PhiS = PhiS
        self.HdBF = HdBF
        self.PhiF = PhiF
        
        self.nbChiffres = int(abs(decade(globdef.PRECISION)))
        
    def __repr__(self):
        t = self.getMathTexteOm0()+ self.getMathTexteMp() + "\n"
        t += self.getMathTexteOm180() + self.getMathTexteMg() + "\n"
        t += self.getMathTexteOmS() + self.getMathTexteQ() + "\n"
        return t
    
    def getMargeG(self):
        if self.HdB180 != None:
            return -self.HdB180*self.sens180
    
    def getMargeP(self):
        if self.Phi0 != None:
            return self.Phi0 + 180
    
    def getMathTexteMp(self):
        if self.Om0 == None:
            t = r"\infty"
        else:
            t = roundN_str(self.getMargeP(), self.nbChiffres)+r"\;\text{deg}"
        return r"$M_p = " + t+r"$"
        
    def getMathTexteOm0(self):
        if self.Om0 == None:
            t = "--"
        else:
            t = roundN_str(self.Om0, self.nbChiffres)+r"\;\text{rad/s}"
        return r"$\omega_{0dB} = "+ t+r"$"
        
    def getMathTexteMg(self):
        if self.Om180 == None:
            t = r"\infty"
        else:
            t = roundN_str(self.getMargeG(), self.nbChiffres)+r"\;\text{dB}"
        return r"$M_g = " + t+"$"
        
    def getMathTexteOm180(self):
        if self.Om180 == None:
            t = "--"
        else:
            t = roundN_str(self.Om180, self.nbChiffres)+r"\;\text{rad/s}"
        return r"$\omega_{-180^\circ} = "+ t +"$"
    
    def getMathTexteQ(self):
        if self.OmS == None:
            t = "--"
        else:
            t = roundN_str(self.HdBF, self.nbChiffres)+r"\;\text{dB}"
        return r"$Q = "+t+"$"
    
    def getMathTexteOmS(self):
        if self.OmS == None:
            t = "--"
        else:
            t = roundN_str(self.OmS, self.nbChiffres)+r"\;\text{rad/s}"
        return r"$\omega_s = " + t+"$"

    def getCoulG(self):
        if self.Om180 != None and self.getMargeG() < 0:
            return globdef.COUL_MARGE_GAIN_NO
        else:
            return globdef.COUL_MARGE_GAIN_OK
    
    def getCoulP(self):
        if self.Om0 != None and self.getMargeP() < 0:
            return globdef.COUL_MARGE_GAIN_NO
        else:
            return globdef.COUL_MARGE_GAIN_OK
        
    def getCoulQ(self):
        if self.OmS != None and (self.getMargeP() < 0 and self.getMargeP() != None) or (self.getMargeG() < 0 and self.getMargeG() != None):
            return  globdef.COUL_MARGE_GAIN_NO
        else:
            return  globdef.COUL_MARGE_GAIN_OK
                
                
        
##########################################################################################################
class DiagAsympBase:
#    def __init__(self, *args, **kargs):
        
        
    def numAsympOmega(self, omega, asymp, strict = True):
        """ Renvoie l'index de l'asymptote comprenant la pulsation omega
        """
        r = len(asymp)-1
        while r >= 0:
            if strict:
                if asymp[r].omega < omega:
                    return r
            else:
                if asymp[r].omega <= omega:
                    return r
            r += -1
        return 0   
           
           
                 
##########################################################################################################
class DiagAsympGain(DiagAsympBase):
    def __init__(self, HdB_1 = 0.0, lstAsymp = [], KdB = 0.0):
        self.HdB_1 = HdB_1
        self.Asymp = lstAsymp
        self.calcOrdOr()
        self.setHdB_1(self.HdB(1) + KdB)
        self.KdB = KdB
        
    def __repr__(self):
        print (self.HdB_1, self.Asymp)
        return ""
    
    def getCassures(self):
        lstO = []
        for a in self.Asymp[1:]:
            lstO.append(a.omega)
        return lstO

    def __add__(self, diag):
        if diag == None: 
            return self
        
        lstO = []
        for a in self.Asymp + diag.Asymp:
            lstO.append(a.omega)
        lstO = list(set(lstO))
        lstO.sort()
        
        lstAsymp = []
        for o in lstO:
            n1 = self.numAsympOmega(o, self.Asymp, False)
            n2 = self.numAsympOmega(o, diag.Asymp, False)
            p = self.Asymp[n1].pente + diag.Asymp[n2].pente
            lstAsymp.append(AsympGain(o, p))
            
        HdBT = self.HdB_1 + diag.HdB_1
        
        diagSom = DiagAsympGain(HdBT, lstAsymp, KdB = self.KdB + diag.KdB)
        
        return diagSom
        
        
        
    def setHdB_1(self, HdB_1):
        # Decalage d'ordonnées à l'origine
        self.HdB_1 = HdB_1

        # On applique le décalage sur les ordonnées à l'origine
        decal = self.HdB_1 - self.HdB(1)

        for a in self.Asymp:
            a.ordor = a.ordor + decal

        
    def calcOrdOr(self):
        """ Calcul des ordonnées à l'origine des différentes asymptotes
        """
    
        # On calcul toutes les ordonnées à l'origines des asymptotes avec la première à 0
        r = 1
        while r < len(self.Asymp):
            logOmegaC = log10(self.Asymp[r].omega)
            HdB_omega = self.Asymp[r-1].pente * logOmegaC + self.Asymp[r-1].ordor
            self.Asymp[r].ordor = HdB_omega - self.Asymp[r].pente * logOmegaC
            r += 1
        

    def HdB(self, omega):
        """ Renvoie HdB pour la pulsation omega
        """
        
        # Asymptote comprenant omega
        r = self.numAsympOmega(omega, self.Asymp)
        a = self.Asymp[r]
        
        HdB_omega = a.pente * log10(omega) + a.ordor
        return HdB_omega
    
    def getMinMax(self, range):
        mini = self.HdB(range[0])
        maxi = mini
        for o in self.Asymp[1:]:
            H = self.HdB(o.omega)
            mini = min(H,mini)
            maxi = max(H,maxi)
        
        H = self.HdB(range[1])
        mini = min(H,mini)
        maxi = max(H,maxi)
        return mini, maxi
         
         
##########################################################################################################
class DiagAsympPhase(DiagAsympBase):
    def __init__(self, HdB_1 = 0.0, lstAsymp = []):
        self.HdB_1 = HdB_1
        self.Asymp = lstAsymp 
        
        
    def __repr__(self):
        print (self.HdB_1, self.Asymp)
        return ""
    
    def __add__(self, diag):
        if diag == None: return self
        
        lstO = []
        for a in self.Asymp+diag.Asymp:
            lstO.append(a.omega)
        lstO = list(set(lstO))
        lstO.sort()
        
        lstAsymp = []
        for o in lstO:
            n1 = self.numAsympOmega(o, self.Asymp, False)
            n2 = self.numAsympOmega(o, diag.Asymp, False)
            p = self.Asymp[n1].phi + diag.Asymp[n2].phi
            a = AsympPhase(o, p)
            lstAsymp.append(a)
            
        HdBT = self.HdB_1 + diag.HdB_1
        
        diagSom = DiagAsympPhase(HdBT, lstAsymp)
        
        return diagSom
    
    
    def Phi(self, omega):
        """ Renvoie Phi pour la pulsation omega
        """
        
        # Asymptote comprenant omega
        r = self.numAsympOmega(omega, self.Asymp)
        a = self.Asymp[r]
        
        Phi_omega = a.phi

        return Phi_omega
    
    def getMinMax(self, range):
        maxi = mini = self.Phi(range[0])
        for o in self.Asymp:
            H = o.phi
            mini = min(H,mini)
            maxi = max(H,maxi)
        return mini, maxi
        
#########################################################################################################
class AsympGain:
    def __init__(self, omega = 0.0, pente = 0.0):
        self.omega = omega
        self.pente = pente
        self.ordor = 0.0
        
    def __repr__(self):
        print (self.omega, self.pente,)
        return ""
    
#########################################################################################################
class AsympPhase:
    def __init__(self, omega = 0.0, phi = 0.0):
        self.omega = omega
        self.phi = phi
        
    def __repr__(self):
        print (self.omega, self.phi,)
        return ""

##########################################################################################################
class DiagNyquist():
    def __init__(self, reponse):
        self.reponse = reponse

    def getMinMaxReel(self):
        return min(self.reponse[1]), max(self.reponse[1]) 
    
    def getMinMaxImag(self):
        return min(self.reponse[2]), max(self.reponse[2]) 
    
    
##########################################################################################################
class DiagBlack():
    def __init__(self, reponse):
        self.reponse = reponse

    def getMinMaxPhase(self):
        return min(self.reponse[1]), max(self.reponse[1]) 
    
    def getMinMaxGain(self):
        return min(self.reponse[2]), max(self.reponse[2]) 
   
   
##########################################################################################################
class DiagBode():
    def __init__(self, reponse):
#        self.FT = FT
#        self.lstPtY = {}
        self.reponse = reponse
    
    def getMinMax(self):
        return min(self.reponse[1]), max(self.reponse[1]) 
#    def __add__(self, diag):
#        if diag == None: return self
#        polyN = self.FT.polyN * diag.FT.polyN
#        polyD = self.FT.polyD * diag.FT.polyD
#        newFT = FonctionTransfertNum(polyN, polyD)
#        somDiag = DiagGain(newFT, self.coul)
#        return somDiag
#    
#    def HdB(self, Om):
#        j = complex(0,1)
#        
#        h = 20 * scipy.log10(abs(self.FT.polyN(j*Om)/self.FT.polyD(j*Om)))
##        print h
#        return h
    

    
###########################################################################################################
#class DiagPhase():
#    def __init__(self, reponse, coul):
##        self.FT = FT
#        self.coul = coul
##        self.lstPtY = {}
#        self.reponse = reponse
#        
#    def getMinMax(self):
#        return min(self.reponse[1]), max(self.reponse[1])  
#    
##    def __add__(self, diag):
##        if diag == None: return self
##        polyN = self.FT.polyN * diag.FT.polyN
##        polyD = self.FT.polyD * diag.FT.polyD
##        newFT = FonctionTransfertNum(polyN, polyD)
##        somDiag = DiagPhase(newFT, self.coul)
##        return somDiag
#    
#    def Phi(self, Om):
#        
#        j = complex(0,1)
#        c = self.FT.polyN(j*Om)/self.FT.polyD(j*Om)
#        a = scipy.angle(c, True)
##        a = arctan2(x1,x2)
##        p = log(c/abs(c))/complexe(0,1)
##        h = p*180/pi
##        print c, a#c, p, h
#        return a
    
    
class ReponseIndicielle():
    def __init__(self, FTBO):
        self.FTBO = FTBO
        
    
        
        
##########################################################################################################
def decade(n):
    """ Retourne la decade dans laquelle se trouve <n>
    """
    l = log10(abs(n))
    if l == 0.0:
        s = 0
    else:
        s = (sign(l)-1)/2
    return int(l) + s


##########################################################################################################
def isclose(a, b, rel_tol=1e-06, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

##########################################################################################################
def roundF(v, f):
    """ Arrondi <v> au plus proche entier multiple de <f>
    """
    return int(round(v)/5)*5

##########################################################################################################
def roundUpDownM(v, f, Up = True):
    """ Arrondi <v> au dessus ou au dessous du plus proche entier multiple de <f>
    """
    with errstate(invalid='ignore'): 
        r = v/f
        if Up:
            if int(r) == r:
                return int(r) * f
            else:
                return int(r+1) * f
        else:
            if int(r) == r:
                return int(r) * f
            else:
                return int(r-1) * f




def getPulsationsD(rng = None):
    """ Renvoie une liste des pulsations à calculer
        dans l'intervalle rng (en decade)
    """
#    if rng == None:
#        rng = self.getRangeDecade()
    return logspace(rng[0], rng[1], num = globdef.NBR_PTS_COURBES)
#    with errstate(invalid='ignore'): 
#        pas = (1.0*(rng[1] - rng[0])) /globdef.NBR_PTS_COURBES
#    
#        d = rng[0]
#        lst = []
#        while d <= rng[1]:
#            lst.append(10**d)
#            d += pas
#        return lst


def getPulsations(rng = None):
    """ Renvoie une liste des pulsations à calculer
        dans l'intervalle rng
    """
#    pas = (1.0*(rng[1] - rng[0])) /NBR_PTS_COURBES
#
#    d = rng[0]
#    lst = []
#    while d <= rng[1]:
#        lst.append(d)
#        d += pas
#    return lst
#    print rng
    with errstate(invalid='ignore'): 
        return getPulsationsD([log10(rng[0]), log10(rng[1])])

##########################################################################################################
#
# Signaux
#
##########################################################################################################
def impulsion(t):
    if t == 0:
        return inf
    else:
        return 0

def echelon(t, amplitude = 1.0):
    if t >= 0:
        return amplitude
    else:
        return 0
    
def rampe(t, pente = 1.0):
    if t >= 0:
        return pente * t
    else:
        return 0
    
def serieImpulsions(t, periode = 1.0, max = 1):
    if t < 0:
        return 0.0
    elif t%periode == 0.0:
        return max
    else:
        return 0.0
    
def carre(t, amplitude = 1.0, periode = 1.0, decalage = 0.0):
    if t < 0:
        return 0.0
    elif t%periode <= periode/2:
        return amplitude + decalage
    elif t%periode > periode/2:
        return decalage
    else:
        return decalage
    
def triangle(t, pente = 1.0, periode = 1.0, decalage = 0.0):
    if t < 0:
        return 0.0
    else:
        dp = periode/2.0
        num = t//periode
        res = t%periode
        ord = pente * periode
        if res < dp:
            return pente * t - ord * num + decalage
        elif res > dp:
            return -pente * t + ord * (num +1) + decalage
        else:
            return ord/2.0 + decalage
    
def sinus(t, amplitude = 1.0, pulsation = 1.0, decalage = 0.0):
    return (t>=0) * (amplitude * sin(pulsation*t) + decalage)
        
def signalPerso(t, U, T):
    return

def pade(tau, n):
    num, den = [], []
    s = 1
    for i in range(n+1):
        if i == 0:
            t = 0
        elif i == 1:
            t = tau/2
        else:
            t = (tau/2)**i / (i*(i-1))
        num[0:0] = [s*t]
        den[0:0] = [t]
        s = -s
    return poly1d(num), poly1d(den)


def prodScalaire(u, v):
    return u[0]*u[1]+v[0]*v[1]
#
# Thanks to Warren Weckesser from scipy-user mailing list
#
#from scipy.signal import lti, lsim2
#from numpy import arange, zeros_like, real, array
#import scipy.linalg as linalg


#def impulse_response(system, X0=None, T=None, N=None):
#    """Impulse response of a single-input continuous-time system.
#
#    Inputs:
#
#      system -- an instance of the LTI class or a tuple with 2, 3, or 4
#                elements representing (num, den), (zero, pole, gain), or
#                (A, B, C, D) representation of the system.
#      X0 -- (optional, default = 0) inital state-vector.
#      T -- (optional) time points (autocomputed if not given).
#      N -- (optional) number of time points to autocompute (100 if not given).
#
#    Ouptuts: (T, yout)
#
#      T -- output time points,
#      yout -- impulse response of system (except possible singularities at 0).
#    """
#    if isinstance(system, lti):
#        sys = system
#    else:
#        sys = lti(*system)
#    B = sys.B
#    if B.shape[-1] != 1:
#        raise ValueError, "impulse_response() requires a single-input system."
#    B = B.squeeze()
#    if X0 is None:
#        X0 = zeros_like(B)
#    if N is None:
#        N = 100
#    if T is None:
#        # Create a reasonable time interval.  This could use some more work.
#        vals = linalg.eigvals(sys.A)
#        r = min(abs(real(vals)))
#        if r == 0.0:
#            r = 1.0
#        tc = 1.0/r
#        T = arange(0, 7*tc, 7*tc / float(N))
#    # Move the impulse in the input to the initial conditions, and then
#    # solve using lsim2().
#    U = zeros_like(T)
#    ic = B + X0
#    Tr, Yr, Xr = lsim2(sys, U, T, ic)
#    return Tr, Yr
#
#impulse = impulse_response

####################################################################################################
#def step2(system, X0=None, T=None, N=None):
#    """Step response of continuous-time system.
#
#    Inputs:
#
#      system -- an instance of the LTI class or a tuple with 2, 3, or 4
#                elements representing (num, den), (zero, pole, gain), or
#                (A, B, C, D) representation of the system.
#      X0 -- (optional, default = 0) inital state-vector.
#      T -- (optional) time points (autocomputed if not given).
#      N -- (optional) number of time points to autocompute (100 if not given).
#
#    Ouptuts: (T, yout)
#
#      T -- output time points,
#      yout -- step response of system.
#    """
#    if isinstance(system, lti):
#        sys = system
#    else:
#        sys = lti(*system)
#    if N is None:
#        N = 100
#    if T is None:
#        T = getAutoRange(sys, N)
##        vals = linalg.eigvals(sys.A)
##        c = min(abs(real(vals)))
##        if c != 0.0:
##            tc = 1.0/min(abs(real(vals)))
##        else:
##            tc = 1.0
##        
##        T = arange(0,7*tc,7*tc / float(N))
#    
#    U = ones(T.shape, sys.A.dtype)
#    vals = lsim2(sys, U, T, X0=X0)
#    return vals[0], vals[1]
#
#step = step2


    
