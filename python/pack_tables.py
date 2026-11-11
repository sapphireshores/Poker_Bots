import zlib
import base64
import json
from tables import FLUSH_TABLE, NONFLUSH_TABLE

data = json.dumps({"flush": FLUSH_TABLE, "nonflush": NONFLUSH_TABLE}).encode('utf-8')
compressed = base64.b64encode(zlib.compress(data, 9)).decode('ascii')

with open("embedded_tables.py", "w") as f:
    f.write(f'EMBEDDED_TABLES = "{compressed}"\n')
print("Tables compressed successfully!")