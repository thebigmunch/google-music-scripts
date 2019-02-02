import math
import re
from collections import defaultdict
from pathlib import Path

import audio_metadata
import google_music_utils as gm_utils
from loguru import logger

from .utils import get_album_art_path


def download_songs(mm, songs, template=None):
	logger.success(f"Downloading {len(songs)} songs from Google Music")

	if not template:
		template = Path.cwd()

	songnum = 0
	total = len(songs)
	pad = len(str(total))

	for song in songs:
		songnum += 1

		try:
			audio, _ = mm.download(song)
		except Exception as e:  # TODO: More specific exception.
			logger.log(
				'FAILURE',
				f"({songnum:>{pad}}/{total}) Failed -- {song} | {e}"
			)
		else:
			tags = audio_metadata.loads(audio).tags
			filepath = gm_utils.template_to_filepath(template, tags).with_suffix('.mp3')

			if filepath.is_file():
				filepath.unlink()

			filepath.parent.mkdir(parents=True, exist_ok=True)
			filepath.touch()
			filepath.write_bytes(audio)

			logger.success(
				f"({songnum:>{pad}}/{total}) Downloaded -- {filepath} ({song['id']})"
			)


def filter_songs(songs, filters):
	if filters:
		logger.success("Filtering songs")

		matched_songs = []

		for filter_ in filters:
			include_filters = defaultdict(list)
			exclude_filters = defaultdict(list)

			for oper, field, value in filter_:
				if oper in ['+', '']:
					include_filters[field].append(value)
				elif oper == '-':
					exclude_filters[field].append(value)

			matched = songs

			# Use all if multiple conditions for inclusion.
			i_use_all = (
				(len(include_filters) > 1)
				or any(
					len(v) > 1
					for v in include_filters.values()
				)
			)
			i_any_all = all if i_use_all else any
			matched = gm_utils.include_items(
				matched, any_all=i_any_all, ignore_case=True, **include_filters
			)

			# Use any if multiple conditions for exclusion.
			e_use_all = not (
				(len(exclude_filters) > 1)
				or any(
					len(v) > 1
					for v in exclude_filters.values()
				)
			)
			e_any_all = all if e_use_all else any
			matched = gm_utils.exclude_items(
				matched, any_all=e_any_all, ignore_case=True, **exclude_filters
			)

			for song in matched:
				if song not in matched_songs:
					matched_songs.append(song)
	else:
		matched_songs = songs

	return matched_songs


def get_local_songs(
	filepaths,
	*,
	filters=None,
	max_depth=math.inf,
	exclude_paths=None,
	exclude_regexes=None,
	exclude_globs=None
):
	def _exclude_paths(path, exclude_paths):
		return any(
			str(Path(exclude_path)) in str(path)
			for exclude_path in exclude_paths
		)

	def _exclude_regexes(path, exclude_regexes):
		return any(
			re.search(regex, str(path))
			for regex in exclude_regexes
		)

	local_songs = []
	for filepath in filepaths:
		if (
			_exclude_paths(filepath, exclude_paths)
			or _exclude_regexes(filepath, exclude_regexes)
		):
			continue

		if filepath.is_dir():
			exclude_files = set()
			for exclude_glob in exclude_globs:
				exclude_files |= set(filepath.rglob(exclude_glob))

			for path in filepath.glob('**/*'):
				if (
					path.is_file()
					and path not in exclude_files
					and not _exclude_paths(path, exclude_paths)
					and not _exclude_regexes(path, exclude_regexes)
				):
					with path.open('rb') as f:
						if audio_metadata.determine_format(
							f.read(4), extension=path.suffix
						) is not None:
							local_songs.append(path)
		elif filepath.is_file():
			with filepath.open('rb') as f:
				if audio_metadata.determine_format(
					f.read(4), extension=filepath.suffix
				) is not None:
					local_songs.append(filepath)

	matched_songs = filter_songs(local_songs, filters)

	return matched_songs


def upload_songs(
	mm,
	filepaths,
	album_art=None,
	no_sample=False,
	delete_on_success=False
):
	logger.success(f"Uploading {len(filepaths)} songs to Google Music")

	filenum = 0
	total = len(filepaths)
	pad = len(str(total))

	for song in filepaths:
		filenum += 1

		album_art_path = get_album_art_path(song, album_art)

		result = mm.upload(
			song,
			album_art_path=album_art_path,
			no_sample=no_sample
		)

		if result['reason'] == 'Uploaded':
			logger.success(
				f"({filenum:>{pad}}/{total}) Uploaded -- {result['filepath']} ({result['song_id']})"
			)
		elif result['reason'] == 'Matched':
			logger.success(
				f"({filenum:>{pad}}/{total}) Matched -- {result['filepath']} ({result['song_id']})"
			)
		else:
			if 'song_id' in result:
				logger.success(
					f"({filenum:>{pad}}/{total}) Already exists -- {result['filepath']} ({result['song_id']})"
				)
			else:
				logger.log(
					'FAILURE'
					f"({filenum:>{pad}}/{total}) Failed -- {result['filepath']} | {result['reason']}"
				)

		if delete_on_success and 'song_id' in result:
			try:
				result['filepath'].unlink()
			except Exception:
				logger.warning(
					f"Failed to remove {result['filepath']} after successful upload"
				)
