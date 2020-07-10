# About this script
`hdnnpy2phono3py.py` is script to interfacing phono3py and hdnnpy 
(high-dimensional neural network potential code, see 
https://github.com/masayoshi-ogura/HDNNP (archived) or
https://github.com/eminamitani/hdnnpy-update (mostly same as the above but including minor update))

## Usage
For prepare the input files to predict the force by hdnnpy
```buildoutcfg
python hdnnpy2phono3py.py prep
```
In this preperation process, the job-script `predictionRun.sh` for hdnnpy calculation 
is generated based on the information written in config file. 
Then, submit hdnnpy job using jobscheduler.
For example
```buildoutcfg
qsub predictionRun.sh
```

After that, run phono3py calculation by
```buildoutcfg
python hdnnpy2phono3py.py run
```

In this script, two situations are considered.
1. 2nd and 3rd order force constant is evaluated in the same size of supercell.
2. different supercell size is used for 2nd and 3rd order force constant

These  two cases can be specified by setting `--dimfc2` in the config file as shown in below.
- config file   
The name of config file for `prep` and `run` is 
`phono3py_config.yaml`.
The meaning of the tags in config file is
```buildoutcfg
dim: [2,2,2] #supercell size for phono3py calculation
symfc: True  #use Acoustic sum rule or not
prefix: crystal #prefix used in hdnnpy calculation
poscar: POSCAR #file name of POSCAR used in phono3py
dimfc2: [3,3,3] #if different supercell size for 2nd order FC case
mesh: [11,11,11] #mesh in phono3py-BTE calculation
pipfile: /Users/emi/PycharmProjects/hdnnpy+phono3py/Pipfile
#path for Pipfile of virtualenv to use hdnnpy and phono3py
nnpoutput: ../output # the path for the directory contain master_nnp.npz (hdnnpy output)
fc3output: ../fc3-output # the path for working directory for 3rd order FC calculation
fc2output: ../fc2-output # the path for working directory for 2nd order FC calculation
mpicommand: mpirun -np 24 #command fo mpi
strpa: [0,1/2,1/2,1/2,0,1/2,1/2,1/2,0] #translation matrix to conventional to primitive cell, optional. used in phono3py
#the header part of job script in your system
jobscriptheader: |
  #!/bin/csh
  #$ -cwd
  #$ -V -S /bin/bash
  #$ -N prediction
  #$ -o stdout
  #$ -e stderr
  #$ -q all.q
  #$ -pe smp 24
  export OMP_NUM_THREADS=1
  root=$PWD
  MPIROOT=/usr/local/openmpi-1.8.8/
  export PATH=$MPIROOT/bin:$PATH
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MPIROOT/lib
  export MANPATH=$MANPATH:$MPIROOT/share/man
```
If `dimfc2` is not empty, the calculation for 2nd order FC is prepared.


## Environment setup

### hdnnpy+phonopy+phono3py using pyenv+pipenv

#### Optional: install pyenv

in mac OS + zsh
```buildoutcfg
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
```
In my case, install 3.7.6 by
`pyenv install 3.7.6`

#### install pipenv by `pip install pipenv`


#### clone hdnnpy with minor update 

Minor update for newer version of several python package is inplemented in initialize branch.
This, after clone, checkout to that branch is recommended.
```buildoutcfg
git clone git@github.com:eminamitani/hdnnpy-update.git
git fetch
git checkout -b initialize origin/initialize
```

This package include Pipfile.
(The Pipfile.lock is also included, but some of library is old.
This, it may be better to remove Pipfile.lock.)
```buildoutcfg
pipenv --python 3.7
pipenv install --dev
```

#### Add phono3py to pipenv virtual environment

Activate virtual environment by pipenv
```buildoutcfg
pipenv shell
```
Then, install phonopy 
```buildoutcfg
pip install phonopy
```
Clone phono3py source package. The development branch version requires phonopy version >2.7.
But pip install phonopy install the stable version of 2.6.
Thus, here I checkout to the master branch after clone.
```buildoutcfg
git clone https://github.com/phonopy/phono3py.git
git fetch
git checkout -b master origin/master
```

new version of gcc is installed by Macport
```bash
sudo port install gcc6
sudo port select --set gcc mp-gcc6
sudo port install OpenBLAS +gcc6
```
Then, make a minor change in `setup.py` if necessary.
In gcc on Mac installed by Macport, 
I encounter compile error caused by openmp related option.
So, I removed before compile
```buildoutcfg
extra_compile_args = [ ]
```
```
if cc == 'gcc' or cc is None:
    lib_omp = ''
```

```buildoutcfg
python setup.py build
pip install -e .
```

In Linux, it is better to make `setup_mkl.py` 
and use intel MKL to avoid compile error.
