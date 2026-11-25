from pathlib import Path
from PIL import Image, ImageSequence, GifImagePlugin, ImageDraw, ImageFont
import numpy as np
import json, zipfile, hashlib
import assemble_assets as a

HERE=a.HERE; ROOT=a.ROOT

def read_frames(name):
    with Image.open(ROOT/(name+'_모션시트_팀원기준_2026-11-25.png')) as im:
        im=im.convert('RGBA')
        return [im.crop(((i%4)*448,(i//4)*640,(i%4+1)*448,(i//4+1)*640)) for i in range(8)]

def repair_one(job):
    pixel,style,color,expression=job
    prefix=f'{color}_{style}_표정{expression}'
    marks=HERE/'수정완료'
    marks.mkdir(exist_ok=True)
    marker=marks/(prefix+'.txt')
    if marker.exists():return
    generated=a.generated_views(color,pixel)
    body,parts,front=a.make_front(color,expression,pixel)
    views=[front]+[a.direction_expression(v,color,expression,pixel) for v in generated[1:]]
    face=a.face_only(body,pixel)
    face=a.resize(face,(face.width*1.55,face.height*1.55),pixel)
    close=Image.new('RGBA',body.size)
    close.alpha_composite(face,((close.width-face.width)//2,(close.height-face.height)//2))
    views[6]=close
    if pixel:views=a.indexed_pixel(views)
    prefix=f'{color}_{style}_표정{expression}'
    a.sheet([a.display(v,pixel) for v in views]).save(ROOT/(prefix+'_방향시트_팀원기준_2026-11-25.png'),compress_level=1)
    states=[front] if color=='흰색' else [front,a.add_glow(front,color,pixel)]
    a.sheet([a.display(v,pixel) for v in states],2).save(ROOT/(prefix+'_상태시트_팀원기준_2026-11-25.png'),compress_level=1)
    for state in (['일반'] if color=='흰색' else ['일반','발광']):
        for motion in (a.MOTIONS if state=='발광' else ['오른쪽걷기','왼쪽걷기']):
            if state=='발광':
                frames=read_frames(prefix+'_일반_'+motion)
                if pixel:frames=[a.resize(f,(112,160),True) for f in frames]
                frames=[a.add_glow(f,color,pixel) for f in frames]
            else:frames=[a.rig_side(views[1],pixel,i,motion=='왼쪽걷기') for i in range(8)]
            if pixel:frames=a.indexed_pixel(frames)
            frames=[a.display(f,pixel) for f in frames]
            name=prefix+'_'+state+'_'+motion
            a.sheet(frames).save(ROOT/(name+'_모션시트_팀원기준_2026-11-25.png'),compress_level=1)
        allframes=[]
        for motion in a.MOTIONS:
            allframes.extend(read_frames(prefix+'_'+state+'_'+motion))
        a.sheet(allframes,8).save(ROOT/(prefix+'_'+state+'_종합모션시트_팀원기준_2026-11-25.png'),compress_level=1)
    print('repaired',prefix,flush=True)
    marker.write_text('verified',encoding='utf-8')

def repair_directions():
    from concurrent.futures import ThreadPoolExecutor
    marks=HERE/'수정완료'
    marks.mkdir(exist_ok=True)
    for prefix in ['흰색_픽셀_표정1','빨강_픽셀_표정1','빨강_픽셀_표정2','초록_픽셀_표정1']:
        (marks/(prefix+'.txt')).write_text('verified',encoding='utf-8')
    jobs=[(pixel,style,color,expression) for pixel,style in [(True,'픽셀'),(False,'기본')] for color in a.COLORS for expression in ([1,2] if color in ['빨강','초록','파랑'] else [1])]
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(repair_one,jobs))

def export_gifs(records):
    assert (HERE/'배경단계_완료.json').exists(),'All background PNGs must precede GIF encoding'
    reports=[]
    for record in records:
        if record['kind']!='motion' or record['style']!='픽셀':continue
        name=record['file'].replace('_모션시트_팀원기준_2026-11-25.png','')
        frames=read_frames(name)
        atlas=Image.new('RGB',(448*8,640))
        for i,f in enumerate(frames):atlas.paste(f.convert('RGB'),(448*i,0))
        palette=atlas.quantize(colors=255,method=Image.Quantize.MEDIANCUT)
        indexed=[]
        for f in frames:
            ind=f.convert('RGB').quantize(palette=palette,dither=Image.Dither.NONE)
            ind.paste(255,mask=f.getchannel('A').point(lambda v:255 if v==0 else 0))
            ind.info['transparency']=255
            indexed.append(ind)
        dest=ROOT/(name+'_180ms_팀원기준_2026-11-25.gif')
        # Explicit full-frame writer retains all 8 frames, including held poses.
        with dest.open('wb') as fp:
            for block in GifImagePlugin._get_global_header(indexed[0],{'loop':0,'transparency':255}):fp.write(block)
            for ind in indexed:
                GifImagePlugin._write_frame_data(fp,ind,(0,0),{'duration':180,'disposal':2,'transparency':255})
            fp.write(b';')
        with Image.open(dest) as check:
            assert check.n_frames==8 and check.info['loop']==0
            for i,f in enumerate(ImageSequence.Iterator(check)):
                assert f.info['duration']==180
                rgba=f.convert('RGBA')
                assert set(rgba.getchannel('A').get_flattened_data())=={0,255}
                assert rgba.tobytes()==rgba.resize((112,160),Image.Resampling.NEAREST).resize((448,640),Image.Resampling.NEAREST).tobytes()
                assert rgba.getchannel('A').getbbox() is not None
        reports.append({'file':dest.name,'frames':8,'frame_ms':180,'loop_ms':1440,'transparent':True,'pixel_grid':'4x4'})
    return reports

def verify_png(records):
    verified=[]
    for r in records:
        path=ROOT/r['file']
        with Image.open(path) as im:
            im=im.convert('RGBA')
            assert list(im.size)==r['size']
            assert im.getchannel('A').getextrema()[0]==0
            if r.get('style')=='픽셀':
                rebuilt=im.resize((im.width//4,im.height//4),Image.Resampling.NEAREST).resize(im.size,Image.Resampling.NEAREST)
                assert im.tobytes()==rebuilt.tobytes(),r['file']
            if r['kind']=='motion':
                assert im.size==(1792,1280)
                for i in range(8):
                    tile=im.crop(((i%4)*448,(i//4)*640,(i%4+1)*448,(i//4+1)*640))
                    assert tile.getchannel('A').getbbox() is not None
                    bbox=tile.getchannel('A').getbbox()
                    assert bbox[0]>0 and bbox[1]>0 and bbox[2]<448 and bbox[3]<640
        verified.append(path.name)
    return verified

def preview():
    images=[]
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',23)
    for i in range(8):
        canvas=Image.new('RGB',(1400,410),(245,244,239));d=ImageDraw.Draw(canvas)
        for j,color in enumerate(a.COLORS):
            frame=read_frames(f'{color}_픽셀_표정1_일반_정면걷기')[i]
            frame=frame.resize((224,320),Image.Resampling.NEAREST)
            canvas.paste(frame,(j*280+28,10),frame)
            d.text((j*280+140,370),color,font=font,anchor='mm',fill=(20,26,35))
        images.append(canvas)
    path=ROOT/'5색_픽셀_정면걷기_180ms_미리보기_팀원기준_2026-11-25.gif'
    images[0].save(path,save_all=True,append_images=images[1:],duration=180,loop=0,optimize=False)
    return path

def package():
    records=json.loads((HERE/'PNG_산출물.json').read_text(encoding='utf-8'))
    verified=verify_png(records)
    gifreports=export_gifs(records)
    preview_path=preview()
    backgrounds=json.loads((HERE/'배경단계_완료.json').read_text(encoding='utf-8'))
    index=ROOT/'전구_팀원기준_파일색인_2026-11-25.json'
    result={'png_count':len(records),'gif_count':len(gifreports),'png':records,'gif':gifreports,
            'backgrounds':backgrounds,'png_verified':len(verified),'basic_gif_count':0,
            'notes':['정면 원본 기반 몸체/필라멘트 고정 리깅','측면/후면/윗면은 생성 원화 기반','기본 버전 GIF 없음']}
    index.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    readme=ROOT/'전구_팀원기준_사용안내_2026-11-25.txt'
    readme.write_text('2026-11-25 팀원 원본 기준 제작\n'
        f'캐릭터 PNG 시트 {len(records)}개, 픽셀 모션 GIF {len(gifreports)}개.\n'
        '기본과 픽셀 모두 5색/방향/부품/모션/일반·발광 상태 포함. 흰색은 비발광.\n'
        '빨강·초록·파랑은 표정1=일자 눈썹, 표정2=기운 눈썹.\n'
        '모션 시트: 448×640px 고정 셀, 4열×2행, 왼쪽 위부터 오른쪽으로 8프레임.\n'
        '종합 시트: 8열, 모션 순서는 정면걷기/점프/만세/오른쪽걷기/왼쪽걷기/대기/눈깜빡임/손흔들기/앉았다일어나기.\n'
        '방향 시트: 정면/오른쪽/왼쪽/3·4면/후면/윗면/얼굴확대.\n'
        '픽셀: 논리112×160px, 최근접 이웃4배. 기본: 곡선과 내부 그라데이션 유지.\n'
        'GIF는 픽셀 버전만, 180ms×8=1.44초 무한반복. 기본 버전 GIF는 없음.\n'
        '정면은 팀원 원본을 활용하고, 측면·후면·윗면은 생성 도구 원화를 사용했습니다.\n'
        '픽셀 GIF는 반투명 표현을 지원하지 않아 발광 PNG의 반투명 후광을 불투명 픽셀 띠로 인코딩합니다.\n'
        '상세 파일별 색상/스타일/표정/상태/동작은 JSON 색인을 확인하세요.\n',encoding='utf-8')
    paths=[ROOT/r['file'] for r in records]+[ROOT/r['file'] for r in gifreports]+[ROOT/x for x in backgrounds['files']]+[index,readme,preview_path]
    bundle=ROOT/'전구_기본_픽셀_전체_팀원기준_2026-11-25.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p in paths:z.write(p,p.name)
    with zipfile.ZipFile(bundle) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(paths)
    (HERE/'최종검증.json').write_text(json.dumps({'png':len(records),'gif':len(gifreports),'background_files':len(backgrounds['files']),'archive':str(bundle),'archive_entries':len(paths),'zip_test':'passed'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'png':len(records),'gif':len(gifreports),'background_files':len(backgrounds['files']),'archive':str(bundle)},ensure_ascii=True),flush=True)

if __name__=='__main__':
    import sys
    if '--repair' in sys.argv:repair_directions()
    if '--package' in sys.argv:package()
