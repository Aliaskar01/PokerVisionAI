"""Extract RST rank glyphs; rank templates are shared across all four suits."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from config import ROOT,rst_portrait_profile
from capture.frame_processor import crop
from vision.rank_suit_classifier import extract_rank

LABELS = {1:{'hole_1':'Q','hole_2':'T','board_1':'3','board_2':'A','board_3':'4'},
          2:{'hole_1':'J','hole_2':'4','board_1':'J','board_2':'2','board_3':'Q'},
          3:{'hole_1':'8','hole_2':'5'}}

def main():
    target = ROOT/'assets/ranks'
    target.mkdir(exist_ok=True)
    tiles=[]
    for index,labels in LABELS.items():
        frame=cv2.imdecode(np.fromfile(ROOT/f'assets/screenshots/rst_reference_{index}.png',np.uint8),1)
        zones=rst_portrait_profile().resolved_regions(frame.shape[1],frame.shape[0])
        for key,rank in labels.items():
            glyph,color=extract_rank(crop(frame,zones[key]))
            if glyph is None:
                raise ValueError(f'Cannot extract rank {index} {key}')
            cv2.imencode('.png',glyph)[1].tofile(target/f'{rank}_ref{index}_{key}.png')
            tile=np.zeros((100,90),np.uint8)
            tile[:72,:48]=cv2.resize(glyph,(48,72))
            cv2.putText(tile,f'{index}:{rank}',(0,95),cv2.FONT_HERSHEY_SIMPLEX,.5,255,1)
            tiles.append(tile)
    cv2.imencode('.png',np.hstack(tiles))[1].tofile(ROOT/'artifacts/rst-ranks.png')

if __name__=='__main__':
    main()
