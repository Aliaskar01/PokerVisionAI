from .ocr_detector import parse_amount
import re

def recognized_bet(text: str) -> float | None:
    if re.search(r'(?i)(call any|check.?fold|любой колл)',text):
        return None
    return parse_amount(text)
