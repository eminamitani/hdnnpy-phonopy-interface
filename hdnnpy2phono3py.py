'''
More generic code for interfacing hdnnpy and phono3py

@author: emi
'''
import argparse
import glob
import sys
import yaml

import ase.io
import subprocess
from pathlib import Path
import shutil
from distutils.dir_util import copy_tree
import os
import pathlib



'''
using traitlets.config to more generic purpose.
same as hdnnpy
'''

class phono3pyConfig:

    prefix=None
    poscar=None
    dim=None
    symfc=None
    strpa=None
    dimfc2=None
    pipfile=None


    def __init__(self, path):
        with open('phono3py_config.yaml') as f:
            config=yaml.safe_load(f)
        self.prefix=config['prefix']
        self.poscar=config['poscar']
        self.dim=config['dim']
        self.symfc=config['symfc']
        self.pipfile=config['pipfile']

        ##optional
        if('dimfc2' in config):
            self.dimfc2=config['dimfc2']
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
        if(pc.dimfc2 is not None):
            strdim=strdim +"    --dimfc2= " + str(pc.dimfc2[0]) + " " + str(pc.dimfc2[1]) + " " \
                 + str(pc.dimfc2[2])
        print(strdim)



if __name__ == '__main__':
    interface=hdnnpy2phono3py()
    if(sys.argv[1]=='prep'):
        print('preperation run')
        interface.prep()





