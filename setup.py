#!/usr/bin/env python

import imp
import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    sys.exit("Sorry, Python < 3.6 is not supported")

# read the contents of the README file
with open("README.rst", encoding="utf-8") as f:
    README = f.read()

VERSION = imp.load_source("", "channel_validation_framework/version.py").__version__

setup(
    name="channel-validation-framework",
    author="bbp-ou-hpc",
    author_email="bbp-ou-hpc@groupes.epfl.ch",
    version=VERSION,
    description="Neuron channel validation framework. Comparison of CoreNeuron+nmodl vs neuron+mod2c",
    long_description=README,
    long_description_content_type="text/x-rst",
    url="https://bbpteam.epfl.ch/documentation/projects/channel-validation-framework",
    project_urls={
        "Tracker": "https://bbpteam.epfl.ch/project/issues/projects/HPCTM/issues",
        "Source": "ssh://bbpcode.epfl.ch/sim/channel-validation-framework",
    },
    license="BBP-internal-confidential",
    install_requires=[],
    packages=find_packages(),
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    scripts=["bin/run_tests"],
)
