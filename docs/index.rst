google-music-scripts
====================

Legacy Commands
---------------

As of version **2.0.0**, google-music-scripts no longer installs the entry points
for the legacy commands (``gmupload, gmdownload, etc.``). Use the ``gms`` command
with subcommands instead.


Configuration
-------------

The configuration file uses the `TOML <https://github.com/toml-lang/toml>`_ format.
It is located in the `user config directory
<https://github.com/ActiveState/appdirs#some-example-output>`_
for your operating system with the app author being **thebigmunch** and app name being
**google-music-scripts**. If the ``-u, --username`` option is given to a command, the
configuration file from subdirectory **username** is used.

google-music-scripts allows configuration of option defaults using the defaults table.
Use option long names (e.g. device-id, uploader-id) as the key.
Defaults can be set for all commands, specific commands, or both with
command-specific defaults taking precedence.

Use **device-id1** for all commands with ``device-id`` argument
and **uploader-id1** for all commands with ``uploader-id`` argument::

	[defaults]
	device-id = "device-id1"
	uploader-id = "uploader-id1"

Use **uploader-id2** for only the **upload** command::

	[defaults.upload]
	uploader-id = "uploader-id2"

Combine them to use **device-id1** for all commands with ``device-id`` argument,
**uploader-id1** for all commands with ``uploader-id`` argument except **upload**,
and **uploader-id2** for the **upload** command::

	[defaults]
	device-id = "device-id1"
	uploader-id = "uploader-id1"

	[defaults.upload]
	uploader-id = "uploader-id2"

Nested commands work the same::

	[defaults.sync.up]
	uploader-id = "uploader-id2"


Filtering
---------

A number of ``gms`` commands allow filtering results based on song metadata (``-f, --filters``).
The syntax is as follows:

	* ``+field[value]`` to include filter condition.
	* ``-field[value]`` to exclude filter condition.
	* Multiple filters can be set in one call: ``-f +field[value] -f +field2[value2]``
	* Multiple conditions can be chained in one filter: ``+field[value]+field2[value2]-field3[value3]``.
	* Values can be valid Python regex.
	* Matching is done case-insensitively.
	* For convenience, a single or first condition can leave off the ``+``, but not ``-``.

E.g:
	* ``gms download -f 'artist[Beck]+album[Guero]-title[E-Pro]'``
	  would download all songs by Beck from the album Guero without E-Pro in the title.
	* ``gms download -f 'artist[Beck]+album[Guero]-title[E-Pro]' -f 'artist[Daft Punk]'``
	  would download all songs by Beck from the album Guero without E-Pro in the title
	  as well as all songs by Daft Punk.


Transcoding - ffmpeg/avconv
---------------------------

Non-MP3 files require ffmpeg or avconv to be in your
PATH to transcode those files to MP3 for upload

Google Music requires an audio sample be sent for most uploads.
ffmpeg/avconv is used for this as well unless the ``--no-sample``
option is given. In this case, an empty audio sample is sent.
If uploading MP3s, ffmpeg/avconv is not required with ``no-sample``.


Aliases
-------

Some commands have shorter aliases to limit the necessary typing in the terminal.

========  =====
Command   Alias
========  =====
delete    del
download  down
upload    up
========  =====


Command-Line Interface
----------------------

Use ``-h, --help`` to display the help for any command.

.. click:: google_music_scripts.cli:gms
	:prog: gms
	:show-nested:
