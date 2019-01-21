#!/usr/bin/env python3

import sys

from . import cli

if __name__ == '__main__':
	try:
		cli.run()
	except KeyboardInterrupt:
		sys.exit("Interrupted by user.")
