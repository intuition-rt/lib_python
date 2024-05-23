from setuptools import setup

VERSION = '0.0.24'
DESCRIPTION = 'Control ilo robot using python command.'
with open('README.md') as f:
    long_description = f.read()

# Setting up
setup(
    name="ilo",
    version=VERSION,
    author="intuition RT (SLB)",
    author_email="<contact@ilorobot.com>",
    url="https://github.com/ilorobot/python-library",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["ilo"],
    package_dir={'':'libname'},
    install_requires=[
        "keyboard",
    ],
    keywords=['python'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)

