import sys

import google_music
import google_music_utils as gm_utils
from google_music_proto.musicmanager.utils import generate_client_id
from loguru import logger
from more_itertools import first_true
from natsort import natsorted
from tbm_utils import filter_filepaths_by_dates

from .core import (
	download_songs,
	filter_google_dates,
	get_google_songs,
	get_local_songs,
	upload_songs,
)
from .utils import template_to_base_path


def do_delete(args):
	logger.log('NORMAL', "Logging in to Mobile Client")
	mc = google_music.mobileclient(args.username, device_id=args.device_id)
	if not mc.is_authenticated:
		sys.exit("Failed to authenticate Mobile Client")

	to_delete = filter_google_dates(
		get_google_songs(mc, filters=args.filters),
		created_in=args.get('created_in'),
		created_on=args.get('created_on'),
		created_before=args.get('created_before'),
		created_after=args.get('created_after'),
		modified_in=args.get('modified_in'),
		modified_on=args.get('modified_on'),
		modified_before=args.get('modified_before'),
		modified_after=args.get('modified_after')
	)

	logger.info("Found {} songs to delete", len(to_delete))

	if not to_delete:
		logger.log('NORMAL', "No songs to delete")
	elif not args.dry_run:
		confirm = args.yes or input(
			f"\nAre you sure you want to delete {len(to_delete)} song(s) from Google Music? (y/n) "
		) in ("y", "Y")

		if confirm:
			logger.log('NORMAL', "Deleting songs")

			song_num = 0
			total = len(to_delete)
			pad = len(str(total))

			for song in to_delete:
				song_num += 1

				title = song.get('title', "<empty>")
				artist = song.get('artist', "<empty>")
				album = song.get('album', "<empty>")
				song_id = song['id']

				logger.trace(
					"Deleting {} -- {} -- {} ({})",
					title,
					artist,
					album,
					song_id
				)

				mc.song_delete(song)

				logger.info(
					"Deleted {:>{}}/{}",
					song_num,
					pad,
					total
				)
		else:
			logger.info("No songs deleted")
	elif logger._min_level <= 15:
		for song in to_delete:
			title = song.get('title', "<empty>")
			artist = song.get('artist', "<empty>")
			album = song.get('album', "<empty>")
			song_id = song['id']

			logger.log(
				'ACTION_SUCCESS',
				"{} -- {} -- {} ({})",
				title,
				artist,
				album,
				song_id
			)


def do_download(args):
	logger.log('NORMAL', "Logging in to Music Manager")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)
	if not mm.is_authenticated:
		sys.exit("Failed to authenticate Music Manager")

	logger.log('NORMAL', "Logging in to Mobile Client")
	mc = google_music.mobileclient(args.username, device_id=args.device_id)
	if not mc.is_authenticated:
		sys.exit("Failed to authenticate Mobile Client")

	google_songs = get_google_songs(mm, filters=args.filters)
	base_path = template_to_base_path(args.output, google_songs)
	filepaths = [base_path, *args.include]

	mc_songs = get_google_songs(mc, filters=args.filters)
	if any(
		args.get(option)
		for option in [
			'created_in',
			'created_on',
			'created_before',
			'created_after',
			'modified_in',
			'modified_on',
			'modified_before',
			'modified_after',
		]
	):
		mc_songs = filter_google_dates(
			mc_songs,
			created_in=args.get('created_in'),
			created_on=args.get('created_on'),
			created_before=args.get('created_before'),
			created_after=args.get('created_after'),
			modified_in=args.get('modified_in'),
			modified_on=args.get('modified_on'),
			modified_before=args.get('modified_before'),
			modified_after=args.get('modified_after')
		)

	local_songs = get_local_songs(
		filepaths,
		filters=args.filters,
		max_depth=args.max_depth,
		exclude_paths=args.exclude_paths,
		exclude_regexes=args.exclude_regexes,
		exclude_globs=args.exclude_globs
	)

	missing_songs = []
	existing_songs = []
	if args.use_hash:
		if google_songs and local_songs:
			logger.log('NORMAL', "Comparing hashes")

			google_client_id_map = {
				mc_song.get('clientId'): mc_song
				for mc_song in mc_songs
			}
			local_client_ids = {generate_client_id(song) for song in local_songs}
			for client_id, mc_song in google_client_id_map.items():
				song = first_true(
					(song for song in google_songs),
					pred=lambda song: song.get('id') == mc_song.get('id')
				)

				if song is not None:
					if client_id not in local_client_ids:
						missing_songs.append(song)
					else:
						existing_songs.append(song)

			logger.info("Found {} songs already exist by audio hash", len(existing_songs))

			if logger._min_level <= 5:
				for song in existing_songs:
					title = song.get('title', "<title>")
					artist = song.get('artist', "<artist>")
					album = song.get('album', "<album>")
					song_id = song['id']

					logger.trace(
						"{} -- {} -- {} ({})",
						title,
						artist,
						album,
						song_id
					)
		else:
			missing_songs = google_songs

			if not google_songs and not local_songs:
				logger.log('NORMAL', "No songs to compare hashes.")
			elif not google_songs:
				logger.log('NORMAL', "No Google songs to compare hashes.")
			elif not local_songs:
				logger.log('NORMAL', "No local songs to compare hashes.")

	if args.use_metadata:
		if args.use_hash:
			google_songs = missing_songs

		if google_songs and local_songs:
			logger.log('NORMAL', "Comparing metadata")

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

			logger.info(
				"Found {} songs already exist by metadata",
				len(existing_songs)
			)

			if logger._min_level <= 5:
				for song in existing_songs:
					title = song.get('title', "<title>")
					artist = song.get('artist', "<artist>")
					album = song.get('album', "<album>")
					song_id = song['id']

					logger.trace(
						"{} -- {} -- {} ({})",
						title,
						artist,
						album,
						song_id
					)
		else:
			if not google_songs and not local_songs:
				logger.log('NORMAL', "No songs to compare metadata.")
			elif not google_songs:
				logger.log('NORMAL', "No Google songs to compare metadata.")
			elif not local_songs:
				logger.log('NORMAL', "No local songs to compare metadata.")

	if not args.use_hash and not args.use_metadata:
		missing_songs = google_songs

	logger.log('NORMAL', "Sorting songs")

	to_download = natsorted(missing_songs)

	logger.info("Found {} songs to download", len(to_download))

	if not args.dry_run:
		download_songs(mm, to_download, template=args.output)
	elif logger._min_level <= 15:
		for song in to_download:
			title = song.get('title', "<title>")
			artist = song.get('artist', "<artist>")
			album = song.get('album', "<album>")
			song_id = song['id']

			logger.log(
				'ACTION_SUCCESS',
				"{} -- {} -- {} ({})",
				title,
				artist,
				album,
				song_id
			)


def do_quota(args):
	logger.log('NORMAL', "Logging in to Music Manager")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)
	if not mm.is_authenticated:
		sys.exit("Failed to authenticate Music Manager")

	uploaded, allowed = mm.quota()

	logger.log(
		'NORMAL',
		"Quota -- {}/{} ({:.2%})",
		uploaded,
		allowed,
		uploaded / allowed
	)


def do_search(args):
	logger.log('NORMAL', "Logging in to Mobile Client")
	mc = google_music.mobileclient(args.username, device_id=args.device_id)
	if not mc.is_authenticated:
		sys.exit("Failed to authenticate Mobile Client")

	search_results = get_google_songs(mc, filters=args.filters)

	if any(
		args.get(option)
		for option in [
			'created_in',
			'created_on',
			'created_before',
			'created_after',
			'modified_in',
			'modified_on',
			'modified_before',
			'modified_after',
		]
	):
		search_results = filter_google_dates(
			search_results,
			created_in=args.get('created_in'),
			created_on=args.get('created_on'),
			created_before=args.get('created_before'),
			created_after=args.get('created_after'),
			modified_in=args.get('modified_in'),
			modified_on=args.get('modified_on'),
			modified_before=args.get('modified_before'),
			modified_after=args.get('modified_after')
		)

	search_results = natsorted(
		search_results,
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
			or input(
				f"\nDisplay {len(search_results)} results? (y/n) "
			) in ("y", "Y")
		)

		if confirm:
			for result in search_results:
				result_num += 1

				title = result.get('title', "<empty>")
				artist = result.get('artist', "<empty>")
				album = result.get('album', "<empty>")
				song_id = result['id']

				logger.log(
					'NORMAL',
					"{:>{}}/{} {} -- {} -- {} ({})",
					result_num,
					pad,
					total,
					title,
					artist,
					album,
					song_id
				)
	else:
		logger.log('NORMAL', "No songs found matching query")


def do_upload(args):
	logger.log('NORMAL', "Logging in to Music Manager")
	mm = google_music.musicmanager(args.username, uploader_id=args.uploader_id)
	if not mm.is_authenticated:
		sys.exit("Failed to authenticate Music Manager")

	logger.log('NORMAL', "Logging in to Mobile Client")
	mc = google_music.mobileclient(args.username, device_id=args.device_id)
	if not mc.is_authenticated:
		sys.exit("Failed to authenticate Mobile Client")

	local_songs = get_local_songs(
		args.include,
		filters=args.filters,
		max_depth=args.max_depth,
		exclude_paths=args.exclude_paths,
		exclude_regexes=args.exclude_regexes,
		exclude_globs=args.exclude_globs
	)

	if any(
		args.get(option)
		for option in [
			'created_in',
			'created_on',
			'created_before',
			'created_after',
			'modified_in',
			'modified_on',
			'modified_before',
			'modified_after',
		]
	):
		local_songs = filter_filepaths_by_dates(
			local_songs,
			created_in=args.get('created_in'),
			created_on=args.get('created_on'),
			created_before=args.get('created_before'),
			created_after=args.get('created_after'),
			modified_in=args.get('modified_in'),
			modified_on=args.get('modified_on'),
			modified_before=args.get('modified_before'),
			modified_after=args.get('modified_after')
		)

	missing_songs = []
	if args.use_hash:
		logger.log('NORMAL', "Comparing hashes")

		existing_songs = []
		google_client_ids = {song.get('clientId', '') for song in get_google_songs(mc)}
		for song in local_songs:
			if generate_client_id(song) not in google_client_ids:
				missing_songs.append(song)
			else:
				existing_songs.append(song)

		logger.info("Found {} songs already exist by audio hash", len(existing_songs))

		if logger._min_level <= 5:
			for song in natsorted(existing_songs):
				logger.trace(song)

	if args.use_metadata:
		if args.use_hash:
			local_songs = missing_songs

		if local_songs:
			logger.log('NORMAL', "Comparing metadata")

			google_songs = get_google_songs(mm, filters=args.filters)

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

			logger.info("Found {} songs already exist by metadata", len(existing_songs))

			if logger._min_level <= 5:
				for song in existing_songs:
					logger.trace(song)

	if not args.use_hash and not args.use_metadata:
		missing_songs = local_songs

	logger.log('NORMAL', "Sorting songs")

	to_upload = natsorted(missing_songs)

	logger.info("Found {} songs to upload", len(to_upload))

	if not args.dry_run:
		upload_songs(
			mm,
			to_upload,
			album_art=args.album_art,
			no_sample=args.no_sample,
			delete_on_success=args.delete_on_success
		)
	elif logger._min_level <= 15:
		for song in to_upload:
			logger.log(
				'ACTION_SUCCESS',
				song
			)
