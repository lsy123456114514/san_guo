# 测试保存进度链路耗时与异常（模拟运行时 data）
import sys, os, time, json
sys.path.insert(0, r'c:\Users\a\Desktop\san_guo\Android')

from ASSET import game_data
from ASSET import login_system

print("data top keys:", list(game_data.data.keys())[:30])

# 模拟主菜单保存：save_user_progress + save_game
t0 = time.time()
try:
    login_system.save_user_progress("tester", game_data.data)
    t1 = time.time()
    print(f"save_user_progress: {t1 - t0:.3f}s")
    ok, msg = login_system.save_game("tester", "测速", game_data.data)
    t2 = time.time()
    print(f"save_game: {t2 - t1:.3f}s -> {ok} {msg}")
except Exception as e:
    print(f"EXCEPTION: {type(e).__name__}: {e}")

# 检查 data 中是否有不可 JSON 序列化 / 巨大对象
def scan(obj, path="data", depth=0, out=None):
    if out is None:
        out = []
    if depth > 8:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            scan(v, f"{path}.{k}", depth + 1, out)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj[:50]):
            scan(v, f"{path}[{i}]", depth + 1, out)
    else:
        if isinstance(obj, (str, int, float, bool, type(None))):
            if isinstance(obj, str) and len(obj) > 100000:
                out.append(f"{path}: HUGE STRING {len(obj)} chars")
        else:
            out.append(f"{path}: type={type(obj).__name__}")
    return out

problems = scan(game_data.data)
for p in problems[:30]:
    print("PROBLEM:", p)
if not problems:
    print("NO non-json / huge objects found in data")

# 测 json.dump 耗时
t0 = time.time()
try:
    s = json.dumps(game_data.data, ensure_ascii=False)
    print(f"json.dumps data: {time.time() - t0:.3f}s, {len(s)} chars")
except Exception as e:
    print(f"json.dumps EXCEPTION: {type(e).__name__}: {e}")

# 清理测试用户
users = login_system.load_users()
users.pop("tester", None)
login_system.save_users(users)
print("DONE")
