# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows
[Semantic Versioning](https://semver.org/). The Python and npm packages share
version numbers.

## [0.1.1] - 2026-10-07

### Changed

- Package homepage now points to https://sportapi.net; the GitHub repository is listed as
  the repository/source link. PyPI also lists a "Live odds data (SportAPI)" link.
- README: PyPI and npm version badges.
- Releases are published automatically from GitHub Actions to PyPI and npm via Trusted
  Publishing (no stored tokens). No library code changes.

## [0.1.0] - 2026-10-07

### Added

- Odds conversion between decimal, fractional, American, Hong Kong, Indonesian
  and Malay formats, implied probability, and a generic `convert`.
- `format_american` / `formatAmerican` for signed moneyline strings.
- Overround, margin and theoretical payout of a market.
- Fair (no-vig) probabilities and odds with the multiplicative, additive,
  power and Shin methods; `shin_z` / `shinZ`.
- Accumulator odds and payouts with win / lose / void legs.
- System bets of any size combination (2/3, 3/4, Trixie, Yankee, Lucky 15, ...):
  number of bets, stake split, maximum payout and payout for given results.
- Expected value, Kelly fraction and Kelly stake (full and fractional).
- Arbitrage detection and stake distribution with optional stake rounding.
- `round_half_up` / `roundHalfUp` decimal rounding.
- `OddsError` for all invalid input.
- Shared JSON test vectors used by both the pytest and node:test suites.
