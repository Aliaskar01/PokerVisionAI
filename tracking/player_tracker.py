class PlayerTracker:
    def __init__(self):
        self.seats = {}

    def update(self, players: list[dict]) -> dict:
        # Unknown current evidence must not inherit a stale active-player label.
        self.seats = {p['seat']:dict(p) for p in players}
        return self.seats.copy()
