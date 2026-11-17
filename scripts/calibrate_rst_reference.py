"""Extract labeled calibration samples from the user-supplied reference.

This is calibration data, not held-out recognition-accuracy evidence.
The runtime still classifies pixels; no screenshot IDs or game states are used.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from config import ROOT,LayoutProfile,rst_portrait_profile
from capture.frame_processor import crop

def save(path,image):
    path.parent.mkdir(parents=True,exist_ok=True)
    cv2.imencode('.png',image)[1].tofile(path)

def main():
    image = cv2.imdecode(np.fromfile(ROOT/'assets/screenshots/rst_reference_2.png',np.uint8),cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('Reference image cannot be decoded')
    profile = LayoutProfile.load(ROOT/'assets/layout_rst_legacy.json')
    regions = profile.resolved_regions(image.shape[1],image.shape[0])
    labels = {'hole_1':'Jc','hole_2':'4h','board_1':'Jd','board_2':'2d','board_3':'Qc'}
    for slot,card in labels.items():
        save(ROOT/f'assets/templates/{card}_rst_{slot}.png',crop(image,regions[slot]))
    save(ROOT/'assets/ui/rst_pre_action.png',crop(image,regions['actions']))
    for name,text in {'pot':'80','hero_stack':'380','stack_1':'411','stack_2':'115K','stack_3':'120K','stack_4':'149K'}.items():
        gray = cv2.cvtColor(crop(image,regions[name]),cv2.COLOR_BGR2GRAY)
        _,mask = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        _,_,stats,_ = cv2.connectedComponentsWithStats(mask)
        height = max(s[3] for s in stats[1:])
        boxes = sorted((s[:4] for s in stats[1:] if s[3]>=height*.5),key=lambda b:b[0])
        if len(boxes) != len(text):
            raise ValueError(f'{name}: expected {len(text)} glyphs, got {len(boxes)}')
        for index,(char,(x,y,w,h)) in enumerate(zip(text,boxes)):
            save(ROOT/f'assets/ocr/{char}_rst_{name}_{index}.png',mask[y:y+h,x:x+w])
    (ROOT/'assets/layout_rst_portrait.json').write_text(rst_portrait_profile().to_json(),encoding='utf-8')

if __name__ == '__main__':
    main()
