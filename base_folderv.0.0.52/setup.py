from setuptools import setup

VERSION = '0.0.52'
DESCRIPTION = 'Control ilo robot using python command.'
with open('README.md') as f:
    long_description = f.read()

# Setting up
setup(
    name="ilo",
    version=VERSION,
    author="intuition RT (SLB)",
    author_email="<contact@ilorobot.com>",
    url="https://ilorobot.com",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["ilo"],
    package_dir={'':'libname'},
    install_requires=[
        "pyperclip",
        "pyserial",
        "websocket-client",
        "nest_asyncio",
        "bleak",
        "prettytable",
        "keyboard_crossplatform",
        "requests",
        "psutil"
    ],
    keywords=['python', 'education'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: OS Independent",
        "Topic :: Education",
    ]
)

