from PIL import Image, ImageOps, ImageFilter
from pathlib import Path
import numpy as np
import json
import assemble_assets as a

HERE=a.HERE;ROOT=a.ROOT
SIZE=(3840,2160); SMALL=(480,270)
ANCHORS={'흰색':(.16,.22),'빨강':(.52,.10),'노랑':(.91,.18),'파랑':(.12,.89),'초록':(.90,.89)}

def fit(im,pixel=False):
    return ImageOps.fit(im,SIZE,method=Image.Resampling.NEAREST if pixel else Image.Resampling.LANCZOS)

def foreground(path,pixel):
    im=fit(a.load(path),pixel)
    ar=np.array(im)
    # The generator added two small orange wedges above the red face. They
    # are not part of the approved mascot; preserve the two lower cheeks.
    yy,xx=np.indices(ar.shape[:2]);rgb=ar[:,:,:3].astype(int)
    extra=(xx>SIZE[0]*.40)&(xx<SIZE[0]*.68)&(yy>SIZE[1]*.10)&(yy<SIZE[1]*.225)
    extra&=(rgb[:,:,0]>220)&(rgb[:,:,1]>105)&(rgb[:,:,1]<210)&(rgb[:,:,1]-rgb[:,:,2]>25)&(ar[:,:,3]>128)
    skin=tuple(ar[round(SIZE[1]*.20),round(SIZE[0]*.53),:3])
    ar[extra,:3]=skin
    bg=np.median(ar[800:1200,1600:2200,3])
    cutoff=round((bg+ar[:,:,3].max())/2) if bg>=128 else (128 if pixel else 12)
    ar[ar[:,:,3]<cutoff]=0
    if pixel:ar[:,:,3]=np.where(ar[:,:,3]>=cutoff,255,0)
    return Image.fromarray(ar)

def run():
    base=fit(a.load(HERE/'하늘_기본원화.png')).convert('RGB')
    files=[]
    for pixel,style in [(False,'기본'),(True,'픽셀')]:
        front=foreground(HERE/f'내려다보기_{style}원화.png',pixel)
        if pixel:
            sky=base.resize(SMALL,Image.Resampling.BOX).quantize(colors=64,dither=Image.Dither.NONE).convert('RGBA')
            front=front.resize(SMALL,Image.Resampling.NEAREST)
            # Palette reduction occurs on the logical grid before integer enlargement.
            alpha=front.getchannel('A')
            front=front.convert('RGB').quantize(colors=128,dither=Image.Dither.NONE).convert('RGBA')
            front.putalpha(alpha)
        else:sky=base.convert('RGBA')
        bg_name=f'5색_{style}_배경만_팀원기준_2026-11-25.png'
        shown=a.resize(sky,SIZE,True) if pixel else sky
        shown.convert('RGB').save(ROOT/bg_name,compress_level=1);files.append(bg_name)
        result=sky.copy();result.alpha_composite(front)
        wall_name=f'5색_{style}_내려다보기_배경화면_팀원기준_2026-11-25.png'
        shown=a.resize(result,SIZE,True) if pixel else result
        shown.convert('RGB').save(ROOT/wall_name,compress_level=1);files.append(wall_name)
        # Assign complete connected components (including detached screw caps)
        # to one of the five requested original edge positions.
        mask=np.array(front.getchannel('A').resize(SMALL,Image.Resampling.NEAREST))>=128
        components=a.connected(mask)
        masks={color:Image.new('L',SMALL) for color in ANCHORS}
        pixels={color:np.zeros((270,480),dtype='uint8') for color in ANCHORS}
        for comp in components:
            if len(comp)<3:continue
            yy,xx=np.array(comp).T
            cx,cy=xx.mean()/480,yy.mean()/270
            color=min(ANCHORS,key=lambda c:(cx-ANCHORS[c][0])**2+(cy-ANCHORS[c][1])**2)
            pixels[color][yy,xx]=255
        poses=[]
        for color in a.COLORS:
            mask=Image.fromarray(pixels[color])
            assert mask.getbbox() is not None,f'Missing edge character: {style}/{color}'
            if not pixel:
                mask=mask.resize(SIZE,Image.Resampling.NEAREST).filter(ImageFilter.MaxFilter(17))
            pose=front.copy()
            pose.putalpha(Image.fromarray(np.minimum(np.array(front.getchannel('A')),np.array(mask))))
            pose=a.trim(pose)
            if pixel:pose=a.resize(pose,(pose.width*8,pose.height*8),True)
            pose_name=f'{color}_{style}_내려다보기_포즈_팀원기준_2026-11-25.png'
            pose.save(ROOT/pose_name,compress_level=1);files.append(pose_name)
            cell=Image.new('RGBA',(896,896))
            if pixel:
                native=pose.resize((pose.width//8,pose.height//8),Image.Resampling.NEAREST)
                factor=min(1,98/native.width,98/native.height)
                native=a.resize(native,(native.width*factor,native.height*factor),True)
                pose=a.resize(native,(native.width*8,native.height*8),True)
                xy=(((112-native.width)//2)*8,((112-native.height)//2)*8)
            else:
                factor=min(784/pose.width,784/pose.height)
                pose=a.resize(pose,(pose.width*factor,pose.height*factor),False)
                xy=((896-pose.width)//2,(896-pose.height)//2)
            cell.alpha_composite(pose,xy)
            poses.append(cell)
        atlas_name=f'5색_{style}_내려다보기_포즈시트_팀원기준_2026-11-25.png'
        a.sheet(poses,4).save(ROOT/atlas_name,compress_level=1);files.append(atlas_name)
    for name in files:
        with Image.open(ROOT/name) as check:
            check.verify()
    for style in ['기본','픽셀']:
        for label in ['배경만','내려다보기_배경화면']:
            with Image.open(ROOT/f'5색_{style}_{label}_팀원기준_2026-11-25.png') as check:
                assert check.size==SIZE
    for name in [n for n in files if '_픽셀_' in n and ('배경만' in n or '배경화면' in n)]:
        with Image.open(ROOT/name) as check:
            assert check.tobytes()==check.resize(SMALL,Image.Resampling.NEAREST).resize(SIZE,Image.Resampling.NEAREST).tobytes()
    (HERE/'배경단계_완료.json').write_text(json.dumps({'files':files,'wallpaper_size':SIZE,'pixel_scale':8,'characters':5,'palms':0,'dinosaurs':0},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'background_png':len(files),'files':files},ensure_ascii=True),flush=True)

if __name__=='__main__':run()
