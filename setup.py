#!/usr/bin/env python3

import os

from setuptools import find_packages, setup

base_dir = os.path.dirname(__file__)

about = {}
with open(os.path.join(base_dir, 'src', 'google_music_scripts', '__about__.py')) as f:
	exec(f.read(), about)

setup(
	name=about['__title__'],
	version=about['__version__'],
	description=about['__summary__'],
	url=about['__url__'],
	license=about['__license__'],
	author=about['__author__'],
	author_email=about['__author_email__'],

	keywords=[],
	classifiers=[
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
	],

	install_requires=[
		'appdirs>=1.4',
		'audio-metadata>=0.4',
		'google-music>=3.0',
		'google-music-utils>=2.1',
		'logzero>=1.5',
		'natsort>=5.2',
		'tomlkit>=0.5'
	],

	extras_require={
		'doc': [
			'sphinx',
			'sphinx-argparse'
		],
		'lint': [
			'flake8',
			'flake8-builtins',
			'flake8-import-order',
			'flake8-import-order-tbm'
		],
	},

	packages=find_packages('src'),
	package_dir={
		'': 'src'
	},

	entry_points={
		'console_scripts': [
			'gms = google_music_scripts.cli:run'
		]
	}
)
