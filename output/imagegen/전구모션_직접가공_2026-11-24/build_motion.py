from pathlib import Path
from PIL import Image, ImageSequence, ImageDraw
import numpy as np
import json
import zipfile

OUT = Path(__file__).resolve().parent
WORK = OUT.parents[2]
GEN = Path('C:/Users/LGPC/.codex/generated_images/01a20743-5d97-7952-97b1-833e3805acd5')
SOURCES = {
    '흰색': WORK / 'output/imagegen/흰전구_걷기/흰전구_걷기_스프라이트.png',
    '빨강': GEN / 'exec-7e640a38-c6ac-4a70-a023-15948c12def9.png',
    '초록': GEN / 'exec-56c7e169-1942-4f18-bf5f-06b68cb05d2b.png',
    '파랑': GEN / 'exec-6e0b1400-2a8a-48f7-b251-964ba31c204f.png',
    '노랑': GEN / 'exec-e6c1d22f-f734-4faa-8776-57dead43cd26.png',
}
LOGICAL = (112, 120)
SCALE = 4
SIZE = tuple(v*SCALE for v in LOGICAL)
REF = Path('C:/Users/LGPC/Downloads/모션 움짤(팔 모션 참고).gif')
with Image.open(REF) as ref:
    DURATIONS = [f.info['duration'] for f in ImageSequence.Iterator(ref)]
assert DURATIONS == [120]*8

def components(mask):
    seen = np.zeros_like(mask, dtype=bool)
    found = []
    h,w = mask.shape
    for y,x in zip(*np.where(mask)):
        if seen[y,x]:
            continue
        stack=[(y,x)]
        seen[y,x]=True
        pts=[]
        while stack:
            cy,cx=stack.pop()
            pts.append((cy,cx))
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=True
                    stack.append((ny,nx))
        found.append(pts)
    return found

def source_frames(path):
    with Image.open(path) as im:
        sheet=im.convert('RGBA')
    frames=[]
    for i in range(8):
        c,r=i%4,i//4
        cell=sheet.crop((round(c*sheet.width/4),round(r*sheet.height/2),
                         round((c+1)*sheet.width/4),round((r+1)*sheet.height/2)))
        a=np.array(cell.resize((112,112),Image.Resampling.NEAREST))
        a[:,:,3]=np.where(a[:,:,3]>=128,255,0)
        # Drop only disconnected one- and two-dot export noise.
        for comp in components(a[:,:,3]>0):
            if len(comp)<3:
                yy,xx=zip(*comp)
                a[yy,xx,3]=0
        a[a[:,:,3]==0,:3]=0
        dark=(np.max(a[:,:,:3],axis=2)<55)&(a[:,:,3]>0)
        a[dark,:3]=(8,10,18)
        frames.append(Image.fromarray(a))
    return frames

def hand_components(frame):
    a=np.array(frame)
    mask=(a[:,:,0]>185)&(a[:,:,1]>155)&(a[:,:,2]>105)&(a[:,:,3]>0)
    mask[:75,:]=False
    hands=[]
    for comp in components(mask):
        yy,xx=np.array(comp).T
        if 5<=len(comp)<=240 and (xx.mean()<43 or xx.mean()>68):
            hands.append((int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1),len(comp)))
    return hands

if __name__ == '__main__':
    raw={k:source_frames(p) for k,p in SOURCES.items()}
    # Transfer only the cream, black-outlined foreground hand, preserving the
    # white character's own head, worried expression, filament, and stepping feet.
    for i, (white,red) in enumerate(zip(raw['흰색'],raw['빨강'])):
        for x0,y0,x1,y1,area in hand_components(red):
            if area<65:
                continue
            box=(max(0,x0-2),max(0,y0-2),min(112,x1+2),min(112,y1+2))
            hand=red.crop(box)
            white.alpha_composite(hand,(box[0],box[1]))
        # Replace the antialiased grey filament with one repeatable staircase
        # symbol. Only neutral-grey filament pixels in the central bulb change.
        a=np.array(white)
        rgb=a[:,:,:3].astype(int)
        neutral=(rgb.max(axis=2)-rgb.min(axis=2)<17)&(rgb[:,:,0]>90)&(rgb[:,:,0]<195)
        region=np.zeros((112,112),dtype=bool)
        region[32:55,42:73]=True
        filament=neutral&region&(a[:,:,3]>0)
        yy,xx=np.where(filament)
        if len(xx):
            cx=round((int(xx.min())+int(xx.max()))/2)
            top=int(yy.min())
            a[filament,:3]=(233,228,241)
            white=Image.fromarray(a)
            d=ImageDraw.Draw(white)
            ink=(151,151,155,255)
            d.rectangle((cx-13,top-1,cx+13,top+16),fill=(233,228,241,255))
            d.rectangle((cx-8,top,cx+8,top+2),fill=ink)
            d.rectangle((cx-1,top+3,cx+1,top+14),fill=ink)
            for step in range(4):
                y=top+3+step*3
                lx=cx-6-step*2
                rx=cx+4+step*2
                d.rectangle((lx,y,lx+2,y+2),fill=ink)
                d.rectangle((rx,y,rx+2,y+2),fill=ink)
            raw['흰색'][i]=white

    common=[(8,10,18),(45,48,54),(83,88,92),(125,130,132),
            (166,171,173),(205,210,209),(235,238,235),(255,255,250),
            (255,247,230),(255,237,214),(255,225,194),(242,205,165),
            (255,124,54),(255,151,77),(255,178,110),
            (0,65,59),(0,94,80),(0,128,106),(0,162,132),
            (0,190,153),(43,214,177),(88,228,193),
            (255,245,176),(255,254,212),
            (103,103,107),(151,151,155)]
    ramps={
        '흰색':[(139,132,158),(162,154,179),(184,177,201),(205,199,219),
                (221,215,232),(233,228,241),(244,240,250),(253,250,255)],
        '빨강':[(153,18,34),(191,25,43),(221,34,49),(246,50,62),
                (255,79,85),(255,117,118),(255,167,160),(255,207,188)],
        '초록':[(30,114,0),(44,157,0),(63,197,0),(86,228,0),
                (113,247,14),(153,255,54),(192,255,111),(225,255,173)],
        '파랑':[(0,68,125),(0,98,164),(0,130,201),(0,161,229),
                (15,193,248),(69,220,255),(130,240,255),(204,251,255)],
        '노랑':[(152,96,15),(186,124,20),(219,155,28),(244,183,47),
                (255,205,75),(255,223,119),(255,236,160),(255,246,200)]}
    report=[]
    exported={}
    for color,frames in raw.items():
        colors=common+ramps[color]
        pal=Image.new('P',(1,1))
        pal.putpalette([v for rgb in colors for v in rgb]+[0]*(768-3*len(colors)))
        indexed=[]
        for i,frame in enumerate(frames):
            canvas=Image.new('RGBA',LOGICAL)
            d=ImageDraw.Draw(canvas)
            # Three opaque grey pixel bands; no feathering or blur.
            wobble=[0,1,0,-1,0,1,0,-1][i]
            d.ellipse((25+wobble,102,87-wobble,109),fill=(151,151,155,255))
            d.ellipse((33+wobble,103,79-wobble,107),fill=(103,103,107,255))
            canvas.alpha_composite(frame,(0,0))
            ind=canvas.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE)
            ind.paste(255,mask=canvas.getchannel('A').point(lambda a:255-a))
            ind.info['transparency']=255
            ind=ind.resize(SIZE,Image.Resampling.NEAREST)
            ind.info['transparency']=255
            indexed.append(ind)
        gif_path=OUT/f'{color}_모션.gif'
        indexed[0].save(gif_path,save_all=True,append_images=indexed[1:],
                        duration=DURATIONS,loop=0,transparency=255,
                        disposal=2,optimize=False)
        sheet=Image.new('P',(SIZE[0]*4,SIZE[1]*2),255)
        sheet.putpalette(pal.getpalette())
        sheet.info['transparency']=255
        for i,f in enumerate(indexed):
            sheet.paste(f,((i%4)*SIZE[0],(i//4)*SIZE[1]))
        sheet_path=OUT/f'{color}_모션시트.png'
        sheet.save(sheet_path,transparency=255,bits=8)
        # Small native-resolution sheet is useful in sprite engines.
        native=sheet.resize((LOGICAL[0]*4,LOGICAL[1]*2),Image.Resampling.NEAREST)
        native.info['transparency']=255
        (OUT/'원배율_시트').mkdir(exist_ok=True)
        native.save(OUT/'원배율_시트'/f'{color}_모션시트_1x.png',transparency=255,bits=8)
        decoded=[]
        with Image.open(gif_path) as check:
            assert check.n_frames==8 and check.info['loop']==0
            assert check.size==SIZE
            for i,f in enumerate(ImageSequence.Iterator(check)):
                assert f.info['duration']==DURATIONS[i]
                rgba=f.convert('RGBA')
                assert set(rgba.getchannel('A').get_flattened_data())=={0,255}
                assert len(rgba.getcolors(rgba.width*rgba.height))<=len(colors)+1
                rebuilt=rgba.resize(LOGICAL,Image.Resampling.NEAREST).resize(SIZE,Image.Resampling.NEAREST)
                assert rgba.tobytes()==rebuilt.tobytes()
                assert rgba.tobytes()==indexed[i].convert('RGBA').tobytes()
                bbox=rgba.getbbox()
                assert bbox[0]>0 and bbox[1]>0 and bbox[2]<SIZE[0] and bbox[3]<SIZE[1]
                decoded.append(rgba.copy())
        assert len({f.tobytes() for f in decoded})==8
        with Image.open(sheet_path) as check:
            assert check.mode=='P'
            for i,f in enumerate(decoded):
                tile=check.crop(((i%4)*SIZE[0],(i//4)*SIZE[1],
                                  ((i%4)+1)*SIZE[0],((i//4)+1)*SIZE[1])).convert('RGBA')
                assert tile.tobytes()==f.tobytes()
        exported[color]=decoded
        report.append({'color':color,'frames':8,'frame_ms':120,'loop_ms':960,
                       'gif_size':SIZE,'sheet_size':sheet.size,'logical_cell':LOGICAL,
                       'pixel_block':'4x4','palette_colors':len(colors),
                       'alpha':'0 or 255','sheet_matches_gif':True,
                       'pixel_grid_verified':True,'no_cropped_pixels':True})

    # A labelled combined preview, outside the five sprite sheets.
    preview=[]
    font_path=Path('C:/Windows/Fonts/malgun.ttf')
    from PIL import ImageFont
    font=ImageFont.truetype(str(font_path),20)
    for i in range(8):
        canvas=Image.new('RGB',(280*5,336),(247,244,236))
        d=ImageDraw.Draw(canvas)
        for j,(color,frames) in enumerate(exported.items()):
            small=frames[i].resize((224,240),Image.Resampling.NEAREST)
            canvas.paste(small,(280*j+28,38),small)
            d.text((280*j+140,298),color,font=font,fill=(28,31,38),anchor='mm')
        preview.append(canvas)
    preview[0].save(OUT/'다섯색상_미리보기.gif',save_all=True,append_images=preview[1:],
                    duration=DURATIONS,loop=0,optimize=False)
    preview[0].save(OUT/'다섯색상_미리보기.png')
    (OUT/'검증결과.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'제작정보.txt').write_text(
        '직접 가공 버전 — 2026-11-24\n'
        'GIF 5개 및 투명 PNG 모션 시트 5개. 8프레임, 120ms/프레임, 0.96초 무한 반복.\n'
        'GIF: 448×480px. 시트: 1792×960px, 4열×2행. 왼쪽 위부터 오른쪽으로 읽기.\n'
        '논리 해상도 112×120px, 최근접 이웃 4배. 8비트 인덱스 팔레트, 디더링 없음.\n'
        '색상별 34색과 투명도, 흐림 없는 픽셀 그림자. 흰색 회색 필라멘트도 픽셀 격자.\n'
        '원배율_시트 폴더에 448×240px 시트 포함.\n'
        '이 버전은 기존 생성 모션 원본을 직접 가공한 결과이며, 내일 생성 도구 버전과 구분됩니다.\n'
        '원본 파일은 덮어쓰지 않았습니다.\n',encoding='utf-8')
    zip_path=OUT.parent/'전구모션_5색_직접가공_2026-11-24.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file() and p.suffix in {'.gif','.png','.txt','.json'}:
                z.write(p,p.relative_to(OUT))
    print(json.dumps({'verified':report,'zip':str(zip_path)},ensure_ascii=False))
