"""Real-image regressions plus transformations and independent OCR strings."""
import cv2
import numpy as np
import pytest
from config import ROOT,LayoutProfile,region,rst_portrait_profile,upgrade_builtin_profile
from capture.frame_processor import crop
from vision.pipeline import VisionPipeline
from vision.ocr_detector import OCRDetector
from vision.rank_suit_classifier import RankSuitClassifier
from poker.game_state import GameState


def reference(index):
    return cv2.imdecode(np.fromfile(ROOT/f'assets/screenshots/rst_reference_{index}.png',np.uint8),cv2.IMREAD_COLOR)


@pytest.mark.parametrize('index,hole,board,pot,stack,players',[
    (1,('Qs','Th'),('3d','Ad','4h'),60,380,[195,1200,942,None]),
    (2,('Jc','4h'),('Jd','2d','Qc'),80,380,[411,1150,1200,1490]),
    (3,('8c','5s'),(),1.5,44.5,[200,316,412,183]),
])
def test_all_originals(index,hole,board,pot,stack,players):
    pipeline=VisionPipeline(rst_portrait_profile())
    result=pipeline.process(reference(index))
    state=result.state
    assert result.valid_cards and state.board_known
    assert state.hole_cards==hole and state.community_cards==board
    assert state.pot==pot and state.hero_stack==stack
    assert [p['stack'] for p in state.players]==players
    assert state.call_amount is None and state.active_opponents is None
    assert state.ui_state==('UNKNOWN' if index==1 else 'PRE_ACTION_AVAILABLE')
    assert pipeline.ocr.backend=='rapidocr' and not pipeline.ocr.error


@pytest.mark.parametrize('text,amount',[('Pot: 108.25',108.25),('2.35K',2350),('976.40',976.4)])
def test_neural_ocr_unseen_values(text,amount,monkeypatch):
    image=np.full((45,250,3),230,np.uint8)
    cv2.putText(image,text,(8,31),cv2.FONT_HERSHEY_SIMPLEX,.8,(30,30,30),1,cv2.LINE_AA)
    ocr=OCRDetector(backend='rapidocr')
    def forbidden(_):
        pytest.fail('Neural OCR unexpectedly fell back to calibrated digit templates')
    monkeypatch.setattr(ocr.numeric,'read',forbidden)
    assert ocr.read_amount(image).value==amount


def test_rank_transfers_from_small_hole_card_to_large_board():
    classifier=RankSuitClassifier(ROOT/'assets/ranks')
    # Retain only the small hero 4 glyph; remove the large board 4 sample.
    # Loading a temporary training subset avoids relying on file ordering.
    from vision.rank_suit_classifier import extract_rank,normalize_glyph
    zones=rst_portrait_profile().resolved_regions(493,1077)
    glyph,_=extract_rank(crop(reference(2),zones['hole_2']))
    classifier.templates=[t for t in classifier.templates if t[0]!='4']
    classifier.templates.append(('4',normalize_glyph(glyph),glyph.shape[1]/glyph.shape[0]))
    board=reference(1)
    zones=rst_portrait_profile().resolved_regions(493,985)
    assert classifier.predict(crop(board,zones['board_3'])).card=='4h'


def test_rank_recognizes_unseen_suit_combination_and_translation():
    image=reference(3)
    zones=rst_portrait_profile().resolved_regions(493,1077)
    card=crop(image,zones['hole_1']).copy()
    hsv=cv2.cvtColor(card,cv2.COLOR_BGR2HSV)
    green=(hsv[:,:,0]>=35)&(hsv[:,:,0]<85)&(hsv[:,:,1]>80)
    hsv[:,:,0][green]=0  # Unobserved 8 of hearts, same rank geometry.
    card=cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
    card=cv2.warpAffine(card,np.float32([[1,0,2],[0,1,1]]),(card.shape[1],card.shape[0]),borderMode=cv2.BORDER_REPLICATE)
    assert RankSuitClassifier(ROOT/'assets/ranks').predict(card).card=='8h'


def test_unreadable_board_is_not_preflop():
    unknown=GameState(hole_cards=('Ah','Kh'),board_known=False,visible_board_count=3)
    assert unknown.street=='FLOP'
    assert GameState(board_known=False).street=='UNKNOWN'
    assert unknown.equity_key()!=GameState(hole_cards=('Ah','Kh')).equity_key()
    assert GameState.from_dict(unknown.to_dict())==unknown


def test_saved_builtin_layout_migrates_but_custom_layout_is_preserved():
    old=LayoutProfile.load(ROOT/'assets/layout_rst_legacy.json')
    upgraded=upgrade_builtin_profile(old)
    assert upgraded.ocr_backend=='rapidocr'
    assert upgraded.regions==rst_portrait_profile().regions
    old.regions['pot']=region(200,400,280,440)
    assert upgrade_builtin_profile(old) is old


@pytest.mark.parametrize('index,hole,pot',[(1,'Qs Th','60'),(3,'8c 5s','1.5')])
def test_normal_load_media_uses_migrated_profile(qtbot,tmp_path,index,hole,pot):
    from gui.main_window import MainWindow
    (tmp_path/'layout.json').write_text((ROOT/'assets/layout_rst_legacy.json').read_text(encoding='utf-8'),encoding='utf-8')
    window=MainWindow(tmp_path)
    qtbot.addWidget(window)
    try:
        window.load_path(ROOT/f'assets/screenshots/rst_reference_{index}.png')
        qtbot.waitUntil(lambda:window.offline.form.inputs['pot'].text()==pot,timeout=15000)
        assert window.offline.form.inputs['hole_cards'].text()==hole
        if index==3:
            assert window.offline.form.inputs['community_cards'].placeholderText()=='No community cards'
            window.offline.form.simulations.setCurrentText('1000')
            window.offline.form.inputs['active_opponents'].setText('4')
            window.offline.calculate()
            qtbot.waitUntil(lambda:window.offline.result is not None,timeout=10000)
            assert 0<=window.offline.result.equity<=1
            assert window.offline.last_state.hole_cards==('8c','5s')
    finally:
        window.close()


def test_unknown_board_blocks_calculation_until_manual_correction(qtbot):
    from gui.dashboard import Dashboard
    panel=Dashboard('offline')
    qtbot.addWidget(panel)
    panel.accept_state(GameState(hole_cards=('Ah','Kh'),active_opponents=1,board_known=False,visible_board_count=3))
    panel.calculate()
    assert not panel.workers and 'unreadable' in panel.status.text()
    assert 'Unknown' in panel.form.inputs['community_cards'].placeholderText()
    panel.form.inputs['community_cards'].setText('2c 3d 4s')
    assert panel.form.state().board_known
    panel.shutdown()
