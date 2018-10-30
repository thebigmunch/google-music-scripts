import os
import sys

import click
import google_music
from logzero import logger

from google_music_scripts.__about__ import __title__, __version__
from google_music_scripts.cli import CustomPath, split_filter_strings
from google_music_scripts.config import configure_logging
from google_music_scripts.core import download_songs, filter_songs


@click.command()
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

	to_download = filter_songs(
		mm.songs(),
		include_filters=include_filter, all_includes=all_includes,
		exclude_filters=exclude_filter, all_excludes=all_excludes
	)

	to_download.sort(key=lambda song: (song.get('artist'), song.get('album'), song.get('track_number')))

	if not to_download:
		logger.info("No songs to download")
	elif dry_run:
		logger.info(f"Found {len(to_download)} songs to download")

		if logger.level <= 10:
			for song in to_download:
				title = song.get('title', "<title>")
				artist = song.get('artist', "<artist>")
				album = song.get('album', "<album>")
				song_id = song['id']

				logger.debug(f"{title} -- {artist} -- {album} ({song_id})")
	else:
		download_songs(mm, to_download, template=output)

	mm.logout()
	logger.info("All done!")
