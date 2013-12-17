# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys

import dingos

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = dingos.__version__

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='django-dingos',
    version=version,
    description='A Django app that provides a generic framework for managing structured information in a generic way.',
    long_description=readme + '\n\n' + history,
    author='Siemens',
    author_email='mantis.cert@siemens.com',
    url='https://github.com/bgro/django-dingos',
    packages=[
        'dingos',
    ],
    include_package_data=True,
    install_requires=['libxml2-python>=2.6.21',
                      'django>=1.5.5',
                      'django-grappelli>=2.4.7',
                      'django-braces>=1.0.0',
                      'lxml>=3.2.1',
                      'django-filter>=0.7',
                      'python-dateutil>=2.2'
    ],
    license="GPLv2+",
    zip_safe=False,
    keywords='django-dingos',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Topic :: Security'
    ],
    test_suite = 'runtests.run_tests'
)
