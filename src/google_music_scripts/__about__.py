__all__ = [
	'__author__',
	'__author_email__',
	'__copyright__',
	'__license__',
	'__summary__',
	'__title__',
	'__url__',
	'__version__',
	'__version_info__',
]

try:
	from importlib.metadata import metadata
except ImportError:
	from importlib_metadata import metadata

meta = metadata('google-music-scripts')

__title__ = meta['Name']
__summary__ = meta['Summary']
__url__ = meta['Home-page']

__version__ = meta['Version']
__version_info__ = tuple(int(i) for i in __version__.split('.') if i.isdigit())

__author__ = meta['Author']
__author_email__ = meta['Author-email']

__license__ = meta['License']
__copyright__ = f'2018-2020 {__author__} <{__author_email__}>'
