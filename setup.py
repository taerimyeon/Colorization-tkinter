# -*- coding: utf-8 -*-
"""
Created on Sun Dec 22 22:42:22 2019

@author: Steven
"""


from distutils.core import setup, Extension
from Cython.Build import cythonize
#import numpy


setup(ext_modules = cythonize("colorizationCy.pyx"))
#setup(ext_modules = cythonize("colorizationFaster.pyx", annotate=True))  
#setup(
#    ext_modules=[
#        Extension("colorizationFaster.pyx", ["colorizationFaster.c"],
#                  include_dirs=[numpy.get_include()]),
#    ],
#)