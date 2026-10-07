# Contributing

Thanks for helping! Bug reports, corrections to formulas and new, well-defined
calculations are all welcome. Please open an issue first for larger changes.

## Ground rules

- **Both packages, same behaviour.** A change to the API or to a result must be
  made in `python/` and `js/` in the same pull request.
- **Add test vectors.** Put new cases in `test-vectors/generate.py`, compute the
  expected value independently (exact fractions, a high-precision tool or by
  hand — never by calling odds-tools), then regenerate `vectors.json`:

  ```bash
  pip install mpmath
  python test-vectors/generate.py
  ```

- **No runtime dependencies** in either package.
- Keep public functions documented (docstrings / TSDoc) and update the README
  and `CHANGELOG.md`.

## Python

```bash
cd python
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest              # unit tests, shared vectors and doctests
ruff check . && ruff format --check .
mypy
python -m build     # optional: build sdist and wheel
```

## JavaScript / TypeScript

```bash
cd js
npm ci
npm run lint        # tsc --noEmit (strict)
npm test            # builds ESM + CJS, then runs node:test
npm pack --dry-run  # optional: inspect the package contents
```

By contributing you agree that your contributions are licensed under the MIT
License.
