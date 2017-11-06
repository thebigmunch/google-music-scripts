__all__ = [
	'convert_cygwin_path', 'delete_file', 'get_supported_filepaths',
	'template_to_base_path', 'walk_depth'
]

import os
import subprocess

import audio_metadata
import google_music_utils as gm_utils
from logzero import logger


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
			["cygpath", "-aw", filepath], check=True, stdout=subprocess.PIPE, universal_newlines=True
		).stdout.strip()
	except (FileNotFoundError, subprocess.CalledProcessError):
		logger.exception("Call to cygpath failed.")
		raise

	return win_path


def delete_file(filepath):
	try:
		os.remove(filepath)
	except (OSError, PermissionError):
		logger.warning(f"Failed to remove file: {filepath}.")


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

	for path in filepaths:
		if os.path.isdir(path):
			for root, __, files in walk_depth(path, max_depth):
				for file_ in files:
					filepath = os.path.join(root, file_)

					with open(filepath, 'rb') as f:
						if audio_metadata.determine_format(f.read(4), extension=os.path.splitext(filepath)[1]) is not None:
							supported_filepaths.append(filepath)
		elif os.path.isfile(path):
			with open(path, 'rb') as f:
				if audio_metadata.determine_format(f.read(4), extension=os.path.splitext(path)[1]) is not None:
					supported_filepaths.append(path)

	return supported_filepaths


def template_to_base_path(template, google_songs):
	"""Get base output path for a list of songs for download."""

	if template == os.getcwd() or template == '%suggested%':
		base_path = os.getcwd()
	else:
		song_paths = [os.path.abspath(gm_utils.template_to_filepath(template, song)) for song in google_songs]
		base_path = os.path.commonpath(song_paths)

	return base_path


def walk_depth(path, max_depth=float('inf')):
	"""Walk a directory tree with configurable depth.

	Parameters:
		path (str): A directory path to walk.

		max_depth (int): The depth in the directory tree to walk.
			A depth of '0' limits the walk to the top directory.
			Default: No limit.

	Yields:
		tuple: A 3-tuple ``(root, dirs, files)`` same as :func:`os.walk`.
	"""

	path = os.path.abspath(path)

	start_level = path.count(os.path.sep)

	for dir_entry in os.walk(path):
		root, dirs, _ = dir_entry
		level = root.count(os.path.sep) - start_level

		yield dir_entry

		if level >= max_depth:
			dirs[:] = []
