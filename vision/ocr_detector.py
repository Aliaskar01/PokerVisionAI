from dataclasses import dataclass
from pathlib import Path
import re
import cv2
import numpy as np
from capture.frame_processor import preprocess
from config import ROOT,DATA

@dataclass
class OCRValue:
    value: float | None
    confidence: float
    text: str = ''

def parse_amount(text: str) -> float | None:
    text = text.strip().replace('\u00a0',' ')
    # Accept decimal comma, compact suffixes, and explicit grouped thousands.
    text = re.sub(r'(?<=\d)[ ,](?=\d{3}(?:\D|$))','',text)
    match = re.fullmatch(r'(?i)(?:pot|stack|call|bet|банк|стек|колл)?\s*[:=]?\s*(\d+(?:[.,]\d{1,2})?)\s*([km]?)',text)
    if not match:
        return None
    value, suffix = match.groups()
    return float(value.replace(',','.')) * {'':1,'k':1000,'m':1000000}[suffix.lower()]

class OCRDetector:
    def __init__(self, threshold=.85, enabled=False, model_dir: Path | None = None, backend='template'):
        self.threshold, self.enabled, self.model_dir = threshold,enabled,model_dir
        self.backend = backend
        self.reader = None
        self.error = 'Using numeric template OCR. For other fonts or action text, enable local EasyOCR or correct manually.'
        self.numeric = NumericTemplateOCR([ROOT/'assets/ocr',DATA/'ocr'])
        if backend=='rapidocr':
            self.error = ''

    def read_text(self, image) -> list[tuple[str,float]]:
        if self.backend=='rapidocr' and not self.enabled:
            try:
                from .local_ocr import recognize
                return recognize(image)
            except Exception as exc:
                self.error = f'Local OCR unavailable: {exc}. Using limited numeric templates.'
                self.backend = 'template'
        if not self.enabled:
            return self.numeric.read(image)
        try:
            if self.reader is None:
                import easyocr
                self.reader = easyocr.Reader(['en','ru'],gpu=False,model_storage_directory=str(self.model_dir),download_enabled=False)
            return [(text,float(conf)) for _,text,conf in self.reader.readtext(preprocess(image))]
        except Exception as exc:
            self.error = f'OCR unavailable: {exc}'
            self.enabled = False
            return self.numeric.read(image)

    def read_amount(self,image) -> OCRValue:
        if self.backend=='rapidocr' and not self.enabled:
            try:
                from .local_ocr import recognize
                readings = recognize(image,single_line=True)
            except Exception as exc:
                self.error = f'Local OCR unavailable: {exc}. Using limited numeric templates.'
                self.backend = 'template'
                readings = self.read_text(image)
        else:
            readings = self.read_text(image)
        results = [(parse_amount(t),c,t) for t,c in readings]
        valid = [(v,c,t) for v,c,t in results if v is not None and c >= self.threshold]
        if len(valid) == 1:
            return OCRValue(*valid[0])
        return OCRValue(None,0,' | '.join(t for _,_,t in results))

class NumericTemplateOCR:
    """Small, conservative CPU fallback for high-contrast numeric labels.

    No language model or digit correction. Unsupported fonts remain unknown.
    """
    def __init__(self, directories=()):
        self.templates = []
        for font in (cv2.FONT_HERSHEY_SIMPLEX,cv2.FONT_HERSHEY_DUPLEX):
            for char in '0123456789KMkm':
                for thickness in (1,2):
                    canvas = np.zeros((48,48),np.uint8)
                    cv2.putText(canvas,char,(3,35),font,1,255,thickness,cv2.LINE_AA)
                    _,mask = cv2.threshold(canvas,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
                    points = cv2.findNonZero(mask)
                    x,y,w,h = cv2.boundingRect(points)
                    self.templates.append((char,cv2.resize(mask[y:y+h,x:x+w],(24,32)),w/h))
        for directory in directories:
            for path in sorted(directory.glob('*.png')):
                char = path.stem.split('_')[0]
                if char not in '0123456789KMkm' or len(char) != 1:
                    continue
                mask = cv2.imdecode(np.fromfile(path,dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
                if mask is not None and mask.size:
                    h,w = mask.shape
                    self.templates.append((char,cv2.resize(mask,(24,32)),w/h))

    def read(self,image):
        if image is None or image.size == 0:
            return []
        gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY) if image.ndim==3 else image
        if float(gray.std()) < 10:
            return []
        _,mask = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        border = np.concatenate((mask[0],mask[-1],mask[:,0],mask[:,-1]))
        if np.mean(border)>127:
            mask = cv2.bitwise_not(mask)
        count,_,stats,_ = cv2.connectedComponentsWithStats(mask)
        parts = sorted((tuple(s[:4]) for s in stats[1:] if s[4]>=1),key=lambda b:b[0])
        if not 1 <= len(parts) <= 12:
            return []
        max_height = max(h for x,y,w,h in parts)
        if max_height < 7:
            return []
        baseline = max(y+h for x,y,w,h in parts if h >= max_height*.5)
        parts = [p for p in parts if p[3] >= max_height*.28 or
                 (p[2] < max_height*.3 and abs(p[1]+p[3]-baseline) <= max(1,max_height*.12))]
        for previous,current in zip(parts,parts[1:]):
            if current[0]-(previous[0]+previous[2]) > max_height*.4:
                return []  # Separate labels must never be concatenated into one amount.
        baselines = [y+h for x,y,w,h in parts if h >= max_height*.5]
        if max(baselines)-min(baselines) > max_height*.25:
            return []
        text,confidence = '',1.0
        for x,y,w,h in parts:
            if h < max_height*.28 and w < max_height*.3:
                # Only a small baseline dot is interpreted as a decimal point.
                if y+h < max(py+ph for px,py,pw,ph in parts)-max_height*.2:
                    return []
                text += '.'
                continue
            query = cv2.resize(mask[y:y+h,x:x+w],(24,32))
            scores = {}
            for char,template,aspect in self.templates:
                score = float(cv2.matchTemplate(query,template,cv2.TM_CCOEFF_NORMED)[0,0])
                score -= min(.3,abs(w/h-aspect)*.3)
                scores[char] = max(scores.get(char,0),score)
            ranked = sorted(scores.items(),key=lambda item:item[1],reverse=True)
            char,score = ranked[0]
            if score<.85 or score-ranked[1][1]<.04:
                return []
            text += char
            confidence = min(confidence,score)
        return [(text,confidence)] if parse_amount(text) is not None else []
