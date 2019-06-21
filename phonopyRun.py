
import argparse
import glob
import ase.io
import subprocess
from pathlib import Path
import shutil
from distutils.dir_util import copy_tree
import os
import yaml
import numpy as np

parser=argparse.ArgumentParser(description='xyz file creation input', fromfile_prefix_chars='@')
parser.add_argument('--prefix', metavar='prefix for hdnnpy tag', type=str,action='store')
parser.add_argument('--poscar', metavar='POSCAR file name', type=str, action='store')
parser.add_argument('--dim', metavar='dimension of supercell', type=int, nargs=3 )
parser.add_argument('--mesh', metavar='dimension of mesh for band calculation', type=int, nargs=3 )

#prepare phono3py displacement & convert them to single xyz
args=parser.parse_args()

prefix = args.prefix
poscar_seed=str(args.poscar)


#copy the prediction result
prout='../output-phonopy/'

shutil.copy(prout+"prediction_result.npz","./prediction_result.npz")

'''
read displacement informations from disp.yaml
'''
with open('phonopy_disp.yaml') as stream:
    datas=yaml.safe_load(stream)


#in phonopy higher than version 1.5.1, displacements data are written in phonopy_disp.yaml
natom=len(datas['supercell']['points'])
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


with open('mesh_conf', "w") as mp:
    mp.write("ATOM_NAME=Si \n")
    mp.write("DIM=" +" "+str(args.dim[0])+" "+str(args.dim[1]) +" "+ str(args.dim[2]) +"\n")
    mp.write("MP="+" "+str(args.mesh[0])+" "+str(args.mesh[1]) +" "+ str(args.mesh[2]) +"\n")

fc_command=['phonopy', '-p', 'mesh_conf','-c', poscar_seed]
gd=subprocess.run(fc_command)

with open('band_conf', "w") as bp:
    bp.write("ATOM_NAME=Si \n")
    bp.write("DIM=" +" "+str(args.dim[0])+" "+str(args.dim[1]) +" "+ str(args.dim[2]) +"\n")
    bp.write("BAND=0.0 0.0 0.0  0.5 0.0 0.5 0.375 0.375 0.75 0.0 0.0 0.0 0.5 0.5 0.5 \n")

band_command=['phonopy', '-p', '-s', 'band.conf', '--band anto' , '-c', poscar_seed]
gd=subprocess.run(band_command)

plot_command=['phonopy-bandplot', '--gnuplot', 'band.yaml']
gd=subprocess.run(plot_command,stdout = subprocess.PIPE, stderr = subprocess.PIPE)
with open('band_data.gp',"w") as gnu:
    gnu.write(gd.stdout.decode('utf8'))
