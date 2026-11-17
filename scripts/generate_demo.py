"""Generate explicitly synthetic assets, never represented as RST screenshots."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from config import ROOT, LayoutProfile

def card_image(rank,suit):
    image = np.full((120,80,3),245,dtype=np.uint8)
    color = (35,35,210) if suit in 'hd' else (30,30,30)
    cv2.putText(image,'10' if rank=='T' else rank,(4,32),cv2.FONT_HERSHEY_SIMPLEX,.85,color,2,cv2.LINE_AA)
    x,y=19,54
    if suit=='d':
        cv2.fillPoly(image,[np.array([(x,y-13),(x+10,y),(x,y+13),(x-10,y)])],color)
    elif suit=='h':
        cv2.circle(image,(x-5,y-5),7,color,-1)
        cv2.circle(image,(x+5,y-5),7,color,-1)
        cv2.fillPoly(image,[np.array([(x-12,y-4),(x+12,y-4),(x,y+13)])],color)
    elif suit=='s':
        cv2.fillPoly(image,[np.array([(x,y-14),(x-12,y+3),(x+12,y+3)])],color)
        cv2.circle(image,(x-5,y+2),7,color,-1)
        cv2.circle(image,(x+5,y+2),7,color,-1)
        cv2.rectangle(image,(x-2,y+1),(x+2,y+14),color,-1)
    else:
        for px,py in [(x,y-7),(x-7,y+2),(x+7,y+2)]:
            cv2.circle(image,(px,py),7,color,-1)
        cv2.rectangle(image,(x-2,y+2),(x+2,y+15),color,-1)
    return image

def main():
    templates = ROOT/'assets/templates'
    templates.mkdir(parents=True,exist_ok=True)
    for rank in '23456789TJQKA':
        for suit in 'cdhs':
            cv2.imencode('.png',card_image(rank,suit))[1].tofile(templates/f'{rank}{suit}.png')
    target = ROOT/'assets/screenshots'
    target.mkdir(parents=True,exist_ok=True)
    frame = np.full((1077,493,3),(45,75,38),np.uint8)
    cv2.putText(frame,'SYNTHETIC DEMO',(90,60),cv2.FONT_HERSHEY_SIMPLEX,.7,(255,255,255),2)
    for i,card in enumerate(('Jd','2d','Qc')):
        frame[450:566,25+i*100:102+i*100] = cv2.resize(card_image(*card),(77,116))
    for i,card in enumerate(('Jc','4h')):
        frame[924:984,194+i*60:234+i*60] = cv2.resize(card_image(*card),(40,60))
    cv2.imencode('.png',frame)[1].tofile(target/'synthetic_demo.png')
    (ROOT/'assets/layout_default.json').write_text(LayoutProfile().to_json(),encoding='utf-8')

if __name__ == '__main__':
    main()
