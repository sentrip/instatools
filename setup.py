#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=6.7', 'requests>=2.18.4',
                'ratelimiter>=1.2.0', 'cached_property>=1.4.3',
                'pillow>=5.1.0']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Djordje Pepic",
    author_email='djordje.m.pepic@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="Simple automation of Instagram account control, maintenance and statistics",
    entry_points={
        'console_scripts': [
            'instatools=instatools.cli:main',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='instatools',
    name='instatools',
    packages=find_packages(include=['instatools', 'instatools.actions', 'instatools.instagram']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/sentrip/instatools',
    version='0.1.3',
    zip_safe=False,
)
