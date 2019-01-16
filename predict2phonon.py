'''
simple script to create FORCE_SETS for phonopy

Emi Minamitani

step1: creating POSCAR-XXX file from phonopy by
"phonopy -d --dim="x x x"

step2: predict forces in each displacement by hdnnpy

step3: using this script to make FORCE_SETS

step4: obtain force constant and calculate phonon band by phonopy
(creating mesh.conf, band.conf is necessary to obtain phonon DOS and phonon Band)
'''

import yaml
import numpy as np
'''
read displacement informations from disp.yaml
'''
with open('disp.yaml') as stream:
    datas=yaml.safe_load(stream)

natom=datas['natom']

print("number of atoms")
print(natom)

disps=datas['displacements']

atom=[]
disp=[]

print("number of displacements from phonopy yaml file")
print(len(disps))

for i in disps:
    atom.append(i['atom'])
    disp.append(i['displacement'])


'''
Here I parse prediction results from hdnnpy
default output npz name: prediction_result.npz
here I assume prediction_result.npz contain
energy and force data for all displacement required by phonopy
with the same ordering in disp.yaml.
To do so, you need to care about the script for generation of xyz file to running prediction.
'''

force_set=[]
prdata=np.load('prediction_result.npz')
keys=prdata.files

for ik in keys:
    if(ik.find('force') >0):
        print('tag to store:'+str(ik))
        force_data=prdata[ik]
        force_set.append(force_data)

'''
To obtain the potential data from presiction_results.npz,
extraxt first element (like force_set[0]).
'''
print("size of hdnnpy data:"+str(len(force_set[0])))
if(len(force_set[0])!=len(disp)):
    print('data size of phonopy displacement and hdnnpy results does not match')

with open('FORCE_SETS', "w") as fs:
    fs.write(str(natom)+ "\n")
    fs.write(str(len(disps))+'\n')
    fs.write('\n')

    for i in range(len(disp)):
        fs.write(str(atom[i])+'\n')
        fs.write("%20.16f %20.16f %20.16f\n" %
            (tuple(disp[i])))

        for f in force_set[0][i]:
            f = f.reshape(-1, 3)
            for l in f:
                #print(l)
                fs.write("%15.10f %15.10f %15.10f\n" % (tuple(l)))
