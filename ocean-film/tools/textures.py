# Procedural analogue textures: paper, 16mm grain plates, dappled leaf-shadow gobo.
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
rng=np.random.default_rng(7)
def fbm(w,h,octaves=6,base=4):
    out=np.zeros((h,w))
    for o in range(octaves):
        n=base*2**o; a=rng.random((max(2,n*h//w+1),n+1))
        out+=np.asarray(Image.fromarray((a*255).astype(np.uint8)).resize((w,h),Image.BICUBIC),float)/255/(1.7**o)
    out-=out.min(); return out/out.max()
# paper
W,H=1920,1080
f=fbm(W,H,7,3); fine=rng.random((H,W))
fib=Image.new('L',(W,H),0); d=ImageDraw.Draw(fib)
for _ in range(2600):
    x,y=rng.random()*W,rng.random()*H; a=rng.random()*np.pi; L=6+rng.random()*30
    d.line([(x,y),(x+np.cos(a)*L,y+np.sin(a)*L)],fill=int(40+rng.random()*80),width=1)
fib=np.asarray(fib.filter(ImageFilter.GaussianBlur(.6)),float)/255
base=np.array([241,232,214],float)
img=base[None,None,:]*(0.93+0.07*f[...,None])-14*fine[...,None]*0.4-18*fib[...,None]
Image.fromarray(np.clip(img,0,255).astype(np.uint8)).save('public/tex/paper.jpg',quality=92)
# grain plates (mid-grey centred, used with overlay blend)
for i in range(8):
    g=rng.normal(128,34,(540,960)); g=np.asarray(Image.fromarray(np.clip(g,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.55)),float)
    g=(g-128)*1.9+128
    Image.fromarray(np.clip(g,0,255).astype(np.uint8)).save(f'public/tex/grain{i}.png')
# leaf shadow gobo: white = no shadow. Trailing pothos-like vines + window mullions.
GW,GH=2600,1500; im=Image.new('L',(GW,GH),255); d=ImageDraw.Draw(im)
def leaf(cx,cy,ang,L,Wd):
    t=np.linspace(0,1,30); top=[(L*u, Wd*np.sin(np.pi*u)**0.7*(1-0.35*u)) for u in t]
    pts=top+[(x,-y) for x,y in reversed(top)]
    d.polygon([(cx+x*np.cos(ang)-y*np.sin(ang), cy+x*np.sin(ang)+y*np.cos(ang)) for x,y in pts],fill=0)
for v in range(7):
    x,y=200+v*340+rng.normal(0,80),-100; ang=np.pi/2+rng.normal(0,.2)
    for s_ in range(60):
        nx,ny=x+np.cos(ang)*30,y+np.sin(ang)*30; d.line([(x,y),(nx,ny)],fill=0,width=6); x,y=nx,ny; ang+=rng.normal(0,.1)
        if s_%4==2:
            side=1 if (s_//4)%2 else -1; L=120+rng.random()*70
            leaf(x,y,ang+side*(0.8+rng.random()*.6),L,L*0.42)
for x in (250,1250):  # window-pane mullions
    d.polygon([(x,0),(x+120,0),(x+500,GH),(x+380,GH)],fill=0)
im=im.filter(ImageFilter.GaussianBlur(18)); im.save('public/tex/gobo.png')
# caustic light for the underwater act: bright thin lines where noise bands cross zero
cw,ch=1600,900
a=fbm(cw,ch,5,3); b=fbm(cw,ch,5,4)
c=np.exp(-np.abs(np.sin(a*18))*9)+np.exp(-np.abs(np.sin(b*15+1))*9)
c=np.clip(c/ c.max()*1.3,0,1)
Image.fromarray((c*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)).save('public/tex/caustic.png')
