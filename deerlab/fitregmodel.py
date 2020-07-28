# fitregmodel.py - Fiting of regularization problems
# --------------------------------------------------
# This file is a part of DeerLab. License is MIT (see LICENSE.md).
# Copyright(c) 2019-2020: Luis Fabregas, Stefan Stoll and other contributors.

import numpy as np
from deerlab.nnls import fnnls, cvxnnls, nnlsbpp
from scipy.optimize import nnls
import deerlab as dl
import copy
from deerlab.utils import hccm, goodness_of_fit
from deerlab.uqst import uqst

def fitregmodel(V,K,r, regtype='tikhonov', alpha='aic', regorder=2, solver='cvx', 
                weights=1, huberparam=1.35, nonnegativity=True, obir = False, 
                uqanalysis=True, renormalize=True, noiselevelaim = -1, full_output=False):
    """  
    Regularization-based fit
    ========================

    Computes a non-parametric regularized distance distribution.

    Usage: 
    -----------
        Pfit,Puq = fitregmodel(V,K,r)
        Pfit,Puq = fitregmodel(V,K,r,regtype,method)
        Pfit,Puq = fitregmodel([V1,V2,__],[K1,K2,__],r)

    Arguments: 
    -----------
    V (N-element array, list of arrays)  
        Dipolar signal, multiple datasets can be globally evaluated by passing a list of signals.
    K (NxM-element array, list of arrays)  
        Dipolar kernel, if a list of signals is specified, a corresponding list of kernels must be passed as well.
    r (M-element array)
        Distance axis, in nanometers.
    regtype (string, default='tikhonov')
        Regularization functional type: 'tikhonov', 'tv', or 'huber'.   
    method (string, default='aic')    
        Method for the selection of the optimal regularization parameter.
            'lr' - L-curve minimum-radius method (LR)
            'lc' - L-curve maximum-curvature method (LC)
            'cv' - Cross validation (CV)
            'gcv' - Generalized Cross Validation (GCV)
            'rgcv' - Robust Generalized Cross Validation (rGCV)
            'srgcv' - Strong Robust Generalized Cross Validation (srGCV)
            'aic' - Akaike information criterion (AIC)
            'bic' - Bayesian information criterion (BIC)
            'aicc' - Corrected Akaike information criterion (AICC)
            'rm' - Residual method (RM)
            'ee' - Extrapolated Error (EE)          
            'ncp' - Normalized Cumulative Periodogram (NCP)
            'gml' - Generalized Maximum Likelihood (GML)
            'mcl' - Mallows' C_L (MCL)

    Return:
    -------
    Pfit (M-element array)
        Fitted distance distribution
    Puq (obj)
        Covariance-based uncertainty quantification of the fitted distance distribution
    stats (dict, if full_output is True)
        Goodness of fit statistical estimators

    Keyword arguments:
    ------------------
    weights (list, default=1)
        List of weights for the weighting of the different datasets in a global fit. 
        If not specified all datasets are weighted equally.
    regorder (int scalar, default=2)
        Order of the regularization operator.
    solver (str, default='cvx')
        Optimizer used to solve the non-negative least-squares problem: 
            'cvx' - Optimization of the NNLS problem using cvxopt
            'fnnls' - Optimization using the fast NNLS algorithm.
            'nnlsbpp' - Optimization using the block principal pivoting NNLS algorithm.
    full_output (boolean, default=False)
        If enabled (True) the function will return additional output arguments in a tuple.
    uqanalysis (boolean, default=True)
        Enable/disable the uncertainty quantification analysis. 
    nonnegativity (boolean, default=True)
        Enforces the non-negativity constraint on computed distance distributions.
    huberparam (scalar, default=1.35)
        Value of the Huber parameter used in Huber regularization.
    renormalize (boolean, True)
        Enable/disable renormalization of the fitted distribution.
    obir (boolean, default=False)
        Enable/disable the use of the Osher-Bregman iterated regularization algorithm.
    noiselevelaim (scalar, default=automatic)
        Noise level at which to stop the OBIR algorithm. 
    """
    V, K, weights, subsets = dl.utils.parse_multidatasets(V, K, weights)

    # Compute regularization matrix
    L = dl.regoperator(r,regorder)

    # Determine the type of problem to solve
    if obir:
        problem = 'obir'
    elif nonnegativity:
        problem = 'nnls'
    else:
        problem = 'unconstrained'

    # If the regularization parameter is not specified, get the optimal choice
    if type(alpha) is str:
        alpha = dl.selregparam(V,K,r,regtype,alpha,regorder=regorder,weights=weights, nonnegativity=nonnegativity,huberparam=huberparam)

    # Prepare components of the LSQ-problem
    [KtKreg, KtV] = dl.lsqcomponents(V,K,L,alpha,weights, regtype=regtype, huberparam=huberparam)

    # Unconstrained LSQ problem
    if problem == 'unconstrained':
        Pfit = np.linalg.solve(KtKreg,KtV)

    # Osher-Bregman iterated regularization
    elif problem == 'obir':
        Pfit = _obir(V,K,L,regtype,alpha,weights,noiselevelaim=noiselevelaim,huberparam = huberparam, solver = solver)
    # Non-negative LSQ problem
    elif problem == 'nnls':

        if solver == 'fnnls':
            Pfit = fnnls(KtKreg,KtV)
        elif solver == 'nnlsbpp':
            Pfit = nnlsbpp(KtKreg,KtV,np.linalg.solve(KtKreg,KtV))
        elif solver == 'cvx':
            Pfit = cvxnnls(KtKreg, KtV)
        else:
            raise KeyError(f'{solver} is not a known non-negative least squares solver')

    # Uncertainty quantification
    # ----------------------------------------------------------------
    if uqanalysis:
        # Construct residual parts for for the residual and regularization terms
        res = weights*(V - K@Pfit)

        # Construct Jacobians for the residual and penalty terms
        Jres = weights*K
        res,J = _augment(res,Jres,regtype,alpha,L,Pfit,huberparam)

        # Calculate the heteroscedasticity consistent covariance matrix 
        covmat = hccm(J,res,'HC1')
        
        # Construct confidence interval structure for P
        NonNegConst = np.zeros(len(r))
        Puq = uqst('covariance',Pfit,covmat,NonNegConst,[])
    else:
        Puq = []
    
    # Re-normalization of the distributions
    # --------------------------------------
    if renormalize:
        Pnorm = np.trapz(Pfit,r)
        Pfit = Pfit/Pnorm
        if uqanalysis:
            Puq_ = copy.deepcopy(Puq) # need a copy to avoid infite recursion on next step
            Puq.ci = lambda p: Puq_.ci(p)/Pnorm


    # Goodness-of-fit
    # --------------------------------------
    Vfit = K@Pfit
    H = K@(np.linalg.pinv(KtKreg)@K.T)
    stats = []
    for subset in subsets: 
        Ndof = len(V[subset]) - np.trace(H)
        stats.append(goodness_of_fit(V[subset],Vfit[subset],Ndof))
    if len(stats)==1: 
        stats = stats[0]

        
    if full_output:
        return Pfit,Puq,stats
    else:
        return Pfit,Puq
# ===========================================================================================


def _augment(res,J,regtype,alpha,L,P,eta):
# ===========================================================================================
    """ 
    LSQ residual and Jacobian augmentation
    =======================================

    Augments the residual and the Jacobian of a LSQ problem to include the
    regularization penalty. The residual and Jacobian contributions of the 
    specific regularization methods are analytically introduced. 
    """
    eps = np.finfo(float).eps
    # Compute the regularization penalty augmentation for the residual and the Jacobian
    if regtype is 'tikhonov':
        resreg = L@P
        Jreg = L
    elif regtype is 'tv':
        resreg =((L@P)**2 + eps)**(1/4)
        Jreg = 2/4*((( ( (L@P)**2 + eps)**(-3/4) )*(L@P))[:, np.newaxis]*L)
    elif regtype is 'huber':
        resreg = np.sqrt(np.sqrt((L@P/eta)**2 + 1) - 1)
        Jreg = 0.5/(eta**2)*( (((np.sqrt((L@P/eta)**2 + 1) - 1 + eps)**(-1/2)*(((L@P/eta)**2 + 1+ eps)**(-1/2)))*(L@P))[:, np.newaxis]*L )

    # Include regularization parameter
    resreg = alpha*resreg
    Jreg = alpha*Jreg

    # Augment jacobian and residual
    res = np.concatenate((res,resreg))
    J = np.concatenate((J,Jreg))

    return res,J
# ===========================================================================================


def _obir(V,K,L, regtype, alpha, weights, noiselevelaim=-1, huberparam=1.35 , solver = 'cvx'):
# ===========================================================================================
    """
    Osher's Bregman-iterated regularization method
    ==============================================

    P = OBIR(V,K,r,'type',alpha)

    OBIR of the N-point signal (V) to a M-point distance
    distribution (P) given a M-point distance axis (r) and NxM point kernel
    (K). The regularization parameter (alpha) controls the regularization
    properties.

    The type of regularization employed in OBIR is set by the 'type'
    input argument. The regularization models implemented in OBIR are:
        'tikhonov' -   Tikhonov regularization
        'tv'       -   Total variation regularization
        'huber'    -   pseudo-Huber regularization

    P = OBIR(...,'Property',Value)
    Additional (optional) arguments can be passed as name-value pairs.
    """

    if noiselevelaim == -1:
        noiselevelaim = dl.noiselevel(V)

    MaxOuterIter = 5000
    stopDivergent = False

    # Preparation
    #-------------------------------------------------------------------------------

    # Initialize
    nr = np.shape(L)[1]
    subGrad = np.zeros(nr)
    Counter = 1
    Iteration = 1
    Pfit = np.zeros(nr)

    # Osher's Bregman Iterated Algorithm
    #-------------------------------------------------------------------------------
    diverged = np.zeros(len(V))
    semiconverged = np.zeros(len(V))

    # Precompute the KtK and KtS input arguments
    [KtKreg,KtV] = dl.lsqcomponents(V,K,L,alpha, weights, regtype=regtype, huberparam=huberparam)

    while Iteration <= MaxOuterIter:

        # Store previous iteration distribution
        Pprev = Pfit
        
        #Update
        KtVsg = KtV - subGrad
        
        #Get solution of current Bregman iteration
        if solver == 'fnnls':
            Pfit = fnnls(KtKreg,KtVsg)
        elif solver == 'nnlsbpp':
            Pfit = nnlsbpp(KtKreg,KtVsg,np.linalg.solve(KtKreg,KtVsg))
        elif solver == 'cvx':
            Pfit = cvxnnls(KtKreg, KtVsg)
        else:
            raise KeyError(f'{solver} is not a known non-negative least squares solver')
        
        # Update subgradient at current solution
        subGrad = subGrad + weights*K.T@(K@Pfit - V)
        
        # Iteration control
        #--------------------------------------------------------------------------
        if Iteration == 1:
            # If at first iteration, the residual deviation is already below the
            # noise deviation then impose oversmoothing and remain at first iteration
            if noiselevelaim  > np.std(K@Pfit - V):
                alpha = alpha*2**Counter
                Counter = Counter + 1
                
                # Recompute the KtK and KtS input arguments with new alpha
                KtKreg,KtV = dl.lsqcomponents(V,K,L,alpha, weights, regtype=regtype, huberparam=huberparam)
            else:
                # Once the residual deviation is above the threshold, then proceed
                # further with the Bregman iterations
                Iteration  = Iteration + 1
        else:
            # For the rest of the Bregman iterations control the condition and stop
            # when fulfilled
            diverged = np.std(K@Pprev - V) < np.std(K@Pfit - V)
            semiconverged = noiselevelaim > np.std(K@Pfit - V)

            if semiconverged:
                break
            else:
                Iteration  = Iteration + 1

            # If residual deviation starts to diverge, stop
            if stopDivergent and diverged:
                Pfit = Pprev
                break

    return Pfit
# ===========================================================================================

