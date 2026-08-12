# 实测大数据量（mc_world placed_blocks）下保存耗时
import sys, os, time, json, random
sys.path.insert(0, r'c:\Users\a\Desktop\san_guo\Android')

from ASSET import game_data
from ASSET import login_system

# 构造大量方块数据
for n in (100, 1000, 5000, 20000):
    blocks = []
    for i in range(n):
        blocks.append({"x": random.randint(-1000, 1000), "y": random.randint(-1000, 1000),
                       "z": random.randint(-1000, 1000), "type": random.choice(["泥土","石头","木头","草地","沙子","水","玻璃","砖块"])})
    game_data.data["mc_world"] = {"placed_blocks": blocks, "hotbar": [None]*9, "player_pos": [0,0,0]}
    # 测试1: save() 序列化整个 data
    t0 = time.time()
    try:
        s = json.dumps(game_data.data, ensure_ascii=False)
        t1 = time.time()
        print(f"blocks={n}: dumps={t1-t0:.3f}s size={len(s)/1024/1024:.2f}MB")
    except Exception as e:
        print(f"blocks={n}: dumps EXC {type(e).__name__}: {e}")

# 测试2: save_user_progress 反复保存后 users.json 膨胀
game_data.data["mc_world"] = {"placed_blocks": [{"x":1,"y":2,"z":3,"type":"石头"} for _ in range(1000)], "hotbar":[None]*9}
u = "bigtest"
users = login_system.load_users()
users.pop(u, None)
login_system.save_users(users)
for i in range(3):
    t0 = time.time()
    login_system.save_user_progress(u, game_data.data)
    ok, msg = login_system.save_game(u, f"s{i}", game_data.data)
    t1 = time.time()
    sz = os.path.getsize(login_system.USERS_PATH)
    print(f"round{i}: {t1-t0:.3f}s -> {ok} {msg}, users.json={sz/1024:.1f}KB")

# 清理
users = login_system.load_users()
users.pop(u, None)
login_system.save_users(users)
print("DONE")
