# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 16:48:57 2019

@author: Emi Minamitani

prediction of IFC

1. make xyz from POSCAR of primitive cell

2. predict by hdnnpy with
c.PredictionConfig.order = 2

3. parse prediction results by this script
 
"""
#check the symmetry of predicted IFC
import numpy as np
f=np.load('prediction_result.npz')
keys=list(f)
#tags/harmonic is the third key
#shape is (1,1,3*n, 3*n) n: number of atoms
IFC=f[keys[2]][0,0]
IFC_T=IFC.T
diff=IFC-IFC_T
norm=(IFC+IFC_T)/2
norm_diff=diff/norm

np.set_printoptions(formatter={'float': '{:0.4e}'.format})
print("IFC\n{}".format(IFC))
print("IFC_T\n{}".format(IFC_T))
print("bare value of difference:\n{}".format(diff))
print("normalized value of difference:\n{}".format(norm_diff))

