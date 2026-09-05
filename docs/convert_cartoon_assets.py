from pathlib import Path
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
for name in ('cartoon-doctor', 'cartoon-patient'):
    source = ROOT / 'static' / 'img' / f'{name}.svg'
    target = ROOT / 'static' / 'img' / f'{name}.png'
    cairosvg.svg2png(url=str(source), write_to=str(target), output_width=720, output_height=720)
    print(target)
