google-music-scripts
====================

Legacy Commands
---------------

As of version **2.0.0**, google-music-scripts no longer installs the entry points
for the legacy commands (``gmupload, gmdownload, etc.``). Use the ``gms`` command
with subcommands instead.

As of version **4.0.0**, the ``sync`` commands are removed in favor of syncing
options for the ``download`` and ``upload`` commands. These allow syncing based
on the hash of the audio data ('clientId' on Google Music) and/or the metadata.
Both sync options are enabled by default. This adds a dependency on the mobile
API, so users will have to authenticate the Mobile Client on first run if they
haven't previously done so through the Mobile API-based commands.


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


Filtering
---------

Metadata
^^^^^^^^

Some ``gms`` commands allow filtering results based on song metadata (``-f, --filter``).
The syntax is as follows:

	* ``+field[value]`` to include filter condition.
	* ``-field[value]`` to exclude filter condition.
	* Multiple filters can be set in one call: ``-f +field[value] -f +field2[value2]``
	* Multiple conditions can be chained in one filter: ``+field[value]+field2[value2]-field3[value3]``.
	* Values can be valid Python regex.
	* Matching is done case-insensitively.
	* For convenience, a single or first condition can leave off the ``+``, but not ``-``.

Examples:
	* ``gms download -f 'artist[Beck]+album[Guero]-title[E-Pro]'``
	  would download all songs by Beck from the album Guero without E-Pro in the title.
	* ``gms download -f 'artist[Beck]+album[Guero]-title[E-Pro]' -f 'artist[Daft Punk]'``
	  would download all songs by Beck from the album Guero without E-Pro in the title
	  as well as all songs by Daft Punk.

Dates
^^^^^

Some ``gms`` commands allow filtering results based on creation/modification times.
The following options are available:

	* ``--created-in``/``--modified-in`` to include results from year or year/month.
	* ``--created-on``/``--modified-on`` to include results from date.
	* ``--created-before``/``--modified-before`` to include results from before datetime.
	* ``--created-after``/``--modified-after`` to include results from after datetime.


The format supported follows ISO 8061 with the abilility to use partial datetimes.
A regex test is found
`here <http://www.pyregex.com/?id=eyJyZWdleCI6Iig%2FUDx5ZWFyPlxcZHs0fSlbLVxcc10%2FKD9QPG1vbnRoPlxcZHsxLDJ9KT9bLVxcc10%2FKD9QPGRheT5cXGR7MSwyfSk%2FW1RcXHNdPyg%2FUDxob3VyPlxcZHsxLDJ9KT9bOlxcc10%2FKD9QPG1pbnV0ZT5cXGR7MSwyfSk%2FWzpcXHNdPyg%2FUDxzZWNvbmQ%2BXFxkezEsMn0pPyg%2FUDx0el9vcGVyPlsrXFwtXFxzXSk%2FKD9QPHR6X2hvdXI%2BXFxkezEsMn0pP1s6XFxzXT8oP1A8dHpfbWludXRlPlxcZHsxLDJ9KT8iLCJmbGFncyI6MCwibWF0Y2hfdHlwZSI6Im1hdGNoIiwidGVzdF9zdHJpbmciOiIyMDE5LTAyLTA0VDEyOjU5OjU5LTA1MDAifQ%3D%3D>`_.

Examples:
	* ``gms upload --created-in 2019`` would upload files created in 2019.
	* ``gms upload --created-in 2019-02`` would upload files created in February 2019.
	* ``gms download --created-on 2019-02-04`` would download songs uploaded to
	  Google Music on February 4th, 2019.
	* ``gms download --created-before 2019`` would download songs uploaded to
	  Google Music before 2019 (i.e. 2018 or earlier).
	* ``gms download --created-after '2019-02-04 12:00:00`` would download songs
	  uploaded to Google Music after 12 noon (UTC) on February 4th, 2019.
	* ``gms delete --created-after '2019-02-04 12:00:00-05:00`` would delete
	  songs uploaded to Google Music after 12 noon (GMT-5:00) on February 4th, 2019.


Output Templates
----------------

The ``download`` command supports defining an output template.
An output template uses patters, as described below, to use
values from metadata fields in the output.
If a field for a pattern does not exist in the song,
the pattern remains in the download filepath.

+----------------+-----------------+
| Pattern        | Fields          |
+================+=================+
| %album%        | - album         |
+----------------+-----------------+
| %albumartist%  | - albumartist   |
|                | - album_artist  |
|                | - albumArtist   |
+----------------+-----------------+
| %artist%       | - artist        |
+----------------+-----------------+
| %date%         | - date          |
+----------------+-----------------+
| %disc%         | - discnumber    |
|                | - disc_number   |
|                | - discNumber    |
+----------------+-----------------+
| %disc2%        | - discnumber    |
|                | - disc_number   |
|                | - discNumber    |
|                |                 |
|                | (zero-padded)   |
+----------------+-----------------+
| %discnumber%   | - discnumber    |
|                | - disc_number   |
|                | - discNumber    |
+----------------+-----------------+
| %discnumber2%  | - discnumber    |
|                | - disc_number   |
|                | - discNumber    |
|                |                 |
|                | (zero-padded)   |
+----------------+-----------------+
| %genre%        | - genre         |
+----------------+-----------------+
| %title%        | - title         |
+----------------+-----------------+
| %track%        | - tracknumber   |
|                | - track_number  |
|                | - trackNumber   |
+----------------+-----------------+
| %track2%       | - tracknumber   |
|                | - track_number  |
|                | - trackNumber   |
|                |                 |
|                | (zero-padded)   |
+----------------+-----------------+
| %tracknumber%  | - tracknumber   |
|                | - track_number  |
|                | - trackNumber   |
+----------------+-----------------+
| %tracknumber2% | - tracknumber   |
|                | - track_number  |
|                | - trackNumber   |
|                |                 |
|                | (zero-padded)   |
+----------------+-----------------+

Examples:
	* ``%track% - %title%``
	* ``%artist%/%album%/%track2% - %title%``


Transcoding - ffmpeg/avconv
---------------------------

Non-MP3 files require ffmpeg or avconv to be in your
PATH to transcode them to MP3 for upload

Google Music requires an audio sample be sent for most uploads.
ffmpeg/avconv is used for this as well unless the ``--no-sample``
option is given. In this case, an empty audio sample is sent.
If uploading MP3s, ffmpeg/avconv is not required with ``--no-sample``.


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

.. argparse::
	:module: google_music_scripts.cli
	:func: gms
	:prog: gms
