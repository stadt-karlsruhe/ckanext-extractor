# Change Log for ckanext-extractor

The format of this file is based on [Keep a Changelog], and this
project uses [Semantic Versioning].


## [Unreleased]

### Changed

- Don't validate package dicts when re-indexing them (contributed by
  [@wardi](https://github.com/stadt-karlsruhe/ckanext-extractor/pull/6))


## [0.3.0] (2017-05-10)

### Added

- `IExtractorRequest` interface for adjusting the download request (contributed
  by [@metaodi](https://github.com/stadt-karlsruhe/ckanext-extractor/pull/5))

### Changed

- Moved change log to a separate file

### Fixed

- Improved handling of errors when downloading resource data (reported by
  [@phisqb](https://github.com/stadt-karlsruhe/ckanext-extractor/issues/4))


## [0.2.0] (2016-10-19)

### Added

- `IExtractorPostprocessor` interface for postprocessing extraction results

### Fixed

- Fixed logging problems in `paster` commands


## 0.1.0 (2016-06-14)

- First release


[Keep a Changelog]: http://keepachangelog.com
[Semantic Versioning]: http://semver.org/

[Unreleased]: https://github.com/stadt-karlsruhe/ckanext-extractor/compare/v0.3.0...master
[0.3.0]: https://github.com/stadt-karlsruhe/ckanext-extractor/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/stadt-karlsruhe/ckanext-extractor/compare/v0.1.0...v0.2.0

