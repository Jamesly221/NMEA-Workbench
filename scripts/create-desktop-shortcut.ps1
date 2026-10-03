# Works both in a source checkout and beside a packaged release.
$projectRoot = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $projectRoot 'NMEA-Workbench.exe'
$launcher = Join-Path $projectRoot 'launch.cmd'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'NMEA Workbench.lnk'))
if (Test-Path $exe) {
    $shortcut.TargetPath = $exe
} elseif (Test-Path $launcher) {
    $shortcut.TargetPath = $env:ComSpec
    $shortcut.Arguments = '/c ""' + $launcher + '""'
} else {
    throw 'No executable or launch.cmd found. Keep scripts inside the project folder.'
}
$shortcut.WorkingDirectory = $projectRoot
$shortcut.IconLocation = (Join-Path $projectRoot 'assets\icons\workbench.ico')
$shortcut.Description = 'NMEA message reference, decoder and log viewer'
$shortcut.Save()
Write-Host 'Created NMEA Workbench shortcut on your desktop.'
