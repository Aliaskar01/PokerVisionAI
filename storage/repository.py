import csv
import json
from datetime import datetime,timezone
from pathlib import Path
from .database import connect

class Repository:
    def __init__(self,path: Path):
        self.connection = connect(path)

    def save(self,state,result=None,analysis=None,mode='offline',hand_id=None,corrections=None,events=None) -> int:
        payload = dict(state=state.to_dict(),probabilities=result.to_dict() if result else None,
                       analysis=analysis.to_dict() if analysis else None,corrections=corrections or [],events=events or [])
        with self.connection:
            cursor = self.connection.execute('INSERT INTO analyses(created,hand_id,mode,payload) VALUES(?,?,?,?)',
                (datetime.now(timezone.utc).isoformat(),hand_id,mode,json.dumps(payload,ensure_ascii=False)))
        return cursor.lastrowid

    def list(self):
        return self.connection.execute('SELECT id,created,mode,hand_id FROM analyses ORDER BY id DESC').fetchall()

    def get(self,identifier):
        row = self.connection.execute('SELECT payload FROM analyses WHERE id=?',(identifier,)).fetchone()
        if row is None:
            raise ValueError('Saved hand not found')
        return json.loads(row[0])

    def export(self,identifier,path: Path):
        payload = self.get(identifier)
        if path.suffix.lower() == '.csv':
            state = payload['state']
            row = {**state,**(payload['probabilities'] or {}),'analysis':payload['analysis'],
                   'corrections':payload['corrections'],'events':payload['events']}
            row = {k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()}
            with path.open('w',newline='',encoding='utf-8-sig') as stream:
                writer = csv.DictWriter(stream,fieldnames=row)
                writer.writeheader()
                writer.writerow(row)
        else:
            path.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8')

    def close(self):
        self.connection.close()
