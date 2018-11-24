import sys

import click
import google_music
from logzero import logger

from google_music_scripts.__about__ import __title__, __version__
from google_music_scripts.config import configure_logging


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
	'-u', '--username',
	metavar='USERNAME',
	help="Your Google username or e-mail address.\nUsed to separate saved credentials."
)
@click.option(
	'--uploader-id',
	metavar='ID',
	help="A unique id given as a MAC address (e.g. '00:11:22:33:AA:BB').\nThis should only be provided when the default does not work."
)
def quota(
	log,
	username,
	uploader_id
):
	"""Get the uploaded track count and allowance."""

	configure_logging(0, username, log_to_file=log)

	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(username, uploader_id=uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	uploaded, allowed = mm.quota()

	logger.info(f"Quota -- {uploaded}/{allowed} ({uploaded / allowed:.2%})")
