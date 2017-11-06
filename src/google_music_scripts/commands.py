import google_music_utils as gm_utils
from logzero import logger

from .core import download_songs, get_google_songs, get_local_songs, upload_songs
from .utils import template_to_base_path


def do_delete(
	mc, dry_run=False, include_filters=None, all_includes=False,
	exclude_filters=None, all_excludes=False, yes=False):
	"""Delete songs from a Google Music library."""

	to_delete = get_google_songs(
		include_filters=include_filters, all_includes=all_includes,
		exclude_filters=exclude_filters, all_excludes=all_excludes
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
				mc.delete_song(song)

				title = song.get('title', "<empty>")
				artist = song.get('artist', "<empty>")
				album = song.get('album', "<empty>")
				song_id = song['id']

				logger.debug(f"Deleting {title} -- {artist} -- {album} ({song_id})")
				logger.info(f"Deleted {song_num:>{pad}}/{total}")
		else:
			logger.info("No songs deleted")

	mc.logout()
	logger.info("All done!")


def do_download(
	mm, output, *, dry_run=False, include_filters=None,
	all_includes=False, exclude_filters=None, all_excludes=False):
	"""Download songs from a Google Music library."""

	to_download = get_google_songs(
		mm, include_filters=include_filters, all_includes=all_includes,
		exclude_filters=exclude_filters, all_excludes=all_excludes
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
		logger.info(f"Downloading {len(to_download)} song(s) from Google Music")

		download_songs(mm, to_download, template=output)

	mm.logout()
	logger.info("All done!")


def do_search(mc, *, include_filters=None, all_includes=False, exclude_filters=None, all_excludes=False, yes=False):
	"""Search a Google Music library."""

	search_results = get_google_songs(
		include_filters=include_filters, all_includes=all_includes,
		exclude_filters=exclude_filters, all_excludes=all_excludes
	)

	search_results.sort(key=lambda song: (song.get('artist'), song.get('album'), song.get('trackNumber')))

	if search_results:
		result_num = 0
		total = len(search_results)
		pad = len(str(total))

		confirm = yes or input(f"\nDisplay {len(search_results)} results? (y/n) ") in ("y", "Y")

		if confirm:
			for result in search_results:
				result_num += 1

				title = result.get('title', "<empty>")
				artist = result.get('artist', "<empty>")
				album = result.get('album', "<empty>")
				song_id = result['id']

				logger.info(f"{result_num:>{pad}}/{total} {title} -- {artist} -- {album} ({song_id})")
	else:
		logger.info("No songs found matching query")

	mc.logout()
	logger.info("All done!")


def do_sync_down(
	mm, output, include_paths, *, dry_run=False, max_depth=float('inf'), include_patterns=None,
	include_filters=None, all_includes=False, exclude_filters=None, all_excludes=False):
	"""Sync songs from a Google Music library."""

	google_songs = get_google_songs(
		mm, include_filters=include_filters, all_includes=all_includes,
		exclude_filters=exclude_filters, all_excludes=all_excludes
	)

	base_path = template_to_base_path(output, google_songs)
	filepaths = [base_path]

	if include_paths:
		filepaths.extend(include_paths)

	local_songs = get_local_songs(
		filepaths, max_depth=max_depth, include_filters=include_filters,
		all_includes=all_includes, exclude_filters=exclude_filters, all_excludes=all_excludes
	)

	logger.info("Comparing song collections")
	to_download = list(
		gm_utils.compare_item_collections(
			google_songs, local_songs, fields=['artist', 'album', 'title', 'tracknumber'], normalize_values=True
		)
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


def do_sync_up(
	mm, input_paths, *, dry_run=False, delete_on_success=False,
	max_depth=float('inf'), transcode_lossless=True, transcode_lossy=True,
	include_filters=None, all_includes=False, exclude_filters=None, all_excludes=False):
	"""Sync songs to a Google Music library."""

	google_songs = get_google_songs(
		mm, include_filters=include_filters, all_includes=all_includes,
		exclude_filters=exclude_filters, all_excludes=all_excludes
	)

	local_songs = get_local_songs(
		input_paths, max_depth=max_depth, include_filters=include_filters,
		all_includes=all_includes, exclude_filters=exclude_filters, all_excludes=all_excludes
	)

	logger.info("Comparing song collections")
	to_upload = list(
		gm_utils.compare_item_collections(
			local_songs, google_songs, fields=['artist', 'album', 'title', 'tracknumber'], normalize_values=True
		)
	)
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
			mm, to_upload, transcode_lossless=transcode_lossless,
			transcode_lossy=transcode_lossy, delete_on_success=delete_on_success
		)

	mm.logout()
	logger.info("All done!")


def do_upload(
	mm, input_paths, *, dry_run=False, delete_on_success=False,
	max_depth=float('inf'), transcode_lossless=True, transcode_lossy=True,
	include_filters=None, all_includes=False, exclude_filters=None, all_excludes=False):
	"""Upload songs to a Google Music library."""

	to_upload = get_local_songs(
		input_paths, max_depth=max_depth, include_filters=include_filters,
		all_includes=all_includes, exclude_filters=exclude_filters, all_excludes=all_excludes
	)

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
			mm, to_upload, transcode_lossless=transcode_lossless,
			transcode_lossy=transcode_lossy, delete_on_success=delete_on_success
		)

	mm.logout()
	logger.info("All done!")
