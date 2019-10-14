import os
import shutil

import nox

ON_TRAVIS = 'TRAVIS' in os.environ

py36 = '3.6'
py37 = '3.7'
py38 = '3.8'

nox.options.reuse_existing_virtualenvs = True


@nox.session
def lint(session):
	session.install('-U', '.[lint]')
	session.run('flake8', 'src/')


@nox.session
def doc(session):
	shutil.rmtree('docs/_build', ignore_errors=True)
	session.install('-U', '.[doc]')
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
