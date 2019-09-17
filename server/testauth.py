import auth
import time

sdb = auth.sessiondb()
# sdb.create()
sid = sdb.create_active_session('jack')
print(sid)
print(time.sleep(5))
print("deleting")
sdb.delete_active_session(sid)
