__all__ = [
	'get_album_art_path',
	'template_to_base_path',
]

import os
from pathlib import Path

import google_music_utils as gm_utils


def get_album_art_path(song, album_art_paths):
	album_art_path = None
	if album_art_paths:
		for path in album_art_paths:
			if (
				path.is_absolute()
				and path.isfile()
			):
				album_art_path = path
				break
			else:
				path = song.parent / path
				if path.is_file():
					album_art_path = path
					break

	return album_art_path


def template_to_base_path(template, google_songs):
	"""Get base output path for a list of songs for download."""

	path = Path(template)

	if (
		path == Path.cwd()
		or path == Path('%suggested%')
	):
		base_path = Path.cwd()
	else:
		song_paths = [
			gm_utils.template_to_filepath(template, song)
			for song in google_songs
		]
		if song_paths:
			base_path = Path(os.path.commonpath(song_paths))
		else:
			base_path = Path.cwd()

	return base_path.resolve()
