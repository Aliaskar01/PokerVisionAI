"""Calibration regression, not an independent estimate of RST accuracy."""
import cv2
import numpy as np
import pytest
from config import ROOT,LayoutProfile,rst_portrait_profile
from vision.pipeline import VisionPipeline
from capture.frame_processor import crop
from vision.card_classifier import ink_color

@pytest.fixture
def reference():
    return cv2.imdecode(np.fromfile(ROOT/'assets/screenshots/rst_reference_2.png',np.uint8),cv2.IMREAD_COLOR)

def test_real_reference_calibration(reference):
    result = VisionPipeline(rst_portrait_profile()).process(reference)
    state = result.state
    assert result.valid_cards
    assert state.hole_cards == ('Jc','4h')
    assert state.community_cards == ('Jd','2d','Qc')
    assert state.street == 'FLOP'
    assert state.pot == 80
    assert state.hero_stack == 380
    assert [p['stack'] for p in state.players] == [411,1150,1200,1490]
    assert state.ui_state == 'PRE_ACTION_AVAILABLE'
    assert state.call_amount is None
    assert state.active_opponents is None

@pytest.mark.parametrize('scale',[.75,1.5,2])
def test_cards_at_different_scales(reference,scale):
    resized = cv2.resize(reference,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
    result = VisionPipeline(rst_portrait_profile()).process(resized)
    assert result.state.hole_cards == ('Jc','4h')
    assert result.state.community_cards == ('Jd','2d','Qc')
    # Low-resolution/fractional-scaling OCR may safely return unknown.
    assert result.state.pot in (80,None)
    assert result.state.hero_stack in (380,None)
    if scale == 2:
        assert result.state.pot == 80 and result.state.hero_stack == 380

def test_height_without_panel_does_not_shift_table(reference):
    profile = rst_portrait_profile()
    original = profile.resolved_regions(493,1077)
    short = profile.resolved_regions(493,985)
    for key in ('pot','hero_stack','hole_1','board_1'):
        assert original[key].pixels(493,1077) == short[key].pixels(493,985)
    assert 'actions' not in short
    # This crop independently exercises optional-panel geometry.
    result = VisionPipeline(profile).process(reference[:985])
    assert result.state.hole_cards == ('Jc','4h')
    assert result.state.ui_state == 'UNKNOWN'

def test_values_are_read_from_pixels_not_reference_state(reference):
    profile = rst_portrait_profile()
    zones = profile.resolved_regions(493,1077)
    first,second = crop(reference,zones['board_1']),crop(reference,zones['board_2'])
    for key,image in [('board_1',second),('board_2',first)]:
        x,y,w,h = zones[key].pixels(493,1077)
        reference[y:y+h,x:x+w] = image
    x,y,w,h = zones['pot'].pixels(493,1077)
    reference[y:y+h,x:x+w] = 0
    x,y,w,h = zones['actions'].pixels(493,1077)
    reference[y:y+h,x:x+w] = 210
    result = VisionPipeline(profile).process(reference)
    assert result.state.community_cards == ('2d','Jd','Qc')
    assert result.state.pot is None
    assert result.state.ui_state == 'UNKNOWN'

def test_duplicate_and_blank_card_rejected(reference):
    profile = rst_portrait_profile()
    zones = profile.resolved_regions(493,1077)
    x,y,w,h = zones['board_1'].pixels(493,1077)
    reference[y:y+h,x:x+w] = crop(reference,zones['board_2'])
    result = VisionPipeline(profile).process(reference)
    assert not result.valid_cards
    assert not result.state.community_cards

def test_profile_roundtrip_and_old_profiles():
    profile = rst_portrait_profile()
    assert LayoutProfile.from_json(profile.to_json()) == profile
    legacy = LayoutProfile()
    assert legacy.resolved_regions(493,985) == legacy.regions

def test_four_color_suits(reference):
    zones = rst_portrait_profile().resolved_regions(493,1077)
    assert ink_color(crop(reference,zones['board_1'])) == 'blue'
    assert ink_color(crop(reference,zones['board_3'])) == 'green'
    assert ink_color(crop(reference,zones['hole_2'])) == 'red'
    hsv = cv2.cvtColor(reference,cv2.COLOR_BGR2HSV)
    blue = (hsv[:,:,0]>85)&(hsv[:,:,0]<130)&(hsv[:,:,1]>85)
    hsv[:,:,0][blue] = 60
    recolored = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
    result = VisionPipeline(rst_portrait_profile()).process(recolored)
    assert not result.valid_cards
    assert result.state.community_cards == ()
