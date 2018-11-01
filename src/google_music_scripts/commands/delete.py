import sys

import click
import google_music
from logzero import logger

from google_music_scripts.__about__ import __title__, __version__
from google_music_scripts.cli import split_filter_strings
from google_music_scripts.config import configure_logging
from google_music_scripts.core import filter_songs


@click.command()
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
	log, verbose, quiet, dry_run, username, device_id,
	include_filter, all_includes, exclude_filter, all_excludes, yes
):
	"""Delete songs from a Google Music library."""

	configure_logging(verbose - quiet, log_to_file=log)

	logger.info("Logging in to Google Music")
	mc = google_music.mobileclient(username, device_id=device_id)

	if not mc.is_authenticated:
		sys.exit("Failed to authenticate client.")

	to_delete = filter_songs(
		mc.songs(),
		include_filters=include_filter, all_includes=all_includes,
		exclude_filters=exclude_filter, all_excludes=all_excludes
	)

	if not to_delete:
		logger.info("No songs to delete")
	elif dry_run:
		logger.info(f"Found {len(to_delete)} songs to delete")

		for song in to_delete:
			title = song.get('title', "<empty>")
			artist = song.get('artist', "<empty>")
			album = song.get('album', "<empty>")
			song_id = song['id']

			logger.info(f"{title} -- {artist} -- {album} ({song_id})")
	else:
		confirm = yes or input(
			f"\nAre you sure you want to delete {len(to_delete)} song(s) from Google Music? (y/n) "
		) in ("y", "Y")

		if confirm:
			song_num = 0
			total = len(to_delete)
			pad = len(str(total))

			for song in to_delete:
				song_num += 1

				logger.debug(f"Deleting {title} -- {artist} -- {album} ({song_id})")
				mc.song_delete(song)

				title = song.get('title', "<empty>")
				artist = song.get('artist', "<empty>")
				album = song.get('album', "<empty>")
				song_id = song['id']

				logger.info(f"Deleted {song_num:>{pad}}/{total}")
		else:
			logger.info("No songs deleted")

	mc.logout()
	logger.info("All done!")