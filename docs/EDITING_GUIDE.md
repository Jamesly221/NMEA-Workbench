# Editing the project

Keep content, resources and behavior separate. Use VS Code to open the whole project folder.

## Reference entries

Each `data/sentences/*.json` file defines one ordinary three-character sentence type. Copy an existing entry and change:

- `type`: three uppercase letters/digits, unique in the library.
- `title`, `description`, `notes`: plain explanatory text.
- `example`: a complete sentence with an appropriate checksum.
- `source`: an HTTPS documentation URL.
- `fields`: an ordered list of objects, each with a `name` and `description`. Fields exclude the sentence address and checksum; preserve empty positions.

Click **Reload reference files** after saving. Bad files are reported and skipped; valid entries still load. Reference reload does not reparse a previously loaded log: reopen the log to use the new definitions.

A new entry supplies labels and descriptions automatically. Built-in numeric and coordinate conversions live in `src/nmea/parser.py`; adding a reference does not automatically implement specialized decoding. Unknown extra fields remain visible.

## Graphics

- Window icon: `assets/icons/workbench.png`.
- Executable and shortcut icon: `assets/icons/workbench.ico`.
- Future illustrations: `assets/images/`.

Replacing the PNG changes the source-mode window icon on the next launch. The current build script generates both icons from `scripts/make_icon.py`; change that generator to preserve a customized packaged icon. Images do not appear in the interface automatically unless a control loads them.

## Logs

Drop plain-text logs into `examples/logs/`, then use **Open log** to choose them. `demo.txt` is the fixed file used by **Load demo**. One sentence per line; blank lines are skipped while original line numbers are retained. Malformed lines are kept for inspection. Put personal recordings in ignored `local-logs/` if you do not want them committed.

CSV export covers the complete loaded log, regardless of the current filter.

## Application code

- `main.py`: entry point and real-window smoke check.
- `src/ui/app.py`: tabs and event handlers.
- `src/ui/theme.py`: fonts, spacing and colors.
- `src/nmea/parser.py`: checksum, field interpretation and value checks.
- `src/nmea/catalog.py`: JSON loading and validation.
- `src/paths.py`: source/release resource location.

## Everyday GitHub workflow

Create a branch for a feature, edit locally, run `python -m unittest discover -s tests -v`, and try the application. Commit descriptive changes and push the branch. Open a pull request and let the Windows workflow test and build it. Merge when it behaves as intended. Pull the merged source on your computer.
