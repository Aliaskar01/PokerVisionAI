import cv2
import numpy as np
import pytest
from config import ROOT,LayoutProfile,Region
from vision.card_classifier import CardClassifier
from vision.card_detector import CardDetector
from vision.ocr_detector import parse_amount,OCRDetector
from vision.ui_state_detector import detect_ui
from vision.pipeline import VisionPipeline
from scripts.generate_demo import card_image

@pytest.mark.parametrize('card',[r+s for r in '23456789TJQKA' for s in 'cdhs'])
def test_all_synthetic_cards(card):
    classifier = CardClassifier([ROOT/'assets/templates'])
    assert classifier.predict(card_image(*card)).card == card

def test_unknown_and_duplicates():
    detector = CardDetector(CardClassifier([ROOT/'assets/templates']))
    assert detector.classifier.predict(np.full((120,80,3),240,np.uint8)).card is None
    frame = np.zeros((140,200,3),np.uint8)
    frame[10:130,10:90] = card_image('A','h')
    frame[10:130,110:190] = card_image('A','h')
    with pytest.raises(ValueError,match='Duplicate'):
        detector.detect(frame)

def test_synthetic_screenshot():
    frame = cv2.imdecode(np.fromfile(ROOT/'assets/screenshots/synthetic_demo.png',dtype=np.uint8),cv2.IMREAD_COLOR)
    result = VisionPipeline(LayoutProfile()).process(frame)
    assert result.valid_cards
    assert result.state.hole_cards == ('Jc','4h')
    assert result.state.community_cards == ('Jd','2d','Qc')
    assert result.state.active_opponents is None
    assert result.state.pot is None

@pytest.mark.parametrize('text,value',[('1.15K',1150),('1.20K',1200),('1.49K',1490),('Pot: 80',80),('1,200',1200),('1,15K',1150),('?',None),('80 90',None),('-10',None)])
def test_ocr_parser(text,value):
    assert parse_amount(text) == value

def test_ocr_confidence_and_ui():
    ocr = OCRDetector()
    ocr.read_text = lambda _: [('80',.3)]
    assert ocr.read_amount(None).value is None
    ocr.read_text = lambda _: [('80',.98)]
    assert ocr.read_amount(None).value == 80
    assert detect_ui('Check/Fold Check Call Any') == 'PRE_ACTION_AVAILABLE'
    assert detect_ui('Fold Call 20 Raise') == 'PLAYER_TURN'
    with pytest.raises(ValueError):
        Region(.8,0,.5,1)

@pytest.mark.parametrize('text,value',[('80',80),('380',380),('1.15K',1150),('80 90',None)])
def test_numeric_image_ocr(text,value):
    frame = np.zeros((60,160,3),np.uint8)
    cv2.putText(frame,text,(5,40),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2,cv2.LINE_AA)
    assert OCRDetector().read_amount(frame).value == value
