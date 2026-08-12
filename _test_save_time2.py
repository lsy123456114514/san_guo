# 用 AppData 真实数据模拟主菜单保存链路
import sys, os, time, json
sys.path.insert(0, r'c:\Users\a\Desktop\san_guo\Android')

from ASSET import game_data
from ASSET import login_system

# 载入 AppData save.json 作为全局 data（模拟登录后 data）
ap = os.path.join(os.environ['APPDATA'], 'SangoHeroes', 'save.json')
with open(ap, encoding='utf-8') as f:
    d = json.load(f)
game_data.data.clear()
game_data.data.update(d)

users = login_system.load_users()
u = d.get('username', '')
print('user:', u, '| in users:', u in users)

# 完整链路：input_save_name 之后的两步
t0 = time.time()
try:
    r1 = login_system.save_user_progress(u, game_data.data)
    t1 = time.time()
    print(f"save_user_progress: {t1 - t0:.3f}s -> {r1}")
    ok, msg = login_system.save_game(u, '实测存档', game_data.data)
    t2 = time.time()
    print(f"save_game: {t2 - t1:.3f}s -> {ok} {msg}")
except Exception as e:
    print(f"EXCEPTION: {type(e).__name__}: {e}")

# 扫描循环引用
seen = set()
loop_refs = []
def scan(o, path="data"):
    if id(o) in seen:
        loop_refs.append(path)
        return
    seen.add(id(o))
    if isinstance(o, dict):
        for k, v in o.items():
            scan(v, f"{path}.{k}")
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            scan(v, f"{path}[{i}]")
scan(game_data.data)
print("loop refs:", loop_refs[:5] if loop_refs else "NONE")

# 还原 users.json（删除测试存档，防止污染）
users = login_system.load_users()
if u in users and users[u].get('saves'):
    users[u]['saves'] = []
    login_system.save_users(users)
    print("cleaned test save")
print("DONE")
