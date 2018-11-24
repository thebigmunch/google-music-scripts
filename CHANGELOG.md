# Change Log

Notable changes to this project based on the [Keep a Changelog](https://keepachangelog.com) format.
This project adheres to [Semantic Versioning](https://semver.org).


## [Unreleased](https://github.com/thebigmunch/google-music-scripts/tree/master)

[Commits](https://github.com/thebigmunch/google-music-scripts/compare/1.1.1...master)

### Added

* Configuration file.
* Ability to set option defaults in configuration file.

### Changed

* Filtering is now done through one option ``-f, --filters`` with different syntax and semantics.
	* ``+field[value]`` is the new syntax for an include filter condition.
	* ``-field[value]`` is the new syntax for an exclude filter condition.
	* Multiple filters can be set in one call. 
	* Multiple conditions can be chained in one filter.
	* Values can still be valid Python regex.
	* Matching is still done case-insensitively.

  E.g:
	* ``gms download -f 'artist[Beck]+album[Guero]-title[E-Pro]'``
	  would download all songs by Beck from the album Guero without E-Pro in the title.
	* ``gms download -f 'artist[Beck]+album[Guero]-title[E-Pro]' -f 'artist[Daft Punk]'``
	  would download all songs by Beck from the album Guero without E-Pro in the title
	  as well as all songs by Daft Punk.

### Removed

* Legacy command entry points (gmupload, gmdownload, etc).
  Use the ``gms`` subcommands instead.



## [1.1.1](https://github.com/thebigmunch/google-music-scripts/releases/tag/1.1.1) (2018-11-13)

[Commits](https://github.com/thebigmunch/google-music-scripts/compare/1.1.0...1.1.1)

### Fixed

* Update required google-music version.


## [1.1.0](https://github.com/thebigmunch/google-music-scripts/releases/tag/1.1.0) (2018-11-13)

[Commits](https://github.com/thebigmunch/google-music-scripts/compare/1.0.1...1.1.0)

### Fixed

* Fixed various issues related to porting code to new framework.

### Changed

* Refactored package structure.


## [1.0.1](https://github.com/thebigmunch/google-music-scripts/releases/tag/1.0.1) (2018-10-28)

[Commits](https://github.com/thebigmunch/google-music-scripts/compare/1.0.0...1.0.1)

### Fixed

* Fix incorrect order of variable assignment.


## [1.0.0](https://github.com/thebigmunch/google-music-scripts/releases/tag/1.0.0) (2018-10-19)

[Commits](https://github.com/thebigmunch/google-music-scripts/commit/e14718c875434922b451d0598da021c6617afdb0)

* Initial release.
