import sys

import click
import google_music
from logzero import logger

from google_music_scripts.__about__ import __title__, __version__
from google_music_scripts.cli import (
	CustomPath,
	default_to_cwd,
	parse_filters
)
from google_music_scripts.config import configure_logging
from google_music_scripts.core import get_local_songs, upload_songs


@click.command()
@click.version_option(
	__version__,
	'-V', '--version',
	prog_name=__title__,
	message="%(prog)s %(version)s"
)
@click.option(
	'-l', '--log',
	is_flag=True,
	default=False,
	help="Log to file."
)
@click.option(
	'-v', '--verbose',
	count=True
)
@click.option(
	'-q', '--quiet',
	count=True
)
@click.option(
	'-n', '--dry-run',
	is_flag=True,
	default=False,
	help="Output list of songs that would be uploaded."
)
@click.option(
	'-u', '--username',
	metavar='USERNAME',
	help="Your Google username or e-mail address.\nUsed to separate saved credentials."
)
@click.option(
	'--uploader-id',
	metavar='ID',
	help="A unique id given as a MAC address (e.g. '00:11:22:33:AA:BB').\nThis should only be provided when the default does not work."
)
@click.option(
	'--no-recursion',
	is_flag=True,
	default=False,
	help="Disable recursion when scanning for local files.\nRecursion is enabled by default."
)
@click.option(
	'--max-depth',
	metavar='DEPTH',
	type=int,
	help="Set maximum depth of recursion when scanning for local files.\nDefault is infinite recursion."
)
@click.option(
	'--delete-on-success',
	is_flag=True,
	default=False,
	help="Delete successfully uploaded local files."
)
@click.option(
	'--transcode-lossless/--no-transcode-lossless',
	is_flag=True,
	default=True,
	help="Transcode lossless files to MP3 for upload."
)
@click.option(
	'--transcode-lossy/--no-transcode-lossy',
	is_flag=True,
	default=True,
	help="Transcode non-MP3 lossy files to MP3 for upload."
)
@click.option(
	'-f', '--filters',
	metavar='FILTER',
	multiple=True,
	callback=parse_filters,
	help="Metadata filters."
)
@click.argument(
	'input-paths',
	nargs=-1,
	type=CustomPath(resolve_path=True),
	callback=default_to_cwd
)
def upload(
	log,
	verbose,
	quiet,
	dry_run,
	username,
	uploader_id,
	no_recursion,
	max_depth,
	delete_on_success,
	transcode_lossless,
	transcode_lossy,
	filters,
	input_paths
):
	"""Upload songs to a Google Music library."""

	configure_logging(verbose - quiet, username, log_to_file=log)

	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(username, uploader_id=uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	if no_recursion:
		max_depth = 0
	elif max_depth is None:
		max_depth = float('inf')

	to_upload = get_local_songs(input_paths, filters=filters, max_depth=max_depth)
	to_upload.sort()

	if not to_upload:
		logger.info("No songs to upload")
	elif dry_run:
		logger.info(f"Found {len(to_upload)} songs to upload")

		if logger.level <= 10:
			for song in to_upload:
				logger.debug(song)
	else:
		upload_songs(
			mm,
			to_upload,
			transcode_lossless=transcode_lossless,
			transcode_lossy=transcode_lossy,
			delete_on_success=delete_on_success
		)

	mm.logout()
	logger.info("All done!")
