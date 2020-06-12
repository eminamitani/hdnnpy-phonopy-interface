'''
More generic code for interfacing hdnnpy and phono3py

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
    mesh = None


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
        self.mesh=config['mesh']

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

    def run(self):
        pc = self.phono3py_config
        # copy the prediction result for 3rd order

        '''
        In phono3py calculation, we can use different supercell size for 
        2nd and 3rd order force constant.
        In this script, 3rd order calculation is done in the directry specified by fc3output phono3py_config.yaml.
        The prediction results are copied as prediction_result_fc3.npz
        '''

        shutil.copy(pc.fc3output + "/prediction_result.npz", "./prediction_result_fc3.npz")

        # creatiing FORCE_FC3
        with open('disp_fc3.yaml') as stream:
            datas = yaml.safe_load(stream)

        natom = datas['natom']

        print("number of atoms")
        print(natom)

        num_first_disp = datas['num_first_displacements']
        num_second_disp = datas['num_second_displacements']

        print("first and second displacements")
        print(str(num_first_disp) + "," + str(num_second_disp))

        first_atoms = datas['first_atoms']
        first_atom_number = []

        first_disp = []
        second_disp = []
        second_atom_number = []
        print("number of displacements for first atom")
        print(len(first_atoms))

        for i in first_atoms:
            second_atom = i['second_atoms']
            first_atom_number.append(i['number'])
            first_disp.append(i['displacement'])

            for s in second_atom:
                second_atom_number.append(s['number'])
                second_disp.append(s['displacements'])

        # print(second_atom_number)
        # print(second_disp)

        '''
        parse prediction results from hdnnpy
        default output npz name: prediction_result.npz
        here I assume prediction_result.npz contain
        energy and force data for all displacement required by phonopy
        with the same ordering in disp.yaml
        
 
        '''

        force_set = []
        prdata = np.load('prediction_result_fc3.npz')
        keys = prdata.files
        print(keys)

        # all force data have same key in default hdnnpy setting.
        # thus the actual data number is counted by len(force_set[0])

        for ik in keys:
            if (ik.find('force') > 0):
                print('tag to store:' + str(ik))
                force_data = prdata[ik]
                force_set.append(force_data)

        print("size of hdnnpy data:" + str(len(force_set[0])))

        if (len(force_set[0]) != num_first_disp + num_second_disp):
            print('data size of phono3py displacement and hdnnpy results does not match')

        counter = 0
        with open('FORCES_FC3', "w") as fs:

            # in phono3py, FC2 part first write down into FORCES_FC3 file
            # see phono3py def write_fc3_dat(force_constants_third, filename='fc3.dat'):
            # in  file_IO.py

            for i, disp1 in enumerate(datas['first_atoms']):
                fs.write("# File: %-5d\n" % (i + 1))
                fs.write("# %-5d " % (disp1['number']))
                fs.write("%20.16f %20.16f %20.16f\n" % tuple(disp1['displacement']))
                for f in force_set[0][counter]:
                    f = f.reshape(-1, 3)

                    for l in f:
                        # print(l)
                        fs.write("%15.10f %15.10f %15.10f\n" % (tuple(l)))

                counter = counter + 1

            # actual FC3 part
            for i, disp1 in enumerate(datas['first_atoms']):
                atom1 = disp1['number']
                for disp2 in disp1['second_atoms']:
                    atom2 = disp2['number']

                    # in disp_fc3.yaml file, the displacements of atom 2 stored as array
                    for each in disp2['displacements']:
                        fs.write("# File: %-5d\n" % (counter + 1))
                        fs.write("# %-5d " % (atom1))
                        fs.write("%20.16f %20.16f %20.16f\n" % tuple(disp1['displacement']))
                        fs.write("# %-5d " % (atom2))
                        fs.write("%20.16f %20.16f %20.16f\n" % tuple(each))

                        for f in force_set[0][counter]:
                            f = f.reshape(-1, 3)
                            for l in f:
                                # print(l)
                                fs.write("%15.10f %15.10f %15.10f\n" % (tuple(l)))

                        counter = counter + 1

        if(pc.dimfc2 is not None):
            shutil.copy(pc.fc2output + "/prediction_result.npz", "./prediction_result_fc2.npz")
            # creatiing FORCE_FC2
            with open('disp_fc2.yaml') as stream:
                datas = yaml.safe_load(stream)

            print("2nd order Force constant setup")
            natom = datas['natom']
            print("number of atoms")
            print(natom)

            num_first_disp = datas['num_first_displacements']
            print("first displacements")
            print(str(num_first_disp))

            first_atoms = datas['first_atoms']
            first_atom_number = []

            first_disp = []
            print("number of displacements for first atom")
            print(len(first_atoms))

            for i in first_atoms:
                first_atom_number.append(i['number'])
                first_disp.append(i['displacement'])
            force_set = []
            prdata = np.load('prediction_result_fc2.npz')
            keys = prdata.files
            print(keys)

            for ik in keys:
                if (ik.find('force') > 0):
                    print('tag to store:' + str(ik))
                    force_data = prdata[ik]
                    force_set.append(force_data)

            print("size of hdnnpy data:" + str(len(force_set[0])))

            if (len(force_set[0]) != num_first_disp):
                print('data size of phono3py displacement and hdnnpy results does not match in 2nd order part')
            counter = 0
            with open('FORCES_FC2', "w") as fs:

                for i, disp1 in enumerate(datas['first_atoms']):
                    fs.write("# File: %-5d\n" % (i + 1))
                    fs.write("# %-5d " % (disp1['number']))
                    fs.write("%20.16f %20.16f %20.16f\n" % tuple(disp1['displacement']))
                    for f in force_set[0][counter]:
                        f = f.reshape(-1, 3)

                        for l in f:
                            # print(l)
                            fs.write("%15.10f %15.10f %15.10f\n" % (tuple(l)))

                    counter = counter + 1

        #phono3py run
        #fc2.hdf, fc3.hdf
        strdim = "--dim= " + str(pc.dim[0]) + " " + str(pc.dim[1]) + " " \
                 + str(pc.dim[2])
        fc_command = ['phono3py', strdim, '-c', pc.poscar]
        if (pc.dimfc2 is not None):
            strdimfc2 = "--dim-fc2= " + str(pc.dimfc2[0]) + " " + str(pc.dimfc2[1]) + " " \
                        + str(pc.dimfc2[2])
            fc_command = ['phono3py', strdim, strdimfc2, '-c', pc.poscar]
        if(pc.symfc):
            fc_command.append('--sym-fc')

        print(fc_command)
        gd = subprocess.run(fc_command)

        # normal
        strmesh = "--mesh= " + str(pc.mesh[0]) + " " + str(pc.mesh[1]) + " " + str(pc.mesh[2])
        bte_command = ['phono3py', strdim, strmesh, '-c', pc.poscar, '--fc3', '--fc2', '--br']
        if (pc.dimfc2 is not None):
            bte_command = ['phono3py', strdim, strmesh,strdim,strdimfc2, '-c', pc.poscar, '--fc3', '--fc2', '--br']
        if(pc.symfc):
            bte_command.append('--sym-fc')
        if(pc.strpa is not None):
            str_pa= "--pa=" +pc.strpa

        print(bte_command)
        gd = subprocess.run(bte_command)

if __name__ == '__main__':
    interface=hdnnpy2phono3py()
    if(sys.argv[1]=='prep'):
        print('preperation run')
        interface.prep()
    elif(sys.argv[1]=='run'):
        print('phono3py run')
        interface.run()





