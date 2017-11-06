import os
import shutil
import tempfile

import audio_metadata
import google_music_utils as gm_utils
from logzero import logger

from .utils import get_supported_filepaths


def download_songs(mm, songs, template=None):
	logger.info(f"Downloading {len(songs)} songs from Google Music")

	if not template:
		template = os.getcwd()

	songnum = 0
	total = len(songs)
	pad = len(str(total))

	for song in songs:
		songnum += 1

		try:
			_, audio = mm.download(song)
		except Exception as e:  # TODO: More specific exception.
			logger.info(
				f"({songnum:>{pad}}/{total}) Failed -- {song} | {e}",
				extra={'success': False}
			)
		else:
			temp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
			temp.write(audio)

			tags = audio_metadata.load(temp.name)
			filepath = gm_utils.template_to_filepath(template, tags) + '.mp3'
			dirname = os.path.dirname(filepath)

			if dirname:
				try:
					os.makedirs(dirname)
				except OSError:
					if not os.path.isdir(dirname):
						raise

			temp.close()
			shutil.move(temp.name, filepath)

			logger.info(
				f"({songnum:>{pad}}/{total}) Downloaded -- {filepath} ({song['id']})",
				extra={'success': True}
			)


def _filter_songs(songs, include_filters=None, exclude_filters=None, all_includes=False, all_excludes=False):
	if include_filters or exclude_filters:
		logger.info("Filtering songs")

	matched_songs = None

	if include_filters:
		if all_includes:
			matched_songs = gm_utils.include_items(songs, any_all=all, ignore_case=True, **include_filters)
		else:
			matched_songs = gm_utils.include_items(songs, any_all=any, ignore_case=True, **include_filters)

	if exclude_filters:
		if all_excludes:
			matched_songs = gm_utils.exclude_items(
				matched_songs, any_all=all, ignore_case=True, **exclude_filters
			)
		else:
			matched_songs = gm_utils.exclude_items(
				songs, any_all=any, ignore_case=True, **exclude_filters
			)

	matched_songs = list(matched_songs) if matched_songs else songs

	return matched_songs


def get_google_songs(mm, include_filters=None, all_includes=False, exclude_filters=None, all_excludes=False):
	logger.info("Loading Google songs")

	google_songs = mm.songs()

	matched_songs = _filter_songs(
		google_songs, include_filters=include_filters, all_includes=all_includes,
		exclude_filters=exclude_filters, all_excludes=all_excludes
	)

	return matched_songs


def get_local_songs(
	filepaths, *, include_filters=None, all_includes=False,
	exclude_filters=None, all_excludes=False, max_depth=float('inf')):

	logger.info("Loading local songs")

	local_songs = get_supported_filepaths(filepaths, max_depth=max_depth)

	matched_songs = _filter_songs(
		local_songs, include_filters=include_filters, all_includes=all_includes,
		exclude_filters=exclude_filters, all_excludes=all_excludes
	)

	return matched_songs


def upload_songs(
	mm, filepaths, include_album_art=True, transcode_lossless=True,
	transcode_lossy=True, transcode_quality='320k', delete_on_success=False
):
	logger.info(f"Uploading {len(filepaths)} songs to Google Music")

	filenum = 0
	total = len(filepaths)
	pad = len(str(total))

	for song in filepaths:
		filenum += 1

		result = mm.upload(
			song, transcode_lossless=transcode_lossless, transcode_lossy=transcode_lossy
		)

		if result['reason'] == 'Uploaded':
			logger.info(
				f"({filenum:>{pad}}/{total}) Uploaded -- {result['filepath']} ({result['song_id']})",
				extra={'success': True}
			)
		elif result['reason'] == 'Matched':
			logger.info(
				f"({filenum:>{pad}}/{total}) Matched -- {result['filepath']} ({result['song_id']})",
				extra={'success': True}
			)
		else:
			if 'song_id' in result:
				logger.info(
					f"({filenum:>{pad}}/{total}) Already exists -- {result['filepath']} ({result['song_id']})",
					extra={'success': True}
				)
			else:
				logger.info(
					f"({filenum:>{pad}}/{total}) Failed -- {result['filepath']} | {result['reason']}",
					extra={'success': False}
				)

		if delete_on_success and 'song_id' in result:
			try:
				os.remove(result['filepath'])
			except (OSError):
				logger.warning(f"Failed to remove {result['filepath']} after successful upload")
