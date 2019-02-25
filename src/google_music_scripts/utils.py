__all__ = [
	'DictMixin',
	'convert_unix_path',
	'get_album_art_path',
	'template_to_base_path',
]

import os
from collections.abc import MutableMapping
from pathlib import Path

import google_music_utils as gm_utils
import pprintpp

from .constants import UNIX_PATH_RE


class DictMixin(MutableMapping):
	def __getattr__(self, attr):
		try:
			return self.__getitem__(attr)
		except KeyError:
			raise AttributeError(attr) from None

	def __setattr__(self, attr, value):
		self.__setitem__(attr, value)

	def __delattr__(self, attr):
		try:
			return self.__delitem__(attr)
		except KeyError:
			raise AttributeError(attr) from None

	def __getitem__(self, key):
		return self.__dict__[key]

	def __setitem__(self, key, value):
		self.__dict__[key] = value

	def __delitem__(self, key):
		del self.__dict__[key]

	def __missing__(self, key):
		return KeyError(key)

	def __iter__(self):
		return iter(self.__dict__)

	def __len__(self):
		return len(self.__dict__)

	def __repr__(self, repr_dict=None):
		return f"<{self.__class__.__name__} ({pprintpp.pformat(self.__dict__)})>"

	def items(self):
		return self.__dict__.items()

	def keys(self):
		return self.__dict__.keys()

	def values(self):
		return self.__dict__.values()


def convert_unix_path(filepath):
	"""Convert Unix filepath string from Cygwin et al to Windows format.

	Parameters:
		filepath (str): A filepath string.

	Returns:
		str: A filepath string in Windows format.

	Raises:
		FileNotFoundError
		subprocess.CalledProcessError
	"""

	match = UNIX_PATH_RE.match(filepath)
	if not match:
		return Path(filepath.replace('/', r'\\'))

	parts = match.group(3).split('/')
	parts[0] = f"{parts[0].upper()}:/"

	return Path(*parts)


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
