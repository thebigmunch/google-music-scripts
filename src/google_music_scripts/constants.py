__all__ = [
	'CHARACTER_REPLACEMENTS',
	'TEMPLATE_PATTERNS',
	'UNIX_PATH_RE',
]

import re

from google_music_utils import CHARACTER_REPLACEMENTS, TEMPLATE_PATTERNS

UNIX_PATH_RE = re.compile(r'(/(cygdrive/)?)(.*)')
"""Regex pattern matching UNIX-style filepaths."""
