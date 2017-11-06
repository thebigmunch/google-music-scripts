import logging
import os
import time

import appdirs
import logzero

from .__about__ import __author__, __title__

LOG_FILEPATH = os.path.join(appdirs.user_data_dir(__title__, __author__), 'logs')
LOG_FORMAT = '%(color)s[%(asctime)s]%(end_color)s %(message)s'
LOG_FILE_FORMAT = '[%(asctime)s] %(message)s'

LOGZERO_COLORS = logzero.LogFormatter.DEFAULT_COLORS
LOG_COLORS = LOGZERO_COLORS.copy()
# LOG_COLORS.update({25: LOGZERO_COLORS[20], 15: LOGZERO_COLORS[10]})

VERBOSITY_LOG_LEVELS = {
	0: logging.CRITICAL,
	1: logging.ERROR,
	2: logging.WARNING,
	3: logging.INFO,
	4: logging.DEBUG
}


def ensure_log_filepath():
	try:
		os.makedirs(LOG_FILEPATH)
	except OSError:
		if not os.path.isdir(LOG_FILEPATH):
			raise


# TODO: For now, copying most of logzero's LogFormatter to hack in a different color
#       for upload/download success without changing the log level.
class ResultFormatter(logzero.LogFormatter):
	def format(self, record):
		try:
			message = record.getMessage()
			assert isinstance(message, logzero.basestring_type)  # guaranteed by logging
			# Encoding notes:  The logging module prefers to work with character
			# strings, but only enforces that log messages are instances of
			# basestring.  In python 2, non-ascii bytestrings will make
			# their way through the logging framework until they blow up with
			# an unhelpful decoding error (with this formatter it happens
			# when we attach the prefix, but there are other opportunities for
			# exceptions further along in the framework).
			#
			# If a byte string makes it this far, convert it to unicode to
			# ensure it will make it out to the logs.  Use repr() as a fallback
			# to ensure that all byte strings can be converted successfully,
			# but don't do it by default so we don't add extra quotes to ascii
			# bytestrings.  This is a bit of a hacky place to do this, but
			# it's worth it since the encoding errors that would otherwise
			# result are so useless (and tornado is fond of using utf8-encoded
			# byte strings whereever possible).
			record.message = logzero._safe_unicode(message)
		except Exception as e:
			record.message = "Bad message (%r): %r" % (e, record.__dict__)

		record.asctime = self.formatTime(record, self.datefmt)

		if record.levelno in self._colors:
			record.color = self._colors[record.levelno]
			record.end_color = self._normal
		else:
			record.color = record.end_color = ''

		if record.__dict__.get('success', True) is False:
			record.color = self._colors[30]

		formatted = self._fmt % record.__dict__

		if record.exc_info:
			if not record.exc_text:
				record.exc_text = self.formatException(record.exc_info)
		if record.exc_text:
			# exc_text contains multiple lines.  We need to _safe_unicode
			# each line separately so that non-utf8 bytes don't cause
			# all the newlines to turn into '\n'.
			lines = [formatted.rstrip()]
			lines.extend(
				logzero._safe_unicode(ln) for ln in record.exc_text.split('\n'))
			formatted = '\n'.join(lines)
		return formatted.replace("\n", "\n    ")


def configure_logging(modifier=0, log_to_file=False):
	stream_formatter = ResultFormatter(fmt=LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S', colors=LOG_COLORS)
	logzero.setup_default_logger(formatter=stream_formatter)

	verbosity = 3 + modifier

	if verbosity < 0:
		verbosity = 0
	elif verbosity > 4:
		verbosity = 4

	log_level = VERBOSITY_LOG_LEVELS[verbosity]
	logzero.loglevel(log_level)

	if log_to_file:
		ensure_log_filepath()
		log_file = os.path.join(LOG_FILEPATH, time.strftime('%Y-%m-%d_%H-%M-%S') + '.log')
		file_formatter = logzero.LogFormatter(fmt=LOG_FILE_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
		logzero.logfile(log_file, formatter=file_formatter)
