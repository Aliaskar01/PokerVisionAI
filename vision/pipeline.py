from dataclasses import dataclass,field
from config import LayoutProfile, Region, ROOT, DATA
from capture.frame_processor import crop
from poker.game_state import GameState
from .card_classifier import CardClassifier
from .card_detector import CardDetector
from .ocr_detector import OCRDetector
from .player_detector import PlayerDetector
from .ui_state_detector import detect_ui,detect_pre_action_image
from .table_detector import detect_table,rst_viewport
import cv2
import numpy as np

@dataclass
class VisionResult:
    state: GameState
    boxes: list
    valid_cards: bool
    regions: dict = field(default_factory=dict)
    viewport: tuple | None = None

class VisionPipeline:
    def __init__(self, profile: LayoutProfile):
        self.profile = profile
        self.cards = CardDetector(CardClassifier([ROOT/'assets/templates',DATA/'templates'],profile.card_threshold))
        self.cards.rst_classifier.use_ocr=profile.ocr_backend=='rapidocr'
        self.ocr = OCRDetector(profile.ocr_threshold,profile.use_easyocr,DATA/'models',profile.ocr_backend)
        self.players = PlayerDetector(self.ocr)
        path = ROOT/'assets/ui/rst_pre_action.png'
        self.pre_action_template = cv2.imdecode(np.fromfile(path,dtype=np.uint8),cv2.IMREAD_COLOR) if path.exists() else None

    def process(self,frame) -> VisionResult:
        original_height,original_width=frame.shape[:2]
        viewport=rst_viewport(frame) if self.profile.auto_table_crop else (0,0,original_width,original_height)
        if viewport is None:
            return VisionResult(GameState(board_known=False,warnings=['Poker table not found. Check the selected mirror window or capture region.']),[],False)
        x,y,width,height=viewport
        working=frame[y:y+height,x:x+width]
        if self.profile.reference_size is not None:
            reference_width = self.profile.reference_size[0]
            if width != reference_width:
                scale=width/reference_width
                working=cv2.resize(working,(reference_width,round(height/scale)),
                                   interpolation=cv2.INTER_AREA if scale>1 else cv2.INTER_CUBIC)
        result=self._process(working)
        sx,sy=width/working.shape[1],height/working.shape[0]
        result.boxes=[(x+round(bx*sx),y+round(by*sy),round(w*sx),round(h*sy),label)
                      for bx,by,w,h,label in result.boxes]
        result.regions={}
        for name,region in self.profile.resolved_regions(working.shape[1],working.shape[0]).items():
            rx,ry,rw,rh=region.pixels(working.shape[1],working.shape[0])
            px,py=x+round(rx*sx),y+round(ry*sy)
            pw,ph=min(original_width-px,round(rw*sx)),min(original_height-py,round(rh*sy))
            result.regions[name]=Region(px/original_width,py/original_height,pw/original_width,ph/original_height)
        result.viewport=(x,y,width,height)
        return result

    def _process(self,frame) -> VisionResult:
        regions = self.profile.resolved_regions(frame.shape[1],frame.shape[0])
        values, boxes, warnings, confidences = {},[],[],[]
        board_known,board_count = False,None
        valid = True
        for name,maximum in [('hole',2),('board',5)]:
            if name not in regions:
                valid = False
                values[name] = ()
                warnings.append(f'{name}: region is outside the captured image')
                continue
            roi = regions[name]
            x,y,_,_ = roi.pixels(frame.shape[1],frame.shape[0])
            try:
                slots = [regions[f'{name}_{i}'] for i in range(1,maximum+1) if f'{name}_{i}' in regions]
                detected = self.cards.detect_slots(frame,slots) if slots else self.cards.detect(crop(frame,roi),maximum)
                cards = tuple(d.card for d in detected if d.card)
                complete = len(cards) == len(detected) and (len(cards)==2 if name=='hole' else len(cards) in (0,3,4,5))
                if name=='board':
                    board_known,board_count = complete,len(detected)
                if not complete:
                    valid = False
                    warnings.append(f'{name}: incomplete or uncertain cards; manual correction required')
                values[name] = cards if complete else ()
                for d in detected:
                    dx,dy,w,h = d.box
                    boxes.append((dx if slots else x+dx,dy if slots else y+dy,w,h,f'{d.card or "UNKNOWN"} {d.confidence:.0%}'))
                    confidences.append(d.confidence if d.card else 0)
            except ValueError as exc:
                valid = False
                values[name] = ()
                warnings.append(str(exc))
        if len(set(values['hole']+values['board'])) != len(values['hole']+values['board']):
            warnings.append('Duplicate card across hole and board; both rejected')
            values = {'hole':(),'board':()}
            board_known = False
            valid = False
        from .ocr_detector import OCRValue
        numbers = {key:self.ocr.read_amount(crop(frame,regions[key])) if key in regions else OCRValue(None,0) for key in ('pot','hero_stack')}
        actions_image = crop(frame,regions['actions']) if 'actions' in regions else None
        text = ' '.join(t for t,c in self.ocr.read_text(actions_image) if c >= self.ocr.threshold) if actions_image is not None else ''
        ui_state = detect_ui(text)
        if ui_state == 'UNKNOWN' and detect_pre_action_image(actions_image,self.pre_action_template):
            ui_state = 'PRE_ACTION_AVAILABLE'
        players = self.players.detect(frame,regions)
        if self.ocr.error:
            warnings.append(self.ocr.error)
        # Avatars/stack labels alone are not evidence of active holdings.
        opponents = sum(p['state']=='ACTIVE' for p in players) if players and all(p['state'] in ('ACTIVE','FOLDED') for p in players) else None
        table = detect_table(frame)
        if table:
            boxes.append((*table,'Table candidate'))
        state = GameState(hole_cards=values['hole'],community_cards=values['board'],pot=numbers['pot'].value,
                          hero_stack=numbers['hero_stack'].value,active_opponents=opponents,
                          detection_confidence=min(confidences,default=0),ui_state=ui_state,players=players,
                          board_known=board_known,visible_board_count=board_count,
                          sources={'hole_cards':'computer vision','community_cards':'computer vision','pot':'OCR','hero_stack':'OCR','ranges':'default assumption'},warnings=warnings)
        for key,roi in regions.items():
            if key.startswith('bet_') or key == 'call_amount':
                value = self.ocr.read_amount(crop(frame,roi)).value
                if key == 'call_amount' and state.ui_state == 'PLAYER_TURN':
                    state.call_amount = value
                    state.sources[key] = 'OCR'
                elif key.startswith('bet_'):
                    state.players.append({'seat':key[4:],'visible_bet':value})
        return VisionResult(state,boxes,valid)
