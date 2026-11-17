from dataclasses import dataclass
import cv2
from .card_classifier import CardClassifier

@dataclass
class DetectedCard:
    card: str | None
    confidence: float
    box: tuple[int,int,int,int]

class CardDetector:
    def __init__(self, classifier: CardClassifier):
        self.classifier = classifier
        from config import ROOT
        from .rank_suit_classifier import RankSuitClassifier
        self.rst_classifier = RankSuitClassifier(ROOT/'assets/ranks')

    def detect_slots(self, frame, slots) -> list[DetectedCard]:
        """Calibrated slots also work when cards touch the pale action panel."""
        detections = []
        for region in slots:
            x,y,w,h = region.pixels(frame.shape[1],frame.shape[0])
            image = frame[y:y+h,x:x+w]
            gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
            # Empty RST card outlines have felt interiors, not light card faces.
            if float((gray > 170).mean()) < .20:
                continue
            prediction = self.rst_classifier.predict(image)
            if prediction.card is None:
                prediction = self.classifier.predict(image)
            detections.append(DetectedCard(prediction.card,prediction.confidence,(x,y,w,h)))
        cards = [d.card for d in detections if d.card]
        if len(cards) != len(set(cards)):
            raise ValueError('Duplicate detected cards; correct the image or layout')
        return detections

    def detect(self, image, maximum=5) -> list[DetectedCard]:
        gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        mask = cv2.inRange(gray,175,255)
        contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        height,width = gray.shape
        boxes = []
        for contour in contours:
            x,y,w,h = cv2.boundingRect(contour)
            if w*h >= max(80,width*height*.008) and .30 <= w/h <= 1.1 and h >= height*.3:
                if cv2.contourArea(contour) / (w*h) > .65:
                    boxes.append((x,y,w,h))
        boxes.sort()
        if len(boxes) > maximum:
            raise ValueError(f'Too many card candidates: {len(boxes)}')
        detections = []
        for x,y,w,h in boxes:
            prediction = self.classifier.predict(image[y:y+h,x:x+w])
            detections.append(DetectedCard(prediction.card,prediction.confidence,(x,y,w,h)))
        cards = [d.card for d in detections if d.card]
        if len(cards) != len(set(cards)):
            raise ValueError('Duplicate detected cards; correct the image or layout')
        return detections
