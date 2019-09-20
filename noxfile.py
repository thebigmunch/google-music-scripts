import os
import shutil

import nox

py36 = '3.6'
py37 = '3.7'
py38 = '3.8'

ON_TRAVIS = 'TRAVIS' in os.environ


@nox.session(reuse_venv=True)
def lint(session):
	session.install('.[lint]')
	session.run('flake8', 'src/')


@nox.session(reuse_venv=True)
def doc(session):
	shutil.rmtree('docs/_build', ignore_errors=True)
	session.install('.[doc]')
	session.cd('docs')
	session.run(
		'sphinx-build',
		'-b',
		'html',
		'-W',
		'-d',
		'_build/doctrees',
		'.',
		'_build/html'
	)
