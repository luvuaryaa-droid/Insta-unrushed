import sys,glob,os
from PIL import Image,ImageDraw
fs=sys.argv[2:];W=int(os.environ.get('W',260));cols=int(os.environ.get('C',5))
rows=(len(fs)+cols-1)//cols
sheet=Image.new('RGB',(W*cols,(W+22)*rows),(255,0,255));d=ImageDraw.Draw(sheet)
for i,f in enumerate(fs):
  im=Image.open(f).convert('RGB');im.thumbnail((W-8,W-8));x,y=(i%cols)*W,(i//cols)*(W+22)
  sheet.paste(im,(x+4,y+4));d.text((x+4,y+W+4),os.path.basename(f),fill='black')
sheet.save(sys.argv[1])
