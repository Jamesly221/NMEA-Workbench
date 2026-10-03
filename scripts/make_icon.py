"""Create a small compass icon from geometry; no external artwork required."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
image = Image.new('RGBA', (256, 256), '#13283f')
draw = ImageDraw.Draw(image)
draw.ellipse((35, 35, 221, 221), outline='#87b9c4', width=7)
draw.line((128, 20, 128, 40), fill='white', width=6)
draw.line((128, 216, 128, 236), fill='white', width=6)
draw.line((20, 128, 40, 128), fill='white', width=6)
draw.line((216, 128, 236, 128), fill='white', width=6)
draw.polygon(((128, 51), (101, 135), (128, 120), (155, 135)), fill='#00b8bb')
draw.polygon(((128, 205), (101, 135), (128, 150), (155, 135)), fill='white')
draw.ellipse((117, 117, 139, 139), fill='#13283f', outline='white', width=3)
directory = root / 'assets' / 'icons'
directory.mkdir(parents=True, exist_ok=True)
image.save(directory / 'workbench.png')
image.save(directory / 'workbench.ico', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
