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

def alternate_brows(front,pixel):
    out=front.copy(); w,h=front.size
    patches=[(.465,.190,.523,.239,-25),(.544,.190,.608,.239,25),
             (.035,.845,.119,.909,-25),(.126,.883,.204,.951,25),
             (.786,.860,.855,.950,-25),(.877,.835,.950,.919,25)]
    for x0,y0,x1,y1,angle in patches:
        box=(round(x0*w),round(y0*h),round(x1*w),round(y1*h))
        patch=out.crop(box); ar=np.array(patch);rgb=ar[:,:,:3].astype(int)
        dark=(rgb.max(axis=2)<90)&(ar[:,:,3]>128)
        comps=[]
        for pts in a.connected(dark):
            yy,xx=np.array(pts).T
            if len(pts)>=3 and xx.max()-xx.min()>=max(2,yy.max()-yy.min()):
                comps.append(pts)
        if not comps:continue
        pts=max(comps,key=len); yy,xx=np.array(pts).T
        mask=np.zeros(dark.shape,dtype='uint8');mask[yy,xx]=255
        mask=Image.fromarray(mask).filter(ImageFilter.MaxFilter(3))
        skin=(rgb[:,:,0]>180)&(rgb[:,:,1]>160)&(rgb[:,:,2]>130)&(ar[:,:,3]>128)
        if not skin.any():continue
        color=tuple(int(v) for v in np.median(rgb[skin],axis=0))+(255,)
        fill=Image.new('RGBA',patch.size,color)
        out.paste(fill,(box[0],box[1]),mask)
        ink=Image.new('RGBA',patch.size,(0,0,0,255));ink.putalpha(mask)
        ink=a.trim(ink)
        ink=ink.rotate(angle,resample=Image.Resampling.NEAREST if pixel else Image.Resampling.BICUBIC,expand=True)
        center=(box[0]+(int(xx.min())+int(xx.max()))/2,box[1]+(int(yy.min())+int(yy.max()))/2)
        out.alpha_composite(ink,(round(center[0]-ink.width/2),round(center[1]-ink.height/2)))
    return out

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
            ar=np.array(front); dark=(ar[:,:,:3].max(axis=2)<60)&(ar[:,:,3]>0);ar[dark,:3]=0
            front=Image.fromarray(ar)
        else:sky=base.convert('RGBA')
        alt=alternate_brows(front,pixel)
        bg_name=f'5색_{style}_배경만_팀원기준_2026-11-25.png'
        shown=a.resize(sky,SIZE,True) if pixel else sky
        shown.convert('RGB').save(ROOT/bg_name,compress_level=1);files.append(bg_name)
        result=sky.copy();result.alpha_composite(front)
        wall_name=f'5색_{style}_내려다보기_배경화면_팀원기준_2026-11-25.png'
        shown=a.resize(result,SIZE,True) if pixel else result
        shown.convert('RGB').save(ROOT/wall_name,compress_level=1);files.append(wall_name)
        alternate=sky.copy();alternate.alpha_composite(alt)
        name=f'5색_{style}_표정2조합_내려다보기_배경화면_팀원기준_2026-11-25.png'
        (a.resize(alternate,SIZE,True) if pixel else alternate).convert('RGB').save(ROOT/name,compress_level=1);files.append(name)
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
        poses=[];alternates=[]
        for color in a.COLORS:
            mask=Image.fromarray(pixels[color])
            assert mask.getbbox() is not None,f'Missing edge character: {style}/{color}'
            if not pixel:
                mask=mask.filter(ImageFilter.MaxFilter(3)).resize(SIZE,Image.Resampling.NEAREST)
            pose=front.copy()
            pose.putalpha(Image.fromarray(np.minimum(np.array(front.getchannel('A')),np.array(mask))))
            pose=a.trim(pose)
            if pixel:pose=a.resize(pose,(pose.width*8,pose.height*8),True)
            pose_name=f'{color}_{style}_내려다보기_포즈_팀원기준_2026-11-25.png'
            pose.save(ROOT/pose_name,compress_level=1);files.append(pose_name)
            if color in ['빨강','초록','파랑']:
                other=alt.copy()
                other.putalpha(Image.fromarray(np.minimum(np.array(alt.getchannel('A')),np.array(mask))))
                other=a.trim(other)
                if pixel:other=a.resize(other,(other.width*8,other.height*8),True)
                other_name=f'{color}_{style}_표정2_내려다보기_포즈_팀원기준_2026-11-25.png'
                other.save(ROOT/other_name,compress_level=1);files.append(other_name)
                alternates.append(other)
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
        for pose in alternates:
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
            cell.alpha_composite(pose,xy);poses.append(cell)
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
