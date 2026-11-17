import cv2
import numpy as np
from config import Region

def crop(frame: np.ndarray, region: Region) -> np.ndarray:
    x,y,w,h = region.pixels(frame.shape[1], frame.shape[0])
    return frame[y:y+h, x:x+w].copy()

def preprocess(image: np.ndarray, scale: float = 2) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return cv2.createCLAHE(2.0,(4,4)).apply(cv2.GaussianBlur(gray,(3,3),0))

def normalized(image: np.ndarray) -> np.ndarray:
    return image.astype(np.float32) / 255.0

class FrameDeduplicator:
    def __init__(self):
        self.last = None

    def changed(self, image) -> bool:
        small = cv2.resize(image, (96,96))
        changed = self.last is None or np.mean(cv2.absdiff(small,self.last)) > .4
        self.last = small
        return changed
