"""RST corner glyph recognition independent of card size, suit and artwork."""
from pathlib import Path
import cv2
import numpy as np
from .card_classifier import Prediction

SUIT_BY_COLOR = {'red':'h','green':'c','blue':'d','black':'s'}

def extract_rank(image):
    hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
    hue,saturation,value = cv2.split(hsv)
    masks = {
        'red':((hue<12)|(hue>170))&(saturation>80)&(value>65),
        'green':(hue>=35)&(hue<85)&(saturation>80)&(value>65),
        'blue':(hue>=85)&(hue<130)&(saturation>80)&(value>65),
        'black':(value<105)&(saturation<115),
    }
    height,width = image.shape[:2]
    choices=[]
    for color,binary in masks.items():
        _,labels,stats,_ = cv2.connectedComponentsWithStats(binary.astype(np.uint8))
        candidates = [(i,s) for i,s in enumerate(stats[1:],1) if 0<s[0]<width*.40 and
                      0<s[1]<height*.30 and height*.22<s[3]<height*.80 and s[2]>2 and s[4]>12]
        if candidates:
            _,anchor=max(candidates,key=lambda item:item[1][4])
            choices.append((int(anchor[4]),color,labels,stats,anchor))
    if not choices:
        return None,None
    _,color,labels,stats,anchor=max(choices,key=lambda item:item[0])
    ax,ay,aw,ah,_ = anchor
    selected = [(i,s) for i,s in enumerate(stats[1:],1) if s[0]<width*.65 and
                abs(s[1]-ay)<ah*.25 and .65*ah<s[3]<1.25*ah and s[4]>8]
    if not selected:
        return None,color
    x=min(s[0] for _,s in selected); y=min(s[1] for _,s in selected)
    right=max(s[0]+s[2] for _,s in selected); bottom=max(s[1]+s[3] for _,s in selected)
    glyph = np.isin(labels,[i for i,_ in selected]).astype(np.uint8)[y:bottom,x:right]*255
    return glyph,color

def normalize_glyph(glyph):
    return cv2.resize(glyph,(32,48),interpolation=cv2.INTER_AREA)

class RankSuitClassifier:
    def __init__(self, directory: Path, threshold=.87, use_ocr=False):
        self.threshold = threshold
        self.use_ocr = use_ocr
        self.templates = []
        for path in sorted(directory.glob('*.png')):
            rank = path.stem.split('_')[0]
            if rank not in '23456789TJQKA' or len(rank)!=1:
                continue
            glyph = cv2.imdecode(np.fromfile(path,np.uint8),cv2.IMREAD_GRAYSCALE)
            if glyph is not None:
                self.templates.append((rank,normalize_glyph(glyph),glyph.shape[1]/glyph.shape[0]))

    def predict(self,image):
        glyph,color = extract_rank(image)
        if glyph is None or not self.templates:
            return Prediction(None,0)
        query = normalize_glyph(glyph)
        aspect = glyph.shape[1]/glyph.shape[0]
        scores = {}
        for rank,template,reference_aspect in self.templates:
            score = float(cv2.matchTemplate(query,template,cv2.TM_CCOEFF_NORMED)[0,0])
            score -= min(.2,abs(aspect-reference_aspect)*.15)
            scores[rank] = max(scores.get(rank,0),score)
        ranked = sorted(scores.items(),key=lambda item:item[1],reverse=True)
        rank,score = ranked[0]
        margin = score-ranked[1][1] if len(ranked)>1 else 1
        if score>=self.threshold and margin>=.06:
            return Prediction(rank+SUIT_BY_COLOR[color],max(0,min(1,score)))
        if self.use_ocr:
            # A pretrained text model can read ranks absent from the small
            # calibration set. Only an exact high-confidence rank is accepted.
            try:
                from .local_ocr import recognize
                padded=cv2.copyMakeBorder(255-glyph,8,8,8,8,cv2.BORDER_CONSTANT,value=255)
                readings=recognize(cv2.cvtColor(padded,cv2.COLOR_GRAY2BGR),single_line=True)
                if len(readings)==1:
                    text,confidence=readings[0]
                    text=text.strip().upper()
                    text='T' if text=='10' else text
                    if len(text)==1 and text in '23456789TJQKA' and confidence>=.94:
                        return Prediction(text+SUIT_BY_COLOR[color],confidence)
            except Exception:
                pass  # The amount/text backend reports model-loading errors.
        return Prediction(None,max(0,min(1,score)))
