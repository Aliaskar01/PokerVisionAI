from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np
from poker.card import Card

@dataclass(frozen=True)
class Prediction:
    card: str | None
    confidence: float

def signature(image):
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    # Keep rank/suit corner; full illustrations are irrelevant to rank and suit.
    corner = gray[:max(1,int(gray.shape[0]*.65)), :max(1,int(gray.shape[1]*.55))]
    return cv2.resize(corner,(40,64),interpolation=cv2.INTER_AREA).astype(np.float32)

def ink_color(image) -> str | None:
    """Four-color RST decks and traditional red/black decks stay distinct."""
    if image.ndim != 3:
        return None
    corner = image[:max(1,int(image.shape[0]*.65)),:max(1,int(image.shape[1]*.40))]
    hsv = cv2.cvtColor(corner,cv2.COLOR_BGR2HSV)
    h,s,v = cv2.split(hsv)
    saturated = (s>85)&(v>65)
    counts = {'red':int((saturated&((h<12)|(h>170))).sum()),
              'green':int((saturated&(h>=35)&(h<85)).sum()),
              'blue':int((saturated&(h>=85)&(h<130)).sum())}
    color,count = max(counts.items(),key=lambda item:item[1])
    if count >= max(6,corner.shape[0]*corner.shape[1]*.025):
        return color
    return 'black' if int(((v<80)&(s<100)).sum())>=6 else None

class CardClassifier:
    def __init__(self, directories: list[Path], threshold=.94):
        self.templates = []
        self.threshold = threshold
        for directory in directories:
            for path in sorted(directory.glob('*.png')):
                try:
                    card = str(Card.parse(path.stem.split('_')[0]))
                    image = cv2.imdecode(np.fromfile(path,dtype=np.uint8),cv2.IMREAD_COLOR)
                    if image is not None:
                        self.templates.append((card,signature(image),ink_color(image)))
                except ValueError:
                    continue

    def predict(self, image) -> Prediction:
        query = signature(image)
        if query.std() < 5 or not self.templates:
            return Prediction(None,0)
        scores = {}
        color = ink_color(image)
        for card, template,template_color in self.templates:
            if color is not None and template_color is not None and color != template_color:
                continue
            # Rank and suit must each match: a large suit cannot hide a wrong rank.
            correlation = min(float(cv2.matchTemplate(query[:29],template[:29],cv2.TM_CCOEFF_NORMED)[0,0]),
                              float(cv2.matchTemplate(query[29:],template[29:],cv2.TM_CCOEFF_NORMED)[0,0]))
            scores[card] = max(scores.get(card,0), correlation)
        if not scores:
            return Prediction(None,0)
        ordered = sorted(scores.items(),key=lambda x:x[1],reverse=True)
        card, score = ordered[0]
        margin = score - ordered[1][1] if len(ordered)>1 else 1
        return Prediction(card if score >= self.threshold and margin >= .025 else None,max(0,min(1,score)))
