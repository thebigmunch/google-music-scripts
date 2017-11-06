__all__ = [
	'CHARACTER_REPLACEMENTS', 'SUPPORTED_PLAYLIST_FORMATS', 'SUPPORTED_SONG_FORMATS',
	'TEMPLATE_PATTERNS', 'UNIX_PATH_RE'
]

import re

CHARACTER_REPLACEMENTS = {
	'\\': '-', '/': ',', ':': '-', '*': 'x', '<': '[',
	'>': ']', '|': '!', '?': '', '"': "''"
}
"""dict: Mapping of invalid filepath characters with appropriate replacements."""

TEMPLATE_PATTERNS = {
	'%artist%': 'artist', '%title%': 'title', '%track%': 'tracknumber',
	'%track2%': 'tracknumber', '%album%': 'album', '%date%': 'date',
	'%genre%': 'genre', '%albumartist%': 'albumartist', '%disc%': 'discnumber'
}
"""dict: Mapping of template patterns to their mutagen 'easy' field name."""

UNIX_PATH_RE = re.compile("^(?:/[^/]+)*/?$")
"""Regex pattern matching UNIX-style filepaths."""
