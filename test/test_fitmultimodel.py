
import numpy as np
from numpy import pi, inf, NaN
from deerlab import dipolarkernel, regoperator, regparamrange, selregparam, whitegaussnoise, fitmultimodel
from deerlab.dd_models import dd_gengauss, dd_gauss, dd_rice, dd_gauss2, dd_rice3, dd_gauss3
from deerlab.bg_models import bg_exp
from deerlab.utils import ovl

def test_multigauss():
#=======================================================================
    "Check that the fit of a multi-Gauss model works"
        
    r = np.linspace(2,6,300)
    t = np.linspace(-0.5,6,500)
    K = dipolarkernel(t,r)
    parin = [4, 0.2, 0.4, 4, 1, 0.4, 3, 0.4, 0.2]
    P = dd_gauss3(r,parin)
    V = K@P

    Pfit,_,_,_,_ = fitmultimodel(V,K,r,dd_gauss,3,'aicc', uqanalysis=False)

    assert ovl(P,Pfit) > 0.99 # more than 99% overlap
#=======================================================================

def test_multirice():
#=======================================================================
    "Check that the fit of a multi-Rician model works"
        
    r = np.linspace(2,6,300)
    t = np.linspace(0,6,500)
    K = dipolarkernel(t,r)
    parin = [4, 0.2, 0.4, 4, 1, 0.4, 3, 0.4, 0.4]
    P = dd_rice3(r,parin)
    V = K@P

    Pfit,_,_,_,_ = fitmultimodel(V,K,r,dd_rice,3,'aicc', uqanalysis=False)

    assert ovl(P,Pfit) > 0.99 # more than 99% overlap
#=======================================================================


def test_multigengauss():
#=======================================================================
    "Check that the fit of a multi-generalized-Gaussian model works"
        
    r = np.linspace(2,6,300)
    t = np.linspace(0,6,500)
    K = dipolarkernel(t,r)
    P = dd_gengauss(r,[2.5, 0.5, 5]) + 0.8*dd_gengauss(r,[3, 0.7, 2])
    P /= np.trapz(P,r)
    V = K@P

    Pfit,_,_,_,_ = fitmultimodel(V,K,r,dd_gengauss,3,'aicc', uqanalysis=False)

    assert ovl(P,Pfit) > 0.99 # more than 99% overlap
#=======================================================================

def test_bounds():
#=======================================================================
    "Check that specifying bounds for the basis function works correctly"
        
    r = np.linspace(2,6,300)
    t = np.linspace(0,6,500)
    K = dipolarkernel(t,r)
    parin = [4, 0.2, 0.4, 4, 1, 0.4, 3, 0.4, 0.2]
    P = dd_gauss3(r,parin)
    V = K@P

    Pfit,_,_,_,_ = fitmultimodel(V,K,r,dd_gauss,3,'aicc',lb = [2,0.1],ub=[5.5,1.5], uqanalysis=False)

    assert ovl(P,Pfit) > 0.99 # more than 99% overlap
#=======================================================================

def test_rescaling():
#=======================================================================
    "Check that rescaling does not change the results"
    t = np.linspace(0,5,100)
    r = np.linspace(2,6,100)
    P = dd_gauss(r,[4, 0.6])
    K = dipolarkernel(t,r)

    scale = 1e3
    V  = K@P

    Pfit1,_,_,_,_ = fitmultimodel(V*scale,K,r,dd_gauss,3,'aic',normP=True,uqanalysis=False)
    Pfit2,_,_,_,_ = fitmultimodel(V,K,r,dd_gauss,3,'aic',normP=False,uqanalysis=False)

    assert max(abs(Pfit1 - Pfit2)) < 1e-4
#=======================================================================

def test_global_multigauss():
#=======================================================================
    "Check that the global fit of a multi-Gauss model works"
        
    r = np.linspace(2,6,300)
    parin = [4, 0.2, 0.4, 4, 1, 0.4, 3, 0.4, 0.2]
    P = dd_gauss3(r,parin)
    
    t1 = np.linspace(-0.5,6,500)
    K1 = dipolarkernel(t1,r)
    V1 = K1@P
    
    t2 = np.linspace(0,5,300)
    K2 = dipolarkernel(t2,r)
    V2 = K2@P

    Pfit,_,_,_,_ = fitmultimodel([V1,V2],[K1,K2],r,dd_gauss,3,'aicc', uqanalysis=False)

    assert ovl(P,Pfit) > 0.99 # more than 99% overlap
#=======================================================================

def test_global_multirice():
#=======================================================================
    "Check that the global fit of a multi-Rician model works"
        
    r = np.linspace(2,6,300)
    parin = [4, 0.2, 0.4, 4, 1, 0.4, 3, 0.4, 0.4]
    P = dd_rice3(r,parin)

    t1 = np.linspace(-0.5,6,500)
    K1 = dipolarkernel(t1,r)
    V1 = K1@P
    
    t2 = np.linspace(0,5,300)
    K2 = dipolarkernel(t2,r)
    V2 = K2@P

    Pfit,_,_,_,_ = fitmultimodel([V1,V2],[K1,K2],r,dd_rice,3,'aicc', uqanalysis=False)

    assert ovl(P,Pfit) > 0.99 # more than 99% overlap
#=======================================================================


def test_background_fit():
#=======================================================================
    "Check the fitting of a non-linear kernel model"
    
    t = np.linspace(-0.3,4,100)
    r = np.linspace(3,6,200)
    InputParam = [4, 0.2, 0.5, 4.3, 0.3, 0.4]
    P = dd_gauss2(r,InputParam)
    B = bg_exp(t,0.15)
    V = dipolarkernel(t,r,0.25,B)@P

    def Kmodel(par):
        lam,k = par
        B = bg_exp(t,k)
        K = dipolarkernel(t,r,lam,B)
        return K

    Pfit,_,_,_,_ = fitmultimodel(V,Kmodel,r,dd_gauss,2,'aicc',lb=[1,0.1],ub=[6,1],lbK=[0.2,0.01],ubK=[0.9,1],uqanalysis=False)

    assert ovl(P,Pfit) > 0.99 # more than 99% overlap
#=======================================================================


def assert_confidence_intervals(pci50,pci95,pfit,lb,ub):
    
    p95lb = pci95[:,0]
    p95ub = pci95[:,1]
    p50lb = pci50[:,0]
    p50ub = pci50[:,1]
    errors = []
    if not np.all(p95lb <= pfit) and not np.all(p50lb <= pfit):
        errors.append("Some fitted values are below the lower bound of the confidence intervals.")
    if not np.all(p95ub >= pfit) and not np.all(p50lb >= pfit):
        errors.append("Some fitted values are over the upper bound of the confidence intervals.")
    if not np.all(p95lb <= p50lb):
        errors.append("The 50%-CI has lower values than the 95%-CI")
    if not np.all(p95ub >= p50ub):
        errors.append("The 50%-CI has larger values than the 95%-CI")
    if not np.all(np.minimum(lb,p95lb)==lb):
        errors.append("The lower bounds are not satisfied by the confidence intervals.")
    if not np.all(np.maximum(ub,p95ub)==ub):
        errors.append("The upper bounds are not satisfied by the confidence intervals.")
    assert not errors, "Errors occured:\n{}".format("\n".join(errors))


def test_confinter_Pfit():
#=======================================================================
    "Check that the confidence intervals of the fitted distribution are correct"
    
    t = np.linspace(-0.3,4,100)
    r = np.linspace(3,6,200)
    InputParam = [4, 0.2, 0.5, 4.3, 0.3, 0.4]
    P = dd_gauss2(r,InputParam)
    K = dipolarkernel(t,r)
    V = K@P

    Pfit,_,Puq,_,_ = fitmultimodel(V,K,r,dd_gauss,3,'aicc',lb=[1,0.1],ub=[6,1])

    lbP = np.zeros(len(r))
    ubP = np.full(len(r), np.inf)
    assert_confidence_intervals(Puq.ci(50),Puq.ci(95),Pfit,lbP,ubP)
#=======================================================================

def test_confinter_parfit():
#=======================================================================
    "Check that the confidence intervals of the fitted parameters are correct"
    
    t = np.linspace(-0.3,4,100)
    r = np.linspace(3,6,200)
    InputParam = [4, 0.2, 0.5, 4.3, 0.3, 0.4]
    P = dd_gauss2(r,InputParam)
    K = dipolarkernel(t,r)
    V = K@P

    lbPpar = [1,0.1]
    ubPpar = [6,1]
    _,parfit,_,paruq,_ = fitmultimodel(V,K,r,dd_gauss,3,'aicc',lb=[1,0.1],ub=[6,1])

    assert_confidence_intervals(paruq.ci(50)[0:2,:],paruq.ci(95)[0:2,:],parfit[1],lbPpar,ubPpar)
#=======================================================================


def test_goodness_of_fit():
#=======================================================================
    "Check the goodness-of-fit statistics are correct" 
        
    r = np.linspace(2,6,300)
    t = np.linspace(-0.5,6,500)
    K = dipolarkernel(t,r)
    parin = [4, 0.2, 0.4, 4, 1, 0.4, 3, 0.4, 0.2]
    P = dd_gauss3(r,parin)
    V = K@P

    _,_,_,_,stats = fitmultimodel(V,K,r,dd_gauss,3,'aicc', uqanalysis=False)

    assert abs(stats['chi2red'] - 1) < 5e-2 and abs(stats['R2'] - 1) < 5e-2
#=======================================================================





