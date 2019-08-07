# !/usr/bin/env python
# coding=utf-8
"""
Spammer
Developer: Leon.Patmore
"""

from setuptools import setup
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file.
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(

    name='spammer',

    version='0.1.2',

    description='A package for helping with load testing.',

    long_description=long_description,

    long_description_content_type='text/markdown',

    author='Leon Patmore',

    author_email='leon.patmore@bath.edu',

    packages=["spammer"],

    package_dir={'spammer': 'spammer'},

    python_requires='>=3.0, <4',

)
