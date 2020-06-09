## environment setup

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
