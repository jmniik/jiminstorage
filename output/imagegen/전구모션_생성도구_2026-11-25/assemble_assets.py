from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np
import math, json, hashlib, time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
REF=HERE/'참고자료/팀원원본_표정_발광'
PIX=HERE/'참고자료/팀원최종기준'
CACHE=HERE/'프레임'
CACHE.mkdir(exist_ok=True)
COLORS={'흰색':'White','빨강':'Red','초록':'Green','파랑':'Blue','노랑':'Yellow'}
PIX_FILES={'흰색':'05_픽셀_흰색_정면.png','빨강':'04_픽셀_빨강_정면.png',
           '초록':'03_픽셀_초록_정면.png','파랑':'02_픽셀_파랑_정면.png','노랑':'01_픽셀_노랑_정면.png'}
MOTIONS=['정면걷기','점프','만세','오른쪽걷기','왼쪽걷기','대기','눈깜빡임','손흔들기','앉았다일어나기']
VIEWS=['정면','오른쪽측면','왼쪽측면','사분의삼측면','후면','윗면','얼굴확대']
RECORDS=[]
RIG_AUDIT=[]

def load(p):
    im=Image.open(p).convert('RGBA')
    a=np.array(im)
    a[a[:,:,3]<3]=0
    return Image.fromarray(a)

def save_png(im,name,kind,**metadata):
    path=ROOT/(name+'_팀원기준_2026-11-25.png')
    # These dated filenames are outputs of this build; source images are never written.
    im.save(path,compress_level=1)
    with Image.open(path) as check:
        assert check.size==im.size
        assert check.convert('RGBA').tobytes()==im.convert('RGBA').tobytes()
    RECORDS.append({'file':path.name,'kind':kind,'size':list(im.size),**metadata})
    return path

def resize(im,size,pixel=False):
    return im.resize(tuple(max(1,round(v)) for v in size),Image.Resampling.NEAREST if pixel else Image.Resampling.LANCZOS)

def original_canvas(im,pixel):
    # Fixed original-coordinate transform, identical for heads, faces and parts.
    im=im.crop((580,0,1420,1080))
    out=Image.new('RGBA',(112,160) if pixel else (448,640))
    out.alpha_composite(resize(im,(92,119) if pixel else (368,476),pixel),(10,30) if pixel else (40,120))
    if pixel:
        a=np.array(out); a[:,:,3]=np.where(a[:,:,3]>=128,255,0); a[a[:,:,3]==0,:3]=0
        out=Image.fromarray(a)
    return out

def trim(im):
    box=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    return im.crop(box) if box else Image.new('RGBA',(1,1))

def pixel_variant(color,expression):
    im=load(PIX/PIX_FILES[color])
    if color in ['빨강','초록','파랑']:
        # Use current named expression sources only for the eyebrow pixels.
        a=np.array(im)
        face_ref=np.array(load(REF/('Blue_face2.PNG' if expression==2 else 'Blue_face.PNG')))
        x0,y0,x1,y1=825,615,1175,695
        bg=tuple(a[600,1000,:3])
        a[y0:y1,x0:x1,:3]=bg
        a[y0:y1,x0:x1,3]=255
        dark=(face_ref[y0:y1,x0:x1,:3].max(axis=2)<90)&(face_ref[y0:y1,x0:x1,3]>128)
        part=a[y0:y1,x0:x1]
        part[dark]=(0,0,0,255)
        im=Image.fromarray(a)
    return im

def make_front(color,expression,pixel):
    en=COLORS[color]
    suffix='2' if expression==2 and color in ['빨강','초록','파랑'] else ''
    body_ref=load(REF/f'{en}_face{suffix}.PNG')
    if pixel:
        full=pixel_variant(color,expression)
        # The body-only alpha removes original stationary hands and shoes.
        a=np.array(full)
        sy=np.indices(a.shape[:2])[0]
        teal=(a[:,:,1].astype(int)>a[:,:,0].astype(int)+20)&(a[:,:,1].astype(int)>a[:,:,2].astype(int)+10)&(sy>=850)
        a[teal,3]=0
        mask=body_ref.getchannel('A').point(lambda v:255 if v>=128 else 0)
        a[:,:,3]=np.minimum(a[:,:,3],np.array(mask))
        body=original_canvas(Image.fromarray(a),True)
        full_canvas=original_canvas(full,True)
    else:
        body=original_canvas(body_ref,False)
        full_canvas=original_canvas(load(REF/f'{en}{suffix}.PNG'),False)
    parts={}
    for label,fn in [('handL','Hand_left.PNG'),('handR','Hand_right.PNG'),('footL','Foot_left.PNG'),('footR','Foot_right.PNG')]:
        part=trim(original_canvas(load(REF/fn),pixel))
        if pixel and label.startswith('hand'):
            a=np.array(part)
            skin=tuple(np.array(full_canvas)[109,56,:3])
            pale=(a[:,:,0]>180)&(a[:,:,1]>140)&(a[:,:,3]>0)
            a[pale,:3]=skin
            part=Image.fromarray(a)
        parts[label]=part
    return body,parts,full_canvas

def recolor_blue(im,color,pixel):
    if color=='파랑': return im.copy()
    a=np.array(im)
    rgb=a[:,:,:3].astype(float)/255
    r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    mask=(b-r>.12)&(b>=g-.025)&(b>.40)&(a[:,:,3]>0)
    # Ramp coordinate from saturated outer blue to pale cyan central highlight.
    level=np.clip((r+.35*g)/1.25,0,1)
    # Preserve center warmth and original outer hue for each named source.
    if color=='빨강':
        outer=np.array([232,45,49]); inner=np.array([255,164,160])
    elif color=='초록':
        outer=np.array([24,150,76]); inner=np.array([233,255,158])
    elif color=='노랑':
        outer=np.array([242,167,49]); inner=np.array([255,236,162])
    else:
        outer=np.array([191,191,207]); inner=np.array([235,241,255])
    mapped=outer[None,None,:]*(1-level[:,:,None])+inner[None,None,:]*level[:,:,None]
    a[mask,:3]=np.clip(mapped[mask],0,255).astype('uint8')
    if color=='흰색':
        # Neutralize the luminous coil, without changing its geometry.
        h,w=a.shape[:2]
        yy=np.indices((h,w))[0]
        filament=(a[:,:,0]>190)&(a[:,:,1]>185)&(a[:,:,2]<240)&(a[:,:,1].astype(int)-a[:,:,2].astype(int)>6)&(yy<h*.57)&(a[:,:,3]>0)
        a[filament,:3]=(174,174,178)
    return Image.fromarray(a)

def generated_views(color,pixel):
    source=load(HERE/('파랑_픽셀_방향원화.png' if pixel else '파랑_기본_방향원화.png'))
    frames=[]
    for i in range(7):
        c,r=i%4,i//4
        cell=source.crop((c*384,r*512,(c+1)*384,(r+1)*512))
        a=np.array(cell)
        # Generated alpha differs between exports: the pixel background is
        # partially opaque white; art is >=245, background is below 240.
        if pixel:
            a[:,:,3]=np.where(a[:,:,3]>=245,255,0)
        else:
            a[:,:,3]=np.where(a[:,:,3]>=160,a[:,:,3],0)
        a[a[:,:,3]==0,:3]=0
        cell=trim(Image.fromarray(a))
        scale=((78 if pixel else 312)/max(1,cell.width) if i==5 else (108 if pixel else 432)/max(1,cell.height))
        cell=resize(cell,(cell.width*scale,cell.height*scale),pixel)
        canvas=Image.new('RGBA',(112,160) if pixel else (448,640))
        baseline=142 if pixel else 568
        canvas.alpha_composite(cell,((canvas.width-cell.width)//2,baseline-cell.height))
        frames.append(recolor_blue(canvas,color,pixel))
    return frames

def connected(mask):
    seen=np.zeros_like(mask,dtype=bool); h,w=mask.shape; result=[]
    for y,x in zip(*np.where(mask)):
        if seen[y,x]:continue
        todo=[(y,x)]; seen[y,x]=True; comp=[]
        while todo:
            cy,cx=todo.pop(); comp.append((cy,cx))
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=True;todo.append((ny,nx))
        result.append(comp)
    return result

def face_only(body,pixel):
    small=body if pixel else resize(body,(112,160),False)
    a=np.array(small); rgb=a[:,:,:3].astype(int)
    skin=(rgb[:,:,0]>185)&(rgb[:,:,1]>150)&(rgb[:,:,2]>90)&(rgb[:,:,0]-rgb[:,:,2]>8)&(rgb[:,:,0]-rgb[:,:,1]<45)&(rgb[:,:,1]-rgb[:,:,2]<60)&(a[:,:,3]>128)
    skin[:85,:]=False
    comps=connected(skin)
    pts=max(comps,key=len)
    points=sorted(set((x,y) for y,x in pts))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for p in points:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    upper=[]
    for p in reversed(points):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    mask=Image.new('L',(112,160));d=ImageDraw.Draw(mask)
    hull=lower[:-1]+upper[:-1]
    d.polygon(hull,fill=255)
    q=1 if pixel else 4
    mask=resize(mask,body.size,pixel)
    outline=mask.filter(ImageFilter.MaxFilter(3 if pixel else 9))
    out=Image.new('RGBA',body.size,(0,0,0,0))
    ink=Image.new('RGBA',body.size,(0,0,0,255));ink.putalpha(outline)
    out.alpha_composite(ink)
    fill=body.copy();fill.putalpha(Image.fromarray(np.minimum(np.array(body.getchannel('A')),np.array(mask))))
    out.alpha_composite(fill)
    return trim(out)

def direction_expression(im,color,expression,pixel):
    small=im if pixel else resize(im,(112,160),False)
    a=np.array(small)
    rgb=a[:,:,:3].astype(int)
    skin=(rgb[:,:,0]>180)&(rgb[:,:,1]>145)&(rgb[:,:,2]>90)&(rgb[:,:,0]-rgb[:,:,2]>8)&(rgb[:,:,0]-rgb[:,:,1]<45)&(rgb[:,:,1]-rgb[:,:,2]<60)&(a[:,:,3]>128)
    skin[:75,:]=False
    comps=connected(skin)
    if not comps:return im
    main=max(comps,key=len)
    if len(main)<70:return im
    yy,xx=np.array(main).T
    x0,x1,y0,y1=int(xx.min()),int(xx.max()),int(yy.min()),int(yy.max())
    fw,fh=x1-x0+1,y1-y0+1
    dark=(rgb.max(axis=2)<85)&(a[:,:,3]>128)
    keep=np.zeros(dark.shape,dtype=bool)
    keep[y0+3:y1-3,x0+3:x1-3]=True
    marks=connected(dark&keep)
    q=1 if pixel else 4
    out=im.copy(); d=ImageDraw.Draw(out)
    skinrgb=tuple(int(v) for v in np.median(rgb[yy,xx],axis=0))+(255,)
    for mark in marks:
        my,mx=np.array(mark).T
        cy=float(my.mean());cx=float(mx.mean())
        rel=(cy-y0)/max(1,fh)
        if len(mark)<2 or len(mark)>45:continue
        if .08<rel<.29 and len(mark)>=3:
            # Existing eyebrow location is retained; only shape changes.
            bx0,bx1=int(mx.min()),int(mx.max());by=round(cy)
            for py,px in mark:d.rectangle((px*q,py*q,(px+1)*q-1,(py+1)*q-1),fill=skinrgb)
            w=max(3,bx1-bx0)
            if color=='흰색':
                delta=-2 if cx<(x0+x1)/2 else 2
            elif color=='노랑' or expression==2:
                delta=2 if cx<(x0+x1)/2 else -2
            else:delta=0
            d.line((bx0*q,(by-delta/2)*q,bx1*q,(by+delta/2)*q),fill=(0,0,0,255),width=max(1,2*q))
        elif color=='흰색' and .50<rel<.86 and len(mark)>=5 and int(mx.max())-int(mx.min())>=4:
            for py,px in mark:d.rectangle((px*q,py*q,(px+1)*q-1,(py+1)*q-1),fill=skinrgb)
            bx0,bx1=int(mx.min()),int(mx.max()); by=round(cy)
            span=bx1-bx0
            points=[(bx0*q,by*q),((bx0+span*.25)*q,(by+.4)*q),
                    ((bx0+span*.5)*q,(by-1.1)*q),((bx0+span*.75)*q,(by+.4)*q),(bx1*q,by*q)]
            d.line(points,fill=(0,0,0,255),width=max(1,2*q),joint='curve')
    return out

def side_parts(im,pixel):
    a=np.array(im); h,w=a.shape[:2]
    q=1 if pixel else 4
    # Extract a shoe as one solid sprite, then retain the head/face rigidly.
    teal=(a[:,:,1].astype(int)>a[:,:,0].astype(int)+20)&(a[:,:,1].astype(int)>a[:,:,2].astype(int)+10)&(a[:,:,3]>128)
    teal[:round(h*.82),:]=False
    fy,fx=np.where(teal)
    if len(fx):footbox=(max(0,int(fx.min())-q),max(0,int(fy.min())-q),min(w,int(fx.max())+q+1),min(h,int(fy.max())+q+1))
    else:footbox=(0,round(h*.81),w,round(h*.90))
    foot=trim(im.crop(footbox))
    body=im.copy()
    body.paste((0,0,0,0),footbox)
    body.paste((0,0,0,0),(0,footbox[3],w,h))
    # Mask the small side hand and its outline. It will be animated separately.
    rgb=a[:,:,:3].astype(int)
    skin=(rgb[:,:,0]>180)&(rgb[:,:,1]>185)&(rgb[:,:,2]>145)&(rgb[:,:,0]-rgb[:,:,1]>3)&(rgb[:,:,0]-rgb[:,:,1]<45)&(rgb[:,:,1]-rgb[:,:,2]<60)&(a[:,:,3]>0)
    skin[:round(h*.60),:]=False
    skin[round(h*.82):,:]=False
    choices=[]
    # Select a complete small skin component, never a rectangular face slice.
    sm=Image.fromarray(skin.astype('uint8')*255).resize((112,160),Image.Resampling.NEAREST)
    for comp in connected(np.array(sm)>0):
        py,px=np.array(comp).T
        if 5<=len(comp)<=180 and px.mean()<63 and py.mean()>103:
            choices.append((abs(px.mean()-58)+abs(py.mean()-122),comp))
    if choices:
        comp=min(choices,key=lambda x:x[0])[1]
        py,px=np.array(comp).T
        xx=np.rint(px*q).astype(int); yy=np.rint(py*q).astype(int)
    else: yy,xx=np.array([],dtype=int),np.array([],dtype=int)
    if len(xx)>3:
        box=(max(0,int(xx.min())-q),max(0,int(yy.min())-q),min(w,int(xx.max())+q+1),min(h,int(yy.max())+q+1))
        hand=trim(im.crop(box))
        body.paste((0,0,0,0),box)
        center=((box[0]+box[2])/2,(box[1]+box[3])/2)
    else:
        hand=Image.new('RGBA',(10*q,10*q),(255,238,218,255))
        center=(w*.43,h*.75)
    return body,hand,foot,center

def paste_center(out,part,xy,pixel,scale=1,angle=0):
    p=resize(part,(part.width*scale,part.height*scale),pixel)
    if angle:
        p=p.rotate(angle,resample=Image.Resampling.NEAREST if pixel else Image.Resampling.BICUBIC,expand=True)
    x,y=round(xy[0]-p.width/2),round(xy[1]-p.height/2)
    out.alpha_composite(p,(x,y))

def shadow(out,pixel,amount=1):
    q=1 if pixel else 4
    d=ImageDraw.Draw(out)
    half=round(32*q*amount)
    d.ellipse((56*q-half,145*q,56*q+half,150*q),fill=(104,106,116,85))
    d.ellipse((56*q-round(half*.73),146*q,56*q+round(half*.73),149*q),fill=(74,76,86,90))

def blink_body(body,pixel,closed):
    if not closed:return body.copy()
    out=body.copy(); q=1 if pixel else 4
    d=ImageDraw.Draw(out)
    bg=out.getpixel((56*q,111*q))
    for cx in (45,66):
        d.rectangle((cx*q-3*q,107*q,cx*q+3*q,113*q),fill=bg)
        d.line((cx*q-2*q,110*q,cx*q+2*q,110*q),fill=(0,0,0,255),width=max(1,q))
    return out

def rig_front(body,parts,motion,pixel,i):
    q=1 if pixel else 4
    phase=2*math.pi*i/8
    out=Image.new('RGBA',body.size)
    yoff=0; spread=0
    if motion=='점프': yoff=-[0,3,10,18,21,16,7,0][i]*q
    if motion=='앉았다일어나기': yoff=[0,2,5,8,10,8,5,2][i]*q; spread=yoff*.3
    shadow(out,pixel,1-abs(min(yoff,0))/(60*q))
    positions={'handL':[27*q,123*q+yoff],'handR':[85*q,123*q+yoff],
               'footL':[40*q-spread,135*q+yoff],'footR':[73*q+spread,135*q+yoff]}
    scales={k:1 for k in parts}; angles={k:0 for k in parts}
    if motion=='정면걷기':
        for k,sign in [('handL',1),('handR',-1)]:
            f=sign*math.sin(phase)
            positions[k][0]+=sign*3*q*f
            positions[k][1]-=max(0,f)*5*q
            scales[k]=1+.35*f
        for k,sign in [('footL',-1),('footR',1)]:
            f=sign*math.sin(phase)
            positions[k][1]-=max(0,f)*5*q
            scales[k]=1+.15*f
            angles[k]=f*12
    elif motion=='만세':
        level=[0,.3,.65,1,1,.65,.3,0][i]
        positions['handL']=[(27-10*level)*q,(123-55*level)*q]
        positions['handR']=[(85+10*level)*q,(123-55*level)*q]
    elif motion=='손흔들기':
        positions['handR']=[(90+4*math.sin(phase))*q,92*q]
        angles['handR']=20*math.sin(phase)
    elif motion=='점프':
        positions['handL'][0]-=5*q; positions['handR'][0]+=5*q
        positions['handL'][1]-=5*q; positions['handR'][1]-=5*q
        angles['footL']=abs(yoff/q)*.6; angles['footR']=-angles['footL']
    else:
        positions['handL'][1]+=round(math.sin(phase))*q
        positions['handR'][1]+=round(math.sin(phase))*q
    backhand='handL' if math.sin(phase)<0 else 'handR'
    paste_center(out,parts[backhand],positions[backhand],pixel,scales[backhand])
    for k in ['footL','footR']:
        paste_center(out,parts[k],positions[k],pixel,scales[k],angles[k])
    current=blink_body(body,pixel,motion=='눈깜빡임' and i in (3,4))
    out.alpha_composite(current,(0,round(yoff)))
    for k in ['handL','handR']:
        if k!=backhand:paste_center(out,parts[k],positions[k],pixel,scales[k],angles[k])
    return out

def rig_side(source,pixel,i,left=False):
    q=1 if pixel else 4
    body,hand,foot,center=side_parts(source,pixel)
    out=Image.new('RGBA',source.size)
    shadow(out,pixel)
    f=math.sin(i*math.pi/4)
    paste_center(out,foot,(55*q-7*q*f,136*q-max(0,f)*4*q),pixel,1,8*f)
    out.alpha_composite(body)
    paste_center(out,foot,(55*q+7*q*f,137*q-max(0,-f)*4*q),pixel,1,-8*f)
    paste_center(out,hand,(center[0]+4*q*f,center[1]-3*q*f),pixel,1+.12*f)
    return ImageOps.mirror(out) if left else out

def add_glow(frame,color,pixel):
    q=1 if pixel else 4
    out=Image.new('RGBA',frame.size)
    palette={'빨강':(255,77,99),'초록':(142,255,95),'파랑':(86,211,255),'노랑':(255,218,85)}
    if color not in palette:return frame.copy()
    d=ImageDraw.Draw(out); rgb=palette[color]
    # A discrete pixel halo in pixel style; smooth halo in basic style.
    for radius,alpha in [(49,18),(45,30),(41,50),(37,70)]:
        d.ellipse(((56-radius)*q,(87-radius)*q,(56+radius)*q,(87+radius)*q),fill=rgb+(alpha,))
    if not pixel:out=out.filter(ImageFilter.GaussianBlur(5))
    solid=frame.getchannel('A').point(lambda v:255 if v>=128 else 0)
    outline=(solid.filter(ImageFilter.MaxFilter(5)) if pixel else
             solid.filter(ImageFilter.GaussianBlur(4)).point(lambda v:min(255,max(0,(v-5)*40))))
    ink=Image.new('RGBA',frame.size,(0,0,0,255));ink.putalpha(outline)
    out.alpha_composite(ink)
    out.alpha_composite(frame)
    return out

def indexed_pixel(frames):
    # One palette shared across every frame in a motion, no dithering.
    atlas=Image.new('RGB',(frames[0].width*len(frames),frames[0].height))
    for i,f in enumerate(frames): atlas.paste(f.convert('RGB'),(i*f.width,0))
    pal=atlas.quantize(colors=127,method=Image.Quantize.MEDIANCUT)
    out=[]
    for f in frames:
        ind=f.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE)
        a=f.getchannel('A')
        ind.paste(255,mask=a.point(lambda v:255 if v==0 else 0))
        ind.info['transparency']=255
        # Keep discretized alpha for pixel glow PNGs via per-index alpha.
        rgba=ind.convert('RGBA')
        rgba.putalpha(a)
        out.append(rgba)
    return out

def display(im,pixel):
    return resize(im,(im.width*4,im.height*4),True) if pixel else im

def sheet(frames,cols=4):
    rows=math.ceil(len(frames)/cols)
    out=Image.new('RGBA',(frames[0].width*cols,frames[0].height*rows))
    for i,f in enumerate(frames):out.alpha_composite(f,((i%cols)*f.width,(i//cols)*f.height))
    return out

def completed_records(prefix,color,style,expression):
    result=[]
    def add(suffix,kind,size,**kw):
        result.append({'file':prefix+suffix+'_팀원기준_2026-11-25.png','kind':kind,'size':size,
                       'color':color,'style':style,'expression':expression,**kw})
    add('_방향시트','directions',[1792,1280],views=VIEWS)
    add('_상태시트','states',[896,640],states=['비발광'] if color=='흰색' else ['일반','발광'])
    for part in ['손','발']:add('_'+part+'부품시트','parts',[1792,1280],part=part)
    for state in (['일반'] if color=='흰색' else ['일반','발광']):
        for motion in MOTIONS:
            add('_'+state+'_'+motion+'_모션시트','motion',[1792,1280],state=state,motion=motion,frames=8,cell=[448,640])
        add('_'+state+'_종합모션시트','master',[3584,5760],state=state,motions=MOTIONS,frames_per_motion=8)
    try:
        for r in result:
            with Image.open(ROOT/r['file']) as im:
                if list(im.size)!=r['size']:return None
                im.verify()
    except (OSError,ValueError):return None
    return result

def run():
    for pixel,style in [(True,'픽셀'),(False,'기본')]:
        for color,en in COLORS.items():
            generated=generated_views(color,pixel)
            for expression in ([1,2] if color in ['빨강','초록','파랑'] else [1]):
                body,parts,front=make_front(color,expression,pixel)
                prefix=f'{color}_{style}_표정{expression}'
                complete=completed_records(prefix,color,style,expression)
                if complete:
                    RECORDS.extend(complete)
                    RIG_AUDIT.append({'color':color,'style':style,'expression':expression,
                        'front_body_sha256':hashlib.sha256(body.tobytes()).hexdigest(),
                        'body_scale':1,'body_rotation':0,'filament_redrawn':False})
                    print('already_saved',prefix,flush=True)
                    continue
                # Restore exact provided front as the first turnaround view.
                views=[front]+[direction_expression(v,color,expression,pixel) for v in generated[1:]]
                # Face enlargement is derived from the original face design.
                q=1 if pixel else 4
                face=face_only(body,pixel)
                close=Image.new('RGBA',body.size)
                face=resize(face,(face.width*1.55,face.height*1.55),pixel)
                close.alpha_composite(face,((close.width-face.width)//2,(close.height-face.height)//2))
                views[6]=close
                if pixel:views=indexed_pixel(views)
                prefix=f'{color}_{style}_표정{expression}'
                save_png(sheet([display(v,pixel) for v in views]),prefix+'_방향시트','directions',color=color,style=style,expression=expression,views=VIEWS)
                stateframes=[]
                for state in (['일반'] if color=='흰색' else ['일반','발광']):
                    stateframes.append(add_glow(front,color,pixel) if state=='발광' else front)
                save_png(sheet([display(f,pixel) for f in stateframes],2),prefix+'_상태시트','states',color=color,style=style,expression=expression,states=['비발광'] if color=='흰색' else ['일반','발광'])
                for partname,keys in [('손',['handL','handR']),('발',['footL','footR'])]:
                    poses=[]
                    for key in keys:
                        for i in range(4):
                            pose=Image.new('RGBA',body.size)
                            paste_center(pose,parts[key],(pose.width/2,pose.height/2),pixel,.8+i*.15,[-20,0,15,30][i])
                            poses.append(display(pose,pixel))
                    save_png(sheet(poses),prefix+f'_{partname}부품시트','parts',color=color,style=style,part=partname,expression=expression)
                base_motions={}
                for motion in MOTIONS:
                    frames=[]
                    for i in range(8):
                        if motion in ['오른쪽걷기','왼쪽걷기']:
                            f=rig_side(views[1],pixel,i,motion=='왼쪽걷기')
                        else:f=rig_front(body,parts,motion,pixel,i)
                        frames.append(f)
                    base_motions[motion]=frames
                # No body scale or filament drawing operation occurs in rigging.
                RIG_AUDIT.append({'color':color,'style':style,'expression':expression,
                    'front_body_sha256':hashlib.sha256(body.tobytes()).hexdigest(),
                    'body_scale':1,'body_rotation':0,'filament_redrawn':False})
                for state in (['일반'] if color=='흰색' else ['일반','발광']):
                    allframes=[]
                    for motion,frames in base_motions.items():
                        f=[add_glow(x,color,pixel) for x in frames] if state=='발광' else frames
                        if pixel:f=indexed_pixel(f)
                        shown=[display(x,pixel) for x in f]
                        name=prefix+'_'+state+'_'+motion
                        save_png(sheet(shown),name+'_모션시트','motion',color=color,style=style,expression=expression,state=state,motion=motion,frames=8,cell=[448,640])
                        allframes.extend(shown)
                    save_png(sheet(allframes,8),prefix+'_'+state+'_종합모션시트','master',color=color,style=style,expression=expression,state=state,motions=MOTIONS,frames_per_motion=8)
                print(json.dumps({'done':prefix,'files':len(RECORDS)},ensure_ascii=True),flush=True)
    (HERE/'PNG_산출물.json').write_text(json.dumps(RECORDS,ensure_ascii=False,indent=2),encoding='utf-8')
    (HERE/'몸체고정_검증.json').write_text(json.dumps(RIG_AUDIT,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PNG_STAGE_COMPLETE',len(RECORDS),flush=True)

if __name__=='__main__':run()
