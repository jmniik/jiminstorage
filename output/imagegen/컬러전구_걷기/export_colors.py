from pathlib import Path
from PIL import Image, ImageSequence
import shutil
import zipfile
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '완성본'
OUT.mkdir(exist_ok=True)
GENERATED = Path(r'C:\Users\LGPC\.codex\generated_images\01a20743-5d97-7952-97b1-833e3805acd5')
SOURCES = {
    '빨강': 'exec-66dc6df9-763c-454c-a667-2dcdda16cbd8.png',
    '초록': 'exec-c0bd119a-d953-403b-95bd-98e9ec9eb385.png',
    '파랑': 'exec-9676ed5f-d724-4bf9-826b-d7aee541e03a.png',
    '노랑': 'exec-8e7417cb-782e-42b6-989a-a9a95e0359ee.png',
}
reference = Image.open(ROOT / '흰색_모션참고.gif')
durations = [f.info.get('duration', 120) for f in ImageSequence.Iterator(reference)]
report = []
for color, filename in SOURCES.items():
    source = GENERATED / filename
    sheet = Image.open(source).convert('RGBA')
    assert sheet.getpixel((0,0))[3] == 0, 'Sheet background must be transparent'
    sheet_path = OUT / f'{color}_모션시트.png'
    shutil.copy2(source, sheet_path)
    frames = []
    for row in range(2):
        for col in range(4):
            cell = sheet.crop((round(col*sheet.width/4), round(row*sheet.height/2),
                               round((col+1)*sheet.width/4), round((row+1)*sheet.height/2)))
            frame = Image.new('RGBA', reference.size)
            frame.paste(cell, ((frame.width-cell.width)//2, (frame.height-cell.height)//2))
            frames.append(frame)
    atlas = Image.new('RGB', (frames[0].width*8, frames[0].height), 'white')
    for index, frame in enumerate(frames):
        atlas.paste(frame, (index*frame.width,0), frame.getchannel('A'))
    palette = atlas.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    indexed_frames = []
    for frame in frames:
        indexed = frame.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE)
        indexed.paste(255, mask=frame.getchannel('A').point(lambda a:255 if a<128 else 0))
        indexed.info['transparency'] = 255
        indexed_frames.append(indexed)
    gif_path = OUT / f'{color}_걷기.gif'
    indexed_frames[0].save(gif_path, save_all=True, append_images=indexed_frames[1:],
                          duration=durations, loop=0, transparency=255, disposal=2, optimize=False)
    check = Image.open(gif_path)
    assert check.n_frames == 8 and check.info['loop'] == 0
    assert check.size == (360,425) and check.info.get('transparency') == 255
    decoded = [f.convert('RGBA').copy() for f in ImageSequence.Iterator(check)]
    assert all(f.getchannel('A').getextrema() == (0,255) for f in decoded)
    assert len({f.tobytes() for f in decoded}) == 8
    report.append({'color':color,'frames':len(decoded),'duration_ms':sum(durations),
                   'size':check.size,'gif_bytes':gif_path.stat().st_size,'sheet_size':sheet.size})

with zipfile.ZipFile(ROOT / '컬러전구_모션_4종.zip', 'w', zipfile.ZIP_DEFLATED) as bundle:
    for path in sorted(OUT.iterdir()):
        if path.suffix.lower() in {'.gif','.png'}:
            bundle.write(path, path.name)
print(json.dumps(report, ensure_ascii=False))
