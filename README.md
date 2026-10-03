# NMEA Workbench

A local desktop application by James Lee for learning and inspecting NMEA 0183 navigation messages.

**Version 0.1.0:** searchable sentence reference, field-by-field decoder, checksum inspection, recorded-log viewer and CSV reports. Everything runs locally; no account, server or network is required. Source links open in your browser only when you choose them.

## Run on Windows

### Packaged application (no Python required)

1. Open this repository's **Actions** tab.
2. Open a successful **Test and build Windows app** run.
3. Download **NMEA-Workbench-Windows** under Artifacts (sign in to GitHub to download).
4. Extract the ZIP fully into a permanent folder.
5. Double-click **NMEA-Workbench.exe**. Keep the executable, `_internal`, `data`, `assets`, `examples` and other included folders together.

The package is generated on each push to `main` and retained for 30 days. The workflow can also be run manually. See [Getting started](docs/GETTING_STARTED.md) for a desktop shortcut and source setup.

### Editable source

Install Python 3.11 or newer with Tcl/Tk support. Clone this repository or download and extract its source ZIP, then double-click **launch.cmd**. There are no pip dependencies needed for source mode.

On macOS/Linux with Python and Tk installed: `python3 main.py`.

## Try it

- **Message decoder:** choose RMC, GGA, VTG or HDT; select a field to read its explanation.
- **Sentence reference:** search by type or purpose; load its example or open the source documentation.
- **Log viewer:** click **Load demo**. Select a message to decode it. Filter messages or export a complete CSV report.
- Keyboard: **Ctrl+O** opens a log; **Ctrl+Enter** decodes the current input.

A valid checksum says the text matches its checksum. It does not establish fix validity or sensor accuracy. Receiver status and field problems are reported separately.

## Organization

| Location | Purpose |
| --- | --- |
| `src/ui/` | Windows, controls and visual theme |
| `src/nmea/` | Parsing and reference loading |
| `data/sentences/` | Editable JSON reference entries |
| `assets/images/` | Future illustrations |
| `assets/icons/` | Window and executable icons |
| `examples/logs/` | Sample logs, one sentence per line |
| `docs/` | Setup, editing guide and scope |
| `scripts/` | Packaging and desktop shortcut |
| `tests/` | Parser and catalog checks |
| `.github/workflows/` | Automatic Windows tests and packaging |

See [Editing guide](docs/EDITING_GUIDE.md). New valid JSON entries appear when you click **Reload reference files**. New reference entries provide field labels; specialized conversions require a change to the parser.

## Development

```bash
python -m unittest discover -s tests -v
python main.py
```

To package on Windows:

```bash
python -m pip install -r requirements-build.txt
python scripts/build_windows.py
```

## Current scope

Four interpreted sentence types: RMC, GGA, VTG and HDT. Other ordinary sentence types are shown as raw fields. Logs accept plain sentences without timestamp prefixes, up to 20 MB and 25,000 lines. Missing checksums, bad checksums, truncated data and invalid values remain inspectable.

Live serial/network input, AIS multipart decoding, NMEA 2000, vessel simulation and map charts are future work. This is an educational inspection tool, not a complete standards validator or a navigational instrument. Device and NMEA-version differences should be checked against the producing instrument's documentation.

Reference entries contain original summaries informed by linked manufacturer documentation, not a reproduction of the proprietary NMEA standard. No license granting redistribution of this project's source has been selected yet.
