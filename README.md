# Probewheel

An `auditwheel`-like tool for Windows binary extension modules. A work-in-progress.

## Usage

* First, install probewheel dependencies by running `install-deps.bat`.
* Then:
```
python probewheel.py <path\to\binary-module.pyd>
```

## Caveats

* Binaries built using `mingw` toolchains should have the GNU binutils `strip` utility run against them before running probewheel.
* Do NOT run `strip` against MSVC-built binaries, since this can/will corrupt them.
* This project is still experimental. I do not promise that it will work in current form, and I can't even promise to help you get it to work for your project.
* External dependencies that are not to be bundled (system-level dependencies) are currently whitelisted internally in `probewheel.py`, modify this as necessary for now. The whitelist may be configurable in a future version.

## Contents

* machomachomangler (for mangling PE binaries). Pulled in from https://github.com/njsmith/machomachomangler
* hashfile.py from auditwheel
* install-deps.bat (installs `pefile` module)
* probewheel.py

## Authors

auditwheel - Derek Steinmoeller (dsteinmo)
machomachomangler - Nathaniel J. Smith (njsmith)

# License

* probewheel is MIT
* machomachomangler is AGPLv3
* pefile is MIT.
