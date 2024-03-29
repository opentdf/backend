# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]: https://github.com/opentdf/backend/compare/main...HEAD

## 1.2.1 - 2023-3-10
- NO-REF
  - Update certifi to address vulnerability
- PLAT-2291
  - README updates, spelling, remove old references
- PLAT-2217
  - Rename KEYCLOAK_URL to OIDC_SERVER_URL
- NO-REF
  - Simplify rewrap modules, Make it more clear that we expect the wrapping type to be a JWE crypto name
- PLAT-2157
  - add post-command and error hooks around rewrap_v2
- NO-REF
  - Update README and CHANGELOG formatting
- NO-REF
  - Remove private key access from WrappedKey 
- PLAT-2237
  - Use local dist of swagger-ui to fix vulnerabilities
- NO-REF
  - Add validation of DPoP (when cnf is present in access token) to KAS upsert and rewrap endpoints
- NO-REF
  - Reverse proxy for kas
- NO-REF
  - Add 412 PreconditionFailed response code
- NO-REF
  - fix kas rewrap-v2 exception on jwt decode
- NO-REF
  - fix protobuf vulnerability
- PLAT-2056
  - Update setup.py for access pdp


## 0.8.7 - 2022-09-22
- NO-REF
  - kas should not force encryptedMetadata to be a json string
- NO-REF
  - dependency bumps
- NO-REF
  - fix 500 on unclaimed jwts
- NO-REF
  - stop using pipenv+pipfile, just use requirements.txt
- NO-REF
  - fix property name in log causing 500
- NO-REF
  - replace kas internal pdp with access pdp
- NO-REF
  - remove paralell attribute definition endpoints
- NO-REF
  - remove timing tracking


## 0.8.6 - 2022-06-10

- PLAT-1641
  - Updates to latest version of cryptography to address vulnerabilities
- PLAT-1417
  - Add 30 seconds of leeway to jwt token expiry, customizable with variable
    `KAS_JWT_LEEWAY` up to 120 seconds (2 minutes)
  - Log details about claims on invalid token attempts

## 0.8.5 - 2021-11-15

- PLAT-1337
  - Update kas and attribute URI validation to allow one-label hostnames
  - Fixes bug in validation that would allow unsupported characters after the
    attribute value

## 0.8.4 - 2021-06-30

PLAT-946

- Pad nanotdf iv for cryptography compliance
  NO-REF
- Let `Context` keys be case-insensitive, to implement RFC 7230
  > Each header field consists of a case-insensitive field name followed by a colon
- `Context.get(key)` now returns a list, not a tuple, for headers with arity > 1

## 0.8.3 - 2021-06-22

PLAT-1166

- Update `cryptography` library
  PLAT-1171
- Prefer storing secrets directly in environment variables, instead of files

## 0.8.1 - 2021-05

PLAT-1102

- Allow `upsert` to return storage links

## 0.8.0 - 2021-04-06

PLAT-1097: ([#353](https://github.com/virtru/etheria/pull/353)) _minor_

- new exception class (PluginBackendError) to allow plugins to report 502s
- logline output and level reduction globally
- some http status code changes for clarity and accuracy

## 0.7.0 - 2021-03-10

PLAT-1034: ([#339](https://github.com/virtru/etheria/pull/339), [#334](https://github.com/virtru/etheria/pull/334), [#333](https://github.com/virtru/etheria/pull/333), [#329](https://github.com/virtru/etheria/pull/329))

- Publish kas/lib to internal nxrm repository

PLAT-432: ([#324](https://github.com/virtru/etheria/pull/324)])

- Moved logging configuration into gunicorn.conf.py

PLAT-879: ([#323](https://github.com/virtru/etheria/pull/323))

- Enable statsd performance logging

PLAT-636: ([#319](https://github.com/virtru/etheria/pull/319))

- Deprecate kas_public_key endpoint

PLAT-987: ([#294](https://github.com/virtru/etheria/pull/294))

- Explicit `healthz` endpoint

PLAT-795: ([#317](https://github.com/virtru/etheria/pull/317))

- Replace requirements.txt with Pipfile

# 0.6.2 - 2020-07-21

PLAT-879: ([#323](https://github.com/virtru/etheria/pull/323))

- Enable statsd performance logging

PLAT-488: ([#12](https://github.com/virtru/etheria/pull/12)): _change_

- Added wrapped key absent exception

PLAT-489: ([#8](https://github.com/virtru/etheria/pull/8)): _change_

- Remove TODO, update comment regarding keys, multi-KAS support.

PLAT-479: ([#4](https://github.com/virtru/etheria/pull/4)): _change_

- Remove TODOs that are covered by new or existing JIRA tickets.

# 0.6.1 - 2020-05-07

PLAT-477: ([#3](https://github.com/virtru/etheria/pull/3)): _change_

- Import into etheria

# 0.6.0 - 2020-03-27

PLAT-363, PLAT-362: ([#44](https://github.com/virtru/tdf3_kas_core/pull/44)): _change_

- Update KAS code to return 408 error when its trouble communicating with ACM on socket timeout.
- Update KAS code to return 404 error when ACM return 503

NOREF/export-errors: ([#38](https://github.com/virtru/tdf3_kas_core/pull/38)): _change_

- exporting a few error classes for the plugins to use.

HOTFIX/collections: ([#37](https://github.com/virtru/tdf3_kas_core/pull/37)): _fixup_

- Updated deprecated "collections" import to "collections.abc"

## [0.4.0] - 2019-06-24

#### Changed

WS-9100: ([#35](https://github.com/virtru/tdf3_kas_core/pull/35)): _change_

- Refactored logging processes and formats

## [0.4.0] - 2019-06-24

#### Changed

WS-9100: ([#35](https://github.com/virtru/tdf3_kas_core/pull/35)): _change_

- Refactored logging processes and formats

## [0.3.2] - 2019-05-31

#### Changed

WS-9100-conftest: ([#34](https://github.com/virtru/tdf3_kas_core/pull/34)): _change_

- Renamed internal variables to match current TDF3 spec to reduce confusion
- Aligned tests and mocks with the new naming conventions

NOREF/requirements: ([#33](https://github.com/virtru/tdf3_kas_core/pull/33)): _change_

- Removed unneeded requirements.txt. All dependencies are in setup.py.

NOREF/logging-improvements: ([#32](https://github.com/virtru/tdf3_kas_core/pull/32)): _change_

- Logging improvements; added data, removed clutter.
- Changed return response for bad key access error from 500 to 403

## [0.3.1] - 2019-05-24

#### Changed

HOTFIX/metadata: ([#26](https://github.com/virtru/tdf3_kas_core/pull/26)): _change_

- Missing encrytptedMetadata field now handled with empty MetaData model.

WS-8945-control:

- Exporting AttributeValue

## [0.3.0] - 2019-03-21

### Changed

NOREF: ([#21](https://github.com/virtru/tdf3_kas_core/pull/21)): _change_

- Altered format of heartbeat ping response to include version

NOREF: ([#17](https://github.com/virtru/tdf3_kas_core/pull/17)): _change_

- Added CHANGELOG.md
- Removed package.json and replaced with script in /scrips
