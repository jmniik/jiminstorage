"""아래에서 올려다본 전구 5색 (480x270 픽셀 -> 4배 = 1920x1080). 사이트와 같은 픽셀 크기(PX=4)."""
import math
from PIL import Image
W,H,PX=480,270,4
im=Image.new('RGB',(W,H)); P=im.load()
mix=lambda a,b,t:tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def put(x,y,c,a=1):
    if 0<=x<W and 0<=y<H: P[x,y]=c if a>=1 else mix(P[x,y],c,a)
# ---- 하늘 (사이트처럼 3px 띠) ----
for y in range(H):
    t=(y//3*3)/H; c=mix((38,104,232),(112,200,244),t)
    for x in range(W): P[x,y]=c
# ---- 구름: 원을 겹친 계단 실루엣 + 2톤 ----
def cloud(circs):
    def inside(x,y,dx,dy): return any((x-cx-dx)**2+(y-cy-dy)**2<r*r for cx,cy,r in circs)
    for y in range(0,H,2):
        for x in range(0,W,2):
            if not inside(x,y,0,0): continue
            c=(255,255,255) if not inside(x,y,-3,6) else (232,248,250) if inside(x,y,-6,16)==False else (204,236,240)
            for j in (0,1):
                for i in (0,1): put(x+i,y+j,c)
cloud([(8,150,34),(50,160,30),(88,190,36),(108,222,36),(120,258,32),(40,220,70)])
cloud([(462,218,32),(424,242,30),(390,262,26),(474,252,40)])
# ---- 전구 ----
K=(6,7,20)
SKIN=(254,238,220); CHEEK=(254,141,78); FIL=(254,252,215)
COL={ # light, mid, dark, 하이라이트, 호, 빛줄기
 'white':((242,236,244),(228,221,234),(203,195,216),(255,255,255),(252,250,254),None),
 'red':((255,92,88),(250,66,64),(222,44,48),(255,234,244),(252,148,144),(250,28,28)),
 'green':((128,252,62),(92,246,28),(58,214,8),(252,255,252),(184,253,146),(40,205,20)),
 'blue':((52,202,254),(24,172,255),(5,129,248),(232,252,255),(134,216,252),(0,140,245)),
 'yellow':((253,212,112),(248,188,78),(230,160,54),(255,249,224),(252,222,150),(232,164,48)),
}
def seg(x,y,a,b,r):
    vx,vy=b[0]-a[0],b[1]-a[1]; t=max(0,min(1,((x-a[0])*vx+(y-a[1])*vy)/(vx*vx+vy*vy)))
    return math.hypot(x-a[0]-vx*t,y-a[1]-vy*t)<r
def filament(x,y):
    x/=.80; y=1.02+(y-.775)*1.62
    return fil0(x,y)
def fil0(x,y):              # 빨강 시트 필라멘트: 가로막대 + 다리 3개 + 네모 발
    ax=abs(x)
    if ax<.35 and 1.58<y<1.75: return True
    if ax<.07 and 1.02<y<1.6: return True
    if ax<.105 and 1.02<y<1.2: return True
    if 1.02<y<1.2 and .30<ax<.50: return True
    if 1.2<=y<1.37 and .24<ax<.44: return True
    if 1.37<=y<1.48 and .16<ax<.36: return True
    if 1.48<=y<1.6 and .12<ax<.28: return True
    return False
MOUTH=[(-.21,-.15),(-.17,-.25),(-.07,-.25),(0,-.16),(.07,-.25),(.17,-.25),(.21,-.15)]
def feature(x,y,face):
    y-=.14; ax=abs(x)
    if face=='flat':
        if .235<ax<.585 and .185<y<.27: return K
    elif face=='sad':
        if seg(ax,y,(.26,.33),(.56,.19),.048): return K
    else:
        if seg(ax,y,(.24,.13),(.50,.25),.05): return K
    if math.hypot(ax-.40,y-.04)<.072: return K
    for a,b in zip(MOUTH,MOUTH[1:]):
        if seg(x,y,a,b,.044): return K
    if max(abs(ax-.615)/.155,abs(y+.205)/.13,(abs(ax-.615)/.155+abs(y+.205)/.13)/1.5)<1: return CHEEK
    return None
def bulb(name,cx,cy,s,deg):
    """cx,cy=얼굴 중심, s=얼굴 반폭, deg=머리(소켓) 방향: 0=위, 시계방향"""
    L,M,Dk,HI,ARC,RAY=COL[name]; face={'white':'sad','yellow':'angry'}.get(name,'flat')
    an=math.radians(deg); ux,uy=math.sin(an),-math.cos(an); rx,ry=-uy,ux
    T=3/s
    GX,GY,GC=1.04,.82,.52
    ell=lambda x,y,ex,ey,a,b:(math.hypot((x-ex)/a,(y-ey)/b)-1)*min(a,b)
    for py in range(H):
        for px in range(W):
            dx,dy=px+.5-cx,py+.5-cy; x=(dx*rx+dy*ry)/s; y=(dx*ux+dy*uy)/s
            if abs(x)>1.7 or y<-1.2 or y>2.9: continue
            c=None
            ax=abs(x)
            if RAY:
                for a,b in (((.48,1.46),(.56,1.56)),((.64,1.34),(.76,1.42))):
                    if seg(ax,y,a,b,.045): c=RAY
            # 소켓 (멀어서 작고 짧게)
            if 1.26<y<1.58:
                t=(y-1.30)/.28; hw=.36-.09*max(0,t)+(.03 if int(t*6)%2==0 else 0)
                if ax<hw:
                    c=K
                    if ax<hw-T and y<1.58-T and y>1.3:
                        stripe=int(t*6)%2==1
                        c=(104,104,108) if stripe else (250,250,250) if -.28<x<-.1 else (176,176,180) if x>.2 else (214,214,218)
            if 1.56<=y<1.65 and ax<.16: c=K
            # 유리
            g=ell(x,y,0,GC,GX,GY)
            if g<0:
                if g>-T: c=K
                else:
                    q=math.hypot((x+.15)/GX,(y-GC-.1)/GY)
                    c=L if q<.62 else M if q<.86 else Dk
                    if seg(x,y,(-.60,1.02),(-.50,1.10),.075): c=HI
                    if abs(x+.76)<.06 and abs(y-.82)<.06: c=HI
                    if abs(math.hypot(x/.86,(y-GC)/.66)-1)<.045 and .35<math.atan2(y-GC,x)<1.0: c=ARC
                    if name!='white':       # 빨강 시트처럼 필라멘트에 붙은 주황빛 (4색 공통)
                        near=lambda r:any(filament(x+r*math.cos(k*.785),y+r*math.sin(k*.785)) for k in range(8))
                        if near(.035): c=(255,178,74)
                        elif near(.075): c=mix(c,(255,160,64),.55)
                    if filament(x,y): c=FIL if name!='white' else (176,173,176)
            # 얼굴
            f=ell(x,y,0,0,1,.70)
            if f<0:
                c=K if f>-T else feature(x,y,face) or SKIN
                if c==SKIN and math.hypot(x,(y-.12)/.75)>.86 and y<.2: c=(246,220,196)
            if c: P[px,py]=c
# 원본(2000x1125) 좌표 x 0.24
bulb('green',85,28,76,169)     # 원본 주황
bulb('red',262,-4,58,180)     # 원본 빨강
bulb('yellow',450,18,60,212)   # 원본 노랑
bulb('blue',56,272,60,23)      # 원본 파랑
bulb('white',425,262,60,-16)   # 원본 분홍
# ---- 햇빛 ----
SX,SY=146,138
for y in range(H):
    for x in range(W):
        dx,dy=x-SX,y-SY; d=math.hypot(dx,dy); a=0
        for r,v in ((46,.10),(32,.14),(21,.22)):
            if d<r: a=max(a,v)
        if a: put(x,y,(255,255,255),a)
for k in range(12):
    an=k*math.pi/6+.2; L=62 if k%2==0 else 36
    for i in range(10,L):
        w=1 if i>L*.5 else 2
        for j in range(w): put(round(SX+math.cos(an)*i),round(SY+math.sin(an)*i)+j,(255,255,255),.75*(1-i/L)+.1)
for y in range(H):
    for x in range(W):
        d=math.hypot(x-SX,y-SY)
        if d<9: P[x,y]=(255,255,255)
        elif d<12: P[x,y]=(255,246,200)
        elif abs(math.hypot(x-150,y-140)-75)<.6: put(x,y,(255,255,255),.22)   # 렌즈 고리

im.resize((W*PX,H*PX),Image.NEAREST).save('img/bulbs-lookdown.png')
