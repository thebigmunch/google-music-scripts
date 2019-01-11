"""Command line interface of google-music-scripts."""

import os
import re
from pathlib import Path

import click

from . import __title__, __version__
from .config import convert_default_keys, get_config
from .constants import UNIX_PATH_RE
from .utils import convert_cygwin_path

CMD_ALIASES = {
	'del': 'delete',
	'down': 'download',
	'up': 'upload'
}
CONTEXT_SETTINGS = dict(
	help_option_names=['-h', '--help'],
	max_content_width=200
)
FILTER_RE = re.compile(r'(([+-]+)?(.*?)\[(.*?)\])', re.I)
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

	def make_context(self, *args, **kwargs):
		ctx = super().make_context(
			*args,
			help_option_names=['-h', '--help'],
			max_content_width=200,
			**kwargs
		)

		username = ''
		for i, arg in enumerate(ctx.args):
			if arg in ('-u', '--username'):
				username = ctx.args[i + 1]
				break

		defaults = convert_default_keys(
			get_config(username=username).get('defaults', {})
		)

		if defaults:
			global_defaults = {
				k: v
				for k, v in defaults.items()
				if k not in self.list_commands(ctx)
			}

			default_map = {}
			for command in self.list_commands(ctx):
				if command == 'sync':
					default_map['sync'] = {**global_defaults}
					sync_defaults = {
						k: v
						for k, v in defaults.get('sync', {}).items()
						if k not in ['down', 'up']
					}
					default_map['sync'].update(sync_defaults)

					for subcommand in ['down', 'up']:
						default_map['sync'][subcommand] = {**global_defaults}
						default_map['sync'][subcommand].update(sync_defaults)
						default_map['sync'][subcommand].update(
							defaults.get('sync', {}).get(subcommand, {})
						)
				else:
					default_map[command] = {**global_defaults}
					default_map[command].update(
						defaults.get(command, {})
					)

					for alias, cmd in CMD_ALIASES.items():
						if command == cmd:
							default_map[alias] = {**default_map[command]}
							default_map[alias].update(
								defaults.get(alias, {})
							)

			ctx.default_map = default_map

		return ctx


# I use Windows Python install from Cygwin.
# This custom click type converts Unix-style paths to Windows-style paths in this case.
class CustomPath(click.Path):
	def convert(self, value, param, ctx):
		if os.name == 'nt' and UNIX_PATH_RE.match(value):
			value = convert_cygwin_path(value)

		value = Path(value)

		return super().convert(value, param, ctx)


# I use Windows Python install from Cygwin.
# This custom click type converts Unix-style paths to Windows-style paths in this case.
class TemplatePath(click.Path):
	def convert(self, value, param, ctx):
		if os.name == 'nt' and UNIX_PATH_RE.match(value):
			value = str(convert_cygwin_path(value))

		return super().convert(value, param, ctx)


# Callback used to allow input/output arguments to default to current directory.
# Necessary because click does not support setting a default directly when using nargs=-1.
def default_to_cwd(ctx, param, value):
	if not value:
		value = (Path.cwd(),)

	return value


def parse_filters(ctx, param, value):
	filters = []
	for filter_ in value:
		conditions = FILTER_RE.findall(filter_)
		if not conditions:
			raise ValueError(f"'{filter_}' is not a valid filter.")

		filters.append(conditions)

	return filters


def split_album_art_paths(ctx, param, value):
	paths = value
	if value:
		paths = []

		if not isinstance(value, list):
			value = value.split(',')

		for val in value:
			if os.name == 'nt' and UNIX_PATH_RE.match(val.strip()):
				paths.append(convert_cygwin_path(val.strip()))
			else:
				paths.append(Path(val))

	return paths


@click.group(cls=AliasedGroup)
@click.version_option(
	__version__,
	'-V', '--version',
	prog_name=__title__,
	message="%(prog)s %(version)s"
)
def gms():
	"""A collection of scripts to interact with Google Music."""

	pass
