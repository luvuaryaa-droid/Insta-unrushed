# Crop the painting area out of each mockup. Boxes were estimated by eye, then each
# edge is snapped to the strongest straight edge within +-28px (mat/painting boundary).
import numpy as np, json, sys
from PIL import Image, ImageFilter
U='/root/.claude/uploads/c2d08bae-1a27-56e7-a13b-a7d58a041b63/'
EST={ # name: (file, x0,y0,x1,y1)
 'nook':('1b126afa',292,197,878,903),'scooter':('98c4cb20',351,165,995,811),
 'diya':('4f721542',311,175,990,797),'arch':('ce3ed132',341,148,1210,748),
 'flowerwoman':('3ffbce6c',292,88,1030,790),'moka':('9893b1d6',316,198,894,946),
 'latte':('98a8812a',318,172,983,850),'jungle':('87369fa4',277,188,884,1008),
 'lantern':('aae8c1f1',335,243,870,992),'mother':('74a68c7b',320,185,905,1013),
 'cat':('eb8491cc',313,200,993,884),'garlic':('5aed9b72',330,270,890,895),
 'redhead':('a5c67bb4',291,158,832,1031),'sapling':('4a690063',320,210,883,948),
 'egg':('922a5054',300,173,1003,877),'tulips':('d4eb3466',253,188,1012,948),
 'knit':('ee07ff8d',253,177,1027,950),'walker':('986595c2',300,156,950,1003),
 'fire':('2e8ae377',240,175,1014,940)}
out={}
for k,(f,x0,y0,x1,y1) in EST.items():
    im=Image.open(U+f+'-image.png').convert('RGB'); a=np.asarray(im).astype(float).mean(2)
    gx=np.abs(np.diff(a,axis=1)); gy=np.abs(np.diff(a,axis=0)); R=28
    def snapx(x):
        cols=gx[y0+40:y1-40, max(0,x-R):x+R].mean(0); return max(0,x-R)+int(cols.argmax())+1
    def snapy(y):
        rows=gy[max(0,y-R):y+R, x0+40:x1-40].mean(1); return max(0,y-R)+int(rows.argmax())+1
    b=[snapx(x0),snapy(y0),snapx(x1),snapy(y1)]
    # take the snap only if it is close; inset 3px to stay clear of the edge line
    b=[b[0]+3,b[1]+3,b[2]-3,b[3]-3]
    out[k]=dict(file=f,box=b,est=[x0,y0,x1,y1])
    im.crop(b).save(f'public/art/{k}.png')
    im.save(f'public/mock/{k}.jpg',quality=93)
    print(k,[x0,y0,x1,y1],'->',b, (b[2]-b[0],b[3]-b[1]))
json.dump(out,open('tools/crops.json','w'),indent=1)
