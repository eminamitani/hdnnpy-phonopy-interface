'''
More generic code for interfacing hdnnpy and phono3py

@author: emi
'''

import glob
import sys
import yaml

import ase.io
import subprocess
import shutil
from distutils.dir_util import copy_tree
import os


'''
using yaml input to more generic purpose.
'''

class phono3pyConfig:

    prefix=None
    poscar=None
    dim=None
    symfc=None
    strpa=None
    dimfc2=None
    pipfile=None
    fc3output=None
    fc2output=None
    nnpoutput=None
    jobscriptheader=None
    mpicommand = None


    def __init__(self, path):
        with open('phono3py_config.yaml') as f:
            config=yaml.safe_load(f)
        self.prefix=config['prefix']
        self.poscar=config['poscar']
        self.dim=config['dim']
        self.symfc=config['symfc']
        self.pipfile=config['pipfile']
        self.nnpoutput=config['nnpoutput']
        self.fc3output=config['fc3output']
        self.jobscriptheader=config['jobscriptheader']
        self.mpicommand=config['mpicommand']

        ##optional for different cell size in 2nd order FC
        if('dimfc2' in config):
            self.dimfc2=config['dimfc2']
            self.fc2output=config['fc2output']
        if('strpa' in config):
            self.strpa = config['strpa']


class hdnnpy2phono3py:
    phono3py_config=None
    def __init__(self):
        self.phono3py_config = phono3pyConfig('phono3py_config.yaml')
        #print(self.phono3py_config)


    def prep(self):
        pc=self.phono3py_config
        strdim = "--dim= " + str(pc.dim[0]) + " " + str(pc.dim[1]) + " " \
                 + str(pc.dim[2])
        disp_generate_command = ['phono3py', '-d', strdim, '-c', pc.poscar]
        if(pc.dimfc2 is not None):
            strdimfc2= "--dim-fc2= " + str(pc.dimfc2[0]) + " " + str(pc.dimfc2[1]) + " " \
                 + str(pc.dimfc2[2])
            disp_generate_command = ['phono3py', '-d', strdim, strdimfc2, '-c', pc.poscar]

        # generate POSCAR-XXXX and POSCAR_FC2-XXXX files

        print(disp_generate_command)
        gd = subprocess.run(disp_generate_command)

        # gather all displacement files for 3rd order FC to dispfc3.xyz
        prefix = pc.prefix
        poscars_init = glob.glob('POSCAR-[0-9]*')
        xyzfc3 = 'dispfc3.xyz'
        poscars = sorted(poscars_init, key=str.lower)
        for poscar in poscars:
            print(poscar)
            atoms = ase.io.read(poscar, format='vasp')
            atoms.info['tag'] = prefix + atoms.get_chemical_formula()
            ase.io.write(xyzfc3, atoms, format='xyz', append=True)

        #fc3 and fc2 prediction are done in different directory
        os.makedirs('predict-fc3', exist_ok=True)
        shutil.copy('dispfc3.xyz','./predict-fc3/dispfc3.xyz')
        copy_tree(pc.nnpoutput, pc.fc3output)
        # prepare the prediction_config.py here
        with open('./predict-fc3/prediction_config.py', 'w') as pp:
            pp.write("c.PredictionApplication.verbose = True \n")
            pp.write("c.PredictionConfig.data_file = 'dispfc3.xyz' \n")
            pp.write("c.PredictionConfig.dump_format = '.npz' \n")
            pp.write("c.PredictionConfig.load_dir = '../"+pc.fc3output+"'\n")
            pp.write("c.PredictionConfig.order = 1 \n")
            pp.write("c.PredictionConfig.tags = ['*'] \n")

        #if different cell size is used for 2nd order, prepare the displacement file of dispfc2.xyz
        if(pc.dimfc2 is not None):
            poscars_init=glob.glob('POSCAR_FC2-[0-9]*')
            xyzfc2='dispfc2.xyz'
            poscarsfc2=sorted(poscars_init, key=str.lower)
            for poscar in poscarsfc2:
                print(poscar)
                atoms = ase.io.read(poscar, format='vasp')
                atoms.info['tag'] = prefix + atoms.get_chemical_formula()
                ase.io.write(xyzfc2, atoms, format='xyz', append=True)

            os.makedirs('predict-fc2', exist_ok=True)
            shutil.copy('dispfc2.xyz', './predict-fc2/dispfc2.xyz')
            copy_tree(pc.nnpoutput, pc.fc2output)
            # prepare the prediction_config.py here
            with open('./predict-fc2/prediction_config.py', 'w') as pp:
                pp.write("c.PredictionApplication.verbose = True \n")
                pp.write("c.PredictionConfig.data_file = 'dispfc2.xyz' \n")
                pp.write("c.PredictionConfig.dump_format = '.npz' \n")
                pp.write("c.PredictionConfig.load_dir = '../" + pc.fc2output + "'\n")
                pp.write("c.PredictionConfig.order = 1 \n")
                pp.write("c.PredictionConfig.tags = ['*'] \n")

        with open('predictionRun.sh', "w") as pr:
            pr.write(pc.jobscriptheader)
            pr.write('cd ./predict-fc3 \n')
            pr.write("export PIPENV_PIPFILE=" + pc.pipfile + "\n")
            pr.write("pipenv run " + pc.mpicommand+ " hdnnpy predict \n")
            if (pc.dimfc2 is not None):
                pr.write('cd ../predict-fc2 \n')
                pr.write("pipenv run " + pc.mpicommand + " hdnnpy predict \n")





if __name__ == '__main__':
    interface=hdnnpy2phono3py()
    if(sys.argv[1]=='prep'):
        print('preperation run')
        interface.prep()





