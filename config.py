from dataclasses import dataclass, field, asdict
from pathlib import Path
import json
import os
import sys

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
DATA = Path(os.environ.get('POKERVISION_DATA', Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'PokerVisionAI'))

@dataclass(frozen=True)
class Region:
    x: float
    y: float
    w: float
    h: float

    def __post_init__(self):
        if not (0 <= self.x < 1 and 0 <= self.y < 1 and 0 < self.w <= 1 and 0 < self.h <= 1 and self.x+self.w <= 1.00001 and self.y+self.h <= 1.00001):
            raise ValueError('Regions must lie within normalized coordinates 0–1')

    def pixels(self, width: int, height: int) -> tuple[int, int, int, int]:
        x, y = int(self.x*width+1e-8), int(self.y*height+1e-8)
        return x, y, max(1, min(width-x, round(self.w*width))), max(1, min(height-y, round(self.h*height)))

def region(x1, y1, x2, y2):
    return Region(x1/493, y1/1077, (x2-x1)/493, (y2-y1)/1077)

def default_regions():
    return {'hole': region(194,924,302,984), 'board': region(13,449,480,567),
            'pot': region(217,370,278,441), 'hero_stack': region(224,860,278,900),
            'seat_1': region(20,127,78,204), 'seat_2': region(415,125,479,207),
            'seat_3': region(22,839,79,912), 'seat_4': region(414,838,479,914),
            'actions': region(0,982,493,1077)}

@dataclass
class LayoutProfile:
    name: str = 'RST portrait 493x1077 (uncalibrated)'
    regions: dict[str, Region] = field(default_factory=default_regions)
    card_threshold: float = .94
    ocr_threshold: float = .85
    use_easyocr: bool = False
    reference_size: tuple[int, int] | None = None
    ocr_backend: str = 'template'
    auto_table_crop: bool = False

    def __post_init__(self):
        if not {'hole','board','pot','hero_stack','actions'} <= self.regions.keys():
            raise ValueError('Profile needs hole, board, pot, hero_stack and actions regions')
        if not 0 <= self.card_threshold <= 1 or not 0 <= self.ocr_threshold <= 1:
            raise ValueError('Thresholds must be 0–1')
        if self.ocr_backend not in ('template','rapidocr'):
            raise ValueError('OCR backend must be template or rapidocr')
        if self.reference_size is not None:
            if len(self.reference_size) != 2 or any(type(x) is not int or x <= 0 for x in self.reference_size):
                raise ValueError('Reference size must contain two positive integers')
            self.reference_size = tuple(self.reference_size)

    def resolved_regions(self, width: int, height: int) -> dict[str, Region]:
        """Width-anchored RST coordinates exclude the optional bottom panel.

        Existing normalized profiles remain unchanged. Out-of-frame zones are
        omitted; an absent action panel is not treated as a betting control.
        """
        if self.reference_size is None:
            return self.regions
        reference_width,reference_height = self.reference_size
        factor = reference_height * width / (reference_width * height)
        resolved = {}
        for name,roi in self.regions.items():
            top,bottom = roi.y*factor,min(1,(roi.y+roi.h)*factor)
            if top >= 1 or (bottom-top)*height < 4:
                continue
            resolved[name] = Region(roi.x,top,roi.w,bottom-top)
        return resolved

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, text: str):
        data = json.loads(text)
        data['regions'] = {k: Region(**v) for k,v in data['regions'].items()}
        if 'auto_table_crop' not in data:
            builtin=rst_portrait_profile()
            if data['regions']==builtin.regions and tuple(data.get('reference_size') or ())==builtin.reference_size:
                data['auto_table_crop']=True
        return cls(**data)

    @classmethod
    def load(cls, path: Path):
        return cls.from_json(path.read_text(encoding='utf-8'))

def rst_portrait_profile() -> LayoutProfile:
    """Measured from the supplied 493×1077 image; width is the scale anchor."""
    zones = default_regions() | {
        'hole':region(194,924,302,982),
        'board':region(10,445,483,570),
        'hole_1':region(196,924,249,982), 'hole_2':region(250,924,300,982),
        'board_1':region(14,450,97,566), 'board_2':region(111,450,194,566),
        'board_3':region(208,450,291,566), 'board_4':region(305,450,388,566),
        'board_5':region(402,450,485,566),
        'pot':region(220,425,290,446), 'hero_stack':region(240,861,280,880),
        'stack_1':region(45,126,82,145), 'stack_2':region(435,125,480,146),
        'stack_3':region(25,836,82,858), 'stack_4':region(430,836,480,858),
    }
    return LayoutProfile(name='RST portrait — width anchored, optional pre-action panel',
                         regions=zones,reference_size=(493,1077),ocr_backend='rapidocr',auto_table_crop=True)

def upgrade_builtin_profile(profile):
    """Only migrate an exact old built-in layout; retain user-adjusted regions."""
    path=ROOT/'assets/layout_rst_legacy.json'
    if path.exists():
        legacy=LayoutProfile.load(path)
        if profile.regions==legacy.regions and profile.reference_size==legacy.reference_size:
            upgraded=rst_portrait_profile()
            upgraded.use_easyocr=profile.use_easyocr
            upgraded.card_threshold=profile.card_threshold
            upgraded.ocr_threshold=profile.ocr_threshold
            return upgraded
    return profile
