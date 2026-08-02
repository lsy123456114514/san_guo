import tkinter as tk
import random

梗列表 = [
    {"text": "鸡你太美", "effect": "speed_up", "color": "#FF69B4"},
    {"text": "奥利给", "effect": "grow_fat", "color": "#FF4500"},
    {"text": "芜湖起飞", "effect": "flash_bg", "color": "#00BFFF"},
    {"text": "反向抽烟", "effect": "reverse_ctrl", "color": "#696969"},
    {"text": "骚猪", "effect": "fat_snake", "color": "#FFD700"},
    {"text": "开挂", "effect": "invincible", "color": "#00FF00"},
    {"text": "小丑竟是我自己", "effect": "lose_points", "color": "#8B0000"},
    {"text": "栓Q", "effect": "shrink", "color": "#FFC0CB"},
    {"text": "遥遥领先", "effect": "speed_up", "color": "#00CED1"},
    {"text": "退退退", "effect": "shrink", "color": "#DC143C"},
    {"text": "挖呀挖", "effct": "invincible", "color": "#FF1493"},
    {"text": "绝绝子", "effect": "grow_fat", "color": "#9370DB"},
    {"text": "emo了", "effect": "shrink", "color": "#2F4F4F"},
    {"text": "内卷", "effect": "speed_up", "color": "#FF6347"},
    {"text": "躺平", "effect": "slow_down", "color": "#708090"},
    {"text": "打工人", "effect": "grow_fat", "color": "#FFDAB9"},
    {"text": "社会人", "effect": "dance_mode", "color": "#FF4500"},
    {"text": "精神小伙", "effect": "dance_mode", "color": "#00FF7F"},
    {"text": "干就完事", "effect": "speed_up", "color": "#FF6347"},
    {"text": "巨魔蘸酱", "effect": "fat_snake", "color": "#8B4513"},
    {"text": "影流之主", "effect": "reverse_ctrl", "color": "#483D8B"},
    {"text": "抖肩舞", "effect": "dance_mode", "color": "#FF1493"},
    {"text": "来了老弟", "effect": "grow_fat", "color": "#FFA500"},
    {"text": "打工是不可能", "effect": "slow_down", "color": "#556B2F"},
    {"text": "电瓶", "effect": "speed_up", "color": "#808080"},
    {"text": "野狼disco", "effect": "dance_mode", "color": "#00CED1"},
    {"text": "左边画个龙", "effect": "flash_bg", "color": "#FF4500"},
    {"text": "淡黄长裙", "effect": "grow_fat", "color": "#32CD32"},
    {"text": "科目三", "effect": "dance_mode", "color": "#FFA500"},
    {"text": "显眼包", "effect": "flash_bg", "color": "#DA70D6"},
    {"text": "蚌埠住了", "effect": "lose_points", "color": "#2F4F4F"},
    {"text": "破防了", "effect": "reverse_ctrl", "color": "#4B0082"},
    {"text": "yyds", "effeect": "flash_bg", "color": "#FFFACD"},
    {"text": "蓬松头发", "effect": "fat_snake", "color": "#FAEBD7"},
    {"text": "reader", "effect": "slow_down", "color": "#DAA520"},
    {"text": "好家伙", "effect": "grow_fat", "color": "#FF6347"},
    {"text": "就这?", "effect": "shrink", "color": "#708090"},
    {"text": "人类高质量", "effect": "invincible", "color": "#FFD700"},
    {"text": "华强买瓜", "effect": "grow_fat", "color": "#FFA500"},
    {"text": "保熟吗", "effect": "grow_fat", "color": "#32CD32"},
    {"text": "找茬是吧", "effect": "lose_points", "color": "#DC143C"},
    {"text": "叶问", "effect": "invincible", "color": "#000080"},
    {"text": "十个", "effect": "grow_fat", "color": "#FF0000"},
    {"text": "马冬梅", "effect": "shrink", "color": "#8B4513"},
    {"text": "夏洛特", "effect": "flash_bg", "color": "#87CEEB"},
    {"text": "王多鱼", "effect": "grow_fat", "color": "#FFD700"},
    {"text": "十亿", "effect": "grow_fat", "color": "#FFD700"},
    {"text": "大翔队", "effect": "lose_points", "color": "#D2691E"},
    {"text": "流浪地球", "effect": "flash_bg", "color": "#1E90FF"},
    {"text": "道路千万条", "effect": "slow_down", "color": "#20B2AA"},
    {"text": "战狼", "effect": "invincible", "color": "#DC143C"},
    {"text": "达康书记", "effect": "speed_up", "color": "#4169E1"},
    {"text": "GDP", "effect": "grow_fat", "color": "#00FF00"},
    {"text": "胜天半子", "effect": "invincible", "color": "#8B0000"},
    {"text": "五五开", "effect": "reverse_ctrl", "color": "#FF69B4"},
    {"text": "大司马", "effect": "speed_up", "color": "#2F4F4F"},
    {"text": "正方形打野", "effect": "grow_fat", "color": "#4682B4"},
    {"text": "大马猴", "effect": "fat_snake", "color": "#CD853F"},
    {"text": "增幅", "effect": "grow_fat", "color": "#9370DB"},
    {"text": "宁配吗", "effect": "shrink", "color": "#8B0000"},
    {"text": "giaogiao", "effect": "dance_mode", "color": "#FF6347"},
    {"text": "黑猫警长", "effect": "invincible", "color": "#000000"},
    {"text": "葫芦娃", "effect": "grow_fat", "color": "#FFD700"},
    {"text": "天线宝宝", "effect": "dance_mode", "color": "#FF69B4"},
    {"text": "海绵宝宝", "effect": "dance_mode", "color": "#00CED1"},
    {"text": "派大星", "effect": "fat_snake", "color": "#FF6347"},
    {"text": "光头强", "effect": "speed_up", "color": "#8B4513"},
    {"text": "喜羊羊", "effect": "grow_fat", "color": "#FFFF00"},
    {"text": "灰太狼", "effect": "lose_points", "color": "#808080"},
    {"text": "巴啦啦", "effect": "flash_bg", "color": "#FF1493"},
    {"text": "铠甲勇士", "effect": "invincible", "color": "#FF4500"},
    {"text": "迪迦", "effect": "invincible", "color": "#00BFFF"},
    {"text": "光之巨人", "effect": "flash_bg", "color": "#FFFF00"},
    {"text": "鸣人", "effect": "speed_up", "color": "#FFA500"},
    {"text": "路飞", "effect": "grow_fat", "color": "#FFD700"},
    {"text": "艾伦", "effect": "speed_up", "color": "#F0E68C"},
    {"text": "炭治郎", "effect": "speed_up", "color": "#DC143C"},
    {"text": "五条悟", "effect": "invincible", "color": "#FFFFFF"},
    {"text": "钟离", "effect": "grow_fat", "color": "#DAA520"},
    {"text": "甘雨", "effect": "slow_down", "color": "#87CEEB"},
    {"text": "琪亚娜", "effect": "speed_up", "color": "#FF69B4"},
    {"text": "阿米娅", "effect": "grow_fat", "color": "#FFDAB9"},
    {"text": "李白", "effect": "speed_up", "color": "#87CEEB"},
    {"text": "亚索", "effect": "speed_up", "color": "#4169E1"},
    {"text": "盲僧", "effect": "reverse_ctrl", "color": "#8B4513"},
    {"text": "吃鸡", "effect": "grow_fat", "color": "#228B22"},
    {"text": "落地成盒", "effect": "lose_points", "color": "#000000"},
    {"text": "苦力怕", "effect": "lose_points", "color": "#32CD32"},
    {"text": "史蒂夫", "effect": "grow_fat", "color": "#D2691E"},
    {"text": "豌豆射手", "effect": "speed_up", "color": "#32CD32"},
    {"text": "僵尸", "effect": "lose_points", "color": "#8B4513"},
    {"text": "4399", "effect": "grow_fat", "color": "#FF6347"},
    {"text": "摩尔庄园", "effect": "dance_mode", "color": "#FFB6C1"},
    {"text": "赛尔号", "effect": "speed_up", "color": "#4169E1"},
    {"text": "狼人杀", "effect": "reverse_ctrl", "color": "#4B0082"},
    {"text": "预言家", "effect": "invincible", "color": "#FFD700"},
    {"text": "斗地主", "effect": "grow_fat", "color": "#DC143C"},
    {"text": "麻将", "effect": "grow_fat", "color": "#8B4513"},
    {"text": "胡了", "effect": "grow_fat", "color": "#FFD700"},
]

背景颜色列表 = ['#F5F5F5', '#FFF8DC', '#FFFAF0', '#F0FFF0', '#E6E6FA', 
                 '#FFF0F5', '#F0F8FF', '#FFFFF0', '#FAFAD2', '#FFFACD']

游戏结束台词 = [
    "游戏结束！你这水平还想玩游戏？",
    "就这？就这？太下饭了！",
    "小丑竟是我自己...不对，是你！",
    "蚌埠住了，你这操作太离谱了！",
    "破防了！你怎么又死了！",
    "栓Q！下次别再玩了！",
    "退退退！这游戏不适合你！",
    "我真的会谢，你是来搞笑的吗？",
    "你干嘛~哎哟！又撞墙了！",
    "小黑子露出鸡脚了！游戏玩这么菜！",
    "打工是不可能打工的，游戏也玩不好！",
    "芜湖~起飞失败！",
    "科目三都比你跳得好！",
    "显眼包就是你！",
    "遥遥领先...个屁！",
    "太酷辣！菜得太酷辣！",
    "社会人玩游戏都比你厉害！",
    "精神小伙都比你强！",
    "奥利给！...给你送葬！",
    "巨魔蘸酱都比你有味！",
]

MAX_LENGTH = 30
MIN_SPEED = 80
MAX_SPEED = 300
BASE_SPEED = 150

class 鬼畜贪吃蛇:
    def __init__(self, 根):
        self.根 = 根
        self.根.title("鬼畜贪吃蛇")
        self.根.geometry("800x650")
        
        self.画布 = tk.Canvas(根, width=800, height=600, bg="#F5F5F5")
        self.画布.pack()
        
        self.分数标签 = tk.Label(根, text="分数: 0 | 长度: 1", font=('Arial', 16))
        self.分数标签.pack()
        
        self.状态标签 = tk.Label(根, text="正常模式", font=('Arial', 14), fg='green')
        self.状态标签.pack()
        
        self.重置按钮 = tk.Button(根, text="重新开始", command=self.重置游戏, font=('Arial', 14))
        self.重置按钮.pack()
        
        self.循环ID = None
        self.初始化游戏()
        
        self.根.bind('<Key>', self.键盘控制)
        
    def 初始化游戏(self):
        self.蛇身 = [(400, 300), (380, 300), (360, 300)]
        self.蛇身集合 = set(self.蛇身)
        self.方向 = (20, 0)
        self.食物 = None
        self.分数 = 0
        self.速度 = BASE_SPEED
        self.游戏运行 = True
        self.无敌时间 = 0
        self.反转控制 = False
        self.胖蛇模式 = False
        self.跳舞模式 = False
        self.跳舞帧 = 0
        
        self.生成食物()
        self.绘制游戏()
        
    def 生成食物(self):
        while True:
            梗 = random.choice(梗列表)
            x = random.randint(20, 780)
            y = random.randint(20, 580)
            x = x - x % 20
            y = y - y % 20
            if (x, y) not in self.蛇身集合:
                self.食物 = {"x": x, "y": y, "text": 梗["text"], 
                              "effect": 梗["effect"], "color": 梗["color"]}
                break
        
    def 绘制游戏(self):
        self.画布.delete(tk.ALL)
        
        if self.跳舞模式:
            self.跳舞帧 += 1
            背景色 = 背景颜色列表[self.跳舞帧 % len(背景颜色列表)]
            self.画布.config(bg=背景色)
        
        if self.无敌时间 > 0:
            蛇色 = "#00FF00"
        elif self.胖蛇模式:
            蛇色 = "#FFD700"
        else:
            蛇色 = "#4A90D9"
            
        大小 = 18 if not self.胖蛇模式 else 25
            
        for i, (x, y) in enumerate(self.蛇身):
            self.画布.create_rectangle(x, y, x+大小, y+大小, fill=蛇色, outline="#000")
            
            if i == 0:
                self.画布.create_oval(x+5, y+5, x+10, y+10, fill="#000")
                self.画布.create_oval(x+10, y+5, x+15, y+10, fill="#000")
                self.画布.create_arc(x+5, y+12, x+15, y+18, start=0, extent=180, fill="#FF6B6B")
        
        if self.食物:
            self.画布.create_rectangle(self.食物["x"]-25, self.食物["y"]-15, 
                                       self.食物["x"]+45, self.食物["y"]+15, 
                                       fill=self.食物["color"], outline="#000")
            self.画布.create_text(self.食物["x"]+10, self.食物["y"], 
                                  text=self.食物["text"], font=('Arial', 12), fill="#000")
        
    def 游戏循环(self):
        if not self.游戏运行:
            return
        
        self.移动蛇()
        self.绘制游戏()
        self.更新状态()
        
        self.循环ID = self.根.after(self.速度, self.游戏循环)
        
    def 移动蛇(self):
        头 = self.蛇身[0]
        新头 = (头[0] + self.方向[0], 头[1] + self.方向[1])
        
        if 新头[0] < 0 or 新头[0] >= 800 or 新头[1] < 0 or 新头[1] >= 600:
            if self.无敌时间 > 0:
                新头 = (800 - 新头[0] if 新头[0] < 0 or 新头[0] >= 800 else 新头[0],
                        600 - 新头[1] if 新头[1] < 0 or 新头[1] >= 600 else 新头[1])
            else:
                self.游戏结束()
                return
        
        if 新头 in self.蛇身集合:
            if self.无敌时间 > 0:
                pass
            else:
                self.游戏结束()
                return
        
        self.蛇身.insert(0, 新头)
        self.蛇身集合.add(新头)
        
        if self.食物 and 新头 == (self.食物["x"], self.食物["y"]):
            self.触发效果(self.食物["effect"], self.食物["text"])
            self.生成食物()
            self.分数 += 10
            self.更新分数()
            
            if len(self.蛇身) > MAX_LENGTH:
                尾 = self.蛇身.pop()
                self.蛇身集合.remove(尾)
        else:
            尾 = self.蛇身.pop()
            self.蛇身集合.remove(尾)
            
    def 触发效果(self, 效果, 文字):
        if 效果 == "speed_up":
            self.速度 = max(MIN_SPEED, self.速度 - 10)
            self.状态标签.config(text=f"触发: {文字}！速度变快！", fg='red')
        elif 效果 == "slow_down":
            self.速度 = min(MAX_SPEED, self.速度 + 20)
            self.状态标签.config(text=f"触发: {文字}！速度变慢！", fg='blue')
        elif 效果 == "grow_fat":
            添加长度 = min(3, MAX_LENGTH - len(self.蛇身))
            for _ in range(添加长度):
                尾 = self.蛇身[-1]
                新尾 = (尾[0] - self.方向[0], 尾[1] - self.方向[1])
                self.蛇身.append(新尾)
                self.蛇身集合.add(新尾)
            self.状态标签.config(text=f"触发: {文字}！变长了！", fg='green')
        elif 效果 == "shrink":
            if len(self.蛇身) > 3:
                删除长度 = min(3, len(self.蛇身) - 3)
                for _ in range(删除长度):
                    尾 = self.蛇身.pop()
                    self.蛇身集合.remove(尾)
                self.状态标签.config(text=f"触发: {文字}！变短了！", fg='orange')
        elif 效果 == "flash_bg":
            self.跳舞模式 = True
            self.状态标签.config(text=f"触发: {文字}！背景闪瞎眼！", fg='purple')
            self.根.after(2000, self.关闭跳舞模式)
        elif 效果 == "reverse_ctrl":
            self.反转控制 = True
            self.状态标签.config(text=f"触发: {文字}！控制反转！", fg='red')
            self.根.after(3000, self.关闭反转)
        elif 效果 == "fat_snake":
            self.胖蛇模式 = True
            self.状态标签.config(text=f"触发: {文字}！蛇变胖了！", fg='gold')
            self.根.after(5000, self.关闭胖蛇)
        elif 效果 == "invincible":
            self.无敌时间 = 5
            self.状态标签.config(text=f"触发: {文字}！无敌时间！", fg='green')
            self.根.after(5000, self.关闭无敌)
        elif 效果 == "lose_points":
            self.分数 = max(0, self.分数 - 20)
            self.状态标签.config(text=f"触发: {文字}！扣分了！", fg='darkred')
        elif 效果 == "dance_mode":
            self.跳舞模式 = True
            self.状态标签.config(text=f"触发: {文字}！跳舞模式！", fg='pink')
            self.根.after(3000, self.关闭跳舞模式)
            
    def 更新状态(self):
        if self.无敌时间 > 0:
            self.无敌时间 -= 1
            if self.无敌时间 <= 0:
                self.关闭无敌()
                
    def 关闭跳舞模式(self):
        self.跳舞模式 = False
        self.画布.config(bg="#F5F5F5")
        self.状态标签.config(text="正常模式", fg='green')
        
    def 关闭反转(self):
        self.反转控制 = False
        self.状态标签.config(text="正常模式", fg='green')
        
    def 关闭胖蛇(self):
        self.胖蛇模式 = False
        self.状态标签.config(text="正常模式", fg='green')
        
    def 关闭无敌(self):
        self.无敌时间 = 0
        self.状态标签.config(text="正常模式", fg='green')
        
    def 键盘控制(self, event):
        键 = event.keysym
        if self.反转控制:
            if 键 == 'Up':
                self.方向 = (0, 20)
            elif 键 == 'Down':
                self.方向 = (0, -20)
            elif 键 == 'Left':
                self.方向 = (20, 0)
            elif 键 == 'Right':
                self.方向 = (-20, 0)
        else:
            if 键 == 'Up' and self.方向 != (0, 20):
                self.方向 = (0, -20)
            elif 键 == 'Down' and self.方向 != (0, -20):
                self.方向 = (0, 20)
            elif 键 == 'Left' and self.方向 != (20, 0):
                self.方向 = (-20, 0)
            elif 键 == 'Right' and self.方向 != (-20, 0):
                self.方向 = (20, 0)
                
    def 更新分数(self):
        self.分数标签.config(text=f"分数: {self.分数} | 长度: {len(self.蛇身)}")
        
    def 游戏结束(self):
        self.游戏运行 = False
        if self.循环ID:
            self.根.after_cancel(self.循环ID)
        台词 = random.choice(游戏结束台词)
        self.画布.create_text(400, 300, text=台词, font=('Arial', 30), fill='#FF0000')
        self.画布.create_text(400, 350, text=f"最终分数: {self.分数}", font=('Arial', 24), fill='#000000')
        
    def 重置游戏(self):
        if self.循环ID:
            self.根.after_cancel(self.循环ID)
        self.初始化游戏()
        self.游戏循环()

if __name__ == "__main__":
    根 = tk.Tk()
    app = 鬼畜贪吃蛇(根)
    app.游戏循环()
    根.mainloop()