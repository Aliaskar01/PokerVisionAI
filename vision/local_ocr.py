"""CPU OCR with bundled ONNX models. No runtime downloads or network calls."""
from collections import OrderedDict
from hashlib import blake2b
from threading import Lock
import cv2

_lock = Lock()
_engine = None
_cache = OrderedDict()

def recognize(image, *, single_line=False):
    global _engine
    if image is None or image.size==0 or image.std()<5:
        return []
    key = (image.shape,single_line,blake2b(image.tobytes(),digest_size=16).digest())
    with _lock:
        if key in _cache:
            _cache.move_to_end(key)
            return list(_cache[key])
        if _engine is None:
            from rapidocr_onnxruntime import RapidOCR
            _engine = RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1)
        factor = 4 if single_line else 2
        enlarged = cv2.resize(image,None,fx=factor,fy=factor,interpolation=cv2.INTER_CUBIC)
        result,_ = _engine(enlarged,use_det=not single_line,use_cls=False)
        output = [(str(row[-2]),float(row[-1])) for row in (result or [])]
        _cache[key] = output
        if len(_cache)>256:
            _cache.popitem(last=False)
        return list(output)
