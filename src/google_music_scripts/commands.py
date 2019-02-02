import sys

import google_music
import google_music_utils as gm_utils
from google_music_proto.musicmanager.utils import generate_client_id
from logzero import logger
from more_itertools import first_true
from natsort import natsorted

from .core import (
	download_songs,
	filter_songs,
	get_local_songs,
	upload_songs
)
from .utils import template_to_base_path


def do_delete(args):
	logger.info("Logging in to Mobile Client")
	mc = google_music.mobileclient(args.username, device_id=args.device_id)
	if not mc.is_authenticated:
		sys.exit("Failed to authenticate Mobile Client")

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
	logger.info("Logging in to Music Manager")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)
	if not mm.is_authenticated:
		sys.exit("Failed to authenticate Music Manager")

	logger.info("Logging in to Mobile Client")
	mc = google_music.mobileclient(args.username, device_id=args.device_id)
	if not mc.is_authenticated:
		sys.exit("Failed to authenticate Mobile Client")

	google_songs = filter_songs(mm.songs(), args.filters)

	base_path = template_to_base_path(args.output, google_songs)
	filepaths = [base_path]
	if args.include:
		filepaths.extend(args.include)

	logger.info("Loading local songs")

	local_songs = get_local_songs(
		filepaths,
		filters=args.filters,
		max_depth=args.max_depth,
		exclude_paths=args.exclude_paths,
		exclude_regexes=args.exclude_regexes,
		exclude_globs=args.exclude_globs
	)
	missing_songs = []
	if args.use_hash:
		logger.info("Comparing hashes")

		existing_songs = []
		google_client_id_map = {
			song.get('clientId'): song
			for song in filter_songs(mc.songs(), args.filters)
		}
		local_client_ids = {generate_client_id(song) for song in local_songs}
		for client_id, mc_song in google_client_id_map.items():
			song = first_true(
				(song for song in google_songs),
				pred=lambda song: song.get('id') == mc_song.get('id')
			)
			if client_id not in local_client_ids:
				missing_songs.append(song)
			else:
				existing_songs.append(song)

		logger.info(f"Found {len(existing_songs)} songs already exist by audio hash")
		if logger.level <= 10:
			for song in existing_songs:
				title = song.get('title', "<title>")
				artist = song.get('artist', "<artist>")
				album = song.get('album', "<album>")
				song_id = song['id']

				logger.debug(f"{title} -- {artist} -- {album} ({song_id})")

	if args.use_metadata:
		if args.use_hash:
			google_songs = missing_songs

		if google_songs:
			logger.info("Comparing metadata")

			missing_songs = natsorted(
				gm_utils.find_missing_items(
					google_songs,
					local_songs,
					fields=['artist', 'album', 'title', 'tracknumber'],
					normalize_values=True
				)
			)

			existing_songs = natsorted(
				gm_utils.find_existing_items(
					google_songs,
					local_songs,
					fields=['artist', 'album', 'title', 'tracknumber'],
					normalize_values=True
				)
			)

			logger.info(f"Found {len(existing_songs)} songs already exist by metadata")
			if logger.level <= 10:
				for song in existing_songs:
					title = song.get('title', "<title>")
					artist = song.get('artist', "<artist>")
					album = song.get('album', "<album>")
					song_id = song['id']

					logger.debug(f"{title} -- {artist} -- {album} ({song_id})")

	if not args.use_hash and not args.use_metadata:
		missing_songs = google_songs

	to_download = natsorted(missing_songs)

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
	logger.info("Logging in to Music Manager")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)
	if not mm.is_authenticated:
		sys.exit("Failed to authenticate Music Manager")

	uploaded, allowed = mm.quota()

	logger.info(f"Quota -- {uploaded}/{allowed} ({uploaded / allowed:.2%})")


def do_search(args):
	logger.info("Logging in to Mobile Client")
	mc = google_music.mobileclient(args.username, device_id=args.device_id)
	if not mc.is_authenticated:
		sys.exit("Failed to authenticate Mobile Client")

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


def do_upload(args):
	logger.info("Logging in to Music Manager")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)
	if not mm.is_authenticated:
		sys.exit("Failed to authenticate Music Manager")

	logger.info("Logging in to Mobile Client")
	mc = google_music.mobileclient(args.username, device_id=args.device_id)
	if not mc.is_authenticated:
		sys.exit("Failed to authenticate Mobile Client")

	logger.info("Loading local songs")

	missing_songs = []
	if args.use_hash:
		logger.info("Comparing hashes")

		existing_songs = []
		google_client_ids = {song.get('clientId', '') for song in mc.songs()}
		for song in get_local_songs(
			args.include,
			filters=args.filters,
			max_depth=args.max_depth,
			exclude_paths=args.exclude_paths,
			exclude_regexes=args.exclude_regexes,
			exclude_globs=args.exclude_globs
		):
			if generate_client_id(song) not in google_client_ids:
				missing_songs.append(song)
			else:
				existing_songs.append(song)

		logger.info(f"Found {len(existing_songs)} songs already exist by audio hash")
		if logger.level <= 10:
			for song in natsorted(existing_songs):
				logger.debug(song)

	if args.use_metadata:
		if args.use_hash:
			local_songs = missing_songs
		else:
			local_songs = get_local_songs(
				args.include,
				filters=args.filters,
				max_depth=args.max_depth,
				exclude_paths=args.exclude_paths,
				exclude_regexes=args.exclude_regexes,
				exclude_globs=args.exclude_globs
			)

		if local_songs:
			logger.info("Comparing metadata")

			google_songs = mm.songs()

			missing_songs = natsorted(
				gm_utils.find_missing_items(
					local_songs,
					google_songs,
					fields=['artist', 'album', 'title', 'tracknumber'],
					normalize_values=True
				)
			)

			existing_songs = natsorted(
				gm_utils.find_existing_items(
					local_songs,
					google_songs,
					fields=['artist', 'album', 'title', 'tracknumber'],
					normalize_values=True
				)
			)

			logger.info(f"Found {len(existing_songs)} songs already exist by metadata")
			if logger.level <= 10:
				for song in existing_songs:
					logger.debug(song)

	if not args.use_hash and not args.use_metadata:
		missing_songs = get_local_songs(
			args.include,
			filters=args.filters,
			max_depth=args.max_depth,
			exclude_paths=args.exclude_paths,
			exclude_regexes=args.exclude_regexes,
			exclude_globs=args.exclude_globs
		)

	to_upload = natsorted(local_songs)

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

	mc.logout()
	mm.logout()
	logger.info("All done!")
