"""Win32 enumeration and client rectangles via ctypes; read-only calls only."""
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import sys

@dataclass(frozen=True)
class Window:
    handle: int
    title: str

def _api():
    if sys.platform != 'win32':
        raise RuntimeError('Window capture is supported on Windows; use region capture elsewhere')
    user = ctypes.WinDLL('user32', use_last_error=True)
    for name in ('IsWindow','IsWindowVisible','IsIconic','GetWindowTextLengthW'):
        getattr(user,name).argtypes = [wintypes.HWND]
    user.GetWindowTextW.argtypes = [wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
    user.GetClientRect.argtypes = [wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
    user.ClientToScreen.argtypes = [wintypes.HWND,ctypes.POINTER(wintypes.POINT)]
    return user

def list_windows() -> list[Window]:
    user, windows = _api(), []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    def visit(hwnd, _):
        size = user.GetWindowTextLengthW(hwnd)
        if user.IsWindowVisible(hwnd) and size:
            title = ctypes.create_unicode_buffer(size+1)
            user.GetWindowTextW(hwnd,title,size+1)
            windows.append(Window(int(hwnd),title.value))
        return True
    user.EnumWindows.argtypes = [callback_type,wintypes.LPARAM]
    user.EnumWindows(callback_type(visit),0)
    return windows

def window_region(handle: int) -> dict:
    user = _api()
    if not user.IsWindow(handle):
        raise RuntimeError('Capture window disappeared; reconnect the phone and select the source again')
    if user.IsIconic(handle):
        raise RuntimeError('Capture window is minimized; restore it to resume')
    rect, point = wintypes.RECT(), wintypes.POINT(0,0)
    if not user.GetClientRect(handle,ctypes.byref(rect)) or not user.ClientToScreen(handle,ctypes.byref(point)):
        raise RuntimeError('Cannot read window dimensions')
    if rect.right <= 0 or rect.bottom <= 0:
        raise RuntimeError('Capture window has no visible client area')
    return dict(left=point.x,top=point.y,width=rect.right,height=rect.bottom)
