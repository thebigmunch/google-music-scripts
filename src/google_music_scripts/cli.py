import argparse
import math
import re
from pathlib import Path

from attr import attrib, attrs
from loguru import logger
from tbm_utils import (
	Namespace,
	SubcommandHelpFormatter,
	UsageHelpFormatter,
	create_parser_dry_run,
	create_parser_filter_dates,
	create_parser_local,
	create_parser_logging,
	create_parser_meta,
	create_parser_yes,
	custom_path,
	datetime_string_to_time_period,
	get_defaults,
	merge_defaults,
	parse_args
)

from .__about__ import __title__, __version__
from .commands import (
	do_delete,
	do_download,
	do_quota,
	do_search,
	do_upload,
)
from .config import configure_logging, read_config_file

COMMAND_ALIASES = {
	'del': 'delete',
	'delete': 'del',
	'down': 'delete',
	'download': 'down',
	'up': 'upload',
	'upload': 'up'
}

COMMAND_KEYS = {
	'del',
	'delete',
	'down',
	'download',
	'quota',
	'search',
	'up',
	'upload',
}

FILTER_RE = re.compile(r'(([+-]+)?(.*?)\[(.*?)\])', re.I)


@attrs(slots=True, frozen=True)
class FilterCondition:
	oper = attrib(converter=lambda o: '+' if o == '' else o)
	field = attrib()
	pattern = attrib()


def parse_filter(value):
	conditions = FILTER_RE.findall(value)
	if not conditions:
		raise ValueError(f"'{value}' is not a valid filter.")

	filter_ = [
		FilterCondition(*condition[1:])
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
			paths.append(custom_path(val.strip()))

	return paths


########
# Meta #
########

meta = create_parser_meta(__title__, __version__)


##########
# Action #
##########

dry_run = create_parser_dry_run()
yes = create_parser_yes()


###########
# Logging #
###########

logging_ = create_parser_logging()


##################
# Identification #
##################

ident = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False)

ident_options = ident.add_argument_group("Identification")
ident_options.add_argument(
	'-u', '--username',
	metavar='USER',
	help=(
		"Your Google username or e-mail address.\n"
		"Used to separate saved credentials."
	)
)

# Mobile Client

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

# Music Manager

mm_ident = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

mm_ident_options = mm_ident.add_argument_group("Identification")
mm_ident_options.add_argument(
	'--uploader-id',
	metavar='ID',
	help=(
		"A unique id given as a MAC address (e.g. '00:11:22:33:AA:BB').\n"
		"This should only be provided when the default does not work."
	)
)


#########
# Local #
#########

local = create_parser_local()


##########
# Filter #
##########

# Metadata

filter_metadata = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

metadata_options = filter_metadata.add_argument_group("Filter")
metadata_options.add_argument(
	'-f', '--filter',
	metavar='FILTER',
	action='append',
	dest='filters',
	type=parse_filter,
	help=(
		"Metadata filters.\n"
		"Can be specified multiple times."
	)
)

# Dates

filter_dates = create_parser_filter_dates()


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
	help=(
		"Don't create audio sample with ffmpeg/avconv.\n"
		"Send empty audio sample."
	)
)
upload_misc_options.add_argument(
	'--album-art',
	metavar='ART_PATHS',
	type=split_album_art_paths,
	help=(
		"Comma-separated list of album art filepaths.\n"
		"Can be relative filenames and/or absolute filepaths."
	)
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
		dry_run,
		yes,
		logging_,
		ident,
		mc_ident,
		filter_metadata,
		filter_dates,
	],
	add_help=False
)
delete_command.set_defaults(func=do_delete)


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
		dry_run,
		logging_,
		ident,
		mm_ident,
		mc_ident,
		local,
		filter_metadata,
		filter_dates,
		sync,
		output,
		include,
	],
	add_help=False
)
download_command.set_defaults(func=do_download)


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
		mm_ident,
	],
	add_help=False
)
quota_command.set_defaults(func=do_quota)


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
		yes,
		logging_,
		mc_ident,
		filter_metadata,
	],
	add_help=False
)
search_command.set_defaults(func=do_search)


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
		dry_run,
		logging_,
		ident,
		mm_ident,
		mc_ident,
		local,
		filter_metadata,
		filter_dates,
		upload_misc,
		sync,
		include,
	],
	add_help=False
)
upload_command.set_defaults(func=do_upload)


def check_args(args):
	if all(
		option in args
		for option in ['use_hash', 'no_use_hash']
	):
		raise ValueError(
			"Use one of --use-hash/--no-use-hash', not both."
		)

	if all(
		option in args
		for option in ['use_metadata', 'no_use_metadata']
	):
		raise ValueError(
			"Use one of --use-metadata/--no-use-metadata', not both."
		)


def default_args(args):
	defaults = Namespace()

	# Set defaults.
	defaults.verbose = 0
	defaults.quiet = 0
	defaults.debug = False
	defaults.dry_run = False
	defaults.username = ''
	defaults.filters = []

	if 'no_log_to_stdout' in args:
		defaults.log_to_stdout = False
		defaults.no_log_to_stdout = True
	else:
		defaults.log_to_stdout = True
		defaults.no_log_to_stdout = False

	if 'log_to_file' in args:
		defaults.log_to_file = True
		defaults.no_log_to_file = False
	else:
		defaults.log_to_file = False
		defaults.no_log_to_file = True

	if args._command in ['down', 'download', 'up', 'upload']:
		defaults.uploader_id = None
		defaults.device_id = None
	elif args._command in ['quota']:
		defaults.uploader_id = None
	else:
		defaults.device_id = None

	if args._command in ['down', 'download', 'up', 'upload']:
		defaults.no_recursion = False
		defaults.max_depth = math.inf
		defaults.exclude_paths = []
		defaults.exclude_regexes = []
		defaults.exclude_globs = []

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

	if args._command in ['down', 'download']:
		defaults.output = str(Path('.').resolve())
		defaults.include = []
	elif args._command in ['up', 'upload']:
		defaults.include = [custom_path('.').resolve()]
		defaults.delete_on_success = False
		defaults.no_sample = False
		defaults.album_art = None

	if args._command in ['del', 'delete', 'search']:
		defaults.yes = False

	config_defaults = get_defaults(
		args._command,
		read_config_file(
			username=args.get('username')
		),
		command_keys=COMMAND_KEYS,
		command_aliases=COMMAND_ALIASES
	)

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
		elif k in [
			'log_to_stdout',
			'log_to_file',
			'use_hash',
			'use_metadata',
		]:
			defaults[k] = v
			defaults[f"no_{k}"] = not v
		elif k in [
			'no_log_to_stdout',
			'no_log_to_file',
			'no_use_hash',
			'no_use_metadata',
		]:
			defaults[k] = v
			defaults[k.replace('no_', '')] = not v
		elif k.startswith(('created', 'modified')):
			if k.endswith('in'):
				defaults[k] = datetime_string_to_time_period(v, in_=True)
			elif k.endswith('on'):
				defaults[k] = datetime_string_to_time_period(v, on=True)
			elif k.endswith('before'):
				defaults[k] = datetime_string_to_time_period(v, before=True)
			elif k.endswith('after'):
				defaults[k] = datetime_string_to_time_period(v, after=True)
		else:
			defaults[k] = v

	return defaults


def run():
	try:
		parsed = parse_args(gms)

		if parsed._command is None:
			gms.parse_args(['-h'])

		check_args(parsed)

		defaults = default_args(parsed)
		args = merge_defaults(defaults, parsed)

		if args.get('no_recursion'):
			args.max_depth = 0

		configure_logging(
			args.verbose - args.quiet,
			username=args.username,
			debug=args.debug,
			log_to_stdout=args.log_to_stdout,
			log_to_file=args.log_to_file
		)

		args.func(args)

		logger.log('NORMAL', "All done!")
	except KeyboardInterrupt:
		gms.exit(130, "\nInterrupted by user")
