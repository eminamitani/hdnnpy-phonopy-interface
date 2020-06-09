'''
More generic code for interfacing hdnnpy and phono3py

@author: emi
'''
import argparse
import glob
import sys

import ase.io
import subprocess
from pathlib import Path
import shutil
from distutils.dir_util import copy_tree
import os
from traitlets import ( Bool, CaselessStrEnum, Dict, Float,
    Int, List, TraitType, Tuple, Unicode, )
from traitlets.config import Application
import pathlib
import traitlets.config



'''
using traitlets.config to more generic purpose.
same as hdnnpy
'''
class Path(TraitType):
    default_value = '.'
    info_text = 'a pathlib.Path instance'

    def validate(self, obj, value):
        if isinstance(value, pathlib.Path):
            return value.absolute()
        elif isinstance(value, str):
            return pathlib.Path(value).absolute()
        else:
            self.error(obj, value)

class Configurable(traitlets.config.Configurable):
    def dump(self):
        dic = {key: value for key, value in self._trait_values.items()
               if key not in ['config', 'parent']}
        return dic

class phono3pyConfig(Configurable):
    prefix=Unicode(help="prefix for hdnnpy config file").tag(config=True)
    poscar=Unicode(default_value="POSCAR", help="POSCAR name for unitcell data").tag(config=True)
    dim=List(trait=Unicode(), help="dimension of supercell for fc3 calculation").tag(config=True)
    dimfc2=List(trait=Unicode(), help="dimension of sulercell for fc2 calculation").tag(config=True)
    strpa=List(trait=Unicode(), help="lattice vector to convert conventional to primitive cell \
                                   if POSCAR is conventional Unitcell").tag(config=True)
    symfc=Bool(default_value=False, help="using symmetric correction on fc2 and fc3 calculation").tag(config=True)
    pipfile=Path(help='path for your Pipfile').tag(config=True)
    header = List(trait=Unicode(), help="header for job script setting")



class prep(Application):
    name=Unicode(u'prep')
    verbose = Bool(
        True,
        help='Set verbose mode'
        ).tag(config=True)
    description='preperation process to obtain 2nd and 3rd order force constant by hdnnpy'
    classes=List([phono3pyConfig])
    config_file=Path('phono3py_config.py', help='Load this config file')

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.phono3py_config = None

    def initialize(self, argv=None):
        self.parse_command_line(argv)
        self.load_config_file(self.config_file)
        print(self.loaded_config_files)
        self.phono3py_config=phono3pyConfig(config=self.config)
        self.update_config(self.config)
        print(self.phono3py_config.symfc)
        print(self.phono3py_config.poscar)

    def start(self):
        pc=self.phono3py_config
        print(pc.symfc)
        print(pc.dim)
        strdim = "--dim= " + str(pc.dim[0]) + " " + str(pc.dim[1]) + " " \
                 + str(pc.dim[2])

class run(Application):
    name=Unicode(u'hdnnpy2phono3py run')
    description='phono3py run using FORCES_FC2 and FORCES_FC3 evaluated by hdnnpy'


class phono3pyInterface(Application):
    name = Unicode(u'hdnnpy2phono3py')
    classes=[
        prep,
        run
    ]

    subcommands = {
        'prep':(prep,prep.description),
        'run':(run,run.description)
    }

    def initialize(self, argv=None):
        assert  sys.argv[1] in self.subcommands, \
            'Only `prep` and `run` are' \
             'avairable'
        super().initialize(argv)

if __name__ == '__main__':
    phono3pyInterface.launch_instance()




