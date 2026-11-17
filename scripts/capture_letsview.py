"""Read one visible LetsView client frame for recognition diagnostics."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from capture.window_detector import list_windows,window_region
from config import ROOT
import cv2
from PIL import ImageGrab
import numpy as np

if __name__=='__main__':
    windows=[]
    for window in list_windows():
        if 'letsview' not in window.title.lower():
            continue
        try:
            candidate=window_region(window.handle)
        except RuntimeError:
            continue
        if candidate['height']>candidate['width']*1.5:
            windows.append(window)
    if len(windows)!=1:
        print(f'Expected one LetsView window, found {len(windows)}')
        raise SystemExit(2)
    frame=cv2.cvtColor(np.asarray(ImageGrab.grab(window=windows[0].handle)),cv2.COLOR_RGB2BGR)
    target=ROOT/'artifacts/letsview-window.png'
    cv2.imencode('.png',frame)[1].tofile(target)
    print(f'Saved {frame.shape[1]}x{frame.shape[0]} to {target}')
