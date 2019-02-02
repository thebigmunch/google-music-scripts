import argparse
import math
import os
import re
from pathlib import Path

from .__about__ import __title__, __version__
from .commands import (
	do_delete,
	do_download,
	do_quota,
	do_search,
	do_upload
)
from .config import configure_logging, get_defaults
from .constants import UNIX_PATH_RE
from .utils import DictMixin, convert_cygwin_path

FILTER_RE = re.compile(r'(([+-]+)?(.*?)\[(.*?)\])', re.I)

DISPATCH = {
	'del': do_delete,
	'delete': do_delete,
	'down': do_download,
	'download': do_download,
	'quota': do_quota,
	'search': do_search,
	'up': do_upload,
	'upload': do_upload
}


class Namespace(DictMixin):
	pass


class UsageHelpFormatter(argparse.RawTextHelpFormatter):
	def add_usage(self, usage, actions, groups, prefix="Usage: "):
		super().add_usage(usage, actions, groups, prefix)


# Removes the command list while leaving the usage metavar intact.
class SubcommandHelpFormatter(UsageHelpFormatter):
	def _format_action(self, action):
		parts = super()._format_action(action)
		if action.nargs == argparse.PARSER:
			parts = "\n".join(parts.split("\n")[1:])
		return parts


#########
# Utils #
#########

# I use Windows Python install from Cygwin.
# This custom click type converts Unix-style paths to Windows-style paths in this case.
def custom_path(value):
	if os.name == 'nt' and UNIX_PATH_RE.match(str(value)):
		value = Path(convert_cygwin_path(str(value)))

	value = Path(value)

	return value


def default_to_cwd():
	return Path.cwd()


def parse_filter(value):
	conditions = FILTER_RE.findall(value)
	if not conditions:
		raise ValueError(f"'{value}' is not a valid filter.")

	filter_ = [
		tuple(condition[1:])
		for condition in conditions
	]

	return filter_


def split_album_art_paths(value):
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


########
# Meta #
########

meta = argparse.ArgumentParser(
	add_help=False
)

meta_options = meta.add_argument_group("Options")
meta_options.add_argument(
	'-h', '--help',
	action='help'
)
meta_options.add_argument(
	'-V', '--version',
	action='version',
	version=f"{__title__} {__version__}",
	help=""
)


###########
# Logging #
###########

logging_ = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

logging_options = logging_.add_argument_group("Logging")
logging_options.add_argument(
	'-l', '--log',
	action='store_true',
	help="Log to file."
)
logging_options.add_argument(
	'-v', '--verbose',
	action='count',
	help="Increase verbosity of output."
)
logging_options.add_argument(
	'-q', '--quiet',
	action='count',
	help="Decrease verbosity of output."
)
logging_options.add_argument(
	'-n', '--dry-run',
	action='store_true',
	help="Output list of songs that would be uploaded."
)


##################
# Identification #
##################

ident = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

ident_options = ident.add_argument_group("Identification")
ident_options.add_argument(
	'-u', '--username',
	metavar='USER',
	help="Your Google username or e-mail address.\nUsed to separate saved credentials."
)


##########
# Mobile #
##########

mc_ident = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

mc_ident_options = mc_ident.add_argument_group("Identification")
mc_ident_options.add_argument(
	'--device-id',
	metavar='ID',
	help="A mobile device id."
)


#################
# Music Manager #
#################

mm_ident = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

mm_ident_options = mm_ident.add_argument_group("Identification")
mm_ident_options.add_argument(
	'--uploader-id',
	metavar='ID',
	help="A unique id given as a MAC address (e.g. '00:11:22:33:AA:BB').\nThis should only be provided when the default does not work."
)


#########
# Local #
#########

local = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

local_options = local.add_argument_group("Local")
local_options.add_argument(
	'--no-recursion',
	action='store_true',
	help="Disable recursion when scanning for local files.\nRecursion is enabled by default."
)
local_options.add_argument(
	'--max-depth',
	metavar='DEPTH',
	type=int,
	help="Set maximum depth of recursion when scanning for local files.\nDefault is infinite recursion."
)
local_options.add_argument(
	'-xp', '--exclude-path',
	metavar='PATH',
	action='append',
	dest='exclude_paths',
	help="Exclude filepaths.\nCan be specified multiple times."
)
local_options.add_argument(
	'-xr', '--exclude-regex',
	metavar='RX',
	action='append',
	dest='exclude_regexes',
	help="Exclude filepaths using regular expressions.\nCan be specified multiple times."
)
local_options.add_argument(
	'-xg', '--exclude-glob',
	metavar='GP',
	action='append',
	dest='exclude_globs',
	help="Exclude filepaths using glob patterns.\nCan be specified multiple times.\nAbsolute glob patterns not supported."
)


##########
# Filter #
##########

filter_ = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

filter_options = filter_.add_argument_group("Filter")
filter_options.add_argument(
	'-f', '--filter',
	metavar='FILTER',
	action='append',
	dest='filters',
	type=parse_filter,
	help="Metadata filters.\nCan be specified multiple times."
)


#######
# Yes #
#######

yes = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

yes_options = yes.add_argument_group("Misc")
yes_options.add_argument(
	'-y', '--yes',
	action='store_true',
	help="Don't ask for confirmation."
)


###############
# Upload Misc #
###############


upload_misc = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

upload_misc_options = upload_misc.add_argument_group("Misc")
upload_misc_options.add_argument(
	'--delete-on-success',
	action='store_true',
	help="Delete successfully uploaded local files."
)
upload_misc_options.add_argument(
	'--no-sample',
	action='store_true',
	help="Don't create audio sample with ffmpeg/avconv.\nSend empty audio sample."
)
upload_misc_options.add_argument(
	'--album-art',
	metavar='ART_PATHS',
	type=split_album_art_paths,
	help="Comma-separated list of album art filepaths.\nCan be relative filenames and/or absolute filepaths."
)


########
# Sync #
########


sync = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

sync_options = sync.add_argument_group("Sync")
sync_options.add_argument(
	'--use-hash',
	action='store_true',
	help="Use audio hash to sync songs."
)
sync_options.add_argument(
	'--no-use-hash',
	action='store_true',
	help="Don't use audio hash to sync songs."
)
sync_options.add_argument(
	'--use-metadata',
	action='store_true',
	help="Use metadata to sync songs."
)
sync_options.add_argument(
	'--no-use-metadata',
	action='store_true',
	help="Don't use metadata to sync songs."
)


##########
# Output #
##########

output = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

output_options = output.add_argument_group("Output")
output_options.add_argument(
	'-o', '--output',
	metavar='TEMPLATE_PATH',
	type=lambda t: str(custom_path(t)),
	help="Output file or directory name which can include template patterns."
)


###########
# Include #
###########

include = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

include_options = include.add_argument_group("Include")
include_options.add_argument(
	'include',
	metavar='PATH',
	type=lambda p: custom_path(p).resolve(),
	nargs='*',
	help="Local paths to include songs from."
)


#######
# gms #
#######

gms = argparse.ArgumentParser(
	prog='gms',
	description="A collection of scripts to interact with Google Music.",
	usage=argparse.SUPPRESS,
	parents=[meta],
	formatter_class=SubcommandHelpFormatter,
	add_help=False
)

subcommands = gms.add_subparsers(
	title="Commands",
	dest='_command',
	metavar="<command>"
)


##########
# Delete #
##########

delete_command = subcommands.add_parser(
	'delete',
	aliases=['del'],
	description="Delete song(s) from Google Music.",
	help="Delete song(s) from Google Music.",
	formatter_class=UsageHelpFormatter,
	usage="gms delete [OPTIONS]",
	parents=[
		meta,
		logging_,
		ident,
		mc_ident,
		filter_,
		yes
	],
	add_help=False
)


############
# Download #
############

download_command = subcommands.add_parser(
	'download',
	aliases=['down'],
	description="Download song(s) from Google Music.",
	help="Download song(s) from Google Music.",
	formatter_class=UsageHelpFormatter,
	usage="gms download [OPTIONS]",
	parents=[
		meta,
		logging_,
		ident,
		mm_ident,
		mc_ident,
		local,
		filter_,
		sync,
		output,
		include
	],
	add_help=False
)


#########
# Quota #
#########

quota_command = subcommands.add_parser(
	'quota',
	description="Get the uploaded song count and allowance.",
	help="Get the uploaded song count and allowance.",
	formatter_class=UsageHelpFormatter,
	usage="gms quota [OPTIONS]",
	parents=[
		meta,
		logging_,
		ident,
		mm_ident
	],
	add_help=False
)


##########
# Search #
##########

search_command = subcommands.add_parser(
	'search',
	description="Search a Google Music library for songs.",
	help="Search for Google Music library songs.",
	formatter_class=UsageHelpFormatter,
	usage="gms search [OPTIONS]",
	parents=[
		meta,
		logging_,
		mc_ident,
		filter_,
		yes
	],
	add_help=False
)


##########
# Upload #
##########

upload_command = subcommands.add_parser(
	'upload',
	aliases=['up'],
	description="Upload song(s) to Google Music.",
	help="Upload song(s) to Google Music.",
	formatter_class=UsageHelpFormatter,
	usage="gms upload [OPTIONS] [INCLUDE_PATH]...",
	parents=[
		meta,
		logging_,
		ident,
		mm_ident,
		mc_ident,
		local,
		filter_,
		upload_misc,
		sync,
		include
	],
	add_help=False
)


def set_defaults(args):
	defaults = Namespace()

	# Set defaults.
	defaults.verbose = 0
	defaults.quiet = 0
	defaults.log = False
	defaults.dry_run = False
	defaults.username = ''
	defaults.filters = []

	if args._command in ['down', 'download', 'up', 'upload']:
		defaults.uploader_id = None
		defaults.device_id = None

		defaults.no_recursion = False
		defaults.max_depth = math.inf
		defaults.exclude_paths = []
		defaults.exclude_regexes = []
		defaults.exclude_globs = []
		defaults.include = [custom_path('.').resolve()]

		if 'no_use_hash' in args:
			defaults.use_hash = False
			defaults.no_use_hash = True
		else:
			defaults.use_hash = True
			defaults.no_use_hash = False

		if 'no_use_metadata' in args:
			defaults.use_metadata = False
			defaults.no_use_metadata = True
		else:
			defaults.use_metadata = True
			defaults.no_use_metadata = False
	elif args._command in ['quota']:
		defaults.uploader_id = None
	else:
		defaults.device_id = None

	if args._command in ['del', 'delete', 'search']:
		defaults.yes = False

	if args._command in ['down', 'download']:
		defaults.output = str(Path('.').resolve())
		defaults.include = [custom_path('.').resolve()]

	if args._command in ['up', 'upload']:
		defaults.delete_on_success = False
		defaults.no_sample = False
		defaults.album_art = None

	config_defaults = get_defaults(args._command, username=args.get('username'))
	for k, v in config_defaults.items():
		if k == 'album_art':
			defaults.album_art = split_album_art_paths(v)
		elif k == 'filters':
			defaults.filters = [
				parse_filter(filter_)
				for filter_ in v
			]
		elif k == 'max_depth':
			defaults.max_depth = int(v)
		elif k == 'output':
			defaults.output = str(custom_path(v))
		elif k == 'include':
			defaults.include = [
				custom_path(val)
				for val in v
			]
		elif k in ['use_hash', 'use_metadata']:
			defaults[k] = v
			defaults[f"no_{k}"] = not v
		elif k in ['no_use_hash', 'no_use_metadata']:
			defaults[k] = v
			defaults[f"{k.replace('no_', '')}"] = not v
		else:
			defaults[k] = v

	return defaults


def run():
	parsed = gms.parse_args(namespace=Namespace())

	if parsed.get('_command'):
		command = parsed._command
	else:
		gms.parse_args(['-h'])

	if all(
		option in parsed
		for option in ['use_hash', 'no_use_hash']
	):
		raise ValueError(
			"Use one of --use-hash/--no-use-hash', not both."
		)

	if all(
		option in parsed
		for option in ['use_metadata', 'no_use_metadata']
	):
		raise ValueError(
			"Use one of --use-metadata/--no-use-metadata', not both."
		)

	args = set_defaults(parsed)
	args.update(parsed)

	if args.get('no_recursion'):
		args.max_depth = 0

	configure_logging(args.verbose - args.quiet, args.username, log_to_file=args.log)

	try:
		DISPATCH[command](args)
	except KeyboardInterrupt:
		gms.exit(130, "Interrupted by user")
