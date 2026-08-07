"""百科/图鉴系统 - 武将、技能、阵营等词条查询"""

import pygame
import random
import time
from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font
from ASSET import safe_exit

# 颜色定义
COLORS = {
    "bg": (245, 245, 245),
    "text": (30, 30, 30),
    "accent": (70, 130, 180),
    "accent_light": (100, 149, 237),
    "success": (60, 179, 113),
    "warning": (255, 165, 0),
    "error": (255, 99, 71),
    "card_bg": (255, 255, 255),
    "border": (200, 200, 200)
}

# 单词库
WORD_LIST = [
    # 基础词汇
    {"word": "apple", "meaning": "苹果", "example": "I eat an apple every day."},
    {"word": "banana", "meaning": "香蕉", "example": "Bananas are yellow."},
    {"word": "cat", "meaning": "猫", "example": "The cat is sleeping."},
    {"word": "dog", "meaning": "狗", "example": "The dog is barking."},
    {"word": "elephant", "meaning": "大象", "example": "Elephants are big."},
    {"word": "fish", "meaning": "鱼", "example": "Fish live in water."},
    {"word": "grape", "meaning": "葡萄", "example": "Grapes are sweet."},
    {"word": "house", "meaning": "房子", "example": "I live in a house."},
    {"word": "ice cream", "meaning": "冰淇淋", "example": "I like ice cream."},
    {"word": "jacket", "meaning": "夹克", "example": "Wear a jacket in winter."},
    {"word": "king", "meaning": "国王", "example": "The king rules the country."},
    {"word": "lion", "meaning": "狮子", "example": "Lions are strong."},
    {"word": "monkey", "meaning": "猴子", "example": "Monkeys are clever."},
    {"word": "notebook", "meaning": "笔记本", "example": "I write in my notebook."},
    {"word": "orange", "meaning": "橙子", "example": "Oranges are orange."},
    {"word": "pencil", "meaning": "铅笔", "example": "I write with a pencil."},
    {"word": "queen", "meaning": "女王", "example": "The queen is elegant."},
    {"word": "rabbit", "meaning": "兔子", "example": "Rabbits are cute."},
    {"word": "sun", "meaning": "太阳", "example": "The sun is bright."},
    {"word": "tree", "meaning": "树", "example": "Trees are tall."},
    
    # 常用词汇
    {"word": "book", "meaning": "书", "example": "I read a book every night."},
    {"word": "computer", "meaning": "电脑", "example": "I use a computer for work."},
    {"word": "phone", "meaning": "手机", "example": "I call my friend on the phone."},
    {"word": "school", "meaning": "学校", "example": "I go to school every day."},
    {"word": "teacher", "meaning": "老师", "example": "My teacher is very nice."},
    {"word": "student", "meaning": "学生", "example": "I am a student."},
    {"word": "friend", "meaning": "朋友", "example": "I have many friends."},
    {"word": "family", "meaning": "家庭", "example": "I love my family."},
    {"word": "food", "meaning": "食物", "example": "I eat healthy food."},
    {"word": "water", "meaning": "水", "example": "I drink water every day."},
    {"word": "open", "meaning": "打开", "example": "Please open the door."},
    {"word": "close", "meaning": "关闭", "example": "Please close the window."},
    {"word": "start", "meaning": "开始", "example": "Let's start the game."},
    {"word": "end", "meaning": "结束", "example": "The game is over."},
    {"word": "game", "meaning": "游戏", "example": "I like to play games."},
    {"word": "play", "meaning": "玩", "example": "I play football every weekend."},
    {"word": "learn", "meaning": "学习", "example": "I learn English every day."},
    {"word": "study", "meaning": "学习", "example": "I study hard for my exams."},
    {"word": "work", "meaning": "工作", "example": "My father goes to work every day."},
    {"word": "rest", "meaning": "休息", "example": "I need to rest after work."},
    {"word": "home", "meaning": "家", "example": "I go home after school."},
    {"word": "room", "meaning": "房间", "example": "My room is clean."},
    {"word": "bed", "meaning": "床", "example": "I sleep on the bed."},
    {"word": "table", "meaning": "桌子", "example": "I put my books on the table."},
    {"word": "chair", "meaning": "椅子", "example": "I sit on the chair."},
    {"word": "window", "meaning": "窗户", "example": "The window is open."},
    {"word": "door", "meaning": "门", "example": "Please close the door."},
    {"word": "light", "meaning": "灯", "example": "Please turn on the light."},
    {"word": "fan", "meaning": "风扇", "example": "The fan is running."},
    {"word": "air conditioner", "meaning": "空调", "example": "The air conditioner is on."},
    {"word": "television", "meaning": "电视", "example": "I watch television every night."},
    {"word": "radio", "meaning": "收音机", "example": "I listen to the radio."},
    {"word": "music", "meaning": "音乐", "example": "I like to listen to music."},
    {"word": "movie", "meaning": "电影", "example": "I watch a movie every weekend."},
    {"word": "sport", "meaning": "运动", "example": "I like to play sports."},
    {"word": "football", "meaning": "足球", "example": "I play football with my friends."},
    {"word": "basketball", "meaning": "篮球", "example": "I play basketball every day."},
    {"word": "volleyball", "meaning": "排球", "example": "I play volleyball with my classmates."},
    {"word": "tennis", "meaning": "网球", "example": "I play tennis with my father."},
    {"word": "swimming", "meaning": "游泳", "example": "I go swimming every summer."},
    {"word": "hiking", "meaning": "徒步旅行", "example": "I go hiking on weekends."},
    {"word": "camping", "meaning": "露营", "example": "I go camping with my family."},
    {"word": "picnic", "meaning": "野餐", "example": "I go on a picnic with my friends."},
    {"word": "travel", "meaning": "旅行", "example": "I like to travel to different places."},
    {"word": "vacation", "meaning": "假期", "example": "I have a vacation every summer."},
    {"word": "holiday", "meaning": "节日", "example": "Christmas is a holiday."},
    {"word": "birthday", "meaning": "生日", "example": "Today is my birthday."},
    {"word": "party", "meaning": "聚会", "example": "I have a party with my friends."},
    {"word": "gift", "meaning": "礼物", "example": "I give a gift to my friend."},
    {"word": "card", "meaning": "卡片", "example": "I write a card to my mother."},
    {"word": "money", "meaning": "钱", "example": "I need money to buy food."},
    {"word": "job", "meaning": "工作", "example": "I have a job at a restaurant."},
    {"word": "career", "meaning": "职业", "example": "I want to have a good career."},
    {"word": "success", "meaning": "成功", "example": "I want to achieve success."},
    {"word": "failure", "meaning": "失败", "example": "Failure is the mother of success."},
    {"word": "goal", "meaning": "目标", "example": "I have a goal to become a doctor."},
    {"word": "dream", "meaning": "梦想", "example": "I have a dream to travel around the world."},
    {"word": "hope", "meaning": "希望", "example": "I have hope for the future."},
    {"word": "wish", "meaning": "愿望", "example": "I wish you a happy birthday."},
    {"word": "love", "meaning": "爱", "example": "I love my family."},
    {"word": "hate", "meaning": "恨", "example": "I hate to be late."},
    {"word": "like", "meaning": "喜欢", "example": "I like to read books."},
    {"word": "dislike", "meaning": "不喜欢", "example": "I dislike rainy days."},
    {"word": "happy", "meaning": "开心", "example": "I am happy today."},
    {"word": "sad", "meaning": "伤心", "example": "I am sad today."},
    {"word": "angry", "meaning": "生气", "example": "I am angry with him."},
    {"word": "calm", "meaning": "冷静", "example": "I need to stay calm."},
    {"word": "excited", "meaning": "兴奋", "example": "I am excited about the trip."},
    {"word": "nervous", "meaning": "紧张", "example": "I am nervous about the exam."},
    {"word": "bored", "meaning": "无聊", "example": "I am bored at home."},
    {"word": "tired", "meaning": "累", "example": "I am tired after work."},
    {"word": "hungry", "meaning": "饿", "example": "I am hungry now."},
    {"word": "thirsty", "meaning": "渴", "example": "I am thirsty now."},
    {"word": "sleepy", "meaning": "困", "example": "I am sleepy now."},
    {"word": "awake", "meaning": "醒着", "example": "I am awake now."},
    {"word": "healthy", "meaning": "健康", "example": "I am healthy."},
    {"word": "sick", "meaning": "生病", "example": "I am sick today."},
    {"word": "well", "meaning": "好", "example": "I am well today."},
    {"word": "ill", "meaning": "生病", "example": "I am ill today."},
    {"word": "strong", "meaning": "强壮", "example": "I am strong."},
    {"word": "weak", "meaning": "虚弱", "example": "I am weak."},
    {"word": "fast", "meaning": "快", "example": "I run fast."},
    {"word": "slow", "meaning": "慢", "example": "I walk slow."},
    {"word": "high", "meaning": "高", "example": "The building is high."},
    {"word": "low", "meaning": "低", "example": "The chair is low."},
    {"word": "far", "meaning": "远", "example": "The school is far from my home."},
    {"word": "near", "meaning": "近", "example": "The shop is near my home."},
    {"word": "big", "meaning": "大", "example": "The elephant is big."},
    {"word": "small", "meaning": "小", "example": "The mouse is small."},
    {"word": "long", "meaning": "长", "example": "The snake is long."},
    {"word": "short", "meaning": "短", "example": "The pencil is short."},
    {"word": "wide", "meaning": "宽", "example": "The road is wide."},
    {"word": "narrow", "meaning": "窄", "example": "The path is narrow."},
    {"word": "deep", "meaning": "深", "example": "The river is deep."},
    {"word": "shallow", "meaning": "浅", "example": "The pool is shallow."},
    {"word": "heavy", "meaning": "重", "example": "The box is heavy."},
    {"word": "light", "meaning": "轻", "example": "The feather is light."},
    {"word": "hot", "meaning": "热", "example": "The sun is hot."},
    {"word": "cold", "meaning": "冷", "example": "The ice is cold."},
    {"word": "warm", "meaning": "温暖", "example": "The sun is warm."},
    {"word": "cool", "meaning": "凉爽", "example": "The wind is cool."},
    {"word": "bright", "meaning": "明亮", "example": "The sun is bright."},
    {"word": "dark", "meaning": "黑暗", "example": "The room is dark."},
    {"word": "clear", "meaning": "清晰", "example": "The sky is clear."},
    {"word": "cloudy", "meaning": "多云", "example": "The sky is cloudy."},
    {"word": "clean", "meaning": "干净", "example": "The room is clean."},
    {"word": "dirty", "meaning": "脏", "example": "The floor is dirty."},
    {"word": "new", "meaning": "新", "example": "I have a new book."},
    {"word": "old", "meaning": "旧", "example": "The book is old."},
    {"word": "modern", "meaning": "现代", "example": "The building is modern."},
    {"word": "traditional", "meaning": "传统", "example": "The house is traditional."},
    {"word": "simple", "meaning": "简单", "example": "The question is simple."},
    {"word": "complex", "meaning": "复杂", "example": "The problem is complex."},
    {"word": "easy", "meaning": "容易", "example": "The task is easy."},
    {"word": "difficult", "meaning": "困难", "example": "The task is difficult."},
    {"word": "possible", "meaning": "可能", "example": "It is possible to finish the task."},
    {"word": "impossible", "meaning": "不可能", "example": "It is impossible to fly."},
    {"word": "necessary", "meaning": "必要", "example": "It is necessary to study hard."},
    {"word": "unnecessary", "meaning": "不必要", "example": "It is unnecessary to worry."},
    {"word": "important", "meaning": "重要", "example": "It is important to study hard."},
    {"word": "unimportant", "meaning": "不重要", "example": "It is unimportant to worry about small things."},
    {"word": "beautiful", "meaning": "美丽", "example": "The flower is beautiful."},
    {"word": "ugly", "meaning": "丑陋", "example": "The monster is ugly."},
    {"word": "smart", "meaning": "聪明", "example": "The boy is smart."},
    {"word": "stupid", "meaning": "愚蠢", "example": "The idea is stupid."},
    {"word": "kind", "meaning": "善良", "example": "The girl is kind."},
    {"word": "cruel", "meaning": "残忍", "example": "The man is cruel."},
    {"word": "honest", "meaning": "诚实", "example": "The boy is honest."},
    {"word": "dishonest", "meaning": "不诚实", "example": "The man is dishonest."},
    {"word": "brave", "meaning": "勇敢", "example": "The boy is brave."},
    {"word": "cowardly", "meaning": "胆小", "example": "The man is cowardly."},
    {"word": "generous", "meaning": "慷慨", "example": "The man is generous."},
    {"word": "selfish", "meaning": "自私", "example": "The boy is selfish."},
    {"word": "patient", "meaning": "耐心", "example": "The teacher is patient."},
    {"word": "impatient", "meaning": "不耐烦", "example": "The man is impatient."},
    {"word": "polite", "meaning": "礼貌", "example": "The boy is polite."},
    {"word": "rude", "meaning": "粗鲁", "example": "The man is rude."},
    {"word": "friendly", "meaning": "友好", "example": "The girl is friendly."},
    {"word": "unfriendly", "meaning": "不友好", "example": "The man is unfriendly."},
    {"word": "happy", "meaning": "开心", "example": "I am happy today."},
    {"word": "sad", "meaning": "伤心", "example": "I am sad today."},
    {"word": "angry", "meaning": "生气", "example": "I am angry with him."},
    {"word": "calm", "meaning": "冷静", "example": "I need to stay calm."},
    {"word": "excited", "meaning": "兴奋", "example": "I am excited about the trip."},
    {"word": "nervous", "meaning": "紧张", "example": "I am nervous about the exam."},
    {"word": "bored", "meaning": "无聊", "example": "I am bored at home."},
    {"word": "tired", "meaning": "累", "example": "I am tired after work."},
    {"word": "hungry", "meaning": "饿", "example": "I am hungry now."},
    {"word": "thirsty", "meaning": "渴", "example": "I am thirsty now."},
    {"word": "sleepy", "meaning": "困", "example": "I am sleepy now."},
    {"word": "awake", "meaning": "醒着", "example": "I am awake now."},
    {"word": "healthy", "meaning": "健康", "example": "I am healthy."},
    {"word": "sick", "meaning": "生病", "example": "I am sick today."},
    {"word": "well", "meaning": "好", "example": "I am well today."},
    {"word": "ill", "meaning": "生病", "example": "I am ill today."},
    
    # 生僻字和专业词汇
    {"word": "abacus", "meaning": "算盘", "example": "The abacus is an ancient calculating tool."},
    {"word": "acorn", "meaning": "橡子", "example": "The squirrel collected acorns for winter."},
    {"word": "agate", "meaning": "玛瑙", "example": "The agate has beautiful patterns."},
    {"word": "albatross", "meaning": "信天翁", "example": "The albatross can fly long distances."},
    {"word": "amber", "meaning": "琥珀", "example": "The amber contains ancient insects."},
    {"word": "amulet", "meaning": "护身符", "example": "The amulet is believed to bring good luck."},
    {"word": "anemone", "meaning": "海葵", "example": "The anemone lives in the ocean."},
    {"word": "antelope", "meaning": "羚羊", "example": "The antelope runs very fast."},
    {"word": "apocalypse", "meaning": "天启", "example": "The movie depicts the apocalypse."},
    {"word": "arachnid", "meaning": "蛛形纲动物", "example": "Spiders are arachnids."},
    {"word": "arcane", "meaning": "神秘的", "example": "The arcane ritual was performed at midnight."},
    {"word": "arduous", "meaning": "艰巨的", "example": "The journey was arduous."},
    {"word": "asylum", "meaning": "庇护所", "example": "The refugees sought asylum in the neighboring country."},
    {"word": "atrophy", "meaning": "萎缩", "example": "The muscle atrophy due to lack of use."},
    {"word": "aurora", "meaning": "极光", "example": "The aurora borealis is a beautiful natural phenomenon."},
    {"word": "avalanche", "meaning": "雪崩", "example": "The avalanche buried the village."},
    {"word": "azalea", "meaning": "杜鹃花", "example": "The azalea blooms in spring."},
    {"word": "baleful", "meaning": "恶意的", "example": "He gave me a baleful look."},
    {"word": "balm", "meaning": "香脂", "example": "The balm soothed the burn."},
    {"word": "banshee", "meaning": "女妖", "example": "The banshee's wail foretells death."},
    {"word": "barren", "meaning": "贫瘠的", "example": "The desert is barren."},
    {"word": "basilisk", "meaning": "蛇怪", "example": "The basilisk can turn people to stone."},
    {"word": "baton", "meaning": "指挥棒", "example": "The conductor waved the baton."},
    {"word": "beacon", "meaning": "灯塔", "example": "The beacon guided ships to safety."},
    {"word": "beetle", "meaning": "甲虫", "example": "The beetle has a hard shell."},
    {"word": "bellow", "meaning": "吼叫", "example": "The bull bellowed loudly."},
    {"word": "benevolent", "meaning": "仁慈的", "example": "The benevolent king helped his people."},
    {"word": "bequest", "meaning": "遗赠", "example": "She received a bequest from her aunt."},
    {"word": "beseech", "meaning": "恳求", "example": "I beseech you to help me."},
    {"word": "betray", "meaning": "背叛", "example": "He betrayed his friend."},
    {"word": "beverage", "meaning": "饮料", "example": "The beverage was refreshing."},
    {"word": "bifurcate", "meaning": "分叉", "example": "The road bifurcates ahead."},
    {"word": "bison", "meaning": "野牛", "example": "The bison roams the plains."},
    {"word": "blasphemy", "meaning": "亵渎", "example": "His words were considered blasphemy."},
    {"word": "blight", "meaning": "枯萎病", "example": "The blight destroyed the crops."},
    {"word": "blithe", "meaning": "无忧无虑的", "example": "She had a blithe personality."},
    {"word": "bode", "meaning": "预示", "example": "The dark clouds bode rain."},
    {"word": "bog", "meaning": "沼泽", "example": "The bog was difficult to cross."},
    {"word": "boulder", "meaning": "巨石", "example": "The boulder blocked the road."},
    {"word": "brazen", "meaning": "厚颜无耻的", "example": "He made a brazen attempt to cheat."},
    {"word": "breach", "meaning": " breach", "example": "The breach in the wall allowed the enemy to enter."},
    {"word": "brittle", "meaning": "易碎的", "example": "The glass is brittle."},
    {"word": "brood", "meaning": "孵蛋", "example": "The hen brooded over her eggs."},
    {"word": "browbeat", "meaning": "恫吓", "example": "He tried to browbeat me into submission."},
    {"word": "brume", "meaning": "薄雾", "example": "The brume covered the valley."},
    {"word": "buxom", "meaning": "丰满的", "example": "The buxom woman was very attractive."},
    {"word": "cabal", "meaning": "阴谋集团", "example": "The cabal plotted to overthrow the government."},
    {"word": "cacophony", "meaning": "刺耳的声音", "example": "The cacophony of the city was overwhelming."},
    {"word": "cadge", "meaning": "乞讨", "example": "He tried to cadge money from me."},
    {"word": "cajole", "meaning": "哄骗", "example": "She cajoled him into buying her a gift."},
    {"word": "calamity", "meaning": "灾难", "example": "The earthquake was a great calamity."},
    {"word": "callous", "meaning": "无情的", "example": "He was callous to the suffering of others."},
    {"word": "camaraderie", "meaning": "同志情谊", "example": "The soldiers shared a strong camaraderie."},
    {"word": "camouflage", "meaning": "伪装", "example": "The soldiers used camouflage to hide."},
    {"word": "candid", "meaning": "坦率的", "example": "She gave a candid opinion."},
    {"word": "canine", "meaning": "犬科的", "example": "Dogs are canine animals."},
    {"word": "canker", "meaning": "溃疡", "example": "The canker spread through the tree."},
    {"word": "canny", "meaning": "精明的", "example": "He was a canny businessman."},
    {"word": "capricious", "meaning": "反复无常的", "example": "Her moods were capricious."},
    {"word": "carcass", "meaning": "尸体", "example": "The vultures feasted on the carcass."},
    {"word": "carnivorous", "meaning": "食肉的", "example": "Lions are carnivorous animals."},
    {"word": "carte blanche", "meaning": "全权委托", "example": "He was given carte blanche to make decisions."},
    {"word": "cascade", "meaning": "瀑布", "example": "The cascade flowed down the mountain."},
    {"word": "castigate", "meaning": "严惩", "example": "The teacher castigated the student for misbehaving."},
    {"word": "catalyst", "meaning": "催化剂", "example": "The discovery was a catalyst for change."},
    {"word": "catharsis", "meaning": "宣泄", "example": "Writing was a catharsis for her."},
    {"word": "caustic", "meaning": "腐蚀性的", "example": "The caustic solution burned his skin."},
    {"word": "cease", "meaning": "停止", "example": "The fighting ceased."},
    {"word": "celestial", "meaning": "天上的", "example": "The stars are celestial bodies."},
    {"word": "censor", "meaning": "审查", "example": "The government censored the news."},
    {"word": "censure", "meaning": "谴责", "example": "The committee censured his behavior."},
    {"word": "cerulean", "meaning": "天蓝色的", "example": "The sky was a cerulean blue."},
    {"word": "chagrin", "meaning": "懊恼", "example": "He felt chagrin at his mistake."},
    {"word": "chastise", "meaning": "惩罚", "example": "The parent chastised the child."},
    {"word": "chimerical", "meaning": "空想的", "example": "His plans were chimerical."},
    {"word": "choleric", "meaning": "易怒的", "example": "He had a choleric temperament."},
    {"word": "churlish", "meaning": "粗鲁的", "example": "His churlish behavior offended everyone."},
    {"word": "circumlocution", "meaning": "迂回表达", "example": "He used circumlocution to avoid answering the question."},
    {"word": "circumspect", "meaning": "谨慎的", "example": "She was circumspect in her dealings."},
    {"word": "citadel", "meaning": "城堡", "example": "The citadel was impregnable."},
    {"word": "clot", "meaning": "血块", "example": "The clot blocked the artery."},
    {"word": "coagulate", "meaning": "凝结", "example": "The blood began to coagulate."},
    {"word": "coda", "meaning": "尾声", "example": "The song ended with a beautiful coda."},
    {"word": "cognizant", "meaning": "意识到的", "example": "He was cognizant of the risks."},
    {"word": "collaborate", "meaning": "合作", "example": "The two companies collaborated on the project."},
    {"word": "collusion", "meaning": "勾结", "example": "There was collusion between the two parties."},
    {"word": "commodious", "meaning": "宽敞的", "example": "The house was commodious."},
    {"word": "commuter", "meaning": "通勤者", "example": "The commuter train was crowded."},
    {"word": "compunction", "meaning": "内疚", "example": "He felt no compunction about lying."},
    {"word": "conceal", "meaning": "隐藏", "example": "She tried to conceal her emotions."},
    {"word": "conciliatory", "meaning": "和解的", "example": "He made a conciliatory gesture."},
    {"word": "conclave", "meaning": "秘密会议", "example": "The conclave elected a new pope."},
    {"word": "concur", "meaning": "同意", "example": "I concur with your opinion."},
    {"word": "condone", "meaning": "宽恕", "example": "The teacher did not condone cheating."},
    {"word": "conflagration", "meaning": "大火", "example": "The conflagration destroyed the entire town."},
    {"word": "confluence", "meaning": "汇合", "example": "The confluence of the two rivers created a beautiful scene."},
    {"word": "connotation", "meaning": "内涵", "example": "The word has a negative connotation."},
    {"word": "conquest", "meaning": "征服", "example": "The conquest of the land took many years."},
    {"word": "consensus", "meaning": "共识", "example": "There was a consensus among the group."},
    {"word": "conspicuous", "meaning": "明显的", "example": "Her red dress was conspicuous in the crowd."},
    {"word": "consternation", "meaning": "惊愕", "example": "The news caused consternation."},
    {"word": "contemn", "meaning": "蔑视", "example": "He contemned the idea."},
    {"word": "contiguous", "meaning": "相邻的", "example": "The two countries are contiguous."},
    {"word": "contrite", "meaning": "悔罪的", "example": "He was contrite for his mistakes."},
    {"word": "contumacious", "meaning": "反抗的", "example": "The contumacious prisoner refused to obey."},
    {"word": "conundrum", "meaning": "难题", "example": "The problem was a conundrum."},
    {"word": "copious", "meaning": "丰富的", "example": "She took copious notes."},
    {"word": "corroborate", "meaning": "证实", "example": "The evidence corroborated his story."},
    {"word": "cosset", "meaning": "宠爱", "example": "She cosseted her pet."},
    {"word": "cower", "meaning": "畏缩", "example": "The child cowered in fear."},
    {"word": "craven", "meaning": "怯懦的", "example": "He was a craven coward."},
    {"word": "crescendo", "meaning": "渐强", "example": "The music reached a crescendo."},
    {"word": "cringe", "meaning": "畏缩", "example": "I cringed at the sight."},
    {"word": "cryptic", "meaning": "神秘的", "example": "The message was cryptic."},
    {"word": "curtail", "meaning": "缩短", "example": "The meeting was curtailed."},
    {"word": "cynical", "meaning": "愤世嫉俗的", "example": "He had a cynical view of life."},
    {"word": "dearth", "meaning": "缺乏", "example": "There was a dearth of food."},
    {"word": "debacle", "meaning": "崩溃", "example": "The project was a debacle."},
    {"word": "defer", "meaning": "推迟", "example": "We decided to defer the decision."},
    {"word": "deft", "meaning": "灵巧的", "example": "She was deft with her hands."},
    {"word": "demagogue", "meaning": "煽动者", "example": "The demagogue rallied the crowd."},
    {"word": "denigrate", "meaning": "诋毁", "example": "He tried to denigrate his opponent."},
    {"word": "deplete", "meaning": "耗尽", "example": "The resources were depleted."},
    {"word": "desuetude", "meaning": "废弃", "example": "The old law fell into desuetude."},
    {"word": "desultory", "meaning": "散漫的", "example": "His conversation was desultory."},
    {"word": "diaphanous", "meaning": "透明的", "example": "The diaphanous fabric was beautiful."},
    {"word": "diffidence", "meaning": "缺乏自信", "example": "His diffidence made it hard for him to make friends."},
    {"word": "diligent", "meaning": "勤奋的", "example": "She was a diligent student."},
    {"word": "discern", "meaning": "辨别", "example": "I could discern a figure in the distance."},
    {"word": "disconcert", "meaning": "使不安", "example": "The news disconcerted him."},
    {"word": "discredit", "meaning": "使失信", "example": "The scandal discredited the politician."},
    {"word": "discreet", "meaning": "谨慎的", "example": "She was discreet about the matter."},
    {"word": "disdain", "meaning": "蔑视", "example": "He looked at her with disdain."},
    {"word": "disinter", "meaning": "挖掘", "example": "The archaeologists disinterred the ancient artifacts."},
    {"word": "dissonance", "meaning": "不和谐", "example": "The dissonance in the music was jarring."},
    {"word": "distraught", "meaning": "心烦意乱的", "example": "She was distraught over the loss."},
    {"word": "divulge", "meaning": "泄露", "example": "He refused to divulge the secret."},
    {"word": "doddering", "meaning": "蹒跚的", "example": "The doddering old man walked slowly."},
    {"word": "dogmatic", "meaning": "教条的", "example": "He had a dogmatic approach to life."},
    {"word": "dormant", "meaning": "休眠的", "example": "The volcano was dormant."},
    {"word": "dubious", "meaning": "可疑的", "example": "His story was dubious."},
    {"word": "duress", "meaning": "胁迫", "example": "He signed the contract under duress."},
    {"word": "dwarf", "meaning": "矮人", "example": "The dwarf worked in the mine."},
    {"word": "ebullient", "meaning": "热情的", "example": "She was ebullient at the party."},
    {"word": "eccentric", "meaning": "古怪的", "example": "The eccentric old man lived alone."},
    {"word": "eclectic", "meaning": "折衷的", "example": "Her taste in music was eclectic."},
    {"word": "edible", "meaning": "可食用的", "example": "The berries were edible."},
    {"word": "effete", "meaning": "衰弱的", "example": "The effete old贵族 was no longer powerful."},
    {"word": "egress", "meaning": "出口", "example": "The egress was blocked."},
    {"word": "elaborate", "meaning": "详细的", "example": "He gave an elaborate explanation."},
    {"word": "elusive", "meaning": "难以捉摸的", "example": "The answer was elusive."},
    {"word": "emaciated", "meaning": "憔悴的", "example": "The prisoner was emaciated."},
    {"word": "embellish", "meaning": "装饰", "example": "She embellished the story."},
    {"word": "embezzle", "meaning": "盗用", "example": "He embezzled funds from the company."},
    {"word": "embolden", "meaning": "鼓励", "example": "His success emboldened him."},
    {"word": "emote", "meaning": "表达情感", "example": "The actor emoted with passion."},
    {"word": "empathy", "meaning": "同理心", "example": "She had empathy for the suffering."},
    {"word": "endemic", "meaning": "地方性的", "example": "The disease was endemic to the region."},
    {"word": "engrave", "meaning": "雕刻", "example": "The words were engraved on the stone."},
    {"word": "enigma", "meaning": "谜", "example": "He was an enigma to everyone."},
    {"word": "ephemeral", "meaning": "短暂的", "example": "The beauty of the moment was ephemeral."},
    {"word": "epicurean", "meaning": "享乐主义的", "example": "He had an epicurean lifestyle."},
    {"word": "epitome", "meaning": "缩影", "example": "She was the epitome of grace."},
    {"word": "equanimity", "meaning": "平静", "example": "He faced the crisis with equanimity."},
    {"word": "equivocal", "meaning": "模棱两可的", "example": "His answer was equivocal."},
    {"word": "eradicate", "meaning": "根除", "example": "The disease was eradicated."},
    {"word": "erratic", "meaning": "不稳定的", "example": "His behavior was erratic."},
    {"word": "erudite", "meaning": "博学的", "example": "The professor was erudite."},
    {"word": "esoteric", "meaning": "深奥的", "example": "The subject was esoteric."},
    {"word": "euphoria", "meaning": "欣快", "example": "She felt euphoria after the victory."},
    {"word": "evoke", "meaning": "唤起", "example": "The music evoked memories."},
    {"word": "exacerbate", "meaning": "加剧", "example": "The problem was exacerbated by the delay."},
    {"word": "exalt", "meaning": "赞扬", "example": "He was exalted for his bravery."},
    {"word": "exigency", "meaning": "紧急情况", "example": "The exigency required immediate action."},
    {"word": "exile", "meaning": "流放", "example": "He was exiled from his country."},
    {"word": "exonerate", "meaning": "无罪释放", "example": "He was exonerated of all charges."},
    {"word": "expatiate", "meaning": "详述", "example": "He expatiated on the topic."},
    {"word": "explicate", "meaning": "解释", "example": "The professor explicated the theory."},
    {"word": "expurgate", "meaning": "删改", "example": "The book was expurgated for children."},
    {"word": "extant", "meaning": "现存的", "example": "The manuscript is still extant."},
    {"word": "extempore", "meaning": "即兴的", "example": "He gave an extempore speech."},
    {"word": "extol", "meaning": "赞美", "example": "The critics extolled the play."},
    {"word": "extricate", "meaning": "解救", "example": "He extricated himself from the situation."},
    {"word": "exuberant", "meaning": "旺盛的", "example": "The garden was exuberant with flowers."},
    {"word": "exult", "meaning": "狂喜", "example": "They exulted in their victory."},
    {"word": "facetious", "meaning": "诙谐的", "example": "He made a facetious remark."},
    {"word": "fallacious", "meaning": "谬误的", "example": "His argument was fallacious."},
    {"word": "falter", "meaning": "犹豫", "example": "His voice faltered."},
    {"word": "fatuous", "meaning": "愚蠢的", "example": "His fatuous remarks made everyone laugh."},
    {"word": "fawn", "meaning": "奉承", "example": "He fawned over his boss."},
    {"word": "fecund", "meaning": "肥沃的", "example": "The soil was fecund."},
    {"word": "fervor", "meaning": "热情", "example": "He spoke with fervor."},
    {"word": "fetter", "meaning": "束缚", "example": "He felt fettered by his responsibilities."},
    {"word": "fickle", "meaning": " fickle", "example": "She was fickle in her affections."},
    {"word": "figment", "meaning": "虚构的事物", "example": "The monster was a figment of his imagination."},
    {"word": "flagrant", "meaning": "明目张胆的", "example": "The flagrant violation of the law was punished."},
    {"word": "flamboyant", "meaning": "华丽的", "example": "He wore flamboyant clothes."},
    {"word": "flinch", "meaning": "退缩", "example": "He didn't flinch at the pain."},
    {"word": "florid", "meaning": "华丽的", "example": "The prose was florid."},
    {"word": "fluster", "meaning": "使慌乱", "example": "The unexpected news flustered her."},
    {"word": "foil", "meaning": "衬托", "example": "The dark background foiled the bright colors."},
    {"word": "forestall", "meaning": "预先阻止", "example": "They tried to forestall the crisis."},
    {"word": "forlorn", "meaning": "孤独的", "example": "The forlorn child sat alone."},
    {"word": "frenetic", "meaning": "狂热的", "example": "The pace was frenetic."},
    {"word": "froward", "meaning": "倔强的", "example": "The froward child refused to obey."},
    {"word": "frugal", "meaning": "节俭的", "example": "She was frugal with her money."},
    {"word": "fugitive", "meaning": "逃亡者", "example": "The fugitive was caught."},
    {"word": "fulminate", "meaning": "谴责", "example": "He fulminated against the injustice."},
    {"word": "fustian", "meaning": "浮夸的", "example": "His speech was fustian."},
    {"word": "gainsay", "meaning": "否认", "example": "No one could gainsay his argument."},
    {"word": "garrulous", "meaning": "唠叨的", "example": "The garrulous old man talked nonstop."},
    {"word": "gauche", "meaning": "笨拙的", "example": "His gauche behavior embarrassed everyone."},
    {"word": "gloat", "meaning": "幸灾乐祸", "example": "He gloated over his rival's failure."},
    {"word": "gregarious", "meaning": "社交的", "example": "She was gregarious and made friends easily."},
    {"word": "grimace", "meaning": "做鬼脸", "example": "He made a grimace at the taste."},
    {"word": "gullible", "meaning": "易受骗的", "example": "She was gullible and believed everything."},
    {"word": "gyrate", "meaning": "旋转", "example": "The dancer gyrated to the music."},
    {"word": "halcyon", "meaning": "平静的", "example": "They enjoyed halcyon days at the beach."},
    {"word": "harangue", "meaning": "长篇大论", "example": "He delivered a harangue against the government."},
    {"word": "harbinger", "meaning": "预兆", "example": "The first snow was a harbinger of winter."},
    {"word": "haughty", "meaning": "傲慢的", "example": "She had a haughty attitude."},
    {"word": "heinous", "meaning": "可憎的", "example": "The crime was heinous."},
    {"word": "hermetic", "meaning": "密封的", "example": "The container was hermetic."},
    {"word": "heterogeneous", "meaning": "异质的", "example": "The group was heterogeneous."},
    {"word": "hiatus", "meaning": "间歇", "example": "There was a hiatus in the conversation."},
    {"word": "hoi polloi", "meaning": "平民", "example": "The hoi polloi gathered in the square."},
    {"word": "homogeneous", "meaning": "同质的", "example": "The mixture was homogeneous."},
    {"word": "hubris", "meaning": "傲慢", "example": "His hubris led to his downfall."},
    {"word": "hypocrisy", "meaning": "虚伪", "example": "Her hypocrisy was evident."},
    {"word": "iconoclast", "meaning": "打破传统的人", "example": "He was an iconoclast who challenged authority."},
    {"word": "idolatry", "meaning": "偶像崇拜", "example": "The society was guilty of idolatry."},
    {"word": "ignominious", "meaning": "耻辱的", "example": "He suffered an ignominious defeat."},
    {"word": "illicit", "meaning": "非法的", "example": "The trade was illicit."},
    {"word": "imminent", "meaning": "即将来临的", "example": "The storm was imminent."},
    {"word": "immutable", "meaning": "不可变的", "example": "The laws of nature are immutable."},
    {"word": "impassive", "meaning": "无动于衷的", "example": "He remained impassive during the crisis."},
    {"word": "impecunious", "meaning": "贫困的", "example": "The impecunious artist struggled to make ends meet."},
    {"word": "implacable", "meaning": "难和解的", "example": "He was implacable in his anger."},
    {"word": "imprecation", "meaning": "诅咒", "example": "He uttered an imprecation."},
    {"word": "impromptu", "meaning": "即兴的", "example": "She gave an impromptu speech."},
    {"word": "impudent", "meaning": "无礼的", "example": "The impudent child talked back."},
    {"word": "incipient", "meaning": "初始的", "example": "The disease was in its incipient stage."},
    {"word": "incite", "meaning": "煽动", "example": "He incited the crowd to riot."},
    {"word": "inconsequential", "meaning": "无关紧要的", "example": "The details were inconsequential."},
    {"word": "indefatigable", "meaning": "不知疲倦的", "example": "She was indefatigable in her work."},
    {"word": "indelible", "meaning": "不可磨灭的", "example": "The memory was indelible."},
    {"word": "indolent", "meaning": "懒惰的", "example": "He was indolent and refused to work."},
    {"word": "ineffable", "meaning": "难以言表的", "example": "The beauty was ineffable."},
    {"word": "ineluctable", "meaning": "不可避免的", "example": "The ineluctable truth was revealed."},
    {"word": "inept", "meaning": "笨拙的", "example": "He was inept at his job."},
    {"word": "inimical", "meaning": "有害的", "example": "The policy was inimical to progress."},
    {"word": "innocuous", "meaning": "无害的", "example": "The comment was innocuous."},
    {"word": "inscrutable", "meaning": "难以理解的", "example": "His expression was inscrutable."},
    {"word": "insensible", "meaning": "无感觉的", "example": "He was insensible to pain."},
    {"word": "insidious", "meaning": "阴险的", "example": "The disease was insidious."},
    {"word": "insinuate", "meaning": "暗示", "example": "He insinuated that I was lying."},
    {"word": "insipid", "meaning": "无味的", "example": "The food was insipid."},
    {"word": "insolent", "meaning": "傲慢的", "example": "The insolent child talked back."},
    {"word": "intransigent", "meaning": "不妥协的", "example": "He was intransigent in his demands."},
    {"word": "intrepid", "meaning": "勇敢的", "example": "The intrepid explorer ventured into the jungle."},
    {"word": "inveterate", "meaning": "根深蒂固的", "example": "He was an inveterate smoker."},
    {"word": "irascible", "meaning": "易怒的", "example": "He was irascible and easily angered."},
    {"word": "irresolute", "meaning": "犹豫不决的", "example": "She was irresolute about her decision."},
    {"word": "jaundice", "meaning": "黄疸", "example": "The patient had jaundice."},
    {"word": "jocular", "meaning": "诙谐的", "example": "He made a jocular remark."},
    {"word": "jovial", "meaning": "快乐的", "example": "He was jovial and friendly."},
    {"word": "judicious", "meaning": "明智的", "example": "He made a judicious decision."},
    {"word": "juggernaut", "meaning": "巨大的力量", "example": "The company was a juggernaut in the industry."},
    {"word": "jumble", "meaning": "混乱", "example": "The room was a jumble of furniture."},
    {"word": "juncture", "meaning": "关键时刻", "example": "We are at a critical juncture."},
    {"word": "lachrymose", "meaning": "爱哭的", "example": "She was lachrymose and cried easily."},
    {"word": "lackluster", "meaning": "无光泽的", "example": "The performance was lackluster."},
    {"word": "lagniappe", "meaning": "小赠品", "example": "The store gave a lagniappe with the purchase."},
    {"word": "languid", "meaning": "疲倦的", "example": "She felt languid in the heat."},
    {"word": "lascivious", "meaning": "淫荡的", "example": "His lascivious remarks were offensive."},
    {"word": "latent", "meaning": "潜在的", "example": "The latent talent was discovered."},
    {"word": "laudable", "meaning": "值得称赞的", "example": "His efforts were laudable."},
    {"word": "lavish", "meaning": "奢华的", "example": "The party was lavish."},
    {"word": "lethargic", "meaning": "昏睡的", "example": "He felt lethargic after the meal."},
    {"word": "libel", "meaning": "诽谤", "example": "The article was a libel."},
    {"word": "licentious", "meaning": "放荡的", "example": "His licentious behavior was scandalous."},
    {"word": "limpid", "meaning": "清澈的", "example": "The water was limpid."},
    {"word": "lithe", "meaning": "柔软的", "example": "The cat was lithe and graceful."},
    {"word": "loath", "meaning": "不愿意的", "example": "He was loath to leave."},
    {"word": "loquacious", "meaning": "健谈的", "example": "The loquacious man talked for hours."},
    {"word": "luculent", "meaning": "清晰的", "example": "The explanation was luculent."},
    {"word": "luminous", "meaning": "发光的", "example": "The moon was luminous."},
    {"word": "lurk", "meaning": "潜伏", "example": "The danger lurked in the shadows."},
    {"word": "maladroit", "meaning": "笨拙的", "example": "He was maladroit in social situations."},
    {"word": "malevolent", "meaning": "恶意的", "example": "The malevolent villain plotted his revenge."},
    {"word": "malinger", "meaning": "装病", "example": "He malingered to avoid work."},
    {"word": "malleable", "meaning": "可塑的", "example": "The metal was malleable."},
    {"word": "mendacious", "meaning": "说谎的", "example": "His mendacious statements were exposed."},
    {"word": "mercurial", "meaning": "善变的", "example": "Her mercurial moods were unpredictable."},
    {"word": "meticulous", "meaning": "细致的", "example": "She was meticulous in her work."},
    {"word": "misanthrope", "meaning": "厌世者", "example": "He was a misanthrope who hated people."},
    {"word": "miserly", "meaning": "吝啬的", "example": "The miserly old man hoarded his money."},
    {"word": "mischievous", "meaning": "调皮的", "example": "The mischievous child played pranks."},
    {"word": "misogynist", "meaning": "厌恶女性的人", "example": "He was a misogynist who hated women."},
    {"word": "modicum", "meaning": "少量", "example": "He had a modicum of respect."},
    {"word": "mollify", "meaning": "安抚", "example": "She tried to mollify his anger."},
    {"word": "morose", "meaning": "忧郁的", "example": "He was morose and silent."},
    {"word": "mundane", "meaning": "平凡的", "example": "The job was mundane."},
    {"word": "munificent", "meaning": "慷慨的", "example": "The munificent donor gave a large sum."},
    {"word": "myriad", "meaning": "无数的", "example": "There were myriad stars in the sky."},
    {"word": "nadir", "meaning": "最低点", "example": "The company reached its nadir."},
    {"word": "nascent", "meaning": "新生的", "example": "The nascent industry was growing."},
    {"word": "negligent", "meaning": "疏忽的", "example": "The doctor was negligent in his duties."},
    {"word": "neophyte", "meaning": "新手", "example": "The neophyte was learning the ropes."},
    {"word": "nepotism", "meaning": "裙带关系", "example": "The company was accused of nepotism."},
    {"word": "nocturnal", "meaning": "夜间的", "example": "The owl is a nocturnal animal."},
    {"word": "noxious", "meaning": "有毒的", "example": "The fumes were noxious."},
    {"word": "nugatory", "meaning": "无价值的", "example": "The argument was nugatory."},
    {"word": "nuptial", "meaning": "婚姻的", "example": "The nuptial ceremony was beautiful."},
    {"word": "obdurate", "meaning": "顽固的", "example": "He was obdurate in his refusal."},
    {"word": "obsequious", "meaning": "谄媚的", "example": "The obsequious waiter fawned over the customers."},
    {"word": "obstreperous", "meaning": "喧闹的", "example": "The obstreperous crowd cheered loudly."},
    {"word": "obtuse", "meaning": "迟钝的", "example": "He was obtuse and didn't understand."},
    {"word": "obviate", "meaning": "避免", "example": "The new system obviated the need for manual labor."},
    {"word": "occult", "meaning": "神秘的", "example": "He was interested in the occult."},
    {"word": "odious", "meaning": "可憎的", "example": "The crime was odious."},
    {"word": "officious", "meaning": "爱管闲事的", "example": "The officious neighbor meddled in everyone's business."},
    {"word": "ominous", "meaning": "不祥的", "example": "The dark clouds were ominous."},
    {"word": "opprobrious", "meaning": "辱骂的", "example": "He hurled opprobrious insults."},
    {"word": "ostensible", "meaning": "表面的", "example": "His ostensible reason was not the real one."},
    {"word": "ostentatious", "meaning": "炫耀的", "example": "The ostentatious display of wealth was vulgar."},
    {"word": "outré", "meaning": "奇特的", "example": "Her fashion sense was outré."},
    {"word": "palliate", "meaning": "减轻", "example": "The medicine palliated the pain."},
    {"word": "palpable", "meaning": "可感知的", "example": "The tension in the room was palpable."},
    {"word": "pander", "meaning": "迎合", "example": "The politician pandered to the crowd."},
    {"word": "paradigm", "meaning": "范例", "example": "The new model was a paradigm for future designs."},
    {"word": "parsimonious", "meaning": "吝啬的", "example": "The parsimonious man never spent money."},
    {"word": "pedantic", "meaning": "学究式的", "example": "The pedantic teacher corrected every mistake."},
    {"word": "pellucid", "meaning": "清晰的", "example": "The explanation was pellucid."},
    {"word": "penurious", "meaning": "贫困的", "example": "The penurious family struggled to survive."},
    {"word": "perfunctory", "meaning": "敷衍的", "example": "He gave a perfunctory apology."},
    {"word": "peripatetic", "meaning": "漫游的", "example": "The peripatetic philosopher traveled the world."},
    {"word": "pernicious", "meaning": "有害的", "example": "The pernicious influence of drugs was evident."},
    {"word": "perspicacious", "meaning": "敏锐的", "example": "The perspicacious detective solved the case."},
    {"word": "pertinacious", "meaning": "固执的", "example": "He was pertinacious in his pursuit of the truth."},
    {"word": "petulant", "meaning": "脾气坏的", "example": "The petulant child threw a tantrum."},
    {"word": "phlegmatic", "meaning": "冷静的", "example": "He remained phlegmatic in the crisis."},
    {"word": "picaresque", "meaning": "流浪冒险的", "example": "The novel was a picaresque tale."},
    {"word": "pied", "meaning": "杂色的", "example": "The pied bird was beautiful."},
    {"word": "pious", "meaning": "虔诚的", "example": "The pious man attended church every week."},
    {"word": "pitfall", "meaning": "陷阱", "example": "He avoided the pitfall of overconfidence."},
    {"word": "pithy", "meaning": "简洁的", "example": "His pithy remarks were memorable."},
    {"word": "placate", "meaning": "安抚", "example": "He tried to placate her anger."},
    {"word": "plaintive", "meaning": "悲伤的", "example": "The plaintive cry of the child was heard."},
    {"word": "platitude", "meaning": "陈词滥调", "example": "His speech was full of platitudes."},
    {"word": "plausible", "meaning": "合理的", "example": "His explanation was plausible."},
    {"word": "plethora", "meaning": "过多", "example": "There was a plethora of options."},
    {"word": "pliable", "meaning": "柔韧的", "example": "The material was pliable."},
    {"word": "poignant", "meaning": "辛酸的", "example": "The poignant story brought tears to her eyes."},
    {"word": "pompous", "meaning": " pompous", "example": "He had a pompous manner."},
    {"word": "portentous", "meaning": "预兆的", "example": "The portentous clouds indicated a storm."},
    {"word": "precarious", "meaning": "不稳定的", "example": "His financial situation was precarious."},
    {"word": "preclude", "meaning": "排除", "example": "The bad weather precluded our plans."},
    {"word": "predilection", "meaning": "偏好", "example": "He had a predilection for chocolate."},
    {"word": "preeminent", "meaning": "卓越的", "example": "She was preeminent in her field."},
    {"word": "premature", "meaning": "过早的", "example": "The premature baby was in intensive care."},
    {"word": "presumptuous", "meaning": "放肆的", "example": "His presumptuous behavior was offensive."},
    {"word": "prevaricate", "meaning": "搪塞", "example": "He prevaricated when asked about his whereabouts."},
    {"word": "pristine", "meaning": "原始的", "example": "The pristine forest was untouched."},
    {"word": "profligate", "meaning": "挥霍的", "example": "The profligate heir spent all the money."},
    {"word": "profound", "meaning": "深刻的", "example": "The book had a profound impact."},
    {"word": "prolix", "meaning": "冗长的", "example": "The prolix speech bored the audience."},
    {"word": "promulgate", "meaning": "颁布", "example": "The government promulgated a new law."},
    {"word": "propitious", "meaning": "有利的", "example": "The weather was propitious for the picnic."},
    {"word": "prosaic", "meaning": "平凡的", "example": "The prosaic life of a clerk was uneventful."},
    {"word": "prostrate", "meaning": "俯卧的", "example": "He lay prostrate on the ground."},
    {"word": "protracted", "meaning": "延长的", "example": "The protracted negotiations lasted for months."},
    {"word": "pugnacious", "meaning": "好斗的", "example": "The pugnacious boxer was always ready to fight."},
    {"word": "pungent", "meaning": "辛辣的", "example": "The pungent smell of garlic filled the room."},
    {"word": "quaff", "meaning": "痛饮", "example": "They quaffed beer at the pub."},
    {"word": "quail", "meaning": "鹌鹑", "example": "The quail nested in the field."},
    {"word": "quaint", "meaning": "古雅的", "example": "The quaint village was charming."},
    {"word": "querulous", "meaning": "爱抱怨的", "example": "The querulous old man complained about everything."},
    {"word": "quixotic", "meaning": "不切实际的", "example": "His quixotic quest was doomed to fail."},
    {"word": "quizzical", "meaning": "疑惑的", "example": "He gave me a quizzical look."},
    {"word": "rabid", "meaning": "狂暴的", "example": "The rabid dog was dangerous."},
    {"word": "raconteur", "meaning": "讲故事的人", "example": "The raconteur entertained the guests."},
    {"word": "rancorous", "meaning": "怨恨的", "example": "He harbored rancorous feelings."},
    {"word": "rarefied", "meaning": "稀薄的", "example": "The air at high altitudes is rarefied."},
    {"word": "recalcitrant", "meaning": "反抗的", "example": "The recalcitrant child refused to obey."},
    {"word": "recant", "meaning": "撤回", "example": "He was forced to recant his views."},
    {"word": "recluse", "meaning": "隐士", "example": "The recluse lived in a cave."},
    {"word": "recondite", "meaning": "深奥的", "example": "The subject was recondite and difficult to understand."},
    {"word": "redundant", "meaning": "多余的", "example": "The redundant workers were laid off."},
    {"word": "refractory", "meaning": " refractory", "example": "The refractory metal was difficult to melt."},
    {"word": "refulgent", "meaning": "辉煌的", "example": "The sun was refulgent in the sky."},
    {"word": "reiterate", "meaning": "重申", "example": "He reiterated his demand."},
    {"word": "rejuvenate", "meaning": "使年轻", "example": "The spa treatment rejuvenated her."},
    {"word": "relapse", "meaning": "复发", "example": "He suffered a relapse of his illness."},
    {"word": "relegate", "meaning": "降级", "example": "He was relegated to a lower position."},
    {"word": "remonstrate", "meaning": "抗议", "example": "She remonstrated against the decision."},
    {"word": "replete", "meaning": "充满的", "example": "The book was replete with information."},
    {"word": "reprehensible", "meaning": "应受谴责的", "example": "His behavior was reprehensible."},
    {"word": "repudiate", "meaning": "拒绝", "example": "He repudiated the contract."},
    {"word": "resigned", "meaning": "顺从的", "example": "He was resigned to his fate."},
    {"word": "resolute", "meaning": "坚决的", "example": "She was resolute in her decision."},
    {"word": "reticent", "meaning": "沉默的", "example": "He was reticent about his past."},
    {"word": "reverent", "meaning": "恭敬的", "example": "She was reverent in the church."},
    {"word": "ribald", "meaning": "粗俗的", "example": "His ribald jokes offended some people."},
    {"word": "rigorous", "meaning": "严格的", "example": "The training was rigorous."},
    {"word": "robust", "meaning": "健壮的", "example": "He was robust and healthy."},
    {"word": "rococo", "meaning": "洛可可式的", "example": "The rococo furniture was ornate."},
    {"word": "sagacious", "meaning": "明智的", "example": "The sagacious old man gave good advice."},
    {"word": "salubrious", "meaning": "有益健康的", "example": "The salubrious climate was good for his health."},
    {"word": "sanctimonious", "meaning": "伪善的", "example": "The sanctimonious preacher condemned others."},
    {"word": "sardonic", "meaning": "讥讽的", "example": "He made a sardonic comment."},
    {"word": "scintillating", "meaning": "闪烁的", "example": "The scintillating stars lit up the sky."},
    {"word": "scorn", "meaning": "蔑视", "example": "He looked at her with scorn."},
    {"word": "scurrilous", "meaning": "下流的", "example": "The scurrilous rumors were false."},
    {"word": "sedulous", "meaning": "勤奋的", "example": "She was sedulous in her studies."},
    {"word": "soporific", "meaning": "催眠的", "example": "The soporific effect of the medicine made him drowsy."},
    {"word": "specious", "meaning": "似是而非的", "example": "His specious argument was not convincing."},
    {"word": "stentorian", "meaning": "声音洪亮的", "example": "The stentorian voice of the announcer filled the stadium."},
    {"word": "stingy", "meaning": "吝啬的", "example": "The stingy man never gave to charity."},
    {"word": "stipulate", "meaning": "规定", "example": "The contract stipulated the terms."},
    {"word": "stygian", "meaning": "黑暗的", "example": "The stygian depths of the cave were terrifying."},
    {"word": "sublime", "meaning": "崇高的", "example": "The sublime beauty of the mountains took his breath away."},
    {"word": "sundry", "meaning": "各种的", "example": "He bought sundry items at the store."},
    {"word": "superfluous", "meaning": "多余的", "example": "The superfluous details were omitted."},
    {"word": "surfeit", "meaning": "过度", "example": "The surfeit of food made him sick."},
    {"word": "susceptible", "meaning": "易受影响的", "example": "She was susceptible to colds."},
    {"word": "sycophant", "meaning": "谄媚者", "example": "The sycophant flattered the king."},
    {"word": "taciturn", "meaning": "沉默寡言的", "example": "The taciturn man rarely spoke."},
    {"word": "tawdry", "meaning": "俗丽的", "example": "The tawdry decorations were tasteless."},
    {"word": "tenacious", "meaning": "固执的", "example": "He was tenacious in his pursuit of the truth."},
    {"word": "temerity", "meaning": "鲁莽", "example": "He had the temerity to challenge the boss."},
    {"word": "timorous", "meaning": "胆小的", "example": "The timorous child was afraid of the dark."},
    {"word": "torpid", "meaning": "迟钝的", "example": "The torpid lizard lay in the sun."},
    {"word": "tortuous", "meaning": "曲折的", "example": "The tortuous road wound through the mountains."},
    {"word": "truculent", "meaning": "好斗的", "example": "The truculent bully picked fights."},
    {"word": "turbid", "meaning": "浑浊的", "example": "The turbid river was difficult to navigate."},
    {"word": "ubiquitous", "meaning": "无处不在的", "example": "The ubiquitous cell phone was everywhere."},
    {"word": "umbrage", "meaning": "生气", "example": "She took umbrage at his remark."},
    {"word": "unctuous", "meaning": "油滑的", "example": "The unctuous salesman was insincere."},
    {"word": "urbane", "meaning": "文雅的", "example": "The urbane gentleman was well-mannered."},
    {"word": "vacillate", "meaning": "犹豫", "example": "He vacillated between two choices."},
    {"word": "vain", "meaning": "虚荣的", "example": "The vain woman spent hours on her appearance."},
    {"word": "valorous", "meaning": "勇敢的", "example": "The valorous soldier fought bravely."},
    {"word": "vehement", "meaning": "强烈的", "example": "He made a vehement protest."},
    {"word": "venal", "meaning": "贪赃枉法的", "example": "The venal politician accepted bribes."},
    {"word": "veracity", "meaning": "真实性", "example": "The veracity of his statement was questioned."},
    {"word": "veritable", "meaning": "真实的", "example": "The veritable chaos was overwhelming."},
    {"word": "vicarious", "meaning": "间接的", "example": "He lived vicariously through his children."},
    {"word": "vindictive", "meaning": "报复的", "example": "The vindictive ex-wife sought revenge."},
    {"word": "virulent", "meaning": "剧毒的", "example": "The virulent disease spread rapidly."},
    {"word": "viscous", "meaning": "粘性的", "example": "The viscous liquid was difficult to pour."},
    {"word": "vivacious", "meaning": "活泼的", "example": "The vivacious girl was full of energy."},
    {"word": "voracious", "meaning": "贪婪的", "example": "The voracious reader devoured books."},
    {"word": "wanton", "meaning": "放纵的", "example": "The wanton behavior of the youth was unacceptable."},
    {"word": "warrant", "meaning": "授权", "example": "The police had a warrant to search the house."},
    {"word": "wastrel", "meaning": "浪费者", "example": "The wastrel spent all his inheritance."},
    {"word": "wistful", "meaning": "渴望的", "example": "She gave a wistful look at the old photo."},
    {"word": "wizen", "meaning": "枯萎的", "example": "The wizened old man had a wrinkled face."},
    {"word": "xenophobia", "meaning": "仇外", "example": "The country was plagued by xenophobia."},
    {"word": "yarn", "meaning": "纱线", "example": "She knitted with yarn."},
    {"word": "yoke", "meaning": "轭", "example": "The farmer put a yoke on the oxen."},
    {"word": "zeal", "meaning": "热情", "example": "He worked with zeal."},
    {"word": "zenith", "meaning": "顶点", "example": "The company reached its zenith."},
    {"word": "zephyr", "meaning": "微风", "example": "A gentle zephyr blew through the trees."},
    
    # 动词
    {"word": "run", "meaning": "跑", "example": "I run every morning."},
    {"word": "walk", "meaning": "走", "example": "I walk to school."},
    {"word": "jump", "meaning": "跳", "example": "The cat can jump high."},
    {"word": "swim", "meaning": "游泳", "example": "I like to swim in the pool."},
    {"word": "fly", "meaning": "飞", "example": "Birds can fly."},
    {"word": "eat", "meaning": "吃", "example": "I eat breakfast every morning."},
    {"word": "drink", "meaning": "喝", "example": "I drink milk every day."},
    {"word": "sleep", "meaning": "睡觉", "example": "I sleep at night."},
    {"word": "study", "meaning": "学习", "example": "I study English every day."},
    {"word": "work", "meaning": "工作", "example": "My father goes to work every day."},
    
    # 形容词
    {"word": "big", "meaning": "大的", "example": "The elephant is big."},
    {"word": "small", "meaning": "小的", "example": "The mouse is small."},
    {"word": "tall", "meaning": "高的", "example": "The tree is tall."},
    {"word": "short", "meaning": "矮的", "example": "The dog is short."},
    {"word": "long", "meaning": "长的", "example": "The snake is long."},
    {"word": "short", "meaning": "短的", "example": "The pencil is short."},
    {"word": "fat", "meaning": "胖的", "example": "The cat is fat."},
    {"word": "thin", "meaning": "瘦的", "example": "The boy is thin."},
    {"word": "happy", "meaning": "开心的", "example": "I am happy today."},
    {"word": "sad", "meaning": "伤心的", "example": "The girl is sad."},
    
    # 颜色
    {"word": "red", "meaning": "红色", "example": "The apple is red."},
    {"word": "blue", "meaning": "蓝色", "example": "The sky is blue."},
    {"word": "green", "meaning": "绿色", "example": "The grass is green."},
    {"word": "yellow", "meaning": "黄色", "example": "The banana is yellow."},
    {"word": "orange", "meaning": "橙色", "example": "The orange is orange."},
    {"word": "purple", "meaning": "紫色", "example": "The flower is purple."},
    {"word": "black", "meaning": "黑色", "example": "The cat is black."},
    {"word": "white", "meaning": "白色", "example": "The snow is white."},
    {"word": "brown", "meaning": "棕色", "example": "The bear is brown."},
    {"word": "gray", "meaning": "灰色", "example": "The mouse is gray."},
    
    # 数字
    {"word": "one", "meaning": "一", "example": "I have one apple."},
    {"word": "two", "meaning": "二", "example": "I have two cats."},
    {"word": "three", "meaning": "三", "example": "I have three books."},
    {"word": "four", "meaning": "四", "example": "I have four friends."},
    {"word": "five", "meaning": "五", "example": "I have five fingers."},
    {"word": "six", "meaning": "六", "example": "I have six pencils."},
    {"word": "seven", "meaning": "七", "example": "I have seven books."},
    {"word": "eight", "meaning": "八", "example": "I have eight apples."},
    {"word": "nine", "meaning": "九", "example": "I have nine cats."},
    {"word": "ten", "meaning": "十", "example": "I have ten fingers."},
    
    # 时间
    {"word": "time", "meaning": "时间", "example": "What time is it?"},
    {"word": "day", "meaning": "天", "example": "I go to school every day."},
    {"word": "week", "meaning": "周", "example": "There are seven days in a week."},
    {"word": "month", "meaning": "月", "example": "There are twelve months in a year."},
    {"word": "year", "meaning": "年", "example": "I am ten years old."},
    {"word": "hour", "meaning": "小时", "example": "There are twenty-four hours in a day."},
    {"word": "minute", "meaning": "分钟", "example": "There are sixty minutes in an hour."},
    {"word": "second", "meaning": "秒", "example": "There are sixty seconds in a minute."},
    {"word": "morning", "meaning": "早上", "example": "I eat breakfast in the morning."},
    {"word": "afternoon", "meaning": "下午", "example": "I go to school in the afternoon."},
    
    # 季节
    {"word": "spring", "meaning": "春天", "example": "Flowers bloom in spring."},
    {"word": "summer", "meaning": "夏天", "example": "It is hot in summer."},
    {"word": "autumn", "meaning": "秋天", "example": "Leaves fall in autumn."},
    {"word": "winter", "meaning": "冬天", "example": "It is cold in winter."},
    
    # 天气
    {"word": "sunny", "meaning": "晴天", "example": "It is sunny today."},
    {"word": "rainy", "meaning": "雨天", "example": "It is rainy today."},
    {"word": "cloudy", "meaning": "多云", "example": "It is cloudy today."},
    {"word": "windy", "meaning": " windy", "example": "It is windy today."},
    {"word": "snowy", "meaning": "雪天", "example": "It is snowy today."},
    
    # 身体部位
    {"word": "head", "meaning": "头", "example": "I have a head."},
    {"word": "eye", "meaning": "眼睛", "example": "I have two eyes."},
    {"word": "ear", "meaning": "耳朵", "example": "I have two ears."},
    {"word": "nose", "meaning": "鼻子", "example": "I have one nose."},
    {"word": "mouth", "meaning": "嘴", "example": "I have one mouth."},
    {"word": "hand", "meaning": "手", "example": "I have two hands."},
    {"word": "foot", "meaning": "脚", "example": "I have two feet."},
    {"word": "arm", "meaning": "胳膊", "example": "I have two arms."},
    {"word": "leg", "meaning": "腿", "example": "I have two legs."},
    {"word": "body", "meaning": "身体", "example": "I have one body."}
]

def get_safe_resolution(screen_width, screen_height, min_width=800, min_height=600, ratio=0.85):
    """获取安全的窗口尺寸，确保不超出屏幕"""
    safe_width = int(screen_width * ratio)
    safe_height = int(screen_height * ratio)
    safe_width = max(min_width, safe_width)
    safe_height = max(min_height, safe_height)
    safe_width = min(safe_width, screen_width - 50)
    safe_height = min(safe_height, screen_height - 50)
    return safe_width, safe_height

# 触发单词和按钮顺序
# 自定义触发单词：修改下面的TRIGGER_WORD变量即可
# 目前设置为8位单词
TRIGGER_WORD = "openthegame"  # 8位触发单词，可自定义
TRIGGER_WORD_WHITEBOARD = "openthebaiban"  # 白板触发词
TRIGGER_BUTTONS = ["study", "pet", "dictionary", "study"]  # 特定按钮顺序（备用）
current_button_sequence = []
last_activity_time = time.time()
AUTO_RETURN_TIME = 300  # 5分钟无操作自动返回词典

class DictionarySystem:
    def __init__(self):
        self.screen = None
        self.clock = None
        self.font_main = None
        self.font_small = None
        self.font_large = None
        self.current_word_index = 0
        self.show_meaning = False
        self.study_mode = True
        self.current_page = "main"
        self.last_activity_time = time.time()
        self.button_sequence = []
        self.search_text = ""  # 搜索输入文本
        self.is_search_active = False  # 搜索框是否激活
        self.favorite_words = []  # 收藏的单词
        self.test_mode = False  # 测试模式
        self.test_words = []  # 测试用的单词
        self.test_current_index = 0  # 当前测试单词索引
        self.test_score = 0  # 测试得分
        self.test_total = 0  # 测试总题数
    
    def initialize(self, screen):
        """初始化词典系统，自适应窗口大小"""
        self.screen = screen
        self.width, self.height = self.screen.get_size()
        
        # 获取屏幕尺寸，确保窗口不超出
        info = pygame.display.Info()
        screen_w, screen_h = info.current_w, info.current_h
        if self.width > screen_w - 50 or self.height > screen_h - 50:
            self.width, self.height = get_safe_resolution(screen_w, screen_h, 800, 600)
            self.screen = pygame.display.set_mode((self.width, self.height))
        
        self.clock = pygame.time.Clock()
        
        # 根据屏幕宽度调整字体大小
        if self.width < 1024:
            font_size_main = 24
            font_size_small = 16
            font_size_large = 40
        else:
            font_size_main = 30
            font_size_small = 20
            font_size_large = 50
        
        # 加载字体 - 优先使用内置字体
        try:
            from ASSET.font_manager import load_font
            self.font_main = load_font(font_size_main)
            self.font_small = load_font(font_size_small)
            self.font_large = load_font(font_size_large)
        except Exception as _e:
            font_name = get_system_font_name()
            try:
                if font_name:
                    self.font_main = pygame.font.SysFont(font_name, font_size_main)
                    self.font_small = pygame.font.SysFont(font_name, font_size_small)
                    self.font_large = pygame.font.SysFont(font_name, font_size_large)
                else:
                    self.font_main = pygame.font.Font(None, font_size_main)
                    self.font_small = pygame.font.Font(None, font_size_small)
                    self.font_large = pygame.font.Font(None, font_size_large)
            except Exception as _e:
                self.font_main = pygame.font.Font(None, font_size_main)
                self.font_small = pygame.font.Font(None, font_size_small)
                self.font_large = pygame.font.Font(None, font_size_large)
        
        return True
    
    def handle_input(self):
        """处理输入"""
        current_time = time.time()
        
        # 检查无操作时间
        if current_time - self.last_activity_time > AUTO_RETURN_TIME:
            self.current_page = "main"
            self.study_mode = True
            self.show_meaning = False
            self.last_activity_time = current_time
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                safe_exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.current_page == "game":
                        self.current_page = "main"
                    else:
                        return False
                # 应急反应键：M键和L键（只在game界面触发）
                elif event.key in [pygame.K_m, pygame.K_l] and self.current_page == "game":
                    # 显示渲染错误框
                    self.show_error_message("渲染错误")
                    # 退出词典系统，返回主程序
                    return False
                elif self.is_search_active:
                    # 处理搜索框输入
                    if event.key == pygame.K_BACKSPACE:
                        self.search_text = self.search_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        # 检查是否输入了触发单词
                        if self.search_text == TRIGGER_WORD:
                            self.current_page = "game"
                            # 退出词典系统，返回游戏
                            return False
                        self.is_search_active = False
                    else:
                        # 只允许输入英文字母和空格
                        if event.unicode.isalpha() or event.unicode == " ":
                            self.search_text += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.last_activity_time = current_time
                    self.handle_mouse_click(pygame.mouse.get_pos())
        
        return True
    
    def handle_mouse_click(self, pos):
        """处理鼠标点击"""
        x, y = pos
        screen_width, screen_height = self.screen.get_size()
        
        # 主界面按钮
        if self.current_page == "main":
            # 学习按钮
            study_rect = pygame.Rect(screen_width // 2 - 100, 200, 200, 50)
            if study_rect.collidepoint(x, y):
                self.button_sequence.append("study")
                self.check_trigger_sequence()
                self.study_mode = True
                self.current_page = "study"
                self.current_word_index = 0
                self.show_meaning = False
                
            # 宠物按钮
            pet_rect = pygame.Rect(screen_width // 2 - 100, 270, 200, 50)
            if pet_rect.collidepoint(x, y):
                self.button_sequence.append("pet")
                self.check_trigger_sequence()
                self.current_page = "pet"
                
            # 词典按钮
            dict_rect = pygame.Rect(screen_width // 2 - 100, 340, 200, 50)
            if dict_rect.collidepoint(x, y):
                self.button_sequence.append("dictionary")
                self.check_trigger_sequence()
                self.current_page = "dictionary"
                
            # 收藏按钮
            favorite_rect = pygame.Rect(screen_width // 2 - 100, 410, 200, 50)
            if favorite_rect.collidepoint(x, y):
                self.button_sequence.append("favorite")
                self.check_trigger_sequence()
                self.current_page = "favorite"
                
            # 测试按钮
            test_rect = pygame.Rect(screen_width // 2 - 100, 480, 200, 50)
            if test_rect.collidepoint(x, y):
                self.button_sequence.append("test")
                self.check_trigger_sequence()
                self.current_page = "test"
                
        # 学习界面
        elif self.current_page == "study":
            # 显示/隐藏含义
            meaning_rect = pygame.Rect(screen_width // 2 - 150, 350, 300, 50)
            if meaning_rect.collidepoint(x, y):
                self.show_meaning = not self.show_meaning
            
            # 下一个单词
            next_rect = pygame.Rect(screen_width // 2 + 50, 420, 100, 40)
            if next_rect.collidepoint(x, y):
                self.current_word_index = (self.current_word_index + 1) % len(WORD_LIST)
                self.show_meaning = False
            
            # 上一个单词
            prev_rect = pygame.Rect(screen_width // 2 - 150, 420, 100, 40)
            if prev_rect.collidepoint(x, y):
                self.current_word_index = (self.current_word_index - 1) % len(WORD_LIST)
                self.show_meaning = False
            
            # 返回主界面
            back_rect = pygame.Rect(50, 50, 100, 40)
            if back_rect.collidepoint(x, y):
                self.current_page = "main"
        
        # 宠物界面
        elif self.current_page == "pet":
            # 返回主界面
            back_rect = pygame.Rect(50, 50, 100, 40)
            if back_rect.collidepoint(x, y):
                self.current_page = "main"
        
        # 词典界面
        elif self.current_page == "dictionary":
            # 返回主界面
            back_rect = pygame.Rect(50, 50, 100, 40)
            if back_rect.collidepoint(x, y):
                self.current_page = "main"
            
            # 搜索框点击
            search_rect = pygame.Rect(screen_width // 2 - 200, 150, 400, 40)
            if search_rect.collidepoint(x, y):
                self.is_search_active = True
            
            # 搜索按钮点击
            search_button_rect = pygame.Rect(screen_width // 2 + 210, 150, 80, 40)
            if search_button_rect.collidepoint(x, y):
                # 检查是否输入了触发单词
                if self.search_text == TRIGGER_WORD:
                    self.current_page = "game"
                    return False
                # 检查是否输入了白板触发单词
                elif self.search_text == TRIGGER_WORD_WHITEBOARD:
                    self.current_page = "whiteboard"
                    return False
                # 执行搜索
                self.is_search_active = False
        
        # 收藏界面
        elif self.current_page == "favorite":
            # 返回主界面
            back_rect = pygame.Rect(50, 50, 100, 40)
            if back_rect.collidepoint(x, y):
                self.current_page = "main"
            
            # 取消收藏按钮
            if self.favorite_words:
                for i, word_data in enumerate(self.favorite_words):
                    word_y = 170 + i * 30
                    remove_rect = pygame.Rect(screen_width - 150, word_y, 80, 25)
                    if remove_rect.collidepoint(x, y):
                        self.favorite_words.remove(word_data)
        
        # 测试界面
        elif self.current_page == "test":
            # 返回主界面
            back_rect = pygame.Rect(50, 50, 100, 40)
            if back_rect.collidepoint(x, y):
                self.current_page = "main"
                self.test_mode = False
                self.test_words = []
                self.test_current_index = 0
                self.test_score = 0
                self.test_total = 0
            
            if not self.test_mode:
                # 开始测试按钮
                start_rect = pygame.Rect(screen_width // 2 - 100, 200, 200, 50)
                if start_rect.collidepoint(x, y):
                    # 开始测试
                    self.test_mode = True
                    self.test_words = random.sample(WORD_LIST, 10)
                    self.test_current_index = 0
                    self.test_score = 0
                    self.test_total = len(self.test_words)
            else:
                if self.test_current_index < len(self.test_words):
                    # 显示含义按钮
                    meaning_rect = pygame.Rect(screen_width // 2 - 150, 300, 300, 50)
                    if meaning_rect.collidepoint(x, y):
                        # 显示单词含义
                        pass
                    
                    # 下一个按钮
                    next_rect = pygame.Rect(screen_width // 2 - 50, 370, 100, 40)
                    if next_rect.collidepoint(x, y):
                        # 进入下一个单词
                        self.test_current_index += 1
                else:
                    # 重新开始按钮
                    restart_rect = pygame.Rect(screen_width // 2 - 100, 300, 200, 50)
                    if restart_rect.collidepoint(x, y):
                        # 重新开始测试
                        self.test_words = random.sample(WORD_LIST, 10)
                        self.test_current_index = 0
                        self.test_score = 0
                        self.test_total = len(self.test_words)
    
    def check_trigger_sequence(self):
        """检查触发序列"""
        # 检查按钮顺序
        if len(self.button_sequence) >= len(TRIGGER_BUTTONS):
            recent_buttons = self.button_sequence[-len(TRIGGER_BUTTONS):]
            if recent_buttons == TRIGGER_BUTTONS:
                self.current_page = "game"
                return True
        
        # 检查是否输入了触发单词
        # 这里可以在词典搜索中实现
        
        return False
    
    def show_error_message(self, message):
        """显示错误消息框"""
        screen_width, screen_height = self.screen.get_size()
        
        # 绘制背景
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # 错误框
        box_width = 400
        box_height = 200
        box_x = (screen_width - box_width) // 2
        box_y = (screen_height - box_height) // 2
        
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_width, box_height), border_radius=10)
        pygame.draw.rect(self.screen, (255, 99, 71), (box_x, box_y, box_width, box_height), 2, border_radius=10)
        
        # 错误标题
        title_surf = self.font_main.render("错误", True, (255, 99, 71))
        title_rect = title_surf.get_rect(center=(screen_width // 2, box_y + 40))
        self.screen.blit(title_surf, title_rect)
        
        # 错误消息
        message_surf = self.font_main.render(message, True, (30, 30, 30))
        message_rect = message_surf.get_rect(center=(screen_width // 2, box_y + 100))
        self.screen.blit(message_surf, message_rect)
        
        # 确认按钮
        button_width = 120
        button_height = 40
        button_x = (screen_width - button_width) // 2
        button_y = box_y + 140
        
        pygame.draw.rect(self.screen, (255, 99, 71), (button_x, button_y, button_width, button_height), border_radius=5)
        button_surf = self.font_small.render("确定", True, (255, 255, 255))
        button_rect = button_surf.get_rect(center=(screen_width // 2, button_y + 20))
        self.screen.blit(button_surf, button_rect)
        
        # 刷新屏幕
        pygame.display.flip()
        
        # 等待用户点击确定
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    safe_exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mx, my = event.pos
                        if button_x <= mx <= button_x + button_width and button_y <= my <= button_y + button_height:
                            waiting = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        waiting = False
    
    def draw_main_menu(self):
        """绘制主菜单"""
        screen_width, screen_height = self.screen.get_size()
        
        # 背景
        self.screen.fill(COLORS["bg"])
        
        # 标题
        title_surf = self.font_large.render("英语词典", True, COLORS["text"])
        title_rect = title_surf.get_rect(center=(screen_width // 2, 100))
        self.screen.blit(title_surf, title_rect)
        
        # 副标题
        subtitle_surf = self.font_main.render("背单词，学英语", True, COLORS["accent"])
        subtitle_rect = subtitle_surf.get_rect(center=(screen_width // 2, 150))
        self.screen.blit(subtitle_surf, subtitle_rect)
        
        # 学习按钮
        study_rect = pygame.Rect(screen_width // 2 - 100, 200, 200, 50)
        pygame.draw.rect(self.screen, COLORS["accent"], study_rect, border_radius=10)
        study_surf = self.font_main.render("开始学习", True, (255, 255, 255))
        study_text_rect = study_surf.get_rect(center=study_rect.center)
        self.screen.blit(study_surf, study_text_rect)
        
        # 宠物按钮
        pet_rect = pygame.Rect(screen_width // 2 - 100, 270, 200, 50)
        pygame.draw.rect(self.screen, COLORS["accent"], pet_rect, border_radius=10)
        pet_surf = self.font_main.render("我的宠物", True, (255, 255, 255))
        pet_text_rect = pet_surf.get_rect(center=pet_rect.center)
        self.screen.blit(pet_surf, pet_text_rect)
        
        # 词典按钮
        dict_rect = pygame.Rect(screen_width // 2 - 100, 340, 200, 50)
        pygame.draw.rect(self.screen, COLORS["accent"], dict_rect, border_radius=10)
        dict_surf = self.font_main.render("词典查询", True, (255, 255, 255))
        dict_text_rect = dict_surf.get_rect(center=dict_rect.center)
        self.screen.blit(dict_surf, dict_text_rect)
        
        # 收藏按钮
        favorite_rect = pygame.Rect(screen_width // 2 - 100, 410, 200, 50)
        pygame.draw.rect(self.screen, COLORS["accent"], favorite_rect, border_radius=10)
        favorite_surf = self.font_main.render("我的收藏", True, (255, 255, 255))
        favorite_text_rect = favorite_surf.get_rect(center=favorite_rect.center)
        self.screen.blit(favorite_surf, favorite_text_rect)
        
        # 测试按钮
        test_rect = pygame.Rect(screen_width // 2 - 100, 480, 200, 50)
        pygame.draw.rect(self.screen, COLORS["accent"], test_rect, border_radius=10)
        test_surf = self.font_main.render("单词测试", True, (255, 255, 255))
        test_text_rect = test_surf.get_rect(center=test_rect.center)
        self.screen.blit(test_surf, test_text_rect)
        
        # 底部信息
        info_surf = self.font_small.render("© 2024 英语词典 v1.0", True, (100, 100, 100))
        info_rect = info_surf.get_rect(center=(screen_width // 2, screen_height - 50))
        self.screen.blit(info_surf, info_rect)
    
    def draw_study_mode(self):
        """绘制学习模式"""
        screen_width, screen_height = self.screen.get_size()
        
        # 背景
        self.screen.fill(COLORS["bg"])
        
        # 返回按钮
        back_rect = pygame.Rect(50, 50, 100, 40)
        pygame.draw.rect(self.screen, COLORS["border"], back_rect, border_radius=5)
        back_surf = self.font_small.render("返回", True, COLORS["text"])
        back_text_rect = back_surf.get_rect(center=back_rect.center)
        self.screen.blit(back_surf, back_text_rect)
        
        # 当前单词
        current_word = WORD_LIST[self.current_word_index]
        
        # 单词卡片
        card_width = screen_width - 200
        card_height = 300
        card_rect = pygame.Rect(100, 120, card_width, card_height)
        pygame.draw.rect(self.screen, COLORS["card_bg"], card_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["border"], card_rect, 2, border_radius=10)
        
        # 单词
        word_surf = self.font_large.render(current_word["word"], True, COLORS["text"])
        word_rect = word_surf.get_rect(center=(screen_width // 2, 180))
        self.screen.blit(word_surf, word_rect)
        
        # 含义
        if self.show_meaning:
            meaning_surf = self.font_main.render(f"含义: {current_word['meaning']}", True, COLORS["text"])
            meaning_rect = meaning_surf.get_rect(center=(screen_width // 2, 240))
            self.screen.blit(meaning_surf, meaning_rect)
            
            example_surf = self.font_small.render(f"例句: {current_word['example']}", True, (100, 100, 100))
            example_rect = example_surf.get_rect(center=(screen_width // 2, 280))
            self.screen.blit(example_surf, example_rect)
        else:
            hint_surf = self.font_main.render("点击显示含义", True, COLORS["accent"])
            hint_rect = hint_surf.get_rect(center=(screen_width // 2, 260))
            self.screen.blit(hint_surf, hint_rect)
        
        # 显示/隐藏含义按钮
        meaning_rect = pygame.Rect(screen_width // 2 - 150, 350, 300, 50)
        pygame.draw.rect(self.screen, COLORS["accent_light"], meaning_rect, border_radius=10)
        meaning_btn_surf = self.font_main.render("显示/隐藏含义", True, (255, 255, 255))
        meaning_btn_rect = meaning_btn_surf.get_rect(center=meaning_rect.center)
        self.screen.blit(meaning_btn_surf, meaning_btn_rect)
        
        # 导航按钮
        prev_rect = pygame.Rect(screen_width // 2 - 150, 420, 100, 40)
        pygame.draw.rect(self.screen, COLORS["border"], prev_rect, border_radius=5)
        prev_surf = self.font_small.render("上一个", True, COLORS["text"])
        prev_text_rect = prev_surf.get_rect(center=prev_rect.center)
        self.screen.blit(prev_surf, prev_text_rect)
        
        next_rect = pygame.Rect(screen_width // 2 + 50, 420, 100, 40)
        pygame.draw.rect(self.screen, COLORS["border"], next_rect, border_radius=5)
        next_surf = self.font_small.render("下一个", True, COLORS["text"])
        next_text_rect = next_surf.get_rect(center=next_rect.center)
        self.screen.blit(next_surf, next_text_rect)
        
        # 进度
        progress = (self.current_word_index + 1) / len(WORD_LIST)
        progress_width = screen_width - 200
        progress_rect = pygame.Rect(100, 480, progress_width, 10)
        pygame.draw.rect(self.screen, COLORS["border"], progress_rect, border_radius=5)
        pygame.draw.rect(self.screen, COLORS["accent"], (
            100, 480, progress_width * progress, 10
        ), border_radius=5)
        
        progress_text = f"{self.current_word_index + 1}/{len(WORD_LIST)}"
        progress_surf = self.font_small.render(progress_text, True, COLORS["text"])
        progress_text_rect = progress_surf.get_rect(center=(screen_width // 2, 505))
        self.screen.blit(progress_surf, progress_text_rect)
    
    def draw_pet_system(self):
        """绘制宠物系统"""
        screen_width, screen_height = self.screen.get_size()
        
        # 背景
        self.screen.fill(COLORS["bg"])
        
        # 返回按钮
        back_rect = pygame.Rect(50, 50, 100, 40)
        pygame.draw.rect(self.screen, COLORS["border"], back_rect, border_radius=5)
        back_surf = self.font_small.render("返回", True, COLORS["text"])
        back_text_rect = back_surf.get_rect(center=back_rect.center)
        self.screen.blit(back_surf, back_text_rect)
        
        # 标题
        title_surf = self.font_large.render("我的宠物", True, COLORS["text"])
        title_rect = title_surf.get_rect(center=(screen_width // 2, 100))
        self.screen.blit(title_surf, title_rect)
        
        # 宠物区域
        pet_area = pygame.Rect(screen_width // 2 - 150, 150, 300, 300)
        pygame.draw.rect(self.screen, COLORS["card_bg"], pet_area, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["border"], pet_area, 2, border_radius=10)
        
        # 宠物图像（简单绘制）
        pet_x = screen_width // 2
        pet_y = 250
        
        # 绘制一个简单的宠物
        pygame.draw.circle(self.screen, (255, 215, 0), (pet_x, pet_y), 50)
        pygame.draw.circle(self.screen, (0, 0, 0), (pet_x - 20, pet_y - 10), 5)
        pygame.draw.circle(self.screen, (0, 0, 0), (pet_x + 20, pet_y - 10), 5)
        pygame.draw.arc(self.screen, (0, 0, 0), (pet_x - 20, pet_y, 40, 20), 0, 3.14, 2)
        
        # 宠物信息
        pet_name = "学习小助手"
        pet_level = 1
        pet_exp = 0
        
        name_surf = self.font_main.render(f"名字: {pet_name}", True, COLORS["text"])
        name_rect = name_surf.get_rect(center=(screen_width // 2, 350))
        self.screen.blit(name_surf, name_rect)
        
        level_surf = self.font_main.render(f"等级: {pet_level}", True, COLORS["text"])
        level_rect = level_surf.get_rect(center=(screen_width // 2, 380))
        self.screen.blit(level_surf, level_rect)
        
        exp_surf = self.font_main.render(f"经验: {pet_exp}/100", True, COLORS["text"])
        exp_rect = exp_surf.get_rect(center=(screen_width // 2, 410))
        self.screen.blit(exp_surf, exp_rect)
        
        # 经验条
        exp_width = 200
        exp_rect = pygame.Rect(screen_width // 2 - 100, 440, exp_width, 10)
        pygame.draw.rect(self.screen, COLORS["border"], exp_rect, border_radius=5)
        pygame.draw.rect(self.screen, COLORS["success"], (
            screen_width // 2 - 100, 440, exp_width * (pet_exp / 100), 10
        ), border_radius=5)
    
    def draw_dictionary_mode(self):
        """绘制词典模式"""
        screen_width, screen_height = self.screen.get_size()
        
        # 背景
        self.screen.fill(COLORS["bg"])
        
        # 返回按钮
        back_rect = pygame.Rect(50, 50, 100, 40)
        pygame.draw.rect(self.screen, COLORS["border"], back_rect, border_radius=5)
        back_surf = self.font_small.render("返回", True, COLORS["text"])
        back_text_rect = back_surf.get_rect(center=back_rect.center)
        self.screen.blit(back_surf, back_text_rect)
        
        # 标题
        title_surf = self.font_large.render("词典查询", True, COLORS["text"])
        title_rect = title_surf.get_rect(center=(screen_width // 2, 100))
        self.screen.blit(title_surf, title_rect)
        
        # 搜索框
        search_rect = pygame.Rect(screen_width // 2 - 200, 150, 400, 40)
        pygame.draw.rect(self.screen, COLORS["card_bg"], search_rect, border_radius=5)
        pygame.draw.rect(self.screen, COLORS["border"], search_rect, 2, border_radius=5)
        
        # 显示搜索文本
        if self.search_text:
            search_surf = self.font_main.render(self.search_text, True, COLORS["text"])
            search_rect = search_surf.get_rect(left=screen_width // 2 - 190, top=155)
            self.screen.blit(search_surf, search_rect)
        else:
            # 搜索提示
            search_hint = self.font_main.render("输入单词...", True, (150, 150, 150))
            search_hint_rect = search_hint.get_rect(center=(screen_width // 2, 170))
            self.screen.blit(search_hint, search_hint_rect)
        
        # 搜索框激活状态
        if self.is_search_active:
            pygame.draw.rect(self.screen, COLORS["accent"], (screen_width // 2 - 200, 150, 400, 40), 2, border_radius=5)
        
        # 搜索按钮
        search_button_rect = pygame.Rect(screen_width // 2 + 210, 150, 80, 40)
        pygame.draw.rect(self.screen, COLORS["accent"], search_button_rect, border_radius=5)
        search_button_surf = self.font_main.render("搜索", True, (255, 255, 255))
        search_button_rect = search_button_surf.get_rect(center=(screen_width // 2 + 250, 170))
        self.screen.blit(search_button_surf, search_button_rect)
        
        # 单词列表
        list_rect = pygame.Rect(100, 220, screen_width - 200, 300)
        pygame.draw.rect(self.screen, COLORS["card_bg"], list_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["border"], list_rect, 2, border_radius=10)
        
        # 显示搜索结果或单词列表
        if self.search_text:
            # 过滤搜索结果 - 不区分大小写
            search_term = self.search_text.lower()
            filtered_words = [word for word in WORD_LIST if search_term in word["word"].lower()]
            display_words = filtered_words[:10]
        else:
            # 显示所有单词
            display_words = WORD_LIST[:10]
        
        # 显示单词列表
        for i, word_data in enumerate(display_words):
            word_y = 240 + i * 30
            word_surf = self.font_main.render(word_data["word"], True, COLORS["text"])
            word_rect = word_surf.get_rect(left=120, top=word_y)
            self.screen.blit(word_surf, word_rect)
            
            meaning_surf = self.font_small.render(word_data["meaning"], True, (100, 100, 100))
            meaning_rect = meaning_surf.get_rect(left=300, top=word_y + 5)
            self.screen.blit(meaning_surf, meaning_rect)
    
    def draw_game_transition(self):
        """绘制游戏过渡界面"""
        screen_width, screen_height = self.screen.get_size()
        
        # 背景
        self.screen.fill(COLORS["bg"])
        
        # 过渡动画
        transition_surf = self.font_large.render("正在进入游戏...", True, COLORS["accent"])
        transition_rect = transition_surf.get_rect(center=(screen_width // 2, screen_height // 2))
        self.screen.blit(transition_surf, transition_rect)
    
    def draw_favorite_mode(self):
        """绘制收藏模式"""
        screen_width, screen_height = self.screen.get_size()
        
        # 背景
        self.screen.fill(COLORS["bg"])
        
        # 返回按钮
        back_rect = pygame.Rect(50, 50, 100, 40)
        pygame.draw.rect(self.screen, COLORS["border"], back_rect, border_radius=5)
        back_surf = self.font_small.render("返回", True, COLORS["text"])
        back_text_rect = back_surf.get_rect(center=back_rect.center)
        self.screen.blit(back_surf, back_text_rect)
        
        # 标题
        title_surf = self.font_large.render("我的收藏", True, COLORS["text"])
        title_rect = title_surf.get_rect(center=(screen_width // 2, 100))
        self.screen.blit(title_surf, title_rect)
        
        # 收藏单词列表
        list_rect = pygame.Rect(100, 150, screen_width - 200, 350)
        pygame.draw.rect(self.screen, COLORS["card_bg"], list_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["border"], list_rect, 2, border_radius=10)
        
        if self.favorite_words:
            # 显示收藏的单词
            for i, word_data in enumerate(self.favorite_words):
                word_y = 170 + i * 30
                word_surf = self.font_main.render(word_data["word"], True, COLORS["text"])
                word_rect = word_surf.get_rect(left=120, top=word_y)
                self.screen.blit(word_surf, word_rect)
                
                meaning_surf = self.font_small.render(word_data["meaning"], True, (100, 100, 100))
                meaning_rect = meaning_surf.get_rect(left=300, top=word_y + 5)
                self.screen.blit(meaning_surf, meaning_rect)
                
                # 取消收藏按钮
                remove_rect = pygame.Rect(screen_width - 150, word_y, 80, 25)
                pygame.draw.rect(self.screen, COLORS["error"], remove_rect, border_radius=5)
                remove_surf = self.font_small.render("取消", True, (255, 255, 255))
                remove_rect = remove_surf.get_rect(center=(screen_width - 110, word_y + 12))
                self.screen.blit(remove_surf, remove_rect)
        else:
            # 空收藏提示
            empty_surf = self.font_main.render("还没有收藏任何单词", True, (150, 150, 150))
            empty_rect = empty_surf.get_rect(center=(screen_width // 2, 250))
            self.screen.blit(empty_surf, empty_rect)
    
    def draw_test_mode(self):
        """绘制测试模式"""
        screen_width, screen_height = self.screen.get_size()
        
        # 背景
        self.screen.fill(COLORS["bg"])
        
        # 返回按钮
        back_rect = pygame.Rect(50, 50, 100, 40)
        pygame.draw.rect(self.screen, COLORS["border"], back_rect, border_radius=5)
        back_surf = self.font_small.render("返回", True, COLORS["text"])
        back_text_rect = back_surf.get_rect(center=back_rect.center)
        self.screen.blit(back_surf, back_text_rect)
        
        # 标题
        title_surf = self.font_large.render("单词测试", True, COLORS["text"])
        title_rect = title_surf.get_rect(center=(screen_width // 2, 100))
        self.screen.blit(title_surf, title_rect)
        
        if not self.test_mode:
            # 测试开始界面
            start_rect = pygame.Rect(screen_width // 2 - 100, 200, 200, 50)
            pygame.draw.rect(self.screen, COLORS["accent"], start_rect, border_radius=10)
            start_surf = self.font_main.render("开始测试", True, (255, 255, 255))
            start_text_rect = start_surf.get_rect(center=start_rect.center)
            self.screen.blit(start_surf, start_text_rect)
            
            # 测试说明
            desc_surf = self.font_small.render("测试将随机选择10个单词，测试你的记忆力", True, COLORS["text"])
            desc_rect = desc_surf.get_rect(center=(screen_width // 2, 280))
            self.screen.blit(desc_surf, desc_rect)
        else:
            # 测试进行中
            if self.test_current_index < len(self.test_words):
                current_word = self.test_words[self.test_current_index]
                
                # 单词卡片
                card_width = screen_width - 200
                card_height = 200
                card_rect = pygame.Rect(100, 150, card_width, card_height)
                pygame.draw.rect(self.screen, COLORS["card_bg"], card_rect, border_radius=10)
                pygame.draw.rect(self.screen, COLORS["border"], card_rect, 2, border_radius=10)
                
                # 单词
                word_surf = self.font_large.render(current_word["word"], True, COLORS["text"])
                word_rect = word_surf.get_rect(center=(screen_width // 2, 220))
                self.screen.blit(word_surf, word_rect)
                
                # 得分显示
                score_surf = self.font_main.render(f"得分: {self.test_score}/{self.test_total}", True, COLORS["text"])
                score_rect = score_surf.get_rect(topright=(screen_width - 50, 100))
                self.screen.blit(score_surf, score_rect)
                
                # 显示/隐藏含义按钮
                meaning_rect = pygame.Rect(screen_width // 2 - 150, 300, 300, 50)
                pygame.draw.rect(self.screen, COLORS["accent_light"], meaning_rect, border_radius=10)
                meaning_btn_surf = self.font_main.render("显示含义", True, (255, 255, 255))
                meaning_btn_rect = meaning_btn_surf.get_rect(center=meaning_rect.center)
                self.screen.blit(meaning_btn_surf, meaning_btn_rect)
                
                # 下一个按钮
                next_rect = pygame.Rect(screen_width // 2 - 50, 370, 100, 40)
                pygame.draw.rect(self.screen, COLORS["accent"], next_rect, border_radius=5)
                next_surf = self.font_main.render("下一个", True, (255, 255, 255))
                next_text_rect = next_surf.get_rect(center=next_rect.center)
                self.screen.blit(next_surf, next_text_rect)
            else:
                # 测试结束
                result_surf = self.font_large.render(f"测试结束！", True, COLORS["text"])
                result_rect = result_surf.get_rect(center=(screen_width // 2, 200))
                self.screen.blit(result_surf, result_rect)
                
                score_surf = self.font_large.render(f"得分: {self.test_score}/{self.test_total}", True, COLORS["accent"])
                score_rect = score_surf.get_rect(center=(screen_width // 2, 250))
                self.screen.blit(score_surf, score_rect)
                
                # 重新开始按钮
                restart_rect = pygame.Rect(screen_width // 2 - 100, 300, 200, 50)
                pygame.draw.rect(self.screen, COLORS["accent"], restart_rect, border_radius=10)
                restart_surf = self.font_main.render("重新开始", True, (255, 255, 255))
                restart_text_rect = restart_surf.get_rect(center=restart_rect.center)
                self.screen.blit(restart_surf, restart_text_rect)
    
    def draw(self):
        """绘制界面"""
        if self.current_page == "main":
            self.draw_main_menu()
        elif self.current_page == "study":
            self.draw_study_mode()
        elif self.current_page == "pet":
            self.draw_pet_system()
        elif self.current_page == "dictionary":
            self.draw_dictionary_mode()
        elif self.current_page == "favorite":
            self.draw_favorite_mode()
        elif self.current_page == "test":
            self.draw_test_mode()
        elif self.current_page == "game":
            self.draw_game_transition()
        
        # 无操作提示
        current_time = time.time()
        idle_time = current_time - self.last_activity_time
        if idle_time > 240:  # 4分钟后显示提示
            minutes = int((AUTO_RETURN_TIME - idle_time) / 60)
            seconds = int((AUTO_RETURN_TIME - idle_time) % 60)
            idle_text = f"无操作，{minutes}:{seconds:02d}后自动返回词典"
            idle_surf = self.font_small.render(idle_text, True, COLORS["warning"])
            idle_rect = idle_surf.get_rect(topright=(self.screen.get_width() - 20, 20))
            self.screen.blit(idle_surf, idle_rect)
        
        # 刷新屏幕
        pygame.display.flip()
    
    def main(self):
        """主循环"""
        running = True
        while running:
            running = self.handle_input()
            self.draw()
            self.clock.tick(60)
        
        return self.current_page == "game" or self.current_page == "whiteboard"

def main(screen):
    """词典系统主函数"""
    dict_system = DictionarySystem()
    if dict_system.initialize(screen):
        result = dict_system.main()
        if result:
            return dict_system.current_page  # 返回页面类型（"game" 或 "whiteboard"）
    return False