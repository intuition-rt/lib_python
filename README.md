# lib-python

# structure of the folder

base-folder	setup.py
base-folder/libname/__init__.py  and ilo.py
	


# install
pip3 install wheel
pip3 install setuptools
pip3 install twine

# run as command line from your folder

python setup.py bdist_wheel   #to create every necessary file
python setup.py bdist_wheel sdist
twine upload dist/*           #give you pip account info


# interresting link
https://www.youtube.com/watch?v=tEFkHEKypLI