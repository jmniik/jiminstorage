from pathlib import Path
from PIL import Image, ImageSequence
import shutil
import zipfile
import json

SOURCE=Path(__file__).resolve().parent
OUT=SOURCE.with_name('전구모션_느린걷기_180ms')
OUT.mkdir(exist_ok=True)

def set_delays(data, centiseconds):
    """Change GIF timing metadata only; preserve compressed image bytes."""
    b=bytearray(data)
    assert b[:6] in (b'GIF87a',b'GIF89a')
    pos=13
    if b[10]&128:
        pos+=3*(2**((b[10]&7)+1))
    count=0
    def skip_blocks(p):
        while b[p]:
            p+=1+b[p]
        return p+1
    while pos<len(b):
        marker=b[pos]
        if marker==0x3b:
            break
        if marker==0x21:
            label=b[pos+1]
            pos+=2
            if label==0xf9:
                assert b[pos]==4
                b[pos+2:pos+4]=centiseconds.to_bytes(2,'little')
                count+=1
            pos=skip_blocks(pos)
        elif marker==0x2c:
            packed=b[pos+9]
            pos+=10
            if packed&128:
                pos+=3*(2**((packed&7)+1))
            pos+=1
            pos=skip_blocks(pos)
        else:
            raise ValueError((pos,marker))
    assert count==8
    return bytes(b)

report=[]
for path in SOURCE.glob('*.gif'):
    target=OUT/path.name
    target.write_bytes(set_delays(path.read_bytes(),18))
    with Image.open(path) as before, Image.open(target) as after:
        assert after.n_frames==8 and after.info['loop']==0
        for f,g in zip(ImageSequence.Iterator(before),ImageSequence.Iterator(after)):
            assert g.info['duration']==180
            assert f.convert('RGBA').tobytes()==g.convert('RGBA').tobytes()
        report.append({'file':target.name,'frames':8,'frame_ms':180,'loop_ms':1440,'pixels_unchanged':True})
for path in SOURCE.glob('*모션시트.png'):
    shutil.copy2(path,OUT/path.name)
shutil.copytree(SOURCE/'원배율_시트',OUT/'원배율_시트',dirs_exist_ok=True)
(OUT/'재생정보.txt').write_text('느린 걷기 버전: 180ms/프레임 × 8프레임 = 1.44초 무한 반복.\n기존 120ms 버전 대비 재생 속도 2/3. 픽셀과 PNG 시트는 동일하며 GIF의 재생 시간 정보만 변경했습니다.\n',encoding='utf-8')
(OUT/'검증결과.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
archive=OUT.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            z.write(p,p.relative_to(OUT))
print(json.dumps({'verified':report,'archive':str(archive)},ensure_ascii=True))
