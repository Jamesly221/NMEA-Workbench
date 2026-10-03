"""Run on Windows after installing requirements-build.txt."""
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if sys.platform != 'win32':
    raise SystemExit('Build Windows releases on Windows, or use the GitHub Actions workflow.')
subprocess.run([sys.executable, str(root / 'scripts' / 'make_icon.py')], check=True)
subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--windowed',
                '--name', 'NMEA-Workbench', '--icon', str(root / 'assets/icons/workbench.ico'),
                str(root / 'main.py')], cwd=root, check=True)
release = root / 'dist' / 'NMEA-Workbench'
for folder in ('data', 'assets', 'examples', 'docs'):
    shutil.copytree(root / folder, release / folder, dirs_exist_ok=True)
(release / 'scripts').mkdir(exist_ok=True)
shutil.copy2(root / 'scripts/create-desktop-shortcut.ps1', release / 'scripts')
shutil.copy2(root / 'README.md', release)
print(f'Ready: {release}. Keep the entire folder together.')
