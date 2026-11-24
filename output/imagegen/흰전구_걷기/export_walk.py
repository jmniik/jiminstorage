from pathlib import Path
from PIL import Image, ImageSequence
import json
import shutil

ROOT = Path(__file__).resolve().parent
SOURCE = Path(r'C:\Users\LGPC\.codex\generated_images\01a20743-5d97-7952-97b1-833e3805acd5\exec-fb3e9465-601a-424f-a5b6-3bf67d7d2c59.png')
REFERENCE = Path(r'C:\Users\LGPC\Downloads\ChatGPT 이미지 2026년 11월 24일 오후 03_27_29.gif')
sheet = Image.open(SOURCE).convert('RGBA')
reference = Image.open(REFERENCE)
durations = [f.info.get('duration', 120) for f in ImageSequence.Iterator(reference)]
frames = []
for row in range(2):
    for col in range(4):
        left = round(col * sheet.width / 4)
        top = round(row * sheet.height / 2)
        right = round((col + 1) * sheet.width / 4)
        bottom = round((row + 1) * sheet.height / 2)
        cell = sheet.crop((left, top, right, bottom))
        # Only split and center the generated frames, without redrawing artwork.
        frame = Image.new('RGBA', reference.size)
        frame.paste(cell, ((frame.width - cell.width)//2, (frame.height - cell.height)//2))
        frames.append(frame)

# A single shared palette prevents colors from changing between frames.
atlas = Image.new('RGB', (frames[0].width * len(frames), frames[0].height), (255,255,255))
for index, frame in enumerate(frames):
    atlas.paste(frame, (index*frame.width, 0), frame.getchannel('A'))
palette = atlas.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
gif_frames = []
for frame in frames:
    rgba = frame.convert('RGBA')
    indexed = rgba.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE)
    indexed.paste(255, mask=rgba.getchannel('A').point(lambda a: 255 if a < 128 else 0))
    indexed.info['transparency'] = 255
    gif_frames.append(indexed)

out = ROOT / '흰전구_걷기_투명.gif'
gif_frames[0].save(out, save_all=True, append_images=gif_frames[1:],
                   duration=durations, loop=0, transparency=255, disposal=2, optimize=False)
frames[0].save(ROOT / '흰전구_픽셀필라멘트.png')
shutil.copy2(SOURCE, ROOT / '흰전구_걷기_스프라이트.png')
check = Image.open(out)
assert check.n_frames == 8 and check.info['loop'] == 0
assert check.size == reference.size
assert all(f.info.get('duration') == durations[i] for i,f in enumerate(ImageSequence.Iterator(check)))
print(json.dumps({'file':str(out), 'size':check.size, 'frames':check.n_frames,
                  'duration_ms':sum(durations), 'loop':check.info['loop'],
                  'transparent_index':check.info.get('transparency'), 'bytes':out.stat().st_size}, ensure_ascii=False))
