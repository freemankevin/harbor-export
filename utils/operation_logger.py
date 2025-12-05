import json
import os
import time
from typing import Any, Dict, Iterable
from config import Config

LOG_PATH = os.path.join(os.path.dirname(__file__), 'logs', 'operations.log')

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def append(record: Dict[str, Any]):
    rec = dict(record)
    rec.setdefault('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

def read_lines(limit: int = 2000) -> Iterable[Dict[str, Any]]:
    if not os.path.exists(LOG_PATH):
        return []
    lines = []
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f.readlines()[-limit:]:
            try:
                lines.append(json.loads(line))
            except:
                pass
    return lines

