from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class HandHistory:
    hand_id: str
    events: list[dict] = field(default_factory=list)

    def record(self, state, correction: bool = False):
        data = state.to_dict()
        if not self.events or self.events[-1]['state'] != data:
            self.events.append({'timestamp':datetime.now(timezone.utc).isoformat(),'state':data,'correction':correction})
