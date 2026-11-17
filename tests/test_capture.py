import cv2
import numpy as np
from capture.screen_capture import CaptureWorker
from capture.frame_processor import FrameDeduplicator
from capture.window_detector import window_region
import pytest

def test_video_pause_seek(qtbot,tmp_path):
    path = tmp_path/'sample.avi'
    writer = cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(100,100))
    assert writer.isOpened()
    for n in range(20):
        writer.write(np.full((100,100,3),n*10,np.uint8))
    writer.release()
    worker = CaptureWorker(video=str(path))
    frames = []
    worker.frame.connect(lambda frame:frames.append(frame))
    worker.pause_event.set()
    worker.start()
    try:
        qtbot.wait(100)
        assert not frames
        worker.seek(10)
        qtbot.waitUntil(lambda:len(frames)==1,timeout=3000)
        assert 95 < frames[-1].mean() < 105
        worker.pause_event.clear()
        qtbot.waitUntil(lambda:len(frames)>=2,timeout=3000)
    finally:
        worker.stop()
        assert worker.wait(3000)

def test_invalid_source_and_duplicate():
    with pytest.raises(ValueError):
        CaptureWorker()
    with pytest.raises(RuntimeError):
        window_region(0)
    dedup = FrameDeduplicator()
    image = np.zeros((200,100,3),np.uint8)
    assert dedup.changed(image)
    assert not dedup.changed(image)
    assert dedup.changed(image+100)
