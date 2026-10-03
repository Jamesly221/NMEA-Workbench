# Getting started

## Windows executable

Download the artifact from a successful GitHub Actions run, extract it fully, and move the entire extracted folder to a permanent location such as `Documents\NMEA-Workbench`. Open `NMEA-Workbench.exe`.

Do not run it inside the ZIP or move only the executable. Its `_internal` folder contains its runtime; `data` and `assets` contain editable resources.

## Windows source setup

1. Install Python 3.11+ from https://www.python.org/downloads/windows/ using a distribution with Tcl/Tk. The python.org installer normally includes it. Enable the Python launcher if offered.
2. In GitHub Desktop, clone `Jamesly221/NMEA-Workbench` into your preferred project directory. Alternatively download and extract the source ZIP.
3. Double-click `launch.cmd` at the top of the project folder.

If launch fails, open a terminal in the folder and run `py -3 main.py` to see the error. `py -3 -m tkinter` should open a small test window if Tk is available. Source mode uses Python's standard library and requires no separate Python packages.

## Desktop shortcut

Open PowerShell in the extracted app folder or source checkout and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create-desktop-shortcut.ps1
```

This command creates a shortcut; its execution-policy option applies only to that invocation. The shortcut points to your folder, so create it after choosing a permanent location. Recreate it if you move the folder.

You can also right-click the executable or `launch.cmd` and use Windows' Create shortcut / Send to Desktop option.

## Updating

For editable source, pull changes with GitHub Desktop, then close and reopen the application. Commit your own modifications before pulling so they can be preserved and merged.

For packaged releases, extract a new build into a new folder and copy over only your own reference entries or resources deliberately. Recreate the shortcut. Packaged apps do not update automatically when GitHub changes.

## First exercise

Decode the RMC example. Select Latitude to see degrees and minutes become decimal degrees. Compare RMC's course over ground with HDT's heading. Then load the demo log and inspect its checksum problems and invalid receiver status.
