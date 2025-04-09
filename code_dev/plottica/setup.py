from setuptools import setup

VERSION = '0.0.1'
DESCRIPTION = 'See your live data with a plotter'
with open('README.md') as f:
    long_description = f.read()

# Setting up
setup(
    name="plottica",
    version=VERSION,
    author="intuition RT (SLB)",
    author_email="<contact@ilorobot.com>",
    url="https://ilorobot.com",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["plottica"],
    install_requires=[
        "numpy",
        "matplotlib",
        "websocket-client",
        "prettytable",
    ],
    keywords=['python'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: OS Independent",
        "Topic :: Education",
    ]
)

