#!/usr/bin/env python

import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    sys.exit("Sorry, Python < 3.6 is not supported")

# read the contents of the README file
with open("README.md", encoding="utf-8") as f:
    README = f.read()

setup(
    name="channel-validation-framework",
    author="bbp-ou-hpc",
    author_email="bbp-ou-hpc@groupes.epfl.ch",
    description="Neuron channel validation framework. Comparison of CoreNeuron+nmodl vs neuron+mod2c",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://bbpteam.epfl.ch/documentation/projects/channel-validation-framework",
    project_urls={
        "Tracker": "https://bbpteam.epfl.ch/project/issues/projects/HPCTM/issues",
        "Source": "ssh://bbpcode.epfl.ch/sim/channel-validation-framework",
    },
    license="BBP-internal-confidential",
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
    extras_require=dict(plotting=["matplotlib"], full=["matplotlib"],),
    install_requires=["recordtype", "termcolor"],
    entry_points=dict(
        console_scripts=["cvf_run_and_compare_tests=channel_validation_framework.commands:cvf_run_and_compare_tests",]
    ),
)
