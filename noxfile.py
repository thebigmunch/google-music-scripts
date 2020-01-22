import shutil

import nox

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
