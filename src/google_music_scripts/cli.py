"""Command line interface of google-music-scripts."""

import os
import sys
from collections import defaultdict

import click
import google_music
from click_default_group import DefaultGroup
from logzero import logger

from . import __title__, __version__
from .commands import do_delete, do_download, do_search, do_sync_down, do_sync_up, do_upload
from .config import configure_logging
from .constants import UNIX_PATH_RE
from .utils import convert_cygwin_path

CMD_ALIASES = {
	'del': 'delete', 'down': 'download', 'up': 'upload'
}


class AliasedGroup(click.Group):
	def get_command(self, ctx, alias):
		cmd = CMD_ALIASES.get(alias, alias)
		if cmd is not None:
			return click.Group.get_command(self, ctx, cmd)

		return None


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


@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
def gms():
	"""A collection of scripts to interact with Google Music."""

	pass


@gms.group(cls=DefaultGroup, default='up', default_if_no_args=True, context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
def sync():
	"""Sync songs to/from a Google Music library."""

	pass


@sync.command('down')
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
@click.option('-l', '--log', is_flag=True, default=False, help="Log to file.")
@click.option('-v', '--verbose', count=True)
@click.option('-q', '--quiet', count=True)
@click.option('-n', '--dry-run', is_flag=True, default=False, help="Output list of songs that would be downloaded.")
@click.option(
	'-u', '--username', metavar='USERNAME', default='',
	help="Your Google username or e-mail address.\nUsed to separate saved credentials."
)
@click.option(
	'--uploader-id', metavar='ID',
	help="A unique id given as a MAC address (e.g. '00:11:22:33:AA:BB').\nThis should only be provided when the default does not work."
)
@click.option(
	'--no-recursion', is_flag=True, default=False,
	help="Disable recursion when scanning for local files.\nRecursion is enabled by default."
)
@click.option(
	'--max-depth', metavar='DEPTH', type=int,
	help="Set maximum depth of recursion when scanning for local files.\nDefault is infinite recursion."
)
@click.option(
	'-f', '--include-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-fa', '--all-includes', is_flag=True, default=False,
	help="Songs must match all include filter criteria to be included."
)
@click.option(
	'-F', '--exclude-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-Fa', '--all-excludes', is_flag=True, default=False,
	help="Songs must match all exclude filter criteria to be included."
)
@click.option(
	'-o', '--output', metavar='TEMPLATE_PATH', default=os.getcwd(), type=CustomPath(),
	help="Output file or directory name which can include template patterns."
)
@click.argument('include-paths', nargs=-1, type=CustomPath(resolve_path=True))
def sync_down(
	log, verbose, quiet, dry_run, username, uploader_id, no_recursion, max_depth,
	include_filter, all_includes, exclude_filter, all_excludes, output, include_paths):
	"""Sync songs from a Google Music library."""

	configure_logging(verbose - quiet, log_to_file=log)

	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(username, uploader_id=uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	if no_recursion:
		max_depth = 0
	elif max_depth is None:
		max_depth = float('inf')

	do_sync_down(
		mm, output, include_paths, dry_run=dry_run, max_depth=max_depth, include_filters=include_filter,
		all_includes=all_includes, exclude_filters=exclude_filter, all_excludes=all_excludes
	)


@sync.command('up')
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
@click.option('-l', '--log', is_flag=True, default=False, help="Log to file.")
@click.option('-v', '--verbose', count=True)
@click.option('-q', '--quiet', count=True)
@click.option('-n', '--dry-run', is_flag=True, default=False, help="Output list of songs that would be uploaded.")
@click.option(
	'-u', '--username', metavar='USERNAME', default='',
	help="Your Google username or e-mail address.\nUsed to separate saved credentials."
)
@click.option(
	'--uploader-id', metavar='ID',
	help="A unique id given as a MAC address (e.g. '00:11:22:33:AA:BB').\nThis should only be provided when the default does not work."
)
@click.option(
	'--no-recursion', is_flag=True, default=False,
	help="Disable recursion when scanning for local files.\nRecursion is enabled by default."
)
@click.option(
	'--max-depth', metavar='DEPTH', type=int,
	help="Set maximum depth of recursion when scanning for local files.\nDefault is infinite recursion."
)
@click.option(
	'-f', '--include-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-fa', '--all-includes', is_flag=True, default=False,
	help="Songs must match all include filter criteria to be included."
)
@click.option(
	'-F', '--exclude-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-Fa', '--all-excludes', is_flag=True, default=False,
	help="Songs must match all exclude filter criteria to be included."
)
@click.option('--delete-on-success', is_flag=True, default=False, help="Delete successfully uploaded local files.")
@click.option(
	'--transcode-lossless/--no-transcode-lossless', is_flag=True, default=True,
	help="Transcode lossless files to MP3 for upload."
)
@click.option(
	'--transcode-lossy/--no-transcode-lossy', is_flag=True, default=True,
	help="Transcode non-MP3 lossy files to MP3 for upload."
)
@click.argument('input-paths', nargs=-1, type=CustomPath(resolve_path=True), callback=default_to_cwd)
def sync_up(
	log, verbose, quiet, dry_run, username, uploader_id, no_recursion, max_depth, delete_on_success,
	transcode_lossless, transcode_lossy, include_filter, all_includes, exclude_filter, all_excludes, input_paths):
	"""Sync songs to a Google Music library."""

	configure_logging(verbose - quiet, log_to_file=log)

	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(username, uploader_id=uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	if no_recursion:
		max_depth = 0
	elif max_depth is None:
		max_depth = float('inf')

	do_sync_up(
		mm, input_paths, dry_run=dry_run, delete_on_success=delete_on_success, max_depth=max_depth,
		include_filters=include_filter, all_includes=all_includes,
		exclude_filters=exclude_filter, all_excludes=all_excludes,
		transcode_lossless=transcode_lossless, transcode_lossy=transcode_lossy
	)


@gms.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
@click.option('-l', '--log', is_flag=True, default=False, help="Log to file.")
@click.option('-v', '--verbose', count=True)
@click.option('-q', '--quiet', count=True)
@click.option('-n', '--dry-run', is_flag=True, default=False, help="Output list of songs that would be deleted.")
@click.option(
	'-u', '--username', metavar='USERNAME', default='',
	help="Your Google username or e-mail address.\nUsed to separate saved credentials."
)
@click.option('--device-id', metavar='ID', help="A mobile device id.")
@click.option(
	'-f', '--include-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-fa', '--all-includes', is_flag=True, default=False,
	help="Songs must match all include filter criteria to be included."
)
@click.option(
	'-F', '--exclude-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-Fa', '--all-excludes', is_flag=True, default=False,
	help="Songs must match all exclude filter criteria to be included."
)
@click.option('-y', '--yes', is_flag=True, default=False, help="Delete songs without asking for confirmation.")
def delete(
	log, verbose, quiet, dry_run, username, device_id, include_filter, all_includes, exclude_filter, all_excludes, yes):
	"""Delete songs from a Google Music library."""

	configure_logging(verbose - quiet, log_to_file=log)

	logger.info("Logging in to Google Music")
	mc = google_music.mobileclient(username, device_id=device_id)

	if not mc.is_authenticated:
		sys.exit("Failed to authenticate client.")

	do_delete(
		mc, dry_run=dry_run, include_filters=include_filter, all_includes=all_includes,
		exclude_filters=exclude_filter, all_excludes=all_excludes, yes=yes
	)


@gms.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
@click.option('-l', '--log', is_flag=True, default=False, help="Log to file.")
@click.option('-v', '--verbose', count=True)
@click.option('-q', '--quiet', count=True)
@click.option('-n', '--dry-run', is_flag=True, default=False, help="Output list of songs that would be downloaded.")
@click.option(
	'-u', '--username', metavar='USERNAME', default='',
	help="Your Google username or e-mail address.\nUsed to separate saved credentials."
)
@click.option(
	'--uploader-id', metavar='ID',
	help="A unique id given as a MAC address (e.g. '00:11:22:33:AA:BB').\nThis should only be provided when the default does not work."
)
@click.option(
	'-f', '--include-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-fa', '--all-includes', is_flag=True, default=False,
	help="Songs must match all include filter criteria to be included."
)
@click.option(
	'-F', '--exclude-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-Fa', '--all-excludes', is_flag=True, default=False,
	help="Songs must match all exclude filter criteria to be included."
)
@click.option(
	'-o', '--output', metavar='TEMPLATE_PATH', default=os.getcwd(), type=CustomPath(),
	help="Output file or directory name which can include template patterns."
)
def download(
	log, verbose, quiet, dry_run, username, uploader_id,
	include_filter, all_includes, exclude_filter, all_excludes, output):
	"""Download songs from a Google Music library."""

	configure_logging(verbose - quiet, log_to_file=log)

	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(username, uploader_id=uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	do_download(
		mm, output, dry_run=dry_run, include_filters=include_filter,
		all_includes=all_includes, exclude_filters=exclude_filter, all_excludes=all_excludes
	)


@gms.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
@click.option('-l', '--log', is_flag=True, default=False, help="Log to file.")
@click.option(
	'-u', '--username', metavar='USERNAME', default='',
	help="Your Google username or e-mail address.\nUsed to separate saved credentials."
)
@click.option(
	'--uploader-id', metavar='ID',
	help="A unique id given as a MAC address (e.g. '00:11:22:33:AA:BB').\nThis should only be provided when the default does not work."
)
def quota(
	log, username, uploader_id):
	""""Get the uploaded track count and allowance."""

	configure_logging(0, log_to_file=log)

	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(username, uploader_id=uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	uploaded, allowed = mm.quota()

	logger.info(f"Quota -- {uploaded}/{allowed} ({uploaded / allowed:.2%})")


@gms.command(context_settings=CONTEXT_SETTINGS)
@click.help_option('-h', '--help')
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
@click.option('-l', '--log', is_flag=True, default=False, help="Log to file.")
@click.option('-v', '--verbose', count=True)
@click.option('-q', '--quiet', count=True)
@click.option(
	'-u', '--username', metavar='USERNAME', default='',
	help="Your Google username or e-mail address.\nUsed to separate saved credentials."
)
@click.option('--device-id', metavar='ID', help="A mobile device id.")
@click.option(
	'-f', '--include-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-fa', '--all-includes', is_flag=True, default=False,
	help="Songs must match all include filter criteria to be included."
)
@click.option(
	'-F', '--exclude-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-Fa', '--all-excludes', is_flag=True, default=False,
	help="Songs must match all exclude filter criteria to be included."
)
@click.option('-y', '--yes', is_flag=True, default=False, help="Display results without asking for confirmation.")
def search(
	log, verbose, quiet, username, device_id, include_filter, all_includes, exclude_filter, all_excludes, yes):
	"""Search a Google Music library for songs."""

	configure_logging(verbose - quiet, log_to_file=log)

	logger.info("Logging in to Google Music")
	mc = google_music.mobileclient(username, device_id=device_id)

	if not mc.is_authenticated:
		sys.exit("Failed to authenticate client.")

	do_search(
		mc, include_filters=include_filter, all_includes=all_includes,
		exclude_filters=exclude_filter, all_excludes=all_excludes, yes=yes
	)


@gms.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-V', '--version', prog_name=__title__, message="%(prog)s %(version)s")
@click.option('-l', '--log', is_flag=True, default=False, help="Log to file.")
@click.option('-v', '--verbose', count=True)
@click.option('-q', '--quiet', count=True)
@click.option('-n', '--dry-run', is_flag=True, default=False, help="Output list of songs that would be uploaded.")
@click.option(
	'-u', '--username', metavar='USERNAME', default='',
	help="Your Google username or e-mail address.\nUsed to separate saved credentials."
)
@click.option(
	'--uploader-id', metavar='ID',
	help="A unique id given as a MAC address (e.g. '00:11:22:33:AA:BB').\nThis should only be provided when the default does not work."
)
@click.option(
	'--no-recursion', is_flag=True, default=False,
	help="Disable recursion when scanning for local files.\nRecursion is enabled by default."
)
@click.option(
	'--max-depth', metavar='DEPTH', type=int,
	help="Set maximum depth of recursion when scanning for local files.\nDefault is infinite recursion."
)
@click.option(
	'-f', '--include-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-fa', '--all-includes', is_flag=True, default=False,
	help="Songs must match all include filter criteria to be included."
)
@click.option(
	'-F', '--exclude-filter', metavar='FILTER', multiple=True, callback=split_filter_strings,
	help="Metadata filters to match Google songs.\nSongs can match any filter criteria."
)
@click.option(
	'-Fa', '--all-excludes', is_flag=True, default=False,
	help="Songs must match all exclude filter criteria to be included."
)
@click.option('--delete-on-success', is_flag=True, default=False, help="Delete successfully uploaded local files.")
@click.option(
	'--transcode-lossless/--no-transcode-lossless', is_flag=True, default=True,
	help="Transcode lossless files to MP3 for upload."
)
@click.option(
	'--transcode-lossy/--no-transcode-lossy', is_flag=True, default=True,
	help="Transcode non-MP3 lossy files to MP3 for upload."
)
@click.argument('input-paths', nargs=-1, type=CustomPath(resolve_path=True), callback=default_to_cwd)
def upload(
	log, verbose, quiet, dry_run, username, uploader_id, no_recursion, max_depth, delete_on_success,
	transcode_lossless, transcode_lossy, include_filter, all_includes, exclude_filter, all_excludes, input_paths):
	"""Upload songs to a Google Music library."""

	configure_logging(verbose - quiet, log_to_file=log)

	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(username, uploader_id=uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	if no_recursion:
		max_depth = 0
	elif max_depth is None:
		max_depth = float('inf')

	do_upload(
		mm, input_paths, dry_run=dry_run, delete_on_success=delete_on_success, max_depth=max_depth,
		include_filters=include_filter, all_includes=all_includes,
		exclude_filters=exclude_filter, all_excludes=all_excludes,
		transcode_lossless=transcode_lossless, transcode_lossy=transcode_lossy
	)
