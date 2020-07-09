from ase.io import read,write
from ase import Atom

a=read('OUTCAR', format='vasp-out')
pos=a.get_positions()
force=a.get_forces()

natom=len(pos)
if(len(pos) != len(force)):
    print("something trouble")
with open("results.txt","w") as r:
    for i,p in enumerate(pos):
        r.write(str(p[0])+" "+str(p[1])+" "+str(p[2])+" "+str(force[i][0])+" "+ str(force[i][1])+" "+str(force[i][2])+"\n")