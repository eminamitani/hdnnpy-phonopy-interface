#!/usr/bin/env python
# coding: utf-8
import sys
import random
import pathlib
import os
from ase.io import read
import shutil
import pprint

"""
This script is to gather the information from snapshot LAMMPS MD + VASP static calculation
for Shimizu-san's HDNNP code
The number of data is so large, thus, I add the function of random selection 
$ gather_data_for_ShimizuNNP [samples] [tag] [dir]
samples: how many samples taken from each directory
tag: information of samples
dir : the directory name to store the all file
"""

args = sys.argv
samples = int(args[1])
tag=args[2]
dir = args[3]

os.makedirs(dir, exist_ok=True)
present = pathlib.Path('./')
dirs = ([p for p in present.iterdir() if p.is_dir()])

for d in dirs:
    targets=[]
    subdirs = ([s for s in d.iterdir() if s.is_dir()])
    targets += random.sample(subdirs, samples)

print("total target number {}".format(len(targets)))
#counter of the file
counter=1

for target in targets:
    output=read(target+'/OUTCAR',format="vasp-out")
    forces=output.get_forces()
    positions=output.get_positions()
    energy=output.get_total_energy()
    natom=len(forces)
    shutil.copy(target+'/XDATCAR',dir+'/positions_'+tag+str(natom)+"atoms"+"_"+str(counter)+".dat")
    with open(dir+'/forces_'+tag+str(natom)+"atoms"+"_"+str(counter)+".dat",'w') as out:
        out.write("--\n")
        out.write(" POSITION                                       TOTAL-FORCE (eV/Angst) \n")
        out.write(" ----------------------------------------------------------------------------------- \n ")
        for i, p in enumerate(positions):
            out.write(str(p[0]) + " " + str(p[1]) + " " + str(p[2]) + " " + str(forces[i][0]) + " " + str(
                forces[i][1]) + " " + str(forces[i][1])+"\n")
    with open(dir + '/energies_' + tag + str(natom) + "atoms" + "_" + str(counter) + ".dat", 'w') as ene:
        ene.write(str(energy)+"\n")
    counter+=1
