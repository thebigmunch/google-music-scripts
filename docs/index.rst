google-music-scripts
====================

Configuration
-------------

The configuration file uses the `TOML <https://github.com/toml-lang/toml>`_ format.
It is located in the `user config directory
<https://github.com/ActiveState/appdirs#some-example-output>`_
for your operating system with the app author being **thebigmunch** and app name being
**google-music-scripts**.

google-music-scripts allows configuration of default option using the defaults table.
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


Command-Line Interface
----------------------

Use ``-h, --help`` to display the help for any command.

.. click:: google_music_scripts.cli:gms
	:prog: gms
	:show-nested:
