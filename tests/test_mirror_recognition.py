"""Mirror chrome, missing hero cards and a newly captured uncalibrated hand."""
from dataclasses import replace
import cv2
import numpy as np
import pytest
from config import ROOT,rst_portrait_profile,LayoutProfile,upgrade_builtin_profile
from vision.pipeline import VisionPipeline,VisionResult
from vision.table_detector import rst_viewport
from vision.rank_suit_classifier import RankSuitClassifier
from poker.game_state import GameState


def read(name):
    return cv2.imdecode(np.fromfile(ROOT/f'assets/screenshots/{name}.png',np.uint8),1)


def test_actual_letsview_window_not_used_for_templates():
    image=read('letsview_reference_4')
    result=VisionPipeline(rst_portrait_profile()).process(image)
    assert result.viewport==(0,50,495,1080)
    assert result.valid_cards
    assert result.state.hole_cards==('5s','4d')
    assert result.state.community_cards==('Qs','8c','Jd')
    assert result.state.pot==4 and result.state.hero_stack==18
    x,y,w,h=result.regions['board_1'].pixels(495,1130)
    assert 500<=y<=504 and 13<=x<=16
    assert next(box for box in result.boxes if box[-1].startswith('Qs '))[:4]==(x,y,w,h)


@pytest.mark.parametrize('width,padding',[(289,28),(493,50),(740,75)])
def test_mirror_toolbar_and_side_padding(width,padding):
    image=read('rst_reference_2')
    image=cv2.resize(image,(width,round(1077*width/493)),interpolation=cv2.INTER_AREA)
    canvas=np.full((image.shape[0]+padding+18,width+40,3),230,np.uint8)
    canvas[padding:padding+image.shape[0],20:20+width]=image
    result=VisionPipeline(rst_portrait_profile()).process(canvas)
    assert abs(result.viewport[0]-20)<=1 and abs(result.viewport[1]-padding)<=1
    assert result.state.community_cards==('Jd','2d','Qc')
    assert result.state.pot in (80,None)
    # Optional pale controls remain part of the cropped phone viewport.
    assert 'actions' in result.regions


def test_spectator_keeps_board_and_pot_without_hero_cards():
    image=read('letsview_reference_4')
    image[975:1034,190:310]=image[700:759,190:310]
    result=VisionPipeline(rst_portrait_profile()).process(image)
    assert not result.valid_cards
    assert result.state.hole_cards==()
    assert result.state.community_cards==('Qs','8c','Jd')
    assert result.state.pot==4 and result.state.street=='FLOP'


def test_no_table_is_unknown_not_preflop():
    frame=np.full((900,400,3),210,np.uint8)
    assert rst_viewport(frame) is None
    result=VisionPipeline(rst_portrait_profile()).process(frame)
    assert not result.valid_cards and not result.state.board_known
    assert result.state.street=='UNKNOWN'
    assert 'table not found' in result.state.warnings[0]


@pytest.mark.parametrize('rank',['6','7','9','K'])
def test_neural_fallback_for_ranks_without_rst_templates(rank):
    from PIL import Image,ImageDraw,ImageFont
    image=Image.new('RGB',(83,116),(235,235,235))
    ImageDraw.Draw(image).text((5,0),rank,font=ImageFont.truetype('C:/Windows/Fonts/times.ttf',60),fill=(200,20,30))
    detector=RankSuitClassifier(ROOT/'assets/ranks',use_ocr=True)
    assert rank not in {sample[0] for sample in detector.templates}
    result=detector.predict(cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR))
    assert result.card==rank+'h'


def test_live_displays_partial_state_and_restores_confirmed_state(qtbot,tmp_path):
    from gui.main_window import MainWindow
    window=MainWindow(tmp_path)
    qtbot.addWidget(window)
    window.capture_target='live'
    image=read('letsview_reference_4')
    full=GameState(hole_cards=('5s','4d'),community_cards=('Qs','8c','Jd'),pot=4)
    try:
        for _ in range(3):
            window.vision_result(image,VisionResult(full,[],True),window.generation)
        partial=replace(full,hole_cards=(),pot=8)
        window.vision_result(image,VisionResult(partial,[],False),window.generation)
        assert window.live.form.inputs['community_cards'].text()=='Qs 8c Jd'
        assert window.live.form.inputs['pot'].text()=='8'
        assert window.live.form.inputs['hole_cards'].text()==''
        assert window.live.result is None and not window.live.debounce.isActive()
        for _ in range(3):
            window.vision_result(image,VisionResult(full,[],True),window.generation)
        assert window.live.form.inputs['hole_cards'].text()=='5s 4d'
        assert window.live.form.inputs['pot'].text()=='4'
    finally:
        window.close()


def test_prior_release_builtin_enables_viewport_detection():
    import json
    profile=rst_portrait_profile()
    data=json.loads(profile.to_json())
    del data['auto_table_crop']
    old=LayoutProfile.from_json(json.dumps(data))
    assert upgrade_builtin_profile(old).auto_table_crop
    data['auto_table_crop']=False
    custom=LayoutProfile.from_json(json.dumps(data))
    assert not upgrade_builtin_profile(custom).auto_table_crop
