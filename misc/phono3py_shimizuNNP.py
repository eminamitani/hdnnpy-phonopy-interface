'''
interfacing Shimizu-san's NNP and phono3py

@author: Emi Minamitani
'''

import glob
import sys
import yaml
import numpy as np
import ase.io
import subprocess
import shutil
from distutils.dir_util import copy_tree
import os

'''
using yaml input to more generic purpose.
'''


class phono3pyConfig:
    prefix = None
    poscar = None
    dim = None
    symfc = None
    strpa = None
    dimfc2 = None
    jobscriptheader = None
    mpicommand = None
    mesh = None

    def __init__(self, path):
        with open('phono3py_config.yaml') as f:
            config = yaml.safe_load(f)
        self.prefix = config['prefix']
        self.poscar = config['poscar']
        self.dim = config['dim']
        self.symfc = config['symfc']
        self.jobscriptheader = config['jobscriptheader']
        self.mpicommand = config['mpicommand']
        self.mesh = config['mesh']

        ##optional for different cell size in 2nd order FC
        if ('dimfc2' in config):
            self.dimfc2 = config['dimfc2']

        if ('strpa' in config):
            self.strpa = config['strpa']


class nnp2phono3py:
    phono3py_config = None

    def __init__(self):
        self.phono3py_config = phono3pyConfig('phono3py_config.yaml')
        # print(self.phono3py_config)

    def prep(self):
        pc = self.phono3py_config
        strdim = "--dim= " + str(pc.dim[0]) + " " + str(pc.dim[1]) + " " \
                 + str(pc.dim[2])
        disp_generate_command = ['phono3py', '-d', strdim, '-c', pc.poscar]
        if (pc.dimfc2 is not None):
            strdimfc2 = "--dim-fc2= " + str(pc.dimfc2[0]) + " " + str(pc.dimfc2[1]) + " " \
                        + str(pc.dimfc2[2])
            disp_generate_command = ['phono3py', '-d', strdim, strdimfc2, '-c', pc.poscar]

        # generate POSCAR-XXXX and POSCAR_FC2-XXXX files

        print(disp_generate_command)
        gd = subprocess.run(disp_generate_command)

        #prepare directories for each POSCAR & POSCAR_FC2-XXXX
        poscars_init = glob.glob('POSCAR-[0-9]*')
        poscars = sorted(poscars_init, key=str.lower)
        for poscar in poscars:
            dirname="disp-"+poscar.split("-")[-1]
            os.makedirs(dirname,exist_ok=True)
            shutil.copy(poscar,dirname+"/"+poscar)
            with open(dirname+"/input_tag.dat","w") as tag:
                tag.write("-"+poscar.split("-")[-1])


        # if different cell size is used for 2nd order, prepare the displacement file of dispfc2.xyz
        if (pc.dimfc2 is not None):
            poscars_init = glob.glob('POSCAR_FC2-[0-9]*')
            poscarsfc2 = sorted(poscars_init, key=str.lower)
            for poscar in poscarsfc2:
                dirname="disp_fc2-"+poscar.split("-")[-1]
                shutil.copy(poscar, dirname+"/"+poscar)
                with open(dirname + "/input_tag.dat", "w") as tag:
                    tag.write("_FC2-" + poscar.split("-")[-1])

        with open('predictionRun.sh', "w") as pr:
            pr.write(pc.jobscriptheader)
            pr.write("for i in $(find ./ -name \"disp-*\" -type d); do \n")
            pr.write('echo ${i} \n')
            pr.write('cd ${i} \n')
            #here I assume a.out is in the upper directory
            pr.write('cp ../a.out . \n')
            pr.write('cp -r ../data_weight . \n')
            pr.write('cp -r ../data_maxmin . \n')
            pr.write('cp ../input_nnp.dat . \n')
            pr.write('cp ../param_nnp.dat  . \n')
            pr.write(pc.mpicommand + " a.out \n")
            pr.write('cd ../ \n')
            pr.write('done \n')


    def run(self):
        pc = self.phono3py_config
        # copy the prediction result for 3rd order

        '''
        In phono3py calculation, we can use different supercell size for 
        2nd and 3rd order force constant.
        '''

        # creatiing FORCE_FC3
        with open('disp_fc3.yaml') as stream:
            datas = yaml.safe_load(stream)

        natom = datas['natom']

        print("number of atoms")
        print(natom)

        num_disp = datas['num_displacements_created']

        fc3_generate_command = ['phono3py', '--cf3', 'disp-{00001..', str(num_disp).zfill(5),'}/vasprun.xml', '-c', pc.poscar]
        print(fc3_generate_command)
        gd = subprocess.run(fc3_generate_command)


        if (pc.dimfc2 is not None):
            # creatiing FORCE_FC2
            with open('disp_fc2.yaml') as stream:
                datas = yaml.safe_load(stream)

            print("2nd order Force constant setup")
            natom = datas['natom']

            print("number of atoms")
            print(natom)

            num_disp = datas['num_displacements_created']
            fc2_generate_command = ['phono3py', '--cf2', 'disp_fc2-{00001..', str(num_disp).zfill(5), '}/vasprun.xml', '-c',
                                    pc.poscar]
            print(fc2_generate_command)
            gd = subprocess.run(fc2_generate_command)


        # phono3py run
        # fc2.hdf, fc3.hdf
        strdim = "--dim= " + str(pc.dim[0]) + " " + str(pc.dim[1]) + " " \
                 + str(pc.dim[2])
        fc_command = ['phono3py', strdim, '-c', pc.poscar]
        if (pc.dimfc2 is not None):
            strdimfc2 = "--dim-fc2= " + str(pc.dimfc2[0]) + " " + str(pc.dimfc2[1]) + " " \
                        + str(pc.dimfc2[2])
            fc_command = ['phono3py', strdim, strdimfc2, '-c', pc.poscar]
        if (pc.symfc):
            fc_command.append('--sym-fc')

        print(fc_command)
        gd = subprocess.run(fc_command)

        # normal
        strmesh = "--mesh= " + str(pc.mesh[0]) + " " + str(pc.mesh[1]) + " " + str(pc.mesh[2])
        bte_command = ['phono3py', strdim, strmesh, '-c', pc.poscar, '--fc3', '--fc2', '--br']
        if (pc.dimfc2 is not None):
            bte_command = ['phono3py', strdim, strmesh, strdim, strdimfc2, '-c', pc.poscar, '--fc3', '--fc2', '--br']
        if (pc.symfc):
            bte_command.append('--sym-fc')
        if (pc.strpa is not None):
            str_pa = "--pa=" + pc.strpa

        print(bte_command)
        gd = subprocess.run(bte_command)


if __name__ == '__main__':
    interface = nnp2phono3py()
    if (sys.argv[1] == 'prep'):
        print('preperation run')
        interface.prep()
    elif (sys.argv[1] == 'run'):
        print('phono3py run')
        interface.run()





