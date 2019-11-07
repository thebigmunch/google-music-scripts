import sys
import time
from pathlib import Path

import appdirs
from loguru import logger
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile

from .__about__ import __author__, __title__

CONFIG_BASE_PATH = Path(appdirs.user_config_dir(__title__, __author__))

LOG_BASE_PATH = Path(appdirs.user_data_dir(__title__, __author__))
LOG_FORMAT = '<lvl>[{time:YYYY-MM-DD HH:mm:ss}]</lvl> {message}'
LOG_DEBUG_FORMAT = LOG_FORMAT

logger.level('NORMAL', no=25, color="<green>")
logger.level('INFO', no=20, color="<green><bold>")
logger.level('ACTION_FAILURE', no=16, color="<red>")
logger.level('ACTION_SUCCESS', no=15, color="<cyan>")

VERBOSITY_LOG_LEVELS = {
	0: 50,
	1: 40,
	2: 30,
	3: 25,
	4: 20,
	5: 16,
	6: 15,
	7: 10,
	8: 5,
}


def read_config_file(username=None):
	config_path = CONFIG_BASE_PATH / (username or '') / 'google-music-scripts.toml'
	config_file = TOMLFile(config_path)

	try:
		config = config_file.read()
	except FileNotFoundError:
		config = TOMLDocument()

	write_config_file(config, username=username)

	return config


def write_config_file(config, username=None):
	config_path = CONFIG_BASE_PATH / (username or '') / 'google-music-scripts.toml'
	config_path.parent.mkdir(parents=True, exist_ok=True)
	config_path.touch()

	config_file = TOMLFile(config_path)
	config_file.write(config)


def ensure_log_dir(username=None):
	log_dir = LOG_BASE_PATH / (username or '') / 'logs'
	log_dir.mkdir(parents=True, exist_ok=True)

	return log_dir


def configure_logging(
	modifier=0,
	*,
	username=None,
	debug=False,
	log_to_stdout=True,
	log_to_file=False
):
	logger.remove()

	if debug:
		logger.enable('audio_metadata')
		logger.enable('google_music')
		logger.enable('google_music-proto')
		logger.enable('google_music_utils')

	verbosity = 3 + modifier

	if verbosity < 0:
		verbosity = 0
	elif verbosity > 7:
		verbosity = 7

	log_level = VERBOSITY_LOG_LEVELS[verbosity]

	if log_to_stdout:
		logger.add(
			sys.stdout,
			level=log_level,
			format=LOG_FORMAT,
			backtrace=False
		)

	if log_to_file:
		log_dir = ensure_log_dir(username=username)
		log_file = (log_dir / time.strftime('%Y-%m-%d_%H-%M-%S')).with_suffix('.log')

		logger.success("Logging to file: {}", log_file)

		logger.add(
			log_file,
			level=log_level,
			format=LOG_FORMAT,
			backtrace=False,
			encoding='utf8',
			newline='\n'
		)
