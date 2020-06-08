'''
More generic code for interfacing hdnnpy and phono3py

@author: emi
'''
import argparse
import glob
import ase.io
import subprocess
from pathlib import Path
import shutil
from distutils.dir_util import copy_tree
import os
from traitlets import ( Bool, CaselessStrEnum, Dict, Float,
    Integer, List, TraitType, Tuple, Unicode, )
from traitlets.config import Application

import traitlets.config


'''
using traitlets.config to more generic purpose.
same as hdnnpy
'''

class Configurable(traitlets.config.Configurable):
    def dump(self):
        dic = {key: value for key, value in self._trait_values.items()
               if key not in ['config', 'parent']}
        return dic

class phono3pyConfig(Configurable):
    prefix=Unicode(help="prefix for hdnnpy config file").tag(config=True)
    poscar=Unicode(default_value="POSCAR", help="POSCAR name for unitcell data").tag(config=True)
    dim=List(trait=Integer, help="dimension of supercell for fc3 calculation").tag(config=True)
    dimfc2=List(trait=Integer, help="dimension of sulercell for fc2 calculation").tag(config=True)
    strpa=List(trait=Unicode, help="lattice vector to convert conventional to primitive cell \
                                   if POSCAR is conventional Unitcell").tag(config=True)
    symfc=Bool(default_value=False, help="using symmetric correction on fc2 and fc3 calculation").tag(config=True)

class jobConfig(Configurable):
    pipfile=Path(help='path for your Pipfile').tag(config=True)
    header=List(trait=Unicode,help="header for job script setting")


class prep(Application):
    name=Unicode(u'hdnnpy2phono3py prep')
    description='preperation process to obtain 2nd and 3rd order force constant by hdnnpy'
    classes=List([phono3pyConfig, jobConfig])


class run(Application):
    name=Unicode(u'hdnnpy2phono3py run')
    description='phono3py run using FORCES_FC2 and FORCES_FC3 evaluated by hdnnpy'


class phono3pyInterface(Application):
    name = Unicode(u'hdnnpy2phono3py')
    classes=[
        prep,
        run
    ]


parser=argparse.ArgumentParser(description='xyz file creation input', fromfile_prefix_chars='@')
parser.add_argument('--prefix', metavar='prefix for hdnnpy tag', type=str,action='store')
parser.add_argument('--poscar', metavar='POSCAR file name', type=str, action='store')
parser.add_argument('--dim', metavar='dimension of supercell', type=int, nargs=3 )

#prepare phono3py displacement & convert them to single xyz
args=parser.parse_args()

prefix = args.prefix
poscar_seed=str(args.poscar)
strdim="--dim= "+str(args.dim[0])+" "+str(args.dim[1])+ " "+str(args.dim[2])

#generate POSCAR-XXXX files
disp_generate_command=['phono3py', '-d', strdim, '-c', poscar_seed ]
gd=subprocess.run(disp_generate_command)

#gather all displacement files to disp.xyz
prefix = args.prefix
poscars_init = glob.glob('POSCAR-[0-9]*')
xyz = 'disp.xyz'
poscars=sorted(poscars_init, key=str.lower)
for poscar in poscars:
    print(poscar)
    atoms = ase.io.read(poscar, format='vasp')
    atoms.info['tag'] = prefix + atoms.get_chemical_formula()
    ase.io.write(xyz, atoms, format='xyz', append=True)

#set default hdnnpy output directory
#change apptopreate when you use this script
nnpout='../output'
#prepare output dir for prediction
prout='../output-phono3py'
copy_tree(nnpout, prout)

#prepare the prediction_config.py here
with open('prediction_config.py', 'w') as pp:
    pp.write("c.PredictionApplication.verbose = True \n")
    pp.write("c.PredictionConfig.data_file = 'disp.xyz' \n")
    pp.write("c.PredictionConfig.dump_format = '.npz' \n")
    pp.write("c.PredictionConfig.load_dir = '../output-phono3py' \n")
    pp.write("c.PredictionConfig.order = 1 \n")
    pp.write("c.PredictionConfig.tags = ['*'] \n")


#prepare jobscript for running prediction
#Pipfile pathlib
pipfile='/home/emi/oguraHDNNP-withphono3py/HDNNP/Pipfile'
with open('predictionRun.sh', "w") as pr:
    pr.write('#!/bin/csh \n')
    pr.write("#$ -cwd \n")
    pr.write("#$ -V -S /bin/bash \n")
    pr.write("#$ -N prediction \n")
    pr.write("#$ -o stdout \n")
    pr.write("#$ -e stderr \n")
    pr.write("#$ -q all.q \n")
    pr.write("#$ -pe smp 24 \n")
    pr.write("export OMP_NUM_THREADS=1 \n")
    pr.write("export PIPENV_PIPFILE="+pipfile +"\n")
    pr.write("pipenv run mpirun -np 24 hdnnpy predict \n")


#subprocess.run(['phono3py', '-d', '-c', poscar_seed, '--dim= 2 2 2',])

#os.system('phono3py -d --dim=\'2 2 2\' -c POSCAR-unitcell')
