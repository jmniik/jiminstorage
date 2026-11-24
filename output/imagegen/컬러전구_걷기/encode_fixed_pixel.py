from pathlib import Path
from PIL import Image, ImageSequence
import zipfile
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '팔원근_8비트_느린걷기'
OUT.mkdir(exist_ok=True)
GEN = Path(r'C:\Users\LGPC\.codex\generated_images\01a20743-5d97-7952-97b1-833e3805acd5')
SOURCES = {
    '빨강': 'exec-7e640a38-c6ac-4a70-a023-15948c12def9.png',
    '초록': 'exec-56c7e169-1942-4f18-bf5f-06b68cb05d2b.png',
    '파랑': 'exec-6e0b1400-2a8a-48f7-b251-964ba31c204f.png',
    '노랑': 'exec-e6c1d22f-f734-4faa-8776-57dead43cd26.png',
}
LOGICAL = (90,106)
SCALE = 4
DISPLAY = (LOGICAL[0]*SCALE, LOGICAL[1]*SCALE)
DURATION = 180
report = []
previews = {}
for color, name in SOURCES.items():
    sheet = Image.open(GEN/name).convert('RGBA')
    frames = []
    for row in range(2):
        for col in range(4):
            cell = sheet.crop((round(col*sheet.width/4), round(row*sheet.height/2),
                               round((col+1)*sheet.width/4), round((row+1)*sheet.height/2)))
            centered = Image.new('RGBA', DISPLAY)
            centered.paste(cell, ((DISPLAY[0]-cell.width)//2,(DISPLAY[1]-cell.height)//2))
            # Raster export on a fixed logical grid; never interpolate edges.
            small = centered.resize(LOGICAL, Image.Resampling.NEAREST)
            small.putalpha(small.getchannel('A').point(lambda a:255 if a>=192 else 0))
            frames.append(small)
    atlas = Image.new('RGB',(LOGICAL[0]*8,LOGICAL[1]),(9,10,22))
    for i, frame in enumerate(frames):
        atlas.paste(frame,(i*LOGICAL[0],0),frame.getchannel('A'))
    # Explicit 32-color ramps keep black outlines and neutral metal stable.
    common = [(9,10,22),(53,58,64),(90,98,101),(143,151,151),(194,199,194),
              (238,240,226),(255,249,229),(255,236,207),(255,224,185),(240,204,164),
              (255,124,51),(255,150,70),(255,177,101),(0,68,61),(0,103,87),
              (0,145,119),(0,184,147),(43,213,175),(255,244,175),(255,253,211)]
    ramps = {
        '빨강':[(151,17,36),(188,23,44),(218,30,50),(244,49,64),(255,76,84),(255,116,118),(255,169,160),(255,208,187)],
        '초록':[(30,112,0),(43,155,0),(62,196,0),(83,225,0),(111,247,12),(151,255,51),(190,255,107),(223,255,169)],
        '파랑':[(0,68,124),(0,97,162),(0,128,199),(0,159,227),(13,192,247),(67,218,255),(127,239,255),(202,250,255)],
        '노랑':[(150,95,15),(184,122,19),(217,153,27),(242,181,45),(255,204,73),(255,222,117),(255,235,157),(255,245,197)],
    }
    rgb_colors=common+ramps[color]+[(0,0,0)]*4
    palette=Image.new('P',(1,1))
    palette.putpalette([v for rgb in rgb_colors for v in rgb]+[0]*(768-len(rgb_colors)*3))
    gif_frames = []
    rgba_frames = []
    for frame in frames:
        indexed = frame.convert('RGB').quantize(palette=palette,dither=Image.Dither.NONE)
        indexed.paste(255, mask=frame.getchannel('A').point(lambda a:255-a))
        indexed.info['transparency'] = 255
        enlarged = indexed.resize(DISPLAY,Image.Resampling.NEAREST)
        enlarged.info['transparency'] = 255
        gif_frames.append(enlarged)
        rgba_frames.append(enlarged.convert('RGBA'))
    gif_path = OUT/f'{color}_걷기_8비트.gif'
    gif_frames[0].save(gif_path,save_all=True,append_images=gif_frames[1:],
                       duration=DURATION,loop=0,disposal=2,transparency=255,optimize=False,
                       palette=bytes(palette.getpalette()))
    contact = Image.new('P',(DISPLAY[0]*4,DISPLAY[1]*2),255)
    contact.putpalette(palette.getpalette())
    contact.info['transparency']=255
    for i, frame in enumerate(gif_frames):
        contact.paste(frame,((i%4)*DISPLAY[0],(i//4)*DISPLAY[1]))
    sheet_path = OUT/f'{color}_모션시트_8비트.png'
    contact.save(sheet_path,transparency=255,bits=8)
    assert Image.open(sheet_path).mode=='P'
    # Verify exported pixels, rather than relying on file bit depth alone.
    check = Image.open(gif_path)
    assert check.n_frames==8 and check.info['loop']==0
    for decoded in ImageSequence.Iterator(check):
        assert decoded.info['duration']==DURATION
        rgba=decoded.convert('RGBA')
        assert set(rgba.getchannel('A').get_flattened_data())=={0,255}
        assert len(rgba.getcolors(rgba.width*rgba.height))<=33
        rebuilt=rgba.resize(LOGICAL,Image.Resampling.NEAREST).resize(DISPLAY,Image.Resampling.NEAREST)
        assert rgba.tobytes()==rebuilt.tobytes(), 'Every dot must be an exact 4x4 block'
    assert contact.tobytes()==contact.resize((360,212),Image.Resampling.NEAREST).resize(contact.size,Image.Resampling.NEAREST).tobytes()
    previews[color]=rgba_frames
    report.append({'color':color,'logical':LOGICAL,'display':DISPLAY,'opaque_colors_max':32,
                   'pixel_scale':SCALE,'frame_ms':DURATION,'loop_ms':DURATION*8,
                   'frames':8,'alpha':'binary','grid_verified':True})

# A side-by-side animation preview outside the deliverable folder.
preview_frames=[]
for i in range(8):
    canvas=Image.new('RGBA',(DISPLAY[0]*4,DISPLAY[1]))
    for j,color in enumerate(SOURCES):
        canvas.paste(previews[color][i],(j*DISPLAY[0],0))
    preview_frames.append(canvas)
preview_frames[0].save(ROOT/'팔원근_8비트_첫프레임.png')
with zipfile.ZipFile(ROOT/'컬러전구_팔원근_8비트_느린걷기.zip','w',zipfile.ZIP_DEFLATED) as bundle:
    for path in sorted(OUT.iterdir()):
        if path.suffix in {'.png','.gif'}:
            bundle.write(path,path.name)
print(json.dumps(report,ensure_ascii=False))
