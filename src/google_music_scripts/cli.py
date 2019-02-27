import argparse
import math
import os
import re
from pathlib import Path

import pendulum
from attr import attrib, attrs
from loguru import logger
from pendulum import DateTime
from pendulum.tz import fixed_timezone

from .__about__ import __title__, __version__
from .commands import (
	do_delete,
	do_download,
	do_quota,
	do_search,
	do_upload,
)
from .config import configure_logging, get_defaults
from .constants import UNIX_PATH_RE
from .utils import DictMixin, convert_unix_path

DATETIME_RE = re.compile(
	r"(?P<year>\d{4})"
	r"[-\s]?"
	r"(?P<month>\d{1,2})?"
	r"[-\s]?"
	r"(?P<day>\d{1,2})?"
	r"[T\s]?"
	r"(?P<hour>\d{1,2})?"
	r"[:\s]?"
	r"(?P<minute>\d{1,2})?"
	r"[:\s]?"
	r"(?P<second>\d{1,2})?"
	r"(?P<tz_oper>[+\-\s])?"
	r"(?P<tz_hour>\d{1,2})?"
	r"[:\s]?"
	r"(?P<tz_minute>\d{1,2})?"
)
FILTER_RE = re.compile(r'(([+-]+)?(.*?)\[(.*?)\])', re.I)


@attrs(slots=True, frozen=True)
class FilterCondition:
	oper = attrib(converter=lambda o: '+' if o == '' else o)
	field = attrib()
	pattern = attrib()


def _convert_to_int(value):
	if value is not None:
		value = int(value)

	return value


@attrs(slots=True, frozen=True, kw_only=True)
class ParsedDateTime:
	year = attrib(converter=_convert_to_int)
	month = attrib(converter=_convert_to_int)
	day = attrib(converter=_convert_to_int)
	hour = attrib(converter=_convert_to_int)
	minute = attrib(converter=_convert_to_int)
	second = attrib(converter=_convert_to_int)
	tz_oper = attrib()
	tz_hour = attrib(converter=_convert_to_int)
	tz_minute = attrib(converter=_convert_to_int)


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
# This type converts Unix-style paths to Windows-style paths in this case.
def custom_path(value):
	if os.name == 'nt' and UNIX_PATH_RE.match(str(value)):
		value = Path(convert_unix_path(str(value)))

	value = Path(value)

	return value


def default_to_cwd():
	return Path.cwd()


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
			if os.name == 'nt' and UNIX_PATH_RE.match(val.strip()):
				paths.append(convert_unix_path(val.strip()))
			else:
				paths.append(Path(val))

	return paths


def time_period(
	dt_string,
	*,
	in_=False,
	on=False,
	before=False,
	after=False
):
	match = DATETIME_RE.match(dt_string)

	if not match or match['year'] is None:
		raise argparse.ArgumentTypeError(
			f"'{dt_string}' is not a supported datetime string."
		)

	parsed = ParsedDateTime(**match.groupdict())

	if parsed.tz_hour:
		tz_offset = 0
		if parsed.tz_hour is not None:
			tz_offset += parsed.tz_hour * 3600
		if parsed.tz_minute is not None:
			tz_offset += parsed.tz_minute * 60
		if parsed.tz_oper == '-':
			tz_offset *= -1
		parsed_tz = fixed_timezone(tz_offset)
	else:
		parsed_tz = pendulum.local_timezone()

	if in_:
		if parsed.day:
			raise argparse.ArgumentTypeError(
				f"Datetime string must contain only year or year/month for 'in' option."
			)
		start = pendulum.datetime(
			parsed.year,
			parsed.month or 1,
			parsed.day or 1,
			tz=parsed_tz
		)

		if parsed.month:
			end = start.end_of('month')
		else:
			end = start.end_of('year')

		return pendulum.period(start, end)
	elif on:
		if (
			not all(
				getattr(parsed, attr)
				for attr in ['year', 'month', 'day']
			)
			or parsed.hour
		):
			raise argparse.ArgumentTypeError(
				f"Datetime string must contain only year, month, and day for 'on' option."
			)

		dt = pendulum.datetime(
			parsed.year,
			parsed.month,
			parsed.day,
			tz=parsed_tz
		)

		return pendulum.period(dt.start_of('day'), dt.end_of('day'))
	elif before:
		start = DateTime.min

		dt = pendulum.datetime(
			parsed.year,
			parsed.month or 1,
			parsed.day or 1,
			parsed.hour or 23,
			parsed.minute or 59,
			parsed.second or 59,
			0,
			tz=parsed_tz
		)

		if not parsed.month:
			dt = dt.start_of('year')
		elif not parsed.day:
			dt = dt.start_of('month')
		elif not parsed.hour:
			dt = dt.start_of('day')
		elif not parsed.minute:
			dt = dt.start_of('hour')
		elif not parsed.second:
			dt = dt.start_of('minute')

		return pendulum.period(start, dt)
	elif after:
		end = DateTime.max

		dt = pendulum.datetime(
			parsed.year,
			parsed.month or 1,
			parsed.day or 1,
			parsed.hour or 23,
			parsed.minute or 59,
			parsed.second or 59,
			99999,
			tz=parsed_tz
		)

		if not parsed.month:
			dt = dt.end_of('year')
		elif not parsed.day:
			dt = dt.end_of('month')
		elif not parsed.hour:
			dt = dt.start_of('day')
		elif not parsed.minute:
			dt = dt.start_of('hour')
		elif not parsed.second:
			dt = dt.start_of('minute')

		return pendulum.period(dt, end)


########
# Meta #
########

meta = argparse.ArgumentParser(add_help=False)

meta_options = meta.add_argument_group("Options")
meta_options.add_argument(
	'-h', '--help',
	action='help',
	help="Display help."
)
meta_options.add_argument(
	'-V', '--version',
	action='version',
	version=f"{__title__} {__version__}",
	help="Output version."
)


##########
# Action #
##########

dry_run = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

dry_run_options = dry_run.add_argument_group("Action")
dry_run_options.add_argument(
	'-n', '--dry-run',
	action='store_true',
	help="Output results without taking action."
)

yes = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

yes_options = yes.add_argument_group("Action")
yes_options.add_argument(
	'-y', '--yes',
	action='store_true',
	help="Don't ask for confirmation."
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
	'--debug',
	action='store_true',
	help="Output log messages from dependencies."
)
logging_options.add_argument(
	'--log-to-stdout',
	action='store_true',
	help="Log to stdout."
)
logging_options.add_argument(
	'--no-log-to-stdout',
	action='store_true',
	help="Don't log to stdout."
)
logging_options.add_argument(
	'--log-to-file',
	action='store_true',
	help="Log to file."
)
logging_options.add_argument(
	'--no-log-to-file',
	action='store_true',
	help="Don't log to file."
)


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

local = argparse.ArgumentParser(argument_default=argparse.SUPPRESS, add_help=False)

local_options = local.add_argument_group("Local")
local_options.add_argument(
	'--no-recursion',
	action='store_true',
	help=(
		"Disable recursion when scanning for local files.\n"
		"Recursion is enabled by default."
	)
)
local_options.add_argument(
	'--max-depth',
	metavar='DEPTH',
	type=int,
	help=(
		"Set maximum depth of recursion when scanning for local files.\n"
		"Default is infinite recursion."
	)
)
local_options.add_argument(
	'-xp', '--exclude-path',
	metavar='PATH',
	action='append',
	dest='exclude_paths',
	help=(
		"Exclude filepaths.\n"
		"Can be specified multiple times."
	)
)
local_options.add_argument(
	'-xr', '--exclude-regex',
	metavar='RX',
	action='append',
	dest='exclude_regexes',
	help=(
		"Exclude filepaths using regular expressions.\n"
		"Can be specified multiple times."
	)
)
local_options.add_argument(
	'-xg', '--exclude-glob',
	metavar='GP',
	action='append',
	dest='exclude_globs',
	help=(
		"Exclude filepaths using glob patterns.\n"
		"Can be specified multiple times.\n"
		"Absolute glob patterns not supported."
	)
)


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

filter_dates = argparse.ArgumentParser(
	argument_default=argparse.SUPPRESS,
	add_help=False
)

dates_options = filter_dates.add_argument_group("Filter")
dates_options.add_argument(
	'--created-in',
	metavar='DATE',
	type=lambda d: time_period(d, in_=True),
	help="Include songs created in year or year/month."
)
dates_options.add_argument(
	'--created-on',
	metavar='DATE',
	type=lambda d: time_period(d, on=True),
	help="Include songs created on date."
)
dates_options.add_argument(
	'--created-before',
	metavar='DATE',
	type=lambda d: time_period(d, before=True),
	help="Include songs created before datetime."
)
dates_options.add_argument(
	'--created-after',
	metavar='DATE',
	type=lambda d: time_period(d, after=True),
	help="Include songs created after datetime."
)
dates_options.add_argument(
	'--modified-in',
	metavar='DATE',
	type=lambda d: time_period(d, in_=True),
	help="Include songs created in year or year/month."
)
dates_options.add_argument(
	'--modified-on',
	metavar='DATE',
	type=lambda d: time_period(d, on=True),
	help="Include songs created on date."
)
dates_options.add_argument(
	'--modified-before',
	metavar='DATE',
	type=lambda d: time_period(d, before=True),
	help="Include songs modified before datetime."
)
dates_options.add_argument(
	'--modified-after',
	metavar='DATE',
	type=lambda d: time_period(d, after=True),
	help="Include songs modified after datetime."
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


def parse_args():
	return gms.parse_args(namespace=Namespace())


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
				defaults[k] = time_period(v, in_=True)
			elif k.endswith('on'):
				defaults[k] = time_period(v, on=True)
			elif k.endswith('before'):
				defaults[k] = time_period(v, before=True)
			elif k.endswith('after'):
				defaults[k] = time_period(v, after=True)
		else:
			defaults[k] = v

	return defaults


def merge_defaults(defaults, parsed):
	args = Namespace()

	args.update(defaults)
	args.update(parsed)

	if args.get('no_recursion'):
		args.max_depth = 0

	return args


def run():
	try:
		parsed = parse_args()

		if parsed._command is None:
			gms.parse_args(['-h'])

		check_args(parsed)

		defaults = default_args(parsed)
		args = merge_defaults(defaults, parsed)

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
