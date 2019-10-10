import math
from collections import defaultdict
from pathlib import Path

import audio_metadata
import google_music_utils as gm_utils
import pendulum
from loguru import logger
from tbm_utils import get_filepaths

from .utils import get_album_art_path


def download_songs(mm, songs, template=None):
	if not songs:
		logger.log('NORMAL', "No songs to download")
	else:
		logger.log('NORMAL', "Downloading songs from Google Music")

		if not template:
			template = Path.cwd()

		songnum = 0
		total = len(songs)
		pad = len(str(total))

		for song in songs:
			songnum += 1

			logger.trace(
				"Downloading -- {} - {} - {} ({})",
				song.get('title', "<title>"),
				song.get('artist', "<artist>"),
				song.get('album', "<album>"),
				song['id']
			)

			try:
				audio, _ = mm.download(song)
			except Exception as e:  # TODO: More specific exception.
				logger.log(
					'ACTION_FAILURE',
					"({:>{}}/{}) Failed -- {} | {}",
					songnum,
					pad,
					total,
					song,
					e
				)
			else:
				tags = audio_metadata.loads(audio).tags
				filepath = gm_utils.template_to_filepath(template, tags).with_suffix('.mp3')
				if filepath.is_file():
					filepath.unlink()

				filepath.parent.mkdir(parents=True, exist_ok=True)
				filepath.touch()
				filepath.write_bytes(audio)

				logger.log(
					'ACTION_SUCCESS',
					"({:>{}}/{}) Downloaded -- {} ({})",
					songnum,
					pad,
					total,
					filepath,
					song['id']
				)


def filter_google_dates(
	songs,
	*,
	created_in=None,
	created_on=None,
	created_before=None,
	created_after=None,
	modified_in=None,
	modified_on=None,
	modified_before=None,
	modified_after=None
):
	matched_songs = songs

	def _dt_from_gm_timestamp(gm_timestamp):
		return pendulum.from_timestamp(gm_utils.from_gm_timestamp(gm_timestamp))

	def _match_created_date(songs, period):
		return (
			song
			for song in songs
			if _dt_from_gm_timestamp(song['creationTimestamp']) in period
		)

	def _match_modified_date(songs, period):
		return (
			song
			for song in songs
			if _dt_from_gm_timestamp(song['lastModifiedTimestamp']) in period
		)

	for period in [
		created_in,
		created_on,
		created_before,
		created_after,
	]:
		if period is not None:
			matched_songs = _match_created_date(matched_songs, period)

	for period in [
		modified_in,
		modified_on,
		modified_before,
		modified_after,
	]:
		if period is not None:
			matched_songs = _match_modified_date(matched_songs, period)

	return list(matched_songs)


def filter_metadata(songs, filters):
	if filters:
		logger.log('NORMAL', "Filtering songs by metadata")
		matched_songs = []

		for filter_ in filters:
			include_filters = defaultdict(list)
			exclude_filters = defaultdict(list)

			for condition in filter_:
				if condition.oper == '+':
					include_filters[condition.field].append(condition.pattern)
				elif condition.oper == '-':
					exclude_filters[condition.field].append(condition.pattern)

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

		logger.info("Filtered {} songs by metadata", len(songs) - len(matched_songs))
	else:
		matched_songs = songs

	return matched_songs


def get_google_songs(client, *, filters=None):
	logger.log('NORMAL', "Loading Google songs with {}", client.__class__.__name__)

	google_songs = client.songs()

	logger.info(
		"Found {} Google songs with {}", len(google_songs), client.__class__.__name__
	)

	matched_songs = filter_metadata(google_songs, filters)

	return matched_songs


def get_local_songs(
	paths,
	*,
	filters=None,
	max_depth=math.inf,
	exclude_paths=None,
	exclude_regexes=None,
	exclude_globs=None
):
	logger.log('NORMAL', "Loading local songs")

	local_songs = [
		filepath
		for filepath in get_filepaths(
			paths,
			max_depth=max_depth,
			exclude_paths=exclude_paths,
			exclude_regexes=exclude_regexes,
			exclude_globs=exclude_globs
		)
		if audio_metadata.determine_format(filepath) is not None
	]

	logger.info("Found {} local songs", len(local_songs))

	matched_songs = filter_metadata(local_songs, filters)

	return matched_songs


def upload_songs(
	mm,
	filepaths,
	*,
	album_art=None,
	no_sample=False,
	delete_on_success=False
):
	if not filepaths:
		logger.log('NORMAL', "No songs to upload")
	else:
		logger.log('NORMAL', "Uploading songs")

		filenum = 0
		total = len(filepaths)
		pad = len(str(total))

		for song in filepaths:
			filenum += 1

			logger.trace(
				"Uploading -- {}",
				song
			)

			album_art_path = get_album_art_path(song, album_art)

			result = mm.upload(
				song,
				album_art_path=album_art_path,
				no_sample=no_sample
			)

			if logger._min_level <= 15:
				if result['reason'] == 'Uploaded':
					logger.log(
						'ACTION_SUCCESS',
						"({:>{}}/{}) Uploaded -- {} ({})",
						filenum,
						pad,
						total,
						result['filepath'],
						result['song_id']
					)
				elif result['reason'] == 'Matched':
					logger.log(
						'ACTION_SUCCESS',
						"({:>{}}/{}) Matched -- {} ({})",
						filenum,
						pad,
						total,
						result['filepath'],
						result['song_id']
					)
				else:
					if 'song_id' in result:
						logger.log(
							'ACTION_SUCCESS',
							"({:>{}}/{}) Already exists -- {} ({})",
							filenum,
							pad,
							total,
							result['filepath'],
							result['song_id']
						)
					else:
						logger.log(
							'ACTION_FAILURE',
							"({:>{}}/{}) Failed -- {} | {}",
							filenum,
							pad,
							total,
							result['filepath'],
							result['reason']
						)

			if delete_on_success and 'song_id' in result:
				try:
					result['filepath'].unlink()
				except Exception:
					logger.warning(
						"Failed to remove {} after successful upload", result['filepath']
					)
