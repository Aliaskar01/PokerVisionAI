from collections import OrderedDict
from threading import Lock
from .monte_carlo import simulate
from .deck import validate_cards

class EquityCalculator:
    def __init__(self, capacity: int = 128):
        self.cache = OrderedDict()
        self.lock = Lock()
        self.capacity = capacity

    def calculate(self, hole, board=(), opponents=1, simulations=10000, ranges=(), seed=None, cancel=None, progress=None):
        hole, board = validate_cards(hole, board)
        key = (tuple(sorted(hole)), tuple(sorted(board)), opponents, simulations, tuple(ranges), seed)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
        result = simulate(hole, board, opponents, simulations, ranges, seed, cancel, progress)
        with self.lock:
            self.cache[key] = result
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
        return result
