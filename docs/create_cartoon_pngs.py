from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / 'static' / 'img'

def draw_character(path, bg, shirt, hair, skin, accessory):
    image = Image.new('RGB', (720, 720), bg)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((35, 35, 685, 685), radius=80, fill=bg)
    draw.ellipse((190, 120, 530, 460), fill=skin)
    draw.pieslice((180, 70, 540, 390), 180, 360, fill=hair)
    draw.ellipse((270, 250, 300, 280), fill='#102a43')
    draw.ellipse((420, 250, 450, 280), fill='#102a43')
    draw.arc((285, 300, 435, 385), 10, 170, fill='#102a43', width=10)
    draw.polygon([(360, 390), (270, 480), (450, 480)], fill=shirt)
    draw.rounded_rectangle((150, 430, 570, 700), radius=80, fill=shirt)
    draw.rectangle((320, 475, 400, 700), fill='#ffffff')
    draw.ellipse((500, 85, 625, 210), fill=accessory)
    draw.line((535, 147, 590, 147), fill='#ffffff', width=14)
    draw.line((562, 120, 562, 175), fill='#ffffff', width=14)
    image.save(path, 'PNG')

draw_character(ROOT / 'cartoon-doctor.png', '#dbeafe', '#14b8a6', '#243b53', '#f6c7a4', '#2563eb')
draw_character(ROOT / 'cartoon-patient.png', '#ccfbf1', '#f97316', '#5b3b2c', '#f2bd94', '#ffffff')
print('created cartoon PNG assets')
