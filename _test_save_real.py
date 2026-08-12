# 用真实 AppData 用户完整跑保存链路
import sys, os, time, json
sys.path.insert(0, r'c:\Users\a\Desktop\san_guo\Android')

from ASSET import game_data
from ASSET import login_system

# 模拟运行时 data = 源码 save.json（含 username）
src = r'c:\Users\a\Desktop\san_guo\Android\ASSET\save.json'
with open(src, encoding='utf-8') as f:
    d = json.load(f)
game_data.data.clear()
game_data.data.update(d)

u = d.get('username', '')
print('source username:', u)
# 确认 AppData 里有没有这个用户
import json as _j
app_users = _j.load(open(os.path.join(os.environ['APPDATA'], 'SangoHeroes', 'users.json'), encoding='utf-8'))
print('user in AppData users:', u in app_users, '| in source users:', u in login_system.load_users())

# 注意：login_system 用的是源码路径（非打包），所以 load_users 读源码 users.json
# 真实场景（打包版）load_users 读 AppData users.json
t0 = time.time()
try:
    r1 = login_system.save_user_progress(u, game_data.data)
    t1 = time.time()
    print(f"save_user_progress: {t1 - t0:.3f}s -> {r1}")
    ok, msg = login_system.save_game(u, '实测存档2', game_data.data)
    t2 = time.time()
    print(f"save_game: {t2 - t1:.3f}s -> {ok} {msg}")
except Exception as e:
    print(f"EXCEPTION: {type(e).__name__}: {e}")

# 扫描 data 中的非 JSON 类型对象
bad = []
def scan(obj, path="data", depth=0):
    if depth > 12 or len(bad) > 20:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            scan(v, f"{path}.{k}", depth + 1)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            scan(v, f"{path}[{i}]", depth + 1)
    elif not isinstance(obj, (str, int, float, bool, type(None))):
        bad.append(f"{path}: type={type(obj).__name__}")
scan(game_data.data)
print("non-json objects:", bad if bad else "NONE")

# 清理
users = login_system.load_users()
users.pop(u, None)
login_system.save_users(users)
print("DONE")
