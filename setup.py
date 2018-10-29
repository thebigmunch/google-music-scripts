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
		'audio-metadata>=0.1',
		'click>=6.0',
		'click-default-group>=1.2',
		'google-music>=1.0',
		'google-music-utils>=1.1',
		'logzero>=1.5',
		'sphinx-click>=1.0'
	],

	packages=find_packages('src'),
	package_dir={
		'': 'src'
	},

	entry_points={
		'console_scripts': [
			'gms = google_music_scripts.cli:gms',
			'gmdelete = google_music_scripts.cli:delete',
			'gmdownload = google_music_scripts.cli:download',
			'gmquota = google_music_scripts.cli:quota',
			'gmsearch = google_music_scripts.cli:search',
			'gmsync = google_music_scripts.cli:sync',
			'gmupload = google_music_scripts.cli:upload'
		]
	}
)
