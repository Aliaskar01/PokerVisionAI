import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QPixmap
from PySide6.QtWidgets import QLabel

class VideoPreview(QLabel):
    def __init__(self):
        super().__init__('Choose a window or load an offline screenshot')
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(280,360)
        self.setStyleSheet('background:#0b1220; border:1px solid #334155; border-radius:8px; color:#94a3b8')
        self.current = None

    def show_frame(self,frame,boxes=(),regions=None):
        image = frame.copy()
        if regions:
            for name,roi in regions.items():
                x,y,w,h = roi.pixels(image.shape[1],image.shape[0])
                cv2.rectangle(image,(x,y),(x+w,y+h),(170,120,60),1)
                cv2.putText(image,name,(x,max(12,y)),cv2.FONT_HERSHEY_SIMPLEX,.35,(230,180,90),1)
        for x,y,w,h,label in boxes:
            cv2.rectangle(image,(x,y),(x+w,y+h),(90,220,70),2)
            cv2.putText(image,label,(x,max(12,y-3)),cv2.FONT_HERSHEY_SIMPLEX,.4,(90,240,100),1)
        image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        self.current = QImage(image.data,image.shape[1],image.shape[0],image.strides[0],QImage.Format.Format_RGB888).copy()
        self._render()

    def _render(self):
        if self.current:
            self.setPixmap(QPixmap.fromImage(self.current).scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self._render()
