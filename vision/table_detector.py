import cv2
import numpy as np


def rst_viewport(frame):
    """Locate a portrait felt rectangle inside a mirror's toolbar/letterboxing.

    Keep the optional pale action panel below the felt. Reject small/landscape
    candidates so arbitrary desktop widgets cannot silently define a table.
    """
    height,width=frame.shape[:2]
    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    mask=cv2.inRange(hsv,(30,45,25),(140,255,230))
    count,labels,stats,_=cv2.connectedComponentsWithStats(mask)
    if count<2:
        return None
    index=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
    x,y,w,h,area=map(int,stats[index])
    if not (1.65<h/w<2.35 and w>width*.45 and area>width*height*.40 and area>w*h*.65):
        return None
    # Ignore narrow screenshot borders and antialiasing at the felt edges.
    tolerance=max(2,round(w*.015))
    if y<=tolerance:
        y=0
        if x<=tolerance:
            x,w=0,w+x
        if width-(x+w)<=tolerance:
            w=width-x
    # A toolbar beneath a full-height phone must not stretch the coordinates.
    return x,y,w,min(height-y,round(w*1077/493))

def detect_table(frame) -> tuple[int,int,int,int] | None:
    """Suggest a colored felt bounding box; never re-map calibrated ROIs automatically."""
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv,(30,45,25),(140,255,230))
    contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours,key=cv2.contourArea)
    return cv2.boundingRect(contour) if cv2.contourArea(contour) > frame.shape[0]*frame.shape[1]*.12 else None
