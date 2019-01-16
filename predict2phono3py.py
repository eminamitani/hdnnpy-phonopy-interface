'''
simple script to create FORCES_FC3 for phono3py

Emi Minamitani

step1: creating POSCAR-XXX file from phono3py by
"phono3py -d --dim="2 2 2" -c POSCAR-unitcell

step2: predict forces in each displacement by hdnnpy
       To create xyz file, you cau use phono3py2xyz script

step3: using this script to make FORCES_FC3

step4: evaluate thermal conductivity by phono3py
"phono3py --dim="2 2 2" --mesh="2 2 2" --sym-fc -c POSCAR-unitcell

phono3py --dim="2 2 2" ( if not based on primitive cell, fix axis as --pa="0 1/2 1/2 1/2 0 1/2 1/2 1/2 0") 
-c POSCAR-unitcell --mesh="11 11 11" --fc3 --fc2 --br"

'''

import yaml
import numpy as np
'''
read displacement informations from disp.yaml
'''
with open('disp_fc3.yaml') as stream:
    datas=yaml.safe_load(stream)

natom=datas['natom']

print("number of atoms")
print(natom)

num_first_disp=datas['num_first_displacements']
num_second_disp=datas['num_second_displacements']

print("first and second displacements")
print(str(num_first_disp)+","+str(num_second_disp))

first_atoms=datas['first_atoms']
first_atom_number=[]

first_disp=[]
second_disp=[]
second_atom_number=[]
print("number of displacements for first atom")
print(len(first_atoms))

for i in first_atoms:
    second_atom=i['second_atoms']
    first_atom_number.append(i['number'])
    first_disp.append(i['displacement'])
    
    for s in second_atom:
        second_atom_number.append(s['number'])
        second_disp.append(s['displacements'])

#print(second_atom_number)
#print(second_disp)

'''
parse prediction results from hdnnpy
default output npz name: prediction_result.npz
here I assume prediction_result.npz contain 
energy and force data for all displacement required by phonopy
with the same ordering in disp.yaml
'''

force_set=[]
prdata=np.load('prediction_result.npz')
keys=prdata.files
print(keys)

#all force data have same key in default hdnnpy setting.
#thus the actual data number is counted by len(force_set[0])

for ik in keys:
    if(ik.find('force') >0):
        print('tag to store:'+str(ik))
        force_data=prdata[ik]
        force_set.append(force_data)

print("size of hdnnpy data:"+str(len(force_set[0])))

if(len(force_set[0])!=num_first_disp+num_second_disp):
    print('data size of phono3py displacement and hdnnpy results does not match')

counter=0
with open('FORCES_FC3', "w") as fs:
    
    #in phono3py, FC2 part first write down into FORCES_FC3 file
    # see phono3py def write_fc3_dat(force_constants_third, filename='fc3.dat'):
    # in  file_IO.py
    
    for i, disp1 in enumerate(datas['first_atoms']):
        fs.write("# File: %-5d\n" % (i + 1))
        fs.write("# %-5d " % (disp1['number']))
        fs.write("%20.16f %20.16f %20.16f\n" % tuple(disp1['displacement']))
        for f in force_set[0][counter]:
            f = f.reshape(-1, 3)
            
            for l in f:
                #print(l)
                fs.write("%15.10f %15.10f %15.10f\n" % (tuple(l)))
                
        counter=counter+1
    
    #actual FC3 part
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
                        #print(l)
                        fs.write("%15.10f %15.10f %15.10f\n" % (tuple(l)))
            
                counter=counter+1
    
