import sys

import google_music
import google_music_utils as gm_utils
from logzero import logger
from natsort import natsorted

from .core import (
	download_songs,
	filter_songs,
	get_local_songs,
	upload_songs
)
from .utils import template_to_base_path


def do_delete(args):
	logger.info("Logging in to Google Music")
	mc = google_music.mobileclient(args.username, device_id=args.device_id)

	if not mc.is_authenticated:
		sys.exit("Failed to authenticate client.")

	to_delete = filter_songs(mc.songs(), args.filters)

	if not to_delete:
		logger.info("No songs to delete")
	elif args.dry_run:
		logger.info(f"Found {len(to_delete)} songs to delete")

		for song in to_delete:
			title = song.get('title', "<empty>")
			artist = song.get('artist', "<empty>")
			album = song.get('album', "<empty>")
			song_id = song['id']

			logger.info(f"{title} -- {artist} -- {album} ({song_id})")
	else:
		confirm = args.yes or input(
			f"\nAre you sure you want to delete {len(to_delete)} song(s) from Google Music? (y/n) "
		) in ("y", "Y")

		if confirm:
			song_num = 0
			total = len(to_delete)
			pad = len(str(total))

			for song in to_delete:
				song_num += 1

				title = song.get('title', "<empty>")
				artist = song.get('artist', "<empty>")
				album = song.get('album', "<empty>")
				song_id = song['id']

				logger.debug(f"Deleting {title} -- {artist} -- {album} ({song_id})")

				mc.song_delete(song)

				logger.info(f"Deleted {song_num:>{pad}}/{total}")
		else:
			logger.info("No songs deleted")

	mc.logout()
	logger.info("All done!")


def do_download(args):
	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	to_download = natsorted(
		filter_songs(mm.songs(), args.filters),
		key=lambda song: (
			song.get('artist', ''),
			song.get('album', ''),
			song.get('track_number', 0)
		)
	)

	if not to_download:
		logger.info("No songs to download")
	elif args.dry_run:
		logger.info(f"Found {len(to_download)} songs to download")

		if logger.level <= 10:
			for song in to_download:
				title = song.get('title', "<title>")
				artist = song.get('artist', "<artist>")
				album = song.get('album', "<album>")
				song_id = song['id']

				logger.debug(f"{title} -- {artist} -- {album} ({song_id})")
	else:
		download_songs(mm, to_download, template=args.output)

	mm.logout()
	logger.info("All done!")


def do_quota(args):
	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	uploaded, allowed = mm.quota()

	logger.info(f"Quota -- {uploaded}/{allowed} ({uploaded / allowed:.2%})")


def do_search(args):
	logger.info("Logging in to Google Music")
	mc = google_music.mobileclient(args.username, device_id=args.device_id)

	if not mc.is_authenticated:
		sys.exit("Failed to authenticate client.")

	search_results = natsorted(
		filter_songs(mc.songs(), args.filters),
		key=lambda song: (
			song.get('artist', ''),
			song.get('album', ''),
			song.get('trackNumber', 0)
		)
	)

	if search_results:
		result_num = 0
		total = len(search_results)
		pad = len(str(total))

		confirm = (
			args.yes
			or input(f"\nDisplay {len(search_results)} results? (y/n) ") in ("y", "Y")
		)

		if confirm:
			for result in search_results:
				result_num += 1

				title = result.get('title', "<empty>")
				artist = result.get('artist', "<empty>")
				album = result.get('album', "<empty>")
				song_id = result['id']

				logger.info(
					f"{result_num:>{pad}}/{total} {title} -- {artist} -- {album} ({song_id})"
				)
	else:
		logger.info("No songs found matching query")

	mc.logout()
	logger.info("All done!")


def do_sync_down(args):
	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	google_songs = filter_songs(mm.songs(), args.filters)

	base_path = template_to_base_path(args.output, google_songs)
	filepaths = [base_path]
	if args.include:
		filepaths.extend(args.include)

	local_songs = get_local_songs(filepaths, max_depth=args.max_depth)

	logger.info("Comparing song collections")
	to_download = natsorted(
		gm_utils.find_missing_items(
			google_songs,
			local_songs,
			fields=['artist', 'album', 'title', 'tracknumber'],
			normalize_values=True
		),
		key=lambda song: (
			song.get('artist', ''),
			song.get('album', ''),
			song.get('track_number', 0)
		)
	)

	if not to_download:
		logger.info("No songs to download")
	elif args.dry_run:
		logger.info(f"Found {len(to_download)} songs to download")

		if logger.level <= 10:
			for song in to_download:
				title = song.get('title', "<title>")
				artist = song.get('artist', "<artist>")
				album = song.get('album', "<album>")
				song_id = song['id']

				logger.debug(f"{title} -- {artist} -- {album} ({song_id})")
	else:
		download_songs(mm, to_download, template=args.output)

	mm.logout()
	logger.info("All done!")


def do_sync_up(args):
	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	google_songs = mm.songs()
	local_songs = get_local_songs(args.include, filters=args.filters, max_depth=args.max_depth)

	logger.info("Comparing song collections")
	to_upload = natsorted(
		gm_utils.find_missing_items(
			local_songs,
			google_songs,
			fields=['artist', 'album', 'title', 'tracknumber'],
			normalize_values=True
		)
	)

	if not to_upload:
		logger.info("No songs to upload")
	elif args.dry_run:
		logger.info(f"Found {len(to_upload)} songs to upload")

		if logger.level <= 10:
			for song in to_upload:
				logger.debug(song)
	else:
		upload_songs(
			mm,
			to_upload,
			album_art=args.album_art,
			no_sample=args.no_sample,
			delete_on_success=args.delete_on_success
		)

	mm.logout()
	logger.info("All done!")


def do_upload(args):
	logger.info("Logging in to Google Music")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)

	if not mm.is_authenticated:
		sys.exit("Failed to authenticate client.")

	to_upload = natsorted(
		get_local_songs(args.include, filters=args.filters, max_depth=args.max_depth)
	)

	if not to_upload:
		logger.info("No songs to upload")
	elif args.dry_run:
		logger.info(f"Found {len(to_upload)} songs to upload")

		if logger.level <= 10:
			for song in to_upload:
				logger.debug(song)
	else:
		upload_songs(
			mm,
			to_upload,
			album_art=args.album_art,
			no_sample=args.no_sample,
			delete_on_success=args.delete_on_success
		)

	mm.logout()
	logger.info("All done!")
