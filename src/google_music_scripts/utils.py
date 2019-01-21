__all__ = [
	'DictMixin',
	'convert_cygwin_path',
	'get_album_art_path',
	'get_supported_filepaths',
	'template_to_base_path'
]

import os
import subprocess
from collections.abc import MutableMapping
from pathlib import Path

import audio_metadata
import google_music_utils as gm_utils
import pprintpp
from logzero import logger


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
		del(self.__dict__[key])

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


def convert_cygwin_path(filepath):
	"""Convert Unix filepath string from Cygwin to Windows format.

	Parameters:
		filepath (str): A filepath string.

	Returns:
		str: A filepath string in Windows format.

	Raises:
		FileNotFoundError
		subprocess.CalledProcessError
	"""

	try:
		win_path = subprocess.run(
			["cygpath", "-aw", filepath],
			check=True,
			stdout=subprocess.PIPE,
			universal_newlines=True
		).stdout.strip()
	except (FileNotFoundError, subprocess.CalledProcessError):
		logger.exception("Call to cygpath failed.")
		raise

	return Path(win_path)


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


def get_supported_filepaths(filepaths, max_depth=float('inf')):
	"""Get supported audio files from given filepaths.

	Parameters:
		filepaths (list): Filepath(s) to check.

		max_depth (int): The depth in the directory tree to walk.
			A depth of '0' limits the walk to the top directory.
			Default: No limit.

	Returns:
		list: A list of filepaths with supported extensions.
	"""

	supported_filepaths = []

	for filepath in filepaths:
		path = Path(filepath)

		if path.is_dir():
			for p in path.glob('**/*'):
				if p.is_file():
					with p.open('rb') as f:
						if audio_metadata.determine_format(
							f.read(4), extension=p.suffix
						) is not None:
							supported_filepaths.append(p)
		elif path.is_file():
			with path.open('rb') as f:
				if audio_metadata.determine_format(
					f.read(4), extension=path.suffix
				) is not None:
					supported_filepaths.append(path)

	return supported_filepaths


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
		base_path = Path(os.path.commonpath(song_paths))

	return base_path.resolve()
