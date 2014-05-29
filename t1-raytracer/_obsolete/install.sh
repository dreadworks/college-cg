#!/bin/bash

# where the virtual environment 
# gets installed
venv=.venv
venvexe=$(which virtualenv)

echo "Checking for virtualenv"
command -v virtualenv >/dev/null 2>&1 || {

	if test "$1" = "--no-root"; then
		cwd=$(pwd)
		binvenv=virtualenv-1.11.4

		mkdir lib; cd lib
		mkdir python2.7; cd python2.7
		mkdir site-packages; cd site-packages
		pth=$(pwd)

		echo "Configuring environment"
		PYTHONPATH="$pth:$PYTHONPATH"
		export PYTHONPATH
		cd "$cwd"/lib

		echo "Retrieving virtualenv"
		wget https://pypi.python.org/packages/source/v/virtualenv/$binvenv.tar.gz

		echo "Extracting"
		tar xvfz $binvenv.tar.gz
		cd $binvenv

		echo "Installing locally"
		python setup.py install --prefix="$cwd"
		cd "$cwd"

		echo "Installed virtualenv"
		venvexe=$(find $pth -name "virtualenv.py")
		chmod u+x $venvexe

		echo "Requesting header files from python3-dev for Pillow"
		mkdir tmp; cd tmp
		apt-get download libpython3.3-dev ||\
            apt-get download libpython3.2-dev ||\
			apt-get download libpython3-dev ||\
            apt-get download python3.2-dev

		ar x -v *.deb
		tar xvf data.tar.*

		if test ! -d usr/include; then
			echo >&2 "Was not able to retrieve python-dev header files"
			exit 2
		fi

		cd "$cwd"
	else
		echo "Checking for pip"
		command -v pip >/dev/null 2>&1 || {
			echo >&2 "Pip was not found. Exiting."
			exit 1
		}

		echo "Installing virtualenv (with root permissions)"
		sudo pip install virtualenv
		venv=$(which virtualenv)
	fi
}

command -v python3 >/dev/null 2>&1 || {
	echo "No python3 interpreter found. Exiting."
	exit 1
}

echo "Installing virtual environment with python 3 interpreter"
"$venvexe" -p python3 "$venv"

if test "$1" = "--no-root"; then
	echo "Moving header files to $venv"
	mv tmp/usr/include "$venv/"
	rm -r tmp
fi

echo "Activating virtual environment"
source "$venv"/bin/activate

echo "Installing Pillow for image rendering"
pip install Pillow

echo "Installing nose for unit testing"
pip install nose

echo "Running unit tests"
# simply invoking nosetests failed on
# some machines...
python $(which nosetests)

echo "Setting permissions"
chmod -x *.py
chmod u+x raytracer.py

echo "Done. Usage:"; echo
echo "source $venv/bin/activate"
echo "./raytracer.py worlds/task.json"
echo

