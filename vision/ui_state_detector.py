def detect_ui(text: str) -> str:
    text = ' '.join(text.lower().split())
    if 'callany' in text.replace(' ',''):
        return 'PRE_ACTION_AVAILABLE'
    if any(x in text for x in ('check/fold','check / fold','call any','чек/фолд','чек / фолд','любой колл')):
        return 'PRE_ACTION_AVAILABLE'
    if any(x in text for x in ('hand finished','wins the pot','выигрывает банк')):
        return 'HAND_FINISHED'
    if ('fold' in text and ('raise' in text or 'bet' in text)) or ('фолд' in text and 'рейз' in text):
        return 'PLAYER_TURN'
    if 'waiting' in text or 'ожидание' in text:
        return 'WAITING_FOR_TURN'
    return 'UNKNOWN'

def detect_pre_action_image(image, template) -> bool:
    """Match all three observed controls; a pale panel alone is insufficient."""
    import cv2
    if template is None or image is None or image.shape[0] < image.shape[1]*.12:
        return False
    query = cv2.resize(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),(300,60))
    reference = cv2.resize(cv2.cvtColor(template,cv2.COLOR_BGR2GRAY),(300,60))
    # Require each control column, including its label, to match.
    for start,end in ((0,100),(100,200),(200,300)):
        part = query[:,start:end]
        if part.std()<5 or float(cv2.matchTemplate(part,reference[:,start:end],cv2.TM_CCOEFF_NORMED)[0,0]) < .96:
            return False
    return True
