"""
Supplemental code for paper:
I. Bell et al., "A Generalized Moving-Boundary Algorithm to Predict the Heat Transfer Rate of 
Counterflow Heat Exchangers for any Phase Configuration", Applied Thermal Engineering, 2014
"""

from __future__ import division

import CoolProp
import CoolProp.CoolProp as CP
from CoolProp.Plots import PropertyPlot

import matplotlib.pyplot as plt
import numpy as np
from math import log
import scipy.optimize

#===============================================================================
# Latex render
#===============================================================================
import matplotlib as mpl
#mpl.use('pgf')

def figsize(scale):
    fig_width_pt = 469.755                          # Get this from LaTeX using \the\textwidth
    inches_per_pt = 1.0/72.27                       # Convert pt to inch
    golden_mean = (np.sqrt(5.0)-1.0)/2.0            # Aesthetic ratio (you could change this)
    fig_width = fig_width_pt*inches_per_pt*scale    # width in inches
    fig_height = fig_width*golden_mean              # height in inches
    fig_size = [fig_width,fig_height]
    return fig_size
 
pgf_with_latex = {                      # setup matplotlib to use latex for output
"pgf.texsystem": "pdflatex",        # change this if using xetex or lautex
"text.usetex": True,                # use LaTeX to write all text
"font.family": "serif",
"font.serif": [],                   # blank entries should cause plots to inherit fonts from the document
"font.sans-serif": [],
"font.monospace": [],
"axes.labelsize": 10,               # LaTeX default is 10pt font.
"font.size": 10,
"legend.fontsize": 8,               # Make the legend/label fonts a little smaller
"legend.labelspacing":0.2,
"xtick.labelsize": 8,
"ytick.labelsize": 8,
"figure.figsize": figsize(0.9),     # default fig size of 0.9 textwidth
"pgf.preamble": [
r"\usepackage[utf8x]{inputenc}",    # use utf8 fonts becasue your computer can handle it :)
r"\usepackage[T1]{fontenc}",        # plots will be generated using this preamble
        ]
    }
mpl.rcParams.update(pgf_with_latex)
#===============================================================================
# END of Latex render
#===============================================================================

# Set to True to enable some debugging output to screen
debug = False

class struct(object): 
    """
    
    A dummy class that allows you to set variables like::
    
        S = struct()
        S.A = 'apple'
        S.N = 3
    """
    pass
    
class HeatExchanger():
    
    def __init__(self,**kwargs):
        
        self.__dict__.update(kwargs)
        """
        
        Parameters
        ----------
        
        """
        
        # Set variables in the class instance
#         self.Fluid_h = Fluid_h
#         self.mdot_h = mdot_h
#         self.h_hi = h_hi
#         self.p_hi = p_hi
#         self.Fluid_c = Fluid_c
#         self.mdot_c = mdot_c
#         self.h_ci = h_ci
#         self.p_ci = p_ci
        
        # Determine the inlet temperatures from the pressure/enthalpy pairs
        self.T_ci = CP.PropsSI('T', 'P', self.p_ci, 'H', self.h_ci, self.Fluid_c)
        self.T_hi = CP.PropsSI('T', 'P', self.p_hi, 'H', self.h_hi, self.Fluid_h)
        
        # Calculate the bubble and dew enthalpies for each stream
        self.T_cbubble = CP.PropsSI('T', 'P', self.p_ci, 'Q', 0, self.Fluid_c)
        self.T_cdew    = CP.PropsSI('T', 'P', self.p_ci, 'Q', 1, self.Fluid_c)
        self.T_hbubble = CP.PropsSI('T', 'P', self.p_hi, 'Q', 0, self.Fluid_h)
        self.T_hdew    = CP.PropsSI('T', 'P', self.p_hi, 'Q', 1, self.Fluid_h)
        self.h_cbubble = CP.PropsSI('H', 'T', self.T_cbubble, 'Q', 0, self.Fluid_c)
        self.h_cdew    = CP.PropsSI('H', 'T', self.T_cdew, 'Q', 1, self.Fluid_c)
        self.h_hbubble = CP.PropsSI('H', 'T', self.T_hbubble, 'Q', 0, self.Fluid_h)
        self.h_hdew    = CP.PropsSI('H', 'T', self.T_hdew, 'Q', 1, self.Fluid_h)
        
    def Update(self,**kwargs):
        #Update the parameters passed in
        # using the dictionary
        self.__dict__.update(kwargs)
        
        # Determine the inlet temperatures from the pressure/enthalpy pairs
        self.T_ci = CP.PropsSI('T', 'P', self.p_ci, 'H', self.h_ci, self.Fluid_c)
        self.T_hi = CP.PropsSI('T', 'P', self.p_hi, 'H', self.h_hi, self.Fluid_h)
        
        # Calculate the bubble and dew enthalpies for each stream
        self.T_cbubble = CP.PropsSI('T', 'P', self.p_ci, 'Q', 0, self.Fluid_c)
        self.T_cdew    = CP.PropsSI('T', 'P', self.p_ci, 'Q', 1, self.Fluid_c)
        self.T_hbubble = CP.PropsSI('T', 'P', self.p_hi, 'Q', 0, self.Fluid_h)
        self.T_hdew    = CP.PropsSI('T', 'P', self.p_hi, 'Q', 1, self.Fluid_h)
        self.h_cbubble = CP.PropsSI('H', 'T', self.T_cbubble, 'Q', 0, self.Fluid_c)
        self.h_cdew    = CP.PropsSI('H', 'T', self.T_cdew, 'Q', 1, self.Fluid_c)
        self.h_hbubble = CP.PropsSI('H', 'T', self.T_hbubble, 'Q', 0, self.Fluid_h)
        self.h_hdew    = CP.PropsSI('H', 'T', self.T_hdew, 'Q', 1, self.Fluid_h)
        
    def external_pinching(self):
        """ Determine the maximum heat transfer rate based on the external pinching analysis """

        # Equation 5
        self.h_ho = CP.PropsSI('H','T',self.T_ci,'P',self.p_hi,self.Fluid_h)        

        # Equation 4
        Qmaxh = self.mdot_h*(self.h_hi-self.h_ho)
        
        # Equation 7
        self.h_co = CP.PropsSI('H','T',self.T_hi,'P',self.p_ci,self.Fluid_c)
        
        # Equation 6
        Qmaxc = self.mdot_c*(self.h_co-self.h_ci)

        Qmax = min(Qmaxh, Qmaxc)
        
        if debug:
            print('Qmax (external pinching) is', Qmax)
        
        self.calculate_cell_boundaries(Qmax)
        
        return Qmax
        
    def calculate_cell_boundaries(self, Q):
        """ Calculate the cell boundaries for each fluid """
        
        # Re-calculate the outlet enthalpies of each stream
        self.h_co = self.h_ci + Q/self.mdot_c
        self.h_ho = self.h_hi - Q/self.mdot_h
        
        # Start with the external boundaries (sorted in increasing enthalpy)
        self.hvec_c = [self.h_ci, self.h_co]
        self.hvec_h = [self.h_ho, self.h_hi]
        
        # Add the bubble and dew enthalpies for the hot stream
        if self.h_hdew is not None and self.h_hi > self.h_hdew > self.h_ho:
            self.hvec_h.insert(-1, self.h_hdew)
        if self.h_hbubble is not None and self.h_hi > self.h_hbubble > self.h_ho:
            self.hvec_h.insert(1, self.h_hbubble)
        
        # Add the bubble and dew enthalpies for the cold stream
        if self.h_cdew is not None and self.h_ci < self.h_cdew < self.h_co:
            self.hvec_c.insert(-1, self.h_cdew)
        if self.h_cbubble is not None and self.h_ci < self.h_cbubble < self.h_co:
            self.hvec_c.insert(1, self.h_cbubble)
            
        if debug:
            print(self.hvec_c, self.hvec_h)
            
        # Fill in the complementary cell boundaries
        # Start at the first element in the vector
        k = 0
        while k < len(self.hvec_c)-1 or k < len(self.hvec_h)-1:
            if len(self.hvec_c) == 2 and len(self.hvec_h) == 2:
                break
                
            # Determine which stream is the limiting next cell boundary
            Qcell_hk = self.mdot_h*(self.hvec_h[k+1]-self.hvec_h[k])
            Qcell_ck = self.mdot_c*(self.hvec_c[k+1]-self.hvec_c[k])
            
            if abs(Qcell_hk/Qcell_ck - 1)< 1e-6:
                k +=1
                break
            elif Qcell_hk > Qcell_ck:
                # Hot stream needs a complementary cell boundary
                self.hvec_h.insert(k+1, self.hvec_h[k] + Qcell_ck/self.mdot_h)
            else:
                # Cold stream needs a complementary cell boundary
                self.hvec_c.insert(k+1, self.hvec_c[k] + Qcell_hk/self.mdot_c)
            
            if debug:
                print(k,len(self.hvec_c),len(self.hvec_h),Qcell_hk, Qcell_ck)
            
            if debug:
                # Calculate the temperature and entropy at each cell boundary
                self.Tvec_c = CP.PropsSI('T','H',self.hvec_c,'P',self.p_ci,self.Fluid_c)
                self.Tvec_h = CP.PropsSI('T','H',self.hvec_h,'P',self.p_hi,self.Fluid_h)
                self.svec_c = CP.PropsSI('S','H',self.hvec_c,'P',self.p_ci,self.Fluid_c)
                self.svec_h = CP.PropsSI('S','H',self.hvec_h,'P',self.p_hi,self.Fluid_h)
                self.plot_cells()
                plt.show()
            
            Qcell_hk = self.mdot_h*(self.hvec_h[k+1]-self.hvec_h[k])
            Qcell_ck = self.mdot_c*(self.hvec_c[k+1]-self.hvec_c[k])
            assert (abs(Qcell_hk/Qcell_ck-1) < 1e-6)
            
            # Increment index
            k += 1
        
        assert(len(self.hvec_h) == len(self.hvec_c))
        Qhs = np.array([self.mdot_h*(self.hvec_h[i+1]-self.hvec_h[i]) for i in range(len(self.hvec_h)-1)])
        Qcs = np.array([self.mdot_c*(self.hvec_c[i+1]-self.hvec_c[i]) for i in range(len(self.hvec_c)-1)])
        if debug:
            if np.max(np.abs(Qcs/Qhs))<1e-5:
                print(Qhs, Qcs)
        
        # Calculate the temperature and entropy at each cell boundary
        self.Tvec_c = CP.PropsSI('T','H',self.hvec_c,'P',self.p_ci,self.Fluid_c)
        self.Tvec_h = CP.PropsSI('T','H',self.hvec_h,'P',self.p_hi,self.Fluid_h)
        self.svec_c = CP.PropsSI('S','H',self.hvec_c,'P',self.p_ci,self.Fluid_c)
        self.svec_h = CP.PropsSI('S','H',self.hvec_h,'P',self.p_hi,self.Fluid_h)
        
        # Calculate the phase in each cell
        self.phases_h = []
        for i in range(len(self.hvec_h)-1):
            havg = (self.hvec_h[i] + self.hvec_h[i+1])/2.0
            if havg < self.h_hbubble:
                self.phases_h.append('liquid')
            elif havg > self.h_hdew:
                self.phases_h.append('vapor')
            else:
                self.phases_h.append('two-phase')
        
        self.phases_c = []
        for i in range(len(self.hvec_c)- 1):
            havg = (self.hvec_c[i] + self.hvec_c[i+1])/2.0
            if havg < self.h_cbubble:
                self.phases_c.append('liquid')
            elif havg > self.h_cdew:
                self.phases_c.append('vapor')
            else:
                self.phases_c.append('two-phase')
            
    def internal_pinching(self, stream):
        """
        Determine the maximum heat transfer rate based on the internal pinching analysis 
        """
        
        if stream == 'hot':
            
            # Try to find the dew point enthalpy as one of the cell boundaries
            # that is not the inlet or outlet
        
            # Check for the hot stream pinch point
            for i in range(1,len(self.hvec_h)-1):
                
                # Check if enthalpy is equal to the dewpoint enthalpy of hot
                # stream and hot stream is colder than cold stream (impossible)
                if (abs(self.hvec_h[i] - self.h_hdew) < 1e-6 
                            and self.Tvec_c[i] > self.Tvec_h[i]):
            
                    # Enthalpy of the cold stream at the pinch temperature
                    # Equation 10
                    h_c_pinch = CP.PropsSI('H','T',self.T_hdew,'P',self.p_ci, self.Fluid_c)
                    
                    # Heat transfer in the cell
                    # Equation 9
                    Qright = self.mdot_h*(self.h_hi-self.h_hdew)
                    
                    # New value for the limiting heat transfer rate
                    # Equation 12
                    Qmax = self.mdot_c*(h_c_pinch-self.h_ci) + Qright
                    
                    # Recalculate the cell boundaries
                    self.calculate_cell_boundaries(Qmax)

                    return Qmax
        
        elif stream == 'cold':
            # Check for the cold stream pinch point
            for i in range(1,len(self.hvec_c)-1):
                
                # Check if enthalpy is equal to the bubblepoint enthalpy of cold
                # stream and hot stream is colder than cold stream (impossible)
                if (abs(self.hvec_c[i] - self.h_cbubble) < 1e-6 
                            and self.Tvec_c[i] > self.Tvec_h[i]):
            
                    # Enthalpy of the cold stream at the pinch temperature
                    # Equation 14
                    h_h_pinch = CP.PropsSI('H','T',self.T_cbubble,'P',self.p_hi, self.Fluid_h)
                    
                    # Heat transfer in the cell
                    # Equation 13
                    Qleft = self.mdot_c*(self.h_cbubble-self.h_ci)
                    
                    # New value for the limiting heat transfer rate
                    # Equation 16
                    Qmax = Qleft + self.mdot_h*(self.h_hi-h_h_pinch)
                    
                    # Recalculate the cell boundaries
                    self.calculate_cell_boundaries(Qmax)

                    return Qmax
        else:
            raise ValueError
        
    def run(self, only_external = False, and_solve = False):
        # Check the external pinching & update cell boundaries  
        Qmax_ext = self.external_pinching()
        Qmax = Qmax_ext

        if not only_external:
            # Check the internal pinching
            for stream in ['hot','cold']:
                # Check stream internal pinching & update cell boundaries
                Qmax_int = self.internal_pinching(stream)
                if Qmax_int is not None:
                    Qmax = Qmax_int
       
        self.Qmax = Qmax

        if and_solve and not only_external:
            Q = self.solve()
            
        Qtotal = self.mdot_c*(self.hvec_c[-1]-self.hvec_c[0])
        print ('Qtotal = '+str(Qtotal)+' W')
        # Build the normalized enthalpy vectors
        self.hnorm_h = self.mdot_h*(np.array(self.hvec_h)-self.hvec_h[0])/Qtotal
        self.hnorm_c = self.mdot_c*(np.array(self.hvec_c)-self.hvec_c[0])/Qtotal
        
        if and_solve:
            return Q
        
    def objective_function(self, Q):
        
        self.calculate_cell_boundaries(Q)

        w = []
        for k in range(len(self.hvec_c)-1):
            Thi = self.Tvec_h[k+1]
            Tci = self.Tvec_c[k]
            Tho = self.Tvec_h[k]
            Tco = self.Tvec_c[k+1]
            DTA = Thi - Tco
            DTB = Tho - Tci

            if DTA == DTB:
                LMTD = DTA
            else:
                try:
                    LMTD = (DTA-DTB)/log(abs(DTA/DTB))
                except ValueError as VE:
                    print(Q, DTA, DTB)
                    raise
            UA_req = self.mdot_h*(self.hvec_h[k+1]-self.hvec_h[k])/LMTD
            if self.phases_c[k] in ['liquid','vapor']:
                alpha_c = 100
            else:
                alpha_c = 1000
            if self.phases_h[k] in ['liquid','vapor']:
                alpha_h = 100
            else:
                alpha_h = 1000
            
            UA_avail = 1/(1/(alpha_h*self.A_h)+1/(alpha_c*self.A_c))
            w.append(UA_req/UA_avail)
            
        if debug:
            print(Q, 1-sum(w))
            
        return 1-sum(w)
    
    def solve(self):
        """ 
        Solve the objective function using Brent's method and the maximum heat transfer 
        rate calculated from the pinching analysis
        """
        print 'solve Q'
        self.Q = scipy.optimize.brentq(self.objective_function, 1e-5, self.Qmax-1e-10, rtol = 1e-14, xtol = 1e-10)
        return self.Q
        
    def plot_objective_function(self, N = 100):
        """ Plot the objective function """
        Q = np.linspace(1e-5,self.Qmax,N)
        r = np.array([self.objective_function(_Q) for _Q in Q])
        plt.plot(Q, r)
        plt.show()
        
    def plot_ph_pair(self):
        """ Plot p-h plots for the pair of working fluids """
        fig = plt.figure()
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        #PropertyPlot(self.Fluid_h,'Ph',axis = ax1)
        #PropertyPlot(self.Fluid_c,'Ph',axis = ax2)
        ax1.set_title('')
        ax1.plot([self.h_hi/1000.0, self.h_ho/1000.0],[self.p_hi/1000.0,self.p_hi/1000.0],'rs-')
        ax1.set_xlabel('$h$ [kJ/kg]')
        ax1.set_ylabel('$P$ [kPa]')
        ax2.set_title('')
        ax2.plot([self.h_ci/1000.0, self.h_co/1000.0],[self.p_ci/1000.0,self.p_ci/1000.0],'bs-')
        ax2.set_xlabel('$h$ [kJ/kg]')
        ax2.set_ylabel('$P$ [kPa]')
        plt.tight_layout()
        plt.show()
    
    def plot_Ts_pair(self):
        """ Plot a T-s plot for the pair of working fluids """
        fig = plt.figure()
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        #PropertyPlot(self.Fluid_h,'Ts',axis= ax1)
        #PropertyPlot(self.Fluid_c,'Ts',axis= ax2)
        ax1.set_title('')
        ax1.plot(self.svec_h/1000.0, self.Tvec_h, 'rs-')
        ax1.set_xlabel('$s$ [kJ/kg-K]')
        ax1.set_ylabel('$T$ [K]')
        ax2.set_title('')
        ax2.plot(self.svec_c/1000.0, self.Tvec_c, 'bs-')
        ax2.set_xlabel('$s$ [kJ/kg-K]')
        ax2.set_ylabel('$T$ [K]')
        plt.tight_layout()        
        plt.show()
        
    def plot_cells(self, fName = '', dpi = 400):
        """ Plot the cells of the heat exchanger """
        plt.figure(figsize = (2.4,2.4))
        plt.plot(self.hnorm_h, self.Tvec_h, 'rs-')
        plt.plot(self.hnorm_c, self.Tvec_c, 'bs-')
        plt.xlim(0,1)
        plt.ylabel('$T$ [K]') 
        plt.xlabel('$\hat h$ [-]')
        plt.tight_layout(pad = 0.2)
        if fName != '':
            plt.savefig(fName, dpi = dpi)
        plt.show()
        
def PropaneEvaporatorPinching():
    p_Water = 101325
    h_Water = CP.PropsSI('H','T',330,'P',p_Water,'Water')
    mdot_h = 0.01
    
    p_ref = CP.PropsSI('P','T',300,'Q',1,'n-Propane')
    h_ref = CP.PropsSI('H','T',275,'P',p_ref,'n-Propane')
    mdot_c = 0.1
    
    HX = HeatExchanger('Water',mdot_c,p_Water,h_Water,'n-Propane',mdot_h,p_ref,h_ref) 
    
    HX.A_h = HX.A_c = 4
    #Actually run the HX code
    HX.run(and_solve = True)
    HX.plot_cells('full.pdf')
    #HX.plot_objective_function()
    #HX.plot_Ts_pair()
    #HX.plot_ph_pair()

def VICompEcon():
    p_h = CP.PropsSI('P','T',315,'Q',1,'R407C')
    h_h = CP.PropsSI('H','P',CP.PropsSI('P','T',315,'Q',1,'R407C'),'T',CP.PropsSI('T','P',CP.PropsSI('P','T',315,'Q',1,'R407C'),'Q',0,'R407C')-5,'R407C')
    mdot_h = 0.059
    
    p_c = 816322.314008
    h_c = CP.PropsSI('H','P',816322.314008,'Q',0.57,'R407C')
    mdot_c = 0.016
    
    params = {
        'Fluid_h':'R407C',
        'mdot_h':mdot_h,
        'h_hi': h_h,
        'p_hi': p_h,
        'Fluid_c': 'R407C',
        'mdot_c':mdot_c,
        'h_ci':h_c,
        'p_ci':p_c,
        'A_h':4,
        'A_c':4,
        }
    
    HX = HeatExchanger(**params) 
        
    #Actually run the HX code
    HX.run(and_solve = True)
    #HX.plot_cells('full.pdf')
    #HX.plot_objective_function()
    HX.plot_Ts_pair()
    #HX.plot_ph_pair()
    
def VICompEconRes():
    Tdew_c = CP.PropsSI('T','P',816322.314008,'Q',1.0,'R407C')
    Tinj = Tdew_c + 5
    hinj = CP.PropsSI('H','P',816322.314008,'T',Tinj,'R407C')
    p_h = CP.PropsSI('P','T',315,'Q',1,'R407C')
    h_h = CP.PropsSI('H','P',CP.PropsSI('P','T',315,'Q',1,'R407C'),'T',CP.PropsSI('T','P',CP.PropsSI('P','T',315,'Q',1,'R407C'),'Q',0,'R407C')-5,'R407C')
    mdot_h = 0.059
    p_c = 816322.314008
    mdot_c = 0.016
    params = {
        'Fluid_h':'R407C',
        'mdot_h':mdot_h,
        'h_hi': h_h,
        'p_hi': p_h,
        'Fluid_c': 'R407C',
        'mdot_c':mdot_c,
        'h_ci':CP.PropsSI('H','P',816322.314008,'Q',0.9,'R407C'),
        'p_ci':p_c,
        'A_h':4,
        'A_c':4,
        }
    HX = HeatExchanger(**params)
    
    def residual(x_in):
        params = {
        'h_ci':CP.PropsSI('H','P',816322.314008,'Q',x_in,'R407C'),
        }
        HX.Update(**params)
        HX.run(and_solve = True)
         
        resid = HX.Tvec_c[-1] - Tinj#mdot_c*(HX.h_co - hinj)
        return resid
     
    x_in_actual = scipy.optimize.brentq(residual,0.01,0.99)
    print('x_in_actual = ', x_in_actual)
    params = {
            'h_ci':CP.PropsSI('H','P',816322.314008,'Q',x_in_actual,'R407C')
            }
    HX.Update(**params)
    #Actually run the HX code
    HX.run(and_solve = True)
    #HX.plot_cells('full.pdf')
    #HX.plot_objective_function()
    HX.plot_Ts_pair()
    #HX.plot_ph_pair()

def VICompEcon_new():
    p_h = CP.PropsSI('P','T',315,'Q',1,'R407C')
    h_h = CP.PropsSI('H','P',CP.PropsSI('P','T',315,'Q',1,'R407C'),'T',CP.PropsSI('T','P',CP.PropsSI('P','T',315,'Q',1,'R407C'),'Q',0,'R407C')-5,'R407C')
    mdot_h = 0.059
    
    p_c = 816322.314008
    h_c = CP.PropsSI('H','P',816322.314008,'Q',0.57,'R407C')
    mdot_c = 0.016
    
    params = {
        'Fluid_h':'R407C',
        'mdot_h':mdot_h,
        'h_hi': h_h,
        'p_hi': p_h,
        'Fluid_c': 'R407C',
        'mdot_c':mdot_c,
        'h_ci':h_c,
        'p_ci':p_c,
        'A_h':4,
        'A_c':4,
        }
    
    HX = HeatExchanger(**params) 
        
    #Actually run the HX code
    HX.run(and_solve = False)
    HX.plot_cells('VICompEcon_new.pdf')
    #HX.plot_objective_function()
    #HX.plot_Ts_pair()
    #HX.plot_ph_pair()
          
if __name__=='__main__':
    # If the script is run directly, this code will be executed.
    #PropaneEvaporatorPinching()
    #VICompEcon()
    VICompEcon_new()
    #VICompEconRes()
