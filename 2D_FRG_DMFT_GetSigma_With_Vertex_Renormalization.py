import numpy as np
from scipy import integrate
import sys
import time

def U_Lam(U,Lambda):
    return U/(1+(Lambda-(2+Lambda**2)/np.sqrt(4+Lambda**2))*U/(2*np.pi)) # this is the form for half-filling only.

def GetSigma(U,N,t,N_repetitions = 10,mu_to_be_calcd = 0,impurity_strength = 0,PHS = True):
    
    #This function will calculate the self energy for the system for a given parameter set.
    
    #U denotes the in-chain interaction, N the chain length, t denotes the cross-chain hopping, which is denoted as t' in the master thesis, N_repetitions denotes 
    #the number of DMFT repetitions. We found that 10 repetitions are usually more than sufficient to obtain an accuracy of better than 10^-6. mu_to_be_calcd denotes
    #the mu value where the system can be calculated. Note that we here have renormalized U in such a way that the renormalization only holds for half-filling, so mu must be chosen accordingly
    #impurity strength denotes the strength V of a site impurity situated at the center of the chain,
    #PHS (Particle hole symmetry) denotes whether or not the term U/2 is added to the initial conditions for the first and last site.
    #If PHS == True, then mu = U corresponds to exactly the half-filled case.
    
    #Again: Notice that in this code we switched the notation t <-> t' comparing to the thesis.
    
    t_prime = 1
    B_Matrix = np.diag([1]*(N-1),1)+np.diag([1]*(N-1),-1)

    
    def ToMatrix(A):
        return np.diag(A[:N])+np.diag(A[N:],1)+np.diag(A[N:],-1)
    
    def ToArray(A):
        return np.append(np.diag(A),np.diag(A,1))
    
    def CosIntegral(a,b,c):
        #returns the value of the integral from 0 to 2pi of 1/(a*i+b+c*cos(x)) dx
        return 2*np.pi*1j/np.sqrt(-b**2-2*1j*a*b+a**2+c**2)*np.sign(-a)


    
    Initial_vals = np.append(np.array([1+0j]*N),np.array([0j]*(N-1)))
    
    
    if(PHS == False):
        Initial_vals[0]-=0.5
        Initial_vals[N-1]-=0.5
    
    
    def Hyb_iz(omega):
    
        return  np.zeros((N,N))
    
    
    def G_tilda_Lam(Sigma_Lam,omega,t_prime,mu):
        Sigma_Matrix = ToMatrix(Sigma_Lam)
        G_0_inv = (mu + 1j*omega)*np.eye(N)+t_prime*B_Matrix-Hyb_iz(omega) #better check again
    
        return np.linalg.inv(G_0_inv-Sigma_Matrix)
    
    def Returnvector(Lambda,Sigma_Lam,t_prime,U,mu):

        G_pos = G_tilda_Lam(Sigma_Lam,Lambda,t_prime,mu)
        G = 2*np.real(G_pos)
    
        Returnable = []
        for i in range(N):
            Summand = 0
            for r in [1,-1]:
                if(0<=(i+r)<=N-1):
                    Summand += G[i+r,i+r]
            Returnable.append(-U_Lam(U, Lambda)/(2*np.pi)*Summand)
            
        for i in range(N-1):
            Returnable.append(U_Lam(U, Lambda)/(2*np.pi)*G[i,i+1])
            
        return Returnable
    
    V_0 = 1000.
    initials = (U_Lam(U,V_0)*Initial_vals).flatten()
    initials[N//2] += impurity_strength

    def G_Matrix_Trace(omega,Sigma,mu):
        Sigma = ToArray(Sigma)
        return np.real(np.trace(G_tilda_Lam(Sigma.flatten(),omega,t_prime,mu))) #HIER
    
    def get_n(Sigma,mu):    
        n_avg = (1/(np.pi)*integrate.quad(G_Matrix_Trace,0,np.inf,args = (Sigma,mu))[0]+0.5*N)/N
        return n_avg
    
    def Next_Hyb_iz(Hyb_iz, returnSigma = False):
        a = integrate.solve_ivp(lambda r,y: Returnvector(r,y,t_prime,U,mu),[V_0,0.00000001],initials,rtol = 1e-6,atol = 1e-9)
        data = a.y[:,-1]
        Sigma = ToMatrix(data)
        Mtbi = t_prime*B_Matrix-Sigma #Matrix to be inverted
        New_Eigenvalues, New_U_Matrix = np.linalg.eig(Mtbi)
        def G_latt_inv_iz(z): 
            return (2*np.pi)*New_U_Matrix@np.diag(1./CosIntegral(z,mu+New_Eigenvalues,2*t))@New_U_Matrix.transpose() 
        
    
        def Hyb_iz_new(z):
    
            return (1j*z+mu)*np.eye(N)+t_prime*B_Matrix-Sigma-G_latt_inv_iz(z)
    
                
        if(returnSigma == False):
            return Hyb_iz_new
        else:
            return Hyb_iz_new,Sigma
        
        
    
    
    for mu in [mu_to_be_calcd]:
        #print(mu)
        SigmaArray = []
        def Hyb_iz(omega):
            return  np.zeros((N,N))
        print("Letsgo")
        
        for j in range(N_repetitions):

            print(j)
            Hyb_iz,Sigma = Next_Hyb_iz(Hyb_iz,returnSigma = True)
            SigmaArray.append(ToArray(Sigma))

        return np.array(SigmaArray) #returns the self energy of all loops in the form of an 2N+1 long array per loop. Contains diagonal elements, then off-diagonal elements. 

t_x = float(sys.argv[1]) #corresponds to t' in the thesis.
N = int(sys.argv[2]) #The chain length of the system
U = float(sys.argv[3]) #The interaction strength

ToBeSaved = GetSigma(U,N,t_x,N_repetitions = 1,mu_to_be_calcd = U,impurity_strength = 1.5,PHS = True)