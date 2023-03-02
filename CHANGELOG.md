# Changelog

All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.1] - 2023-03-02

### Fixed
- `eduPersonAffiliation` attribute can be provided as a list,
  not only a string comma-separated.

## [2.1.0] - 2023-01-12

### Added
- Extract IDP's logo from metadata.

## [2.0.0] - 2022-11-28

### Changed
- Retrieve a *list* of roles from `eduPersonAffiliation` attribute

## [1.0.1] - 2022-09-15

### Added
- IDP faker, allow to customize the user attributes.
- IDP faker, allow to override the port used to generate metadata.

## [1.0.0] - 2022-06-24

### Added
- Federation metadata parser.
- "Féderation Éducation-Recherche" SAML authentication backend.
- Django integration: add metadata store with cache
- Django integration: add cache refresh management command.
- Django integration: add common views for SAML FER backend use.
- User's first name/last name/full name cleanup pipeline step.

[unreleased]: https://github.com/openfun/social-edu-federation/compare/v2.1.1...main
[2.1.1]: https://github.com/openfun/social-edu-federation/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/openfun/social-edu-federation/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/openfun/social-edu-federation/compare/v1.0.1...v2.0.0
[1.0.1]: https://github.com/openfun/social-edu-federation/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/openfun/social-edu-federation/compare/8d3b675d043e1e791ca78c3a0b2ba3f44635128e...v1.0.0
