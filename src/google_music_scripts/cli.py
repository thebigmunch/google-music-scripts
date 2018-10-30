"""Command line interface of google-music-scripts."""

import os
from collections import defaultdict

import click

from . import __title__, __version__
from .constants import UNIX_PATH_RE
from .utils import convert_cygwin_path

CMD_ALIASES = {
	'del': 'delete', 'down': 'download', 'up': 'upload'
}
PLUGIN_DIR = os.path.join(os.path.dirname(__file__), 'commands')


class AliasedGroup(click.Group):
	def get_command(self, ctx, alias):
		cmd = CMD_ALIASES.get(alias, alias)

		ns = {}
		filepath = os.path.join(os.path.join(PLUGIN_DIR, cmd + '.py'))
		with open(filepath) as f:
			code = compile(f.read(), filepath, 'exec')
			eval(code, ns, ns)

		return ns[cmd]

	def list_commands(self, ctx):
		rv = []
		for filename in os.listdir(PLUGIN_DIR):
			if filename.endswith('.py') and not filename == '__init__.py':
				rv.append(filename[:-3])

		rv.sort()

		return rv


# I use Windows Python install from Cygwin.
# This custom click type converts Unix-style paths to Windows-style paths in this case.
class CustomPath(click.Path):
	def convert(self, value, param, ctx):
		if os.name == 'nt' and UNIX_PATH_RE.match(value):
			value = convert_cygwin_path(value)

		return super().convert(value, param, ctx)


# Callback used to allow input/output arguments to default to current directory.
# Necessary because click does not support setting a default directly when using nargs=-1.
def default_to_cwd(ctx, param, value):
	if not value:
		value = (os.getcwd(),)

	return value


# Callback to split filter strings into dict containing field:value_list items.
def split_filter_strings(ctx, param, value):
	filters = defaultdict(list)

	for filt in value:
		field, val = filt.split(':', 1)
		filters[field].append(val)

	return filters


CONTEXT_SETTINGS = dict(max_content_width=200, help_option_names=['-h', '--help'])


@click.command(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
def gms():
	"""A collection of scripts to interact with Google Music."""

	pass
