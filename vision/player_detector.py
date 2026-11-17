from capture.frame_processor import crop

class PlayerDetector:
    def __init__(self, ocr):
        self.ocr = ocr

    def detect(self,frame,regions):
        players = []
        for seat,region in regions.items():
            if not seat.startswith('seat_'):
                continue
            texts = self.ocr.read_text(crop(frame,region))
            text = ' '.join(t for t,c in texts if c >= self.ocr.threshold).lower()
            state = 'UNKNOWN'
            if 'fold' in text or 'пас' in text:
                state = 'FOLDED'
            elif 'disconnect' in text or 'нет связи' in text:
                state = 'DISCONNECTED'
            elif 'all-in' in text or 'олл-ин' in text:
                state = 'ACTIVE'
            stack_region = regions.get(seat.replace('seat_','stack_'),region)
            stack = self.ocr.read_amount(crop(frame,stack_region))
            players.append({'seat':seat,'state':state,'occupied':True if stack.value is not None else None,
                            'stack':stack.value,'dealer':True if text.strip() == 'dealer' else None})
        return players
