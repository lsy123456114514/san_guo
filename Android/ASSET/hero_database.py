# -*- coding: utf-8 -*-
"""
三国武将数据库 - 100+武将详细数据
每个武将包含：基础属性、成长属性、技能、背景故事、阵营、品质、专属装备
"""
import random

# 武将品质定义
HERO_QUALITY = {
    "common":    {"name": "普通", "color": (150, 150, 150), "stars": 1, "base_attr": 1.0,  "prob": 40},
    "rare":      {"name": "稀有", "color": (70, 130, 220),  "stars": 2, "base_attr": 1.3,  "prob": 30},
    "epic":      {"name": "史诗", "color": (128, 0, 128),   "stars": 3, "base_attr": 1.7,  "prob": 18},
    "legendary": {"name": "传说", "color": (255, 165, 0),   "stars": 4, "base_attr": 2.2,  "prob": 9},
    "mythic":    {"name": "神话", "color": (255, 50, 50),   "stars": 5, "base_attr": 3.0,  "prob": 3}
}

# 阵营定义
FACTIONS = {
    "shu":  {"name": "蜀", "color": (220, 80, 80)},
    "wei":  {"name": "魏", "color": (80, 80, 200)},
    "wu":   {"name": "吴", "color": (80, 180, 80)},
    "qun":  {"name": "群", "color": (200, 180, 50)},
    "jin":  {"name": "晋", "color": (150, 100, 200)}
}

# ============================================================
# 武将完整数据库
# ============================================================
HERO_DATABASE = {
    # ==================== 蜀国武将 ====================
    "刘备": {
        "faction": "shu", "quality": "legendary", "element": "风",
        "title": "昭烈帝", "weapon_type": "剑",
        "base": {"attack": 320, "defense": 280, "health": 1200, "speed": 85, "critical": 0.08},
        "growth": {"attack": 28, "defense": 24, "health": 120, "speed": 6, "critical": 0.003},
        "skill": {"name": "仁义之剑", "damage": 45, "element": "风", "type": "heal_attack",
                  "description": "对敌方造成45%攻击力的风属性伤害，并恢复己方全体15%生命"},
        "ultimate": {"name": "蜀汉复兴", "damage": 120, "element": "风", "type": "buff_all",
                     "description": "对敌方全体造成120%伤害，提升己方全体攻击力30%，持续3回合"},
        "passive": {"name": "仁德之心", "description": "每回合恢复己方全体5%生命值"},
        "story": "字玄德，汉景帝阁下玄孙，中山靖王之后。蜀汉开国皇帝，以仁德闻名天下。桃园三结义与关羽、张飞义结金兰，三顾茅庐请诸葛亮出山。",
        "exclusive_equipment": "双股剑"
    },
    "关羽": {
        "faction": "shu", "quality": "mythic", "element": "火",
        "title": "武圣", "weapon_type": "刀",
        "base": {"attack": 450, "defense": 300, "health": 1400, "speed": 90, "critical": 0.15},
        "growth": {"attack": 38, "defense": 26, "health": 140, "speed": 7, "critical": 0.005},
        "skill": {"name": "青龙偃月", "damage": 55, "element": "火", "type": "aoe",
                  "description": "挥舞青龙偃月刀，对敌方前排造成55%攻击力的火属性伤害，附加灼烧"},
        "ultimate": {"name": "武圣降临", "damage": 180, "element": "火", "type": "execute",
                     "description": "对单体造成180%伤害，目标生命低于30%直接斩杀"},
        "passive": {"name": "武圣之威", "description": "攻击时有20%概率造成2倍暴击，击杀目标恢复自身20%生命"},
        "story": "字云长，汉末三国时期蜀汉名将，五虎上将之首。温酒斩华雄，斩颜良诛文丑，过五关斩六将，单刀赴会，水淹七军，威震华夏。",
        "exclusive_equipment": "青龙偃月刀"
    },
    "张飞": {
        "faction": "shu", "quality": "mythic", "element": "土",
        "title": "万人敌", "weapon_type": "矛",
        "base": {"attack": 420, "defense": 350, "health": 1600, "speed": 75, "critical": 0.10},
        "growth": {"attack": 36, "defense": 30, "health": 160, "speed": 5, "critical": 0.003},
        "skill": {"name": "丈八蛇矛", "damage": 50, "element": "土", "type": "stun_attack",
                  "description": "蛇矛横扫，对敌方前排造成50%伤害，15%概率眩晕1回合"},
        "ultimate": {"name": "咆哮如雷", "damage": 150, "element": "土", "type": "fear",
                     "description": "对全体造成150%伤害，50%概率使敌人恐惧2回合（无法行动）"},
        "passive": {"name": "万人之敌", "description": "生命值越低攻击力越高，生命低于50%时攻击力提升40%"},
        "story": "字翼德，蜀汉名将，五虎上将之一。当阳桥前一声怒吼，吓退曹操百万雄兵。义释严颜，大破张郃，勇猛无双。",
        "exclusive_equipment": "丈八蛇矛"
    },
    "赵云": {
        "faction": "shu", "quality": "mythic", "element": "风",
        "title": "常胜将军", "weapon_type": "枪",
        "base": {"attack": 380, "defense": 320, "health": 1300, "speed": 110, "critical": 0.18},
        "growth": {"attack": 34, "defense": 28, "health": 130, "speed": 9, "critical": 0.006},
        "skill": {"name": "龙胆亮枪", "damage": 48, "element": "风", "type": "pierce",
                  "description": "快速刺击，对单体造成48%伤害，无视30%防御"},
        "ultimate": {"name": "七进七出", "damage": 200, "element": "风", "type": "multi_hit",
                     "description": "对随机敌人发动7次攻击，每次造成30%伤害，每次附带10%吸血"},
        "passive": {"name": "一身是胆", "description": "闪避率提升15%，每回合有20%概率获得护盾"},
        "story": "字子龙，蜀汉名将，五虎上将之一。长坂坡七进七出曹营，单骑救主。截江夺阿斗，汉水破曹军，一身是胆。",
        "exclusive_equipment": "龙胆亮银枪"
    },
    "马超": {
        "faction": "shu", "quality": "legendary", "element": "土",
        "title": "锦马超", "weapon_type": "枪",
        "base": {"attack": 400, "defense": 260, "health": 1200, "speed": 105, "critical": 0.12},
        "growth": {"attack": 35, "defense": 22, "health": 120, "speed": 8, "critical": 0.004},
        "skill": {"name": "西凉铁骑", "damage": 50, "element": "土", "type": "charge",
                  "description": "率领铁骑冲锋，对敌方造成50%伤害，降低目标速度20%"},
        "ultimate": {"name": "铁骑踏营", "damage": 160, "element": "土", "type": "charge_all",
                     "description": "对敌方全体造成160%伤害，击退目标行动条30%"},
        "passive": {"name": "西凉之魂", "description": "速度高于目标时，额外造成20%伤害"},
        "story": "字孟起，蜀汉名将，五虎上将之一。西凉军阀马腾之子，杀得曹操割须弃袍。后归刘备，助力平定西川。",
        "exclusive_equipment": "虎头湛金枪"
    },
    "黄忠": {
        "faction": "shu", "quality": "legendary", "element": "风",
        "title": "老将", "weapon_type": "弓",
        "base": {"attack": 380, "defense": 220, "health": 1100, "speed": 80, "critical": 0.25},
        "growth": {"attack": 34, "defense": 20, "health": 110, "speed": 6, "critical": 0.008},
        "skill": {"name": "百步穿杨", "damage": 52, "element": "风", "type": "snipe",
                  "description": "精准射击，对单体造成52%伤害，暴击率额外提升20%"},
        "ultimate": {"name": "烈弓穿心", "damage": 220, "element": "风", "type": "true_damage",
                     "description": "对单体造成220%伤害，无视所有防御和护盾"},
        "passive": {"name": "老当益壮", "description": "年龄越大伤害越高，暴击伤害提升50%"},
        "story": "字汉升，蜀汉名将，五虎上将之一。长沙之战与关羽大战百余回合不分胜负。定军山一战斩杀夏侯渊，威名远扬。",
        "exclusive_equipment": "宝雕弓"
    },
    "诸葛亮": {
        "faction": "shu", "quality": "mythic", "element": "雷",
        "title": "卧龙", "weapon_type": "扇",
        "base": {"attack": 280, "defense": 200, "health": 1000, "speed": 95, "critical": 0.10},
        "growth": {"attack": 26, "defense": 18, "health": 100, "speed": 7, "critical": 0.004},
        "skill": {"name": "八阵图", "damage": 40, "element": "雷", "type": "debuff",
                  "description": "布下八阵图，对敌方造成40%伤害，降低20%攻击力2回合"},
        "ultimate": {"name": "呼风唤雨", "damage": 130, "element": "雷", "type": "aoe_storm",
                     "description": "召唤暴风雨，对全体造成130%伤害，附加麻痹2回合"},
        "passive": {"name": "神机妙算", "description": "每回合有30%概率使敌方技能冷却增加1回合"},
        "story": "字孔明，号卧龙，蜀汉丞相。三顾茅庐出山，草船借箭，借东风，空城计退敌。六出祁山，鞠躬尽瘁，死而后已。",
        "exclusive_equipment": "白羽扇"
    },
    "庞统": {
        "faction": "shu", "quality": "legendary", "element": "土",
        "title": "凤雏", "weapon_type": "扇",
        "base": {"attack": 260, "defense": 190, "health": 950, "speed": 90, "critical": 0.08},
        "growth": {"attack": 24, "defense": 17, "health": 95, "speed": 7, "critical": 0.003},
        "skill": {"name": "连环计", "damage": 38, "element": "土", "type": "chain",
                  "description": "计谋连环，对敌方造成38%伤害，使目标受到的伤害提升15%"},
        "ultimate": {"name": "凤雏涅槃", "damage": 140, "element": "土", "type": "sacrifice",
                     "description": "对全体造成140%伤害，自身损失20%生命，但己方全体获得30%伤害减免"},
        "passive": {"name": "连环之策", "description": "攻击时有25%概率使敌方互相攻击"},
        "story": "字士元，号凤雏，与诸葛亮齐名。献连环计助周瑜火烧赤壁。攻雒城时中箭身亡，英年早逝。",
        "exclusive_equipment": "凤雏羽扇"
    },
    "魏延": {
        "faction": "shu", "quality": "epic", "element": "火",
        "title": "反骨", "weapon_type": "刀",
        "base": {"attack": 340, "defense": 240, "health": 1150, "speed": 85, "critical": 0.10},
        "growth": {"attack": 30, "defense": 21, "health": 115, "speed": 6, "critical": 0.003},
        "skill": {"name": "奇袭", "damage": 44, "element": "火", "type": "surprise",
                  "description": "出奇制胜，对单体造成44%伤害，降低目标30%防御"},
        "ultimate": {"name": "反骨之叛", "damage": 170, "element": "火", "type": "berserk",
                     "description": "对单体造成170%伤害，自身进入狂暴状态3回合（攻击+40%）"},
        "passive": {"name": "桀骜不驯", "description": "受到攻击时有20%概率反击，造成50%攻击力伤害"},
        "story": "字文长，蜀汉名将。随刘备入蜀，屡立战功。诸葛亮北伐时为先锋，后因谋反被杀。",
        "exclusive_equipment": "鬼头大刀"
    },
    "姜维": {
        "faction": "shu", "quality": "legendary", "element": "风",
        "title": "麒麟儿", "weapon_type": "枪",
        "base": {"attack": 350, "defense": 250, "health": 1150, "speed": 95, "critical": 0.12},
        "growth": {"attack": 31, "defense": 22, "health": 115, "speed": 7, "critical": 0.004},
        "skill": {"name": "天水麒麟", "damage": 46, "element": "风", "type": "counter",
                  "description": "麒麟之才，对单体造成46%伤害，获得反击状态2回合"},
        "ultimate": {"name": "九伐中原", "damage": 155, "element": "风", "type": "persistent",
                     "description": "对全体造成155%伤害，之后3回合每回合造成30%追加伤害"},
        "passive": {"name": "继承遗志", "description": "己方有武将阵亡时，全属性提升20%"},
        "story": "字伯约，蜀汉后期大将军。诸葛亮传人，九伐中原，力图恢复汉室。蜀亡后假降钟会，图谋复国，事败被杀。",
        "exclusive_equipment": "绿沉枪"
    },
    "法正": {
        "faction": "shu", "quality": "epic", "element": "水",
        "title": "谋主", "weapon_type": "扇",
        "base": {"attack": 240, "defense": 180, "health": 900, "speed": 88, "critical": 0.08},
        "growth": {"attack": 22, "defense": 16, "health": 90, "speed": 7, "critical": 0.003},
        "skill": {"name": "奇谋", "damage": 35, "element": "水", "type": "strategy",
                  "description": "出奇谋，对敌方造成35%伤害，使己方下次技能伤害提升30%"},
        "ultimate": {"name": "定军之策", "damage": 120, "element": "水", "type": "mark",
                     "description": "对全体造成120%伤害，标记目标3回合，被标记目标受到伤害增加25%"},
        "passive": {"name": "奇谋百出", "description": "技能命中时20%概率重置技能冷却"},
        "story": "字孝直，蜀汉重要谋士。助刘备取益州，定汉中，是刘备取西川的首席功臣。"
    },
    "关平": {
        "faction": "shu", "quality": "rare", "element": "火",
        "title": "义子", "weapon_type": "刀",
        "base": {"attack": 280, "defense": 200, "health": 1000, "speed": 80, "critical": 0.08},
        "growth": {"attack": 25, "defense": 18, "health": 100, "speed": 6, "critical": 0.003},
        "skill": {"name": "忠义刀法", "damage": 40, "element": "火", "type": "attack",
                  "description": "继承关羽刀法，对单体造成40%伤害"},
        "ultimate": {"name": "父子连心", "damage": 130, "element": "火", "type": "combo",
                     "description": "与关羽合击，造成130%伤害，若关羽在场上额外造成50%伤害"},
        "passive": {"name": "忠孝两全", "description": "关羽在场时，攻击力和防御力各提升15%"},
        "story": "关羽义子，随关羽镇守荆州，与关羽一同殉难于临沮。"
    },
    "关兴": {
        "faction": "shu", "quality": "rare", "element": "火",
        "title": "少将", "weapon_type": "刀",
        "base": {"attack": 290, "defense": 190, "health": 980, "speed": 82, "critical": 0.09},
        "growth": {"attack": 26, "defense": 17, "health": 98, "speed": 6, "critical": 0.003},
        "skill": {"name": "复仇之刃", "damage": 42, "element": "火", "type": "attack",
                  "description": "为父报仇，对单体造成42%伤害，对击杀关羽的敌人额外造成30%伤害"},
        "ultimate": {"name": "关氏刀法", "damage": 135, "element": "火", "type": "attack",
                     "description": "继承家传刀法，对单体造成135%伤害"},
        "passive": {"name": "将门虎子", "description": "暴击时恢复自身5%生命"},
        "story": "关羽之子，与张苞结义，随刘备伐吴，斩杀潘璋马忠，为父报仇。"
    },
    "张苞": {
        "faction": "shu", "quality": "rare", "element": "土",
        "title": "少将", "weapon_type": "矛",
        "base": {"attack": 300, "defense": 210, "health": 1050, "speed": 78, "critical": 0.08},
        "growth": {"attack": 27, "defense": 19, "health": 105, "speed": 5, "critical": 0.003},
        "skill": {"name": "矛术传承", "damage": 43, "element": "土", "type": "attack",
                  "description": "继承张飞矛术，对单体造成43%伤害"},
        "ultimate": {"name": "猛虎下山", "damage": 140, "element": "土", "type": "stun",
                     "description": "对单体造成140%伤害，20%概率眩晕1回合"},
        "passive": {"name": "虎父无犬子", "description": "攻击时10%概率发动二段攻击"},
        "story": "张飞之子，与关兴结义兄弟，随刘备伐吴，屡立战功。"
    },
    "马岱": {
        "faction": "shu", "quality": "rare", "element": "风",
        "title": "骑将", "weapon_type": "枪",
        "base": {"attack": 270, "defense": 190, "health": 950, "speed": 88, "critical": 0.07},
        "growth": {"attack": 24, "defense": 17, "health": 95, "speed": 7, "critical": 0.002},
        "skill": {"name": "骑射", "damage": 38, "element": "风", "type": "ranged",
                  "description": "边骑边射，对单体造成38%伤害，降低目标速度15%"},
        "ultimate": {"name": "西凉冲锋", "damage": 125, "element": "风", "type": "charge",
                     "description": "对前排造成125%伤害，击退目标行动条20%"},
        "passive": {"name": "马家枪法", "description": "速度高于目标时，暴击率提升10%"},
        "story": "马超堂弟，随马超归刘备。后斩杀魏延，为蜀汉后期将领。"
    },
    "廖化": {
        "faction": "shu", "quality": "common", "element": "土",
        "title": "老将", "weapon_type": "刀",
        "base": {"attack": 220, "defense": 170, "health": 850, "speed": 72, "critical": 0.05},
        "growth": {"attack": 20, "defense": 15, "health": 85, "speed": 5, "critical": 0.002},
        "skill": {"name": "先锋", "damage": 32, "element": "土", "type": "attack",
                  "description": "作为先锋冲锋，对单体造成32%伤害"},
        "ultimate": {"name": "坚守", "damage": 90, "element": "土", "type": "defense",
                     "description": "对单体造成90%伤害，自身防御提升30%2回合"},
        "passive": {"name": "忠心耿耿", "description": "生命低于30%时，防御力提升50%"},
        "story": "字元俭，蜀汉后期将领，从关羽镇守荆州到蜀亡，历经蜀汉兴衰。"
    },
    "周仓": {
        "faction": "shu", "quality": "common", "element": "土",
        "title": "护卫", "weapon_type": "刀",
        "base": {"attack": 240, "defense": 220, "health": 1000, "speed": 65, "critical": 0.05},
        "growth": {"attack": 21, "defense": 20, "health": 100, "speed": 4, "critical": 0.002},
        "skill": {"name": "护卫", "damage": 30, "element": "土", "type": "protect",
                  "description": "保护友军，对单体造成30%伤害，为最低生命友军提供护盾"},
        "ultimate": {"name": "忠勇护主", "damage": 100, "element": "土", "type": "taunt",
                     "description": "对全体造成100%伤害，强制敌人攻击自身2回合"},
        "passive": {"name": "力大无穷", "description": "受到伤害的10%反弹给攻击者"},
        "story": "原黄巾军，后归顺关羽，为关羽扛刀，忠心耿耿，关羽死后自刎而亡。"
    },
    "徐庶": {
        "faction": "shu", "quality": "epic", "element": "水",
        "title": "谋士", "weapon_type": "扇",
        "base": {"attack": 230, "defense": 175, "health": 880, "speed": 85, "critical": 0.07},
        "growth": {"attack": 21, "defense": 16, "health": 88, "speed": 6, "critical": 0.002},
        "skill": {"name": "破阵", "damage": 34, "element": "水", "type": "debuff",
                  "description": "破解敌方阵型，造成34%伤害，降低25%防御2回合"},
        "ultimate": {"name": "走马荐诸葛", "damage": 110, "element": "水", "type": "support",
                     "description": "对全体造成110%伤害，己方全体恢复15%生命和10点怒气"},
        "passive": {"name": "孝子", "description": "为友军承受20%伤害"},
        "story": "字元直，蜀汉谋士。走马荐诸葛，后因母被曹操所擒，被迫归曹，终生不设一谋。"
    },

    # ==================== 魏国武将 ====================
    "曹操": {
        "faction": "wei", "quality": "mythic", "element": "火",
        "title": "魏武王", "weapon_type": "剑",
        "base": {"attack": 380, "defense": 300, "health": 1350, "speed": 95, "critical": 0.12},
        "growth": {"attack": 34, "defense": 26, "health": 135, "speed": 7, "critical": 0.004},
        "skill": {"name": "魏武挥鞭", "damage": 48, "element": "火", "type": "leadership",
                  "description": "挥鞭指挥，对敌方造成48%伤害，提升己方全体攻击力15%"},
        "ultimate": {"name": "宁教我负天下", "damage": 165, "element": "火", "type": "dominate",
                     "description": "对全体造成165%伤害，降低敌方全体30%攻击力，持续3回合"},
        "passive": {"name": "乱世奸雄", "description": "击杀目标后，恢复自身25%生命并提升20%攻击力"},
        "story": "字孟德，魏国奠基者。挟天子以令诸侯，官渡之战大败袁绍，统一北方。文武双全，乱世之奸雄，治世之能臣。",
        "exclusive_equipment": "倚天剑"
    },
    "司马懿": {
        "faction": "wei", "quality": "mythic", "element": "雷",
        "title": "冢虎", "weapon_type": "扇",
        "base": {"attack": 290, "defense": 250, "health": 1100, "speed": 90, "critical": 0.10},
        "growth": {"attack": 26, "defense": 22, "health": 110, "speed": 7, "critical": 0.004},
        "skill": {"name": "鬼谋", "damage": 42, "element": "雷", "type": "strategy",
                  "description": "鬼神莫测之谋，对敌方造成42%伤害，降低30%怒气获取"},
        "ultimate": {"name": "鹰视狼顾", "damage": 145, "element": "雷", "type": "silence",
                     "description": "对全体造成145%伤害，沉默全体2回合（无法使用技能）"},
        "passive": {"name": "隐忍", "description": "受到攻击时有30%概率将伤害转化为护盾"},
        "story": "字仲达，魏国权臣。隐忍数十年，熬死诸葛亮。高平陵之变夺权，为西晋奠定基业。",
        "exclusive_equipment": "冥蛇扇"
    },
    "典韦": {
        "faction": "wei", "quality": "legendary", "element": "火",
        "title": "古之恶来", "weapon_type": "戟",
        "base": {"attack": 430, "defense": 280, "health": 1400, "speed": 80, "critical": 0.12},
        "growth": {"attack": 37, "defense": 24, "health": 140, "speed": 6, "critical": 0.004},
        "skill": {"name": "双戟乱舞", "damage": 52, "element": "火", "type": "double_attack",
                  "description": "双戟齐出，对单体造成2次26%伤害"},
        "ultimate": {"name": "恶来之怒", "damage": 190, "element": "火", "type": "berserk",
                     "description": "对单体造成190%伤害，自身攻击力提升50%但每回合损失5%生命"},
        "passive": {"name": "死战不退", "description": "生命低于20%时，攻击力翻倍"},
        "story": "曹操贴身猛将，力大无穷。宛城之战为保护曹操，独挡叛军，力战而亡。",
        "exclusive_equipment": "双铁戟"
    },
    "许褚": {
        "faction": "wei", "quality": "legendary", "element": "土",
        "title": "虎痴", "weapon_type": "锤",
        "base": {"attack": 400, "defense": 320, "health": 1500, "speed": 70, "critical": 0.08},
        "growth": {"attack": 35, "defense": 28, "health": 150, "speed": 5, "critical": 0.003},
        "skill": {"name": "虎痴之力", "damage": 50, "element": "土", "type": "heavy",
                  "description": "力大如虎，对单体造成50%伤害，15%概率眩晕"},
        "ultimate": {"name": "裸衣决战", "damage": 175, "element": "土", "type": "sacrifice",
                     "description": "对全体造成175%伤害，自身防御降低30%但攻击提升40%"},
        "passive": {"name": "虎卫", "description": "为曹操分担30%伤害（若曹操在场上）"},
        "story": "字仲康，曹魏猛将。裸衣斗马超，护驾有功，号称虎痴。",
        "exclusive_equipment": "虎头锤"
    },
    "张辽": {
        "faction": "wei", "quality": "legendary", "element": "风",
        "title": "威震逍遥", "weapon_type": "戟",
        "base": {"attack": 380, "defense": 270, "health": 1200, "speed": 100, "critical": 0.14},
        "growth": {"attack": 34, "defense": 23, "health": 120, "speed": 8, "critical": 0.005},
        "skill": {"name": "突袭", "damage": 48, "element": "风", "type": "charge",
                  "description": "快速突袭，对单体造成48%伤害，无视20%防御"},
        "ultimate": {"name": "威震逍遥津", "damage": 200, "element": "风", "type": "fear_aoe",
                     "description": "对全体造成200%伤害，40%概率恐惧2回合"},
        "passive": {"name": "八百破十万", "description": "敌人数量越多，攻击力越高（每个敌人+5%）"},
        "story": "字文远，曹魏名将。原属吕布，后归曹操。逍遥津八百勇士破孙权十万大军，威震江东。",
        "exclusive_equipment": "问天戟"
    },
    "夏侯惇": {
        "faction": "wei", "quality": "epic", "element": "火",
        "title": "独眼", "weapon_type": "枪",
        "base": {"attack": 350, "defense": 290, "health": 1300, "speed": 82, "critical": 0.09},
        "growth": {"attack": 31, "defense": 25, "health": 130, "speed": 6, "critical": 0.003},
        "skill": {"name": "刚烈", "damage": 44, "element": "火", "type": "counter",
                  "description": "性格刚烈，对单体造成44%伤害，获得反击状态"},
        "ultimate": {"name": "拔矢啖睛", "damage": 160, "element": "火", "type": "self_heal",
                     "description": "对单体造成160%伤害，恢复自身30%生命"},
        "passive": {"name": "独目", "description": "受到致命伤害时，有30%概率保留1点生命"},
        "story": "字元让，曹魏宗族名将。拔矢啖睛，勇猛无双。曹操起兵时即为股肱，深受信任。"
    },
    "夏侯渊": {
        "faction": "wei", "quality": "epic", "element": "风",
        "title": "神射", "weapon_type": "弓",
        "base": {"attack": 340, "defense": 220, "health": 1050, "speed": 95, "critical": 0.15},
        "growth": {"attack": 30, "defense": 19, "health": 105, "speed": 7, "critical": 0.005},
        "skill": {"name": "神速", "damage": 42, "element": "风", "type": "fast",
                  "description": "神速攻击，对单体造成42%伤害，自身行动条前进20%"},
        "ultimate": {"name": "千里追击", "damage": 165, "element": "风", "type": "pursue",
                     "description": "对单体造成165%伤害，击杀后对随机敌人发动追击（100%伤害）"},
        "passive": {"name": "三日五百", "description": "速度提升20%，暴击伤害提升30%"},
        "story": "字妙才，曹魏名将。善于奔袭，三日五百，六日一千。定军山被黄忠斩杀。"
    },
    "徐晃": {
        "faction": "wei", "quality": "epic", "element": "金",
        "title": "周亚夫之风", "weapon_type": "斧",
        "base": {"attack": 330, "defense": 260, "health": 1150, "speed": 78, "critical": 0.08},
        "growth": {"attack": 29, "defense": 23, "health": 115, "speed": 6, "critical": 0.003},
        "skill": {"name": "开山斧", "damage": 44, "element": "金", "type": "heavy",
                  "description": "斧如开山，对单体造成44%伤害，破甲20%"},
        "ultimate": {"name": "治军严明", "damage": 145, "element": "金", "type": "buff_team",
                     "description": "对全体造成145%伤害，己方全体防御提升25%3回合"},
        "passive": {"name": "周亚夫之风", "description": "己方全体受到伤害减少8%"},
        "story": "字公明，曹魏名将。治军严整，有周亚夫之风。樊城之战击败关羽。"
    },
    "张郃": {
        "faction": "wei", "quality": "epic", "element": "土",
        "title": "巧变", "weapon_type": "枪",
        "base": {"attack": 340, "defense": 240, "health": 1100, "speed": 88, "critical": 0.10},
        "growth": {"attack": 30, "defense": 21, "health": 110, "speed": 7, "critical": 0.003},
        "skill": {"name": "巧变", "damage": 43, "element": "土", "type": "adaptive",
                  "description": "善于应变，对单体造成43%伤害，根据目标弱点切换元素"},
        "ultimate": {"name": "木门埋伏", "damage": 155, "element": "土", "type": "trap",
                     "description": "对全体造成155%伤害，20%概率立即再次行动"},
        "passive": {"name": "五子良将", "description": "场上每有一个魏国武将，攻击力提升5%"},
        "story": "字俊乂，曹魏名将，五子良将之一。善于巧变，料敌先机。木门道中伏身亡。"
    },
    "曹丕": {
        "faction": "wei", "quality": "legendary", "element": "水",
        "title": "文帝", "weapon_type": "剑",
        "base": {"attack": 320, "defense": 260, "health": 1150, "speed": 88, "critical": 0.10},
        "growth": {"attack": 28, "defense": 23, "health": 115, "speed": 7, "critical": 0.003},
        "skill": {"name": "帝王之术", "damage": 42, "element": "水", "type": "control",
                  "description": "帝王心术，对单体造成42%伤害，降低目标20%怒气"},
        "ultimate": {"name": "篡汉建魏", "damage": 150, "element": "水", "type": "usurp",
                     "description": "对全体造成150%伤害，偷取敌方全体10%攻击力3回合"},
        "passive": {"name": "帝王之威", "description": "己方魏国武将全属性提升10%"},
        "story": "字子桓，曹操之子，魏国开国皇帝。代汉建魏，在位七年。文学家，建安文学代表。"
    },
    "甄姬": {
        "faction": "wei", "quality": "epic", "element": "水",
        "title": "洛神", "weapon_type": "扇",
        "base": {"attack": 260, "defense": 200, "health": 950, "speed": 92, "critical": 0.08},
        "growth": {"attack": 24, "defense": 18, "health": 95, "speed": 7, "critical": 0.003},
        "skill": {"name": "洛水之舞", "damage": 36, "element": "水", "type": "heal",
                  "description": "如洛神起舞，对敌方造成36%伤害，恢复己方全体10%生命"},
        "ultimate": {"name": "凌波微步", "damage": 120, "element": "水", "type": "dodge",
                     "description": "对全体造成120%伤害，己方全体闪避率提升30%2回合"},
        "passive": {"name": "洛神赋", "description": "每回合恢复己方生命最低的武将15%生命"},
        "story": "魏文帝曹丕之妻，美貌绝伦。曹植作《洛神赋》咏之，洛水之神。"
    },
    "郭嘉": {
        "faction": "wei", "quality": "legendary", "element": "水",
        "title": "鬼才", "weapon_type": "扇",
        "base": {"attack": 250, "defense": 180, "health": 900, "speed": 95, "critical": 0.10},
        "growth": {"attack": 23, "defense": 16, "health": 90, "speed": 8, "critical": 0.004},
        "skill": {"name": "十胜十败", "damage": 38, "element": "水", "type": "predict",
                  "description": "预判敌方，造成38%伤害，标记目标2回合（受到伤害+20%）"},
        "ultimate": {"name": "遗计定辽东", "damage": 130, "element": "水", "type": "posthumous",
                     "description": "对全体造成130%伤害，即使阵亡，效果仍持续2回合"},
        "passive": {"name": "天妒英才", "description": "阵亡时，己方全体获得30%攻击力和20%速度提升"},
        "story": "字奉孝，曹魏首席谋士。十胜十败论定军心，遗计定辽东。英年早逝，曹操痛哭。"
    },
    "荀彧": {
        "faction": "wei", "quality": "epic", "element": "水",
        "title": "王佐之才", "weapon_type": "扇",
        "base": {"attack": 230, "defense": 200, "health": 920, "speed": 85, "critical": 0.07},
        "growth": {"attack": 21, "defense": 18, "health": 92, "speed": 6, "critical": 0.002},
        "skill": {"name": "驱虎吞狼", "damage": 35, "element": "水", "type": "strategy",
                  "description": "驱使敌人互相攻击，造成35%伤害，使目标攻击其他敌人"},
        "ultimate": {"name": "王佐", "damage": 115, "element": "水", "type": "support",
                     "description": "对全体造成115%伤害，己方全体恢复20%生命并净化负面状态"},
        "passive": {"name": "坚守忠义", "description": "己方全体受到暴击伤害减少25%"},
        "story": "字文若，曹魏谋主。王佐之才，助曹操统一北方。后因反对曹操称魏公，忧愤而终。"
    },
    "贾诩": {
        "faction": "wei", "quality": "epic", "element": "雷",
        "title": "毒士", "weapon_type": "扇",
        "base": {"attack": 245, "defense": 185, "health": 880, "speed": 88, "critical": 0.09},
        "growth": {"attack": 22, "defense": 17, "health": 88, "speed": 7, "critical": 0.003},
        "skill": {"name": "毒计", "damage": 36, "element": "雷", "type": "poison",
                  "description": "毒辣计谋，造成36%伤害，附加中毒（每回合10%最大生命伤害）"},
        "ultimate": {"name": "算无遗策", "damage": 125, "element": "雷", "type": "predict",
                     "description": "对全体造成125%伤害，使敌方下次攻击伤害降低50%"},
        "passive": {"name": "明哲保身", "description": "受到攻击时有25%概率闪避"},
        "story": "字文和，曹魏谋士。计谋毒辣，算无遗策。历经多主，终得善终。"
    },
    "于禁": {
        "faction": "wei", "quality": "rare", "element": "金",
        "title": "毅重", "weapon_type": "枪",
        "base": {"attack": 290, "defense": 250, "health": 1100, "speed": 75, "critical": 0.06},
        "growth": {"attack": 26, "defense": 22, "health": 110, "speed": 5, "critical": 0.002},
        "skill": {"name": "毅重", "damage": 40, "element": "金", "type": "defense",
                  "description": "性格毅重，造成40%伤害，自身防御提升20%"},
        "ultimate": {"name": "严整", "damage": 120, "element": "金", "type": "defense_team",
                     "description": "对全体造成120%伤害，己方全体获得护盾"},
        "passive": {"name": "五子良将", "description": "场上每有一个魏国武将，防御力提升5%"},
        "story": "字文则，曹魏名将，五子良将之一。治军严整，后投降关羽，晚节不保。"
    },
    "乐进": {
        "faction": "wei", "quality": "rare", "element": "火",
        "title": "先登", "weapon_type": "刀",
        "base": {"attack": 310, "defense": 200, "health": 1000, "speed": 85, "critical": 0.08},
        "growth": {"attack": 28, "defense": 18, "health": 100, "speed": 6, "critical": 0.003},
        "skill": {"name": "先登", "damage": 42, "element": "火", "type": "first_strike",
                  "description": "率先登城，造成42%伤害，若先手则额外造成20%伤害"},
        "ultimate": {"name": "破城", "damage": 135, "element": "火", "type": "siege",
                     "description": "对单体造成135%伤害，破除目标所有护盾和防御加成"},
        "passive": {"name": "五子良将", "description": "场上每有一个魏国武将，速度提升5%"},
        "story": "字文谦，曹魏名将，五子良将之一。以胆烈著称，先登陷阵，屡立战功。"
    },

    # ==================== 吴国武将 ====================
    "孙权": {
        "faction": "wu", "quality": "legendary", "element": "水",
        "title": "吴大帝", "weapon_type": "剑",
        "base": {"attack": 330, "defense": 290, "health": 1250, "speed": 88, "critical": 0.10},
        "growth": {"attack": 29, "defense": 25, "health": 125, "speed": 7, "critical": 0.003},
        "skill": {"name": "江东之盾", "damage": 42, "element": "水", "type": "shield",
                  "description": "守护江东，造成42%伤害，己方全体获得护盾"},
        "ultimate": {"name": "制衡天下", "damage": 145, "element": "水", "type": "balance",
                     "description": "对全体造成145%伤害，平衡己方全体生命值（均分）"},
        "passive": {"name": "生子当如孙仲谋", "description": "己方吴国武将全属性提升10%"},
        "story": "字仲谋，吴国开国皇帝。坐断东南，曹操叹曰：生子当如孙仲谋。赤壁之战联刘抗曹，建立东吴。",
        "exclusive_equipment": "古锭刀"
    },
    "周瑜": {
        "faction": "wu", "quality": "mythic", "element": "火",
        "title": "美周郎", "weapon_type": "扇",
        "base": {"attack": 350, "defense": 220, "health": 1050, "speed": 100, "critical": 0.14},
        "growth": {"attack": 32, "defense": 19, "health": 105, "speed": 8, "critical": 0.005},
        "skill": {"name": "火烧赤壁", "damage": 50, "element": "火", "type": "burn_aoe",
                  "description": "烈火焚天，对全体造成50%伤害，附加灼烧3回合"},
        "ultimate": {"name": "赤壁之战", "damage": 175, "element": "火", "type": "burn_all",
                     "description": "对全体造成175%伤害，附加强力灼烧（每回合20%最大生命）"},
        "passive": {"name": "雅量高致", "description": "己方全体暴击率提升10%，火属性伤害提升20%"},
        "story": "字公瑾，东吴大都督。赤壁之战火烧曹军，三分天下。精通音律，曲有误周郎顾。英年早逝。",
        "exclusive_equipment": "火凤扇"
    },
    "陆逊": {
        "faction": "wu", "quality": "legendary", "element": "火",
        "title": "白面书生", "weapon_type": "扇",
        "base": {"attack": 320, "defense": 230, "health": 1050, "speed": 92, "critical": 0.12},
        "growth": {"attack": 29, "defense": 20, "health": 105, "speed": 7, "critical": 0.004},
        "skill": {"name": "火烧连营", "damage": 48, "element": "火", "type": "burn_chain",
                  "description": "火烧连营七百里，造成48%伤害，灼烧在敌人间传递"},
        "ultimate": {"name": "石亭之战", "damage": 160, "element": "火", "type": "trap_aoe",
                     "description": "对全体造成160%伤害，附加灼烧，灼烧目标行动时受到额外伤害"},
        "passive": {"name": "忍辱负重", "description": "受到攻击时积累怒气，达到5次后下次攻击伤害翻倍"},
        "story": "字伯言，东吴名将。夷陵之战火烧连营七百里，大败刘备。后任丞相，治国安邦。"
    },
    "吕蒙": {
        "faction": "wu", "quality": "epic", "element": "土",
        "title": "白衣渡江", "weapon_type": "枪",
        "base": {"attack": 340, "defense": 260, "health": 1200, "speed": 82, "critical": 0.09},
        "growth": {"attack": 30, "defense": 23, "health": 120, "speed": 6, "critical": 0.003},
        "skill": {"name": "白衣渡江", "damage": 46, "element": "土", "type": "stealth",
                  "description": "伪装渡江，造成46%伤害，自身隐身1回合"},
        "ultimate": {"name": "刮目相看", "damage": 155, "element": "土", "type": "evolve",
                     "description": "对单体造成155%伤害，永久提升自身15%全属性"},
        "passive": {"name": "士别三日", "description": "每场战斗开始时，全属性提升10%（每场限1次）"},
        "story": "字子明，东吴名将。从目不识丁到饱读兵书，白衣渡江袭取荆州，击败关羽。"
    },
    "甘宁": {
        "faction": "wu", "quality": "epic", "element": "水",
        "title": "锦帆贼", "weapon_type": "刀",
        "base": {"attack": 360, "defense": 200, "health": 1050, "speed": 95, "critical": 0.12},
        "growth": {"attack": 32, "defense": 18, "health": 105, "speed": 8, "critical": 0.004},
        "skill": {"name": "锦帆", "damage": 46, "element": "水", "type": "naval",
                  "description": "锦帆水贼，造成46%伤害，速度提升15%"},
        "ultimate": {"name": "百骑劫营", "damage": 170, "element": "水", "type": "night_raid",
                     "description": "对随机敌人发动5次攻击，每次35%伤害，全部暴击"},
        "passive": {"name": "水上霸王", "description": "速度高于目标时，伤害提升25%"},
        "story": "字兴霸，东吴名将。原为水贼，后归孙权。百骑劫曹营，不损一人。"
    },
    "太史慈": {
        "faction": "wu", "quality": "epic", "element": "风",
        "title": "神射", "weapon_type": "弓",
        "base": {"attack": 350, "defense": 230, "health": 1100, "speed": 90, "critical": 0.14},
        "growth": {"attack": 31, "defense": 20, "health": 110, "speed": 7, "critical": 0.005},
        "skill": {"name": "神亭岭", "damage": 46, "element": "风", "type": "duel",
                  "description": "与敌决战，造成46%伤害，1v1时额外造成30%伤害"},
        "ultimate": {"name": "双戟齐出", "damage": 160, "element": "风", "type": "double",
                     "description": "对单体造成2次80%伤害"},
        "passive": {"name": "信义笃烈", "description": "攻击时15%概率连击"},
        "story": "字子义，东吴名将。神亭岭与孙策大战，后归孙权。猿臂善射，箭无虚发。"
    },
    "黄盖": {
        "faction": "wu", "quality": "rare", "element": "火",
        "title": "苦肉计", "weapon_type": "鞭",
        "base": {"attack": 300, "defense": 250, "health": 1200, "speed": 72, "critical": 0.07},
        "growth": {"attack": 27, "defense": 22, "health": 120, "speed": 5, "critical": 0.002},
        "skill": {"name": "苦肉计", "damage": 42, "element": "火", "type": "sacrifice",
                  "description": "苦肉计，造成42%伤害，自损5%生命，伤害提升50%"},
        "ultimate": {"name": "诈降火攻", "damage": 140, "element": "火", "type": "fire",
                     "description": "对全体造成140%伤害，附加灼烧，自损10%生命"},
        "passive": {"name": "老将", "description": "生命越低攻击越高，生命低于50%时攻击力提升30%"},
        "story": "字公覆，东吴老将。赤壁之战献苦肉计，诈降曹操，为火攻成功立下大功。"
    },
    "鲁肃": {
        "faction": "wu", "quality": "epic", "element": "水",
        "title": "长者", "weapon_type": "扇",
        "base": {"attack": 240, "defense": 210, "health": 950, "speed": 85, "critical": 0.07},
        "growth": {"attack": 22, "defense": 19, "health": 95, "speed": 6, "critical": 0.002},
        "skill": {"name": "榻上策", "damage": 35, "element": "水", "type": "strategy",
                  "description": "榻上策定天下，造成35%伤害，提升己方怒气获取20%"},
        "ultimate": {"name": "单刀赴会", "damage": 120, "element": "水", "type": "negotiate",
                     "description": "对全体造成120%伤害，降低敌方全体怒气30%"},
        "passive": {"name": "好施", "description": "每回合恢复己方全体5%生命"},
        "story": "字子敬，东吴谋士外交家。榻上策比隆中对更早提出三分天下。促成孙刘联盟。"
    },
    "孙策": {
        "faction": "wu", "quality": "legendary", "element": "火",
        "title": "小霸王", "weapon_type": "枪",
        "base": {"attack": 390, "defense": 250, "health": 1200, "speed": 105, "critical": 0.15},
        "growth": {"attack": 35, "defense": 22, "health": 120, "speed": 9, "critical": 0.005},
        "skill": {"name": "霸王枪法", "damage": 50, "element": "火", "type": "fierce",
                  "description": "小霸王之勇，造成50%伤害，15%概率追加攻击"},
        "ultimate": {"name": "横扫江东", "damage": 175, "element": "火", "type": "sweep",
                     "description": "对前排造成175%伤害，击退行动条40%"},
        "passive": {"name": "小霸王", "description": "攻击时10%概率立即再次行动"},
        "story": "字伯符，孙权之兄。以传国玉玺借兵，横扫江东，奠定东吴基业。遇刺身亡，年仅26。"
    },
    "孙坚": {
        "faction": "wu", "quality": "epic", "element": "火",
        "title": "江东猛虎", "weapon_type": "刀",
        "base": {"attack": 350, "defense": 270, "health": 1250, "speed": 82, "critical": 0.09},
        "growth": {"attack": 31, "defense": 24, "health": 125, "speed": 6, "critical": 0.003},
        "skill": {"name": "江东猛虎", "damage": 46, "element": "火", "type": "fierce",
                  "description": "猛虎下山，造成46%伤害，提升自身攻击力15%"},
        "ultimate": {"name": "跨江击刘表", "damage": 155, "element": "火", "type": "charge",
                     "description": "对前排造成155%伤害，无视30%防御"},
        "passive": {"name": "猛虎之血", "description": "攻击时有15%概率造成2倍伤害"},
        "story": "字文台，孙策孙权之父。讨董联军先锋，得传国玉玺。征刘表时中伏身亡。"
    },
    "大乔": {
        "faction": "wu", "quality": "rare", "element": "水",
        "title": "国色", "weapon_type": "扇",
        "base": {"attack": 220, "defense": 180, "health": 880, "speed": 85, "critical": 0.06},
        "growth": {"attack": 20, "defense": 16, "health": 88, "speed": 6, "critical": 0.002},
        "skill": {"name": "沉鱼", "damage": 32, "element": "水", "type": "heal",
                  "description": "如沉鱼落雁，造成32%伤害，恢复己方生命最低武将20%生命"},
        "ultimate": {"name": "国色天香", "damage": 105, "element": "水", "type": "charm",
                     "description": "对全体造成105%伤害，20%概率迷惑目标1回合"},
        "passive": {"name": "江东二乔", "description": "小乔在场上时，治疗效果提升30%"},
        "story": "孙策之妻，与小乔并称江东二乔，国色天香。"
    },
    "小乔": {
        "faction": "wu", "quality": "rare", "element": "水",
        "title": "天香", "weapon_type": "扇",
        "base": {"attack": 230, "defense": 170, "health": 850, "speed": 88, "critical": 0.07},
        "growth": {"attack": 21, "defense": 15, "health": 85, "speed": 7, "critical": 0.002},
        "skill": {"name": "落雁", "damage": 34, "element": "水", "type": "buff",
                  "description": "如落雁之姿，造成34%伤害，提升己方全体速度10%"},
        "ultimate": {"name": "琴音缭绕", "damage": 110, "element": "水", "type": "debuff",
                     "description": "对全体造成110%伤害，降低敌方全体速度20%"},
        "passive": {"name": "江东二乔", "description": "大乔在场上时，技能伤害提升25%"},
        "story": "周瑜之妻，与大乔并称江东二乔，天香国色。"
    },
    "周泰": {
        "faction": "wu", "quality": "rare", "element": "土",
        "title": "忠勇", "weapon_type": "刀",
        "base": {"attack": 290, "defense": 270, "health": 1300, "speed": 70, "critical": 0.06},
        "growth": {"attack": 26, "defense": 24, "health": 130, "speed": 5, "critical": 0.002},
        "skill": {"name": "忠勇", "damage": 40, "element": "土", "type": "protect",
                  "description": "忠心护主，造成40%伤害，为孙权分担伤害2回合"},
        "ultimate": {"name": "身披十二创", "damage": 130, "element": "土", "type": "endure",
                     "description": "对全体造成130%伤害，3回合内不会死亡"},
        "passive": {"name": "不屈", "description": "受到致命伤害时，有40%概率保留1点生命（每场1次）"},
        "story": "字幼平，东吴将领。多次舍身保护孙权，身披十二创而不死，忠勇可嘉。"
    },

    # ==================== 群雄武将 ====================
    "吕布": {
        "faction": "qun", "quality": "mythic", "element": "雷",
        "title": "飞将", "weapon_type": "戟",
        "base": {"attack": 500, "defense": 300, "health": 1500, "speed": 100, "critical": 0.18},
        "growth": {"attack": 42, "defense": 26, "health": 150, "speed": 8, "critical": 0.006},
        "skill": {"name": "方天画戟", "damage": 58, "element": "雷", "type": "devastate",
                  "description": "无双方天画戟，对单体造成58%伤害，无视40%防御"},
        "ultimate": {"name": "天下无双", "damage": 250, "element": "雷", "type": "supreme",
                     "description": "对单体造成250%伤害，击杀后恢复50%生命并无敌1回合"},
        "passive": {"name": "人中吕布", "description": "攻击力为全武将最高，暴击伤害提升80%"},
        "story": "字奉先，三国第一猛将。人中吕布，马中赤兔。三英战吕布，辕门射戟。后有勇无谋，白门楼殒命。",
        "exclusive_equipment": "方天画戟"
    },
    "貂蝉": {
        "faction": "qun", "quality": "legendary", "element": "水",
        "title": "闭月", "weapon_type": "扇",
        "base": {"attack": 250, "defense": 170, "health": 850, "speed": 95, "critical": 0.08},
        "growth": {"attack": 23, "defense": 15, "health": 85, "speed": 8, "critical": 0.003},
        "skill": {"name": "美人计", "damage": 36, "element": "水", "type": "charm",
                  "description": "倾国倾城，造成36%伤害，25%概率迷惑目标2回合"},
        "ultimate": {"name": "闭月羞花", "damage": 130, "element": "水", "type": "control_all",
                     "description": "对全体造成130%伤害，30%概率迷惑全体1回合"},
        "passive": {"name": "连环计", "description": "男性武将对其造成的伤害降低30%"},
        "story": "四大美女之一，王允义女。连环计离间董卓吕布，拯救汉室。闭月之容，倾国倾城。",
        "exclusive_equipment": "霓裳羽衣"
    },
    "董卓": {
        "faction": "qun", "quality": "epic", "element": "火",
        "title": "暴相", "weapon_type": "戟",
        "base": {"attack": 380, "defense": 320, "health": 1600, "speed": 70, "critical": 0.08},
        "growth": {"attack": 34, "defense": 28, "health": 160, "speed": 5, "critical": 0.003},
        "skill": {"name": "暴虐", "damage": 48, "element": "火", "type": "tyrant",
                  "description": "暴虐无道，造成48%伤害，自身恢复造成伤害20%生命"},
        "ultimate": {"name": "焚城", "damage": 155, "element": "火", "type": "burn_city",
                     "description": "对全体造成155%伤害，灼烧3回合，自身防御提升30%"},
        "passive": {"name": "魔王", "description": "生命越高攻击越高，生命每多10%，攻击+5%"},
        "story": "字仲颖，西凉军阀。废少帝立献帝，火烧洛阳，残暴无道。后被王允设计，为吕布所杀。"
    },
    "袁绍": {
        "faction": "qun", "quality": "epic", "element": "金",
        "title": "四世三公", "weapon_type": "剑",
        "base": {"attack": 320, "defense": 280, "health": 1300, "speed": 78, "critical": 0.08},
        "growth": {"attack": 28, "defense": 25, "health": 130, "speed": 6, "critical": 0.003},
        "skill": {"name": "名门", "damage": 42, "element": "金", "type": "noble",
                  "description": "四世三公，造成42%伤害，召唤2名士兵协助攻击"},
        "ultimate": {"name": "官渡之战", "damage": 150, "element": "金", "type": "army",
                     "description": "对全体造成150%伤害，己方全体获得20%攻击力加成"},
        "passive": {"name": "名门望族", "description": "己方群雄武将全属性提升8%"},
        "story": "字本初，汝南袁氏四世三公。讨董联军盟主。官渡之战被曹操击败，忧愤而死。"
    },
    "颜良": {
        "faction": "qun", "quality": "epic", "element": "火",
        "title": "勇冠三军", "weapon_type": "刀",
        "base": {"attack": 370, "defense": 230, "health": 1150, "speed": 82, "critical": 0.11},
        "growth": {"attack": 33, "defense": 20, "health": 115, "speed": 6, "critical": 0.004},
        "skill": {"name": "快刀", "damage": 48, "element": "火", "type": "fast",
                  "description": "刀快如风，造成48%伤害，15%概率追击"},
        "ultimate": {"name": "勇冠三军", "damage": 165, "element": "火", "type": "fierce",
                     "description": "对单体造成165%伤害，自身攻击提升25%"},
        "passive": {"name": "河北四庭柱", "description": "文丑在场上时，攻击力提升20%"},
        "story": "袁绍麾下大将，勇冠三军。白马之战被关羽斩杀。"
    },
    "文丑": {
        "faction": "qun", "quality": "epic", "element": "土",
        "title": "河北名将", "weapon_type": "枪",
        "base": {"attack": 360, "defense": 250, "health": 1200, "speed": 80, "critical": 0.10},
        "growth": {"attack": 32, "defense": 22, "health": 120, "speed": 6, "critical": 0.003},
        "skill": {"name": "猛攻", "damage": 47, "element": "土", "type": "heavy",
                  "description": "力大无穷，造成47%伤害，破甲15%"},
        "ultimate": {"name": "奋力一击", "damage": 160, "element": "土", "type": "heavy",
                     "description": "对单体造成160%伤害，无视25%防御"},
        "passive": {"name": "河北四庭柱", "description": "颜良在场上时，防御力提升25%"},
        "story": "袁绍麾下大将，与颜良齐名。延津之战中曹操之计，被关羽斩杀。"
    },
    "华雄": {
        "faction": "qun", "quality": "rare", "element": "火",
        "title": "西凉猛将", "weapon_type": "刀",
        "base": {"attack": 340, "defense": 240, "health": 1150, "speed": 78, "critical": 0.09},
        "growth": {"attack": 30, "defense": 21, "health": 115, "speed": 6, "critical": 0.003},
        "skill": {"name": "西凉刀法", "damage": 44, "element": "火", "type": "attack",
                  "description": "西凉勇将，造成44%伤害"},
        "ultimate": {"name": "连斩", "damage": 140, "element": "火", "type": "chain_kill",
                     "description": "对单体造成140%伤害，击杀后对随机敌人追击"},
        "passive": {"name": "西凉之勇", "description": "对普通品质武将额外造成30%伤害"},
        "story": "董卓麾下猛将，汜水关前连斩数将。后被关羽温酒斩之。"
    },
    "华佗": {
        "faction": "qun", "quality": "epic", "element": "水",
        "title": "神医", "weapon_type": "扇",
        "base": {"attack": 200, "defense": 180, "health": 900, "speed": 85, "critical": 0.05},
        "growth": {"attack": 18, "defense": 16, "health": 90, "speed": 6, "critical": 0.002},
        "skill": {"name": "青囊术", "damage": 28, "element": "水", "type": "heal",
                  "description": "神医妙手，造成28%伤害，恢复己方全体20%生命"},
        "ultimate": {"name": "麻沸散", "damage": 90, "element": "水", "type": "revive",
                     "description": "对全体造成90%伤害，复活1名阵亡武将（50%生命）"},
        "passive": {"name": "神医", "description": "每回合恢复己方全体8%生命，可解除负面状态"},
        "story": "字元化，神医。发明麻沸散，创五禽戏。为关羽刮骨疗毒，后为曹操所杀。"
    },
    "左慈": {
        "faction": "qun", "quality": "legendary", "element": "雷",
        "title": "仙人", "weapon_type": "杖",
        "base": {"attack": 260, "defense": 190, "health": 950, "speed": 92, "critical": 0.10},
        "growth": {"attack": 24, "defense": 17, "health": 95, "speed": 7, "critical": 0.004},
        "skill": {"name": "幻术", "damage": 40, "element": "雷", "type": "illusion",
                  "description": "仙人幻术，造成40%伤害，25%概率使目标攻击友军"},
        "ultimate": {"name": "遁甲天书", "damage": 140, "element": "雷", "type": "transform",
                     "description": "对全体造成140%伤害，随机变形1名敌人（属性减半）2回合"},
        "passive": {"name": "仙术", "description": "每回合有20%概率随机召唤1个幻影协助战斗"},
        "story": "字元放，方士。掷杯戏曹操，遁甲天书，变幻莫测。"
    },
    "于吉": {
        "faction": "qun", "quality": "epic", "element": "雷",
        "title": "道士", "weapon_type": "杖",
        "base": {"attack": 240, "defense": 175, "health": 880, "speed": 88, "critical": 0.08},
        "growth": {"attack": 22, "defense": 16, "health": 88, "speed": 7, "critical": 0.003},
        "skill": {"name": "符水", "damage": 35, "element": "雷", "type": "curse",
                  "description": "符水之术，造成35%伤害，附加诅咒（每回合损失10%攻击力）"},
        "ultimate": {"name": "太平经", "damage": 125, "element": "雷", "type": "curse_all",
                     "description": "对全体造成125%伤害，全体诅咒3回合"},
        "passive": {"name": "蛊惑", "description": "攻击时有15%概率降低目标30%怒气"},
        "story": "琅琊道士，以符水治病。孙策以蛊惑人心为由杀之。"
    },
    "张角": {
        "faction": "qun", "quality": "legendary", "element": "雷",
        "title": "天公将军", "weapon_type": "杖",
        "base": {"attack": 300, "defense": 200, "health": 1000, "speed": 90, "critical": 0.10},
        "growth": {"attack": 27, "defense": 18, "health": 100, "speed": 7, "critical": 0.004},
        "skill": {"name": "雷击", "damage": 44, "element": "雷", "type": "lightning",
                  "description": "召唤雷电，造成44%伤害，20%概率麻痹1回合"},
        "ultimate": {"name": "苍天已死", "damage": 155, "element": "雷", "type": "revolution",
                     "description": "对全体造成155%伤害，降低敌方全体20%全属性"},
        "passive": {"name": "太平道", "description": "己方群雄武将每回合恢复5%生命"},
        "story": "巨鹿人，黄巾起义领袖。苍天已死，黄天当立。太平道创始人。"
    },
    "孟获": {
        "faction": "qun", "quality": "rare", "element": "土",
        "title": "南蛮王", "weapon_type": "锤",
        "base": {"attack": 330, "defense": 290, "health": 1350, "speed": 68, "critical": 0.07},
        "growth": {"attack": 29, "defense": 26, "health": 135, "speed": 5, "critical": 0.002},
        "skill": {"name": "蛮力", "damage": 44, "element": "土", "type": "heavy",
                  "description": "蛮族之力，造成44%伤害，15%概率眩晕"},
        "ultimate": {"name": "七擒七纵", "damage": 140, "element": "土", "type": "endure",
                     "description": "对全体造成140%伤害，3回合内受到致命伤害时免死1次"},
        "passive": {"name": "南蛮", "description": "受到伤害减少15%"},
        "story": "南蛮之王，诸葛亮七擒七纵，最终归降蜀汉。"
    },
    "祝融": {
        "faction": "qun", "quality": "rare", "element": "火",
        "title": "火神", "weapon_type": "飞刀",
        "base": {"attack": 320, "defense": 200, "health": 1000, "speed": 88, "critical": 0.12},
        "growth": {"attack": 29, "defense": 18, "health": 100, "speed": 7, "critical": 0.004},
        "skill": {"name": "飞刀", "damage": 42, "element": "火", "type": "ranged",
                  "description": "百发百中，造成42%伤害，附加灼烧"},
        "ultimate": {"name": "火神之怒", "damage": 145, "element": "火", "type": "burn_aoe",
                     "description": "对全体造成145%伤害，附加灼烧2回合"},
        "passive": {"name": "火神后裔", "description": "火属性伤害提升25%"},
        "story": "孟获之妻，传为火神祝融氏后裔。善使飞刀，百发百中。"
    },

    # ==================== 更多武将（扩展） ====================
    "曹仁": {
        "faction": "wei", "quality": "rare", "element": "金",
        "title": "固若金汤", "weapon_type": "盾",
        "base": {"attack": 280, "defense": 320, "health": 1400, "speed": 68, "critical": 0.05},
        "growth": {"attack": 25, "defense": 28, "health": 140, "speed": 5, "critical": 0.002},
        "skill": {"name": "铜墙铁壁", "damage": 35, "element": "金", "type": "defense",
                  "description": "固若金汤，造成35%伤害，自身防御提升30%"},
        "ultimate": {"name": "坚守樊城", "damage": 115, "element": "金", "type": "fortress",
                     "description": "对全体造成115%伤害，己方全体获得大量护盾"},
        "passive": {"name": "铁壁", "description": "受到伤害减少12%"},
        "story": "字子孝，曹魏宗族名将。坚守樊城，铜墙铁壁，善守之名传天下。"
    },
    "程昱": {
        "faction": "wei", "quality": "rare", "element": "雷",
        "title": "谋士", "weapon_type": "扇",
        "base": {"attack": 240, "defense": 185, "health": 880, "speed": 82, "critical": 0.08},
        "growth": {"attack": 22, "defense": 17, "health": 88, "speed": 6, "critical": 0.003},
        "skill": {"name": "十面埋伏", "damage": 36, "element": "雷", "type": "trap",
                  "description": "十面埋伏，造成36%伤害，使目标下次攻击伤害降低40%"},
        "ultimate": {"name": "伏兵", "damage": 125, "element": "雷", "type": "ambush",
                     "description": "对全体造成125%伤害，20%概率眩晕"},
        "passive": {"name": "深谋", "description": "技能命中时15%概率使目标沉默1回合"},
        "story": "字仲德，曹魏谋士。十面埋伏伏击袁绍，多出奇谋。"
    },
    "满宠": {
        "faction": "wei", "quality": "common", "element": "水",
        "title": "执法", "weapon_type": "剑",
        "base": {"attack": 210, "defense": 190, "health": 850, "speed": 75, "critical": 0.05},
        "growth": {"attack": 19, "defense": 17, "health": 85, "speed": 5, "critical": 0.002},
        "skill": {"name": "执法如山", "damage": 32, "element": "水", "type": "judge",
                  "description": "执法不阿，造成32%伤害，降低目标15%攻击力"},
        "ultimate": {"name": "酷吏", "damage": 100, "element": "水", "type": "debuff",
                     "description": "对全体造成100%伤害，降低全体20%攻击力和速度"},
        "passive": {"name": "执法", "description": "对品质高于自身的敌人造成额外15%伤害"},
        "story": "字伯宁，曹魏名将。执法如山，镇守合肥多年。"
    },
    "程普": {
        "faction": "wu", "quality": "rare", "element": "火",
        "title": "老将", "weapon_type": "矛",
        "base": {"attack": 300, "defense": 250, "health": 1200, "speed": 75, "critical": 0.07},
        "growth": {"attack": 27, "defense": 22, "health": 120, "speed": 5, "critical": 0.002},
        "skill": {"name": "火矛", "damage": 42, "element": "火", "type": "burn",
                  "description": "矛如烈火，造成42%伤害，附加灼烧"},
        "ultimate": {"name": "老当益壮", "damage": 130, "element": "火", "type": "burn_aoe",
                     "description": "对全体造成130%伤害，附加灼烧2回合"},
        "passive": {"name": "三朝元老", "description": "每回合恢复自身8%生命"},
        "story": "字德谋，东吴三朝老将。随孙坚、孙策、孙权三代，战功赫赫。"
    },
    "韩当": {
        "faction": "wu", "quality": "common", "element": "水",
        "title": "弓将", "weapon_type": "弓",
        "base": {"attack": 260, "defense": 190, "health": 900, "speed": 82, "critical": 0.08},
        "growth": {"attack": 23, "defense": 17, "health": 90, "speed": 6, "critical": 0.003},
        "skill": {"name": "弓射", "damage": 38, "element": "水", "type": "ranged",
                  "description": "善射，造成38%伤害"},
        "ultimate": {"name": "齐射", "damage": 120, "element": "水", "type": "aoe",
                     "description": "对全体造成120%伤害"},
        "passive": {"name": "弓术", "description": "暴击率提升8%"},
        "story": "字义公，东吴老将。弓马娴熟，随孙氏三代征战。"
    },
    "丁奉": {
        "faction": "wu", "quality": "rare", "element": "风",
        "title": "雪中奋短兵", "weapon_type": "刀",
        "base": {"attack": 290, "defense": 230, "health": 1050, "speed": 80, "critical": 0.08},
        "growth": {"attack": 26, "defense": 20, "health": 105, "speed": 6, "critical": 0.003},
        "skill": {"name": "短兵", "damage": 40, "element": "风", "type": "surprise",
                  "description": "雪中奋短兵，造成40%伤害，降低目标速度15%"},
        "ultimate": {"name": "突袭", "damage": 130, "element": "风", "type": "charge",
                     "description": "对前排造成130%伤害，击退行动条25%"},
        "passive": {"name": "老将", "description": "生命低于40%时，攻击力提升25%"},
        "story": "字承渊，东吴老将。雪中奋短兵，大败魏军。历仕四朝，至暮年仍立战功。"
    },
    "潘璋": {
        "faction": "wu", "quality": "common", "element": "水",
        "title": "擒将", "weapon_type": "刀",
        "base": {"attack": 270, "defense": 200, "health": 950, "speed": 78, "critical": 0.07},
        "growth": {"attack": 24, "defense": 18, "health": 95, "speed": 6, "critical": 0.002},
        "skill": {"name": "擒拿", "damage": 36, "element": "水", "type": "capture",
                  "description": "擒拿敌将，造成36%伤害，10%概率禁锢1回合"},
        "ultimate": {"name": "伏击", "damage": 120, "element": "水", "type": "ambush",
                     "description": "对单体造成120%伤害，先手时额外造成50%伤害"},
        "passive": {"name": "贪财", "description": "击杀目标时额外获得资源"},
        "story": "字文珪，东吴将领。擒获关羽，后因夺关兴之马被杀。"
    },
    "凌统": {
        "faction": "wu", "quality": "rare", "element": "风",
        "title": "少年英雄", "weapon_type": "枪",
        "base": {"attack": 310, "defense": 220, "health": 1000, "speed": 90, "critical": 0.09},
        "growth": {"attack": 28, "defense": 19, "health": 100, "speed": 7, "critical": 0.003},
        "skill": {"name": "国士之风", "damage": 42, "element": "风", "type": "honor",
                  "description": "国士之风，造成42%伤害，自身获得10%伤害减免"},
        "ultimate": {"name": "怒袭", "damage": 140, "element": "风", "type": "revenge",
                     "description": "对单体造成140%伤害，已损失生命越多伤害越高"},
        "passive": {"name": "孝义", "description": "父亲阵亡后攻击力永久提升15%"},
        "story": "字公绩，东吴将领。少年英雄，与甘宁化敌为友，忠勇可嘉。"
    },
    "张任": {
        "faction": "qun", "quality": "rare", "element": "风",
        "title": "蜀中名将", "weapon_type": "弓",
        "base": {"attack": 300, "defense": 220, "health": 1000, "speed": 85, "critical": 0.10},
        "growth": {"attack": 27, "defense": 19, "health": 100, "speed": 6, "critical": 0.003},
        "skill": {"name": "落凤", "damage": 42, "element": "风", "type": "snipe",
                  "description": "射杀凤雏，造成42%伤害，对谋士额外造成20%伤害"},
        "ultimate": {"name": "忠义不降", "damage": 135, "element": "风", "type": "loyalty",
                     "description": "对单体造成135%伤害，若自身阵亡则伤害翻倍"},
        "passive": {"name": "忠义", "description": "无法被迷惑，攻击谋士时伤害提升15%"},
        "story": "刘璋部将，射杀庞统。城破不降，从容赴死。"
    },
    "严颜": {
        "faction": "shu", "quality": "rare", "element": "土",
        "title": "老将", "weapon_type": "弓",
        "base": {"attack": 280, "defense": 240, "health": 1100, "speed": 72, "critical": 0.07},
        "growth": {"attack": 25, "defense": 21, "health": 110, "speed": 5, "critical": 0.002},
        "skill": {"name": "老将之勇", "damage": 40, "element": "土", "type": "counter",
                  "description": "老当益壮，造成40%伤害，获得反击状态"},
        "ultimate": {"name": "宁死不降", "damage": 130, "element": "土", "type": "endure",
                     "description": "对单体造成130%伤害，2回合内受到致命伤免死1次"},
        "passive": {"name": "只有断头将军", "description": "受到攻击时20%概率反击50%伤害"},
        "story": "刘璋部将，张飞义释严颜，后归蜀汉。老将之勇，忠义无双。"
    },
    "王平": {
        "faction": "shu", "quality": "common", "element": "土",
        "title": "无当飞军", "weapon_type": "枪",
        "base": {"attack": 250, "defense": 220, "health": 1000, "speed": 75, "critical": 0.06},
        "growth": {"attack": 22, "defense": 20, "health": 100, "speed": 5, "critical": 0.002},
        "skill": {"name": "无当", "damage": 36, "element": "土", "type": "defense",
                  "description": "无当飞军，造成36%伤害，自身和相邻友军防御提升15%"},
        "ultimate": {"name": "飞军突袭", "damage": 115, "element": "土", "type": "charge",
                     "description": "对前排造成115%伤害"},
        "passive": {"name": "稳重", "description": "不会被击退行动条"},
        "story": "字子均，蜀汉将领。统无当飞军，街亭劝谏马谡不听。后成为蜀汉后期重要将领。"
    },
    "马谡": {
        "faction": "shu", "quality": "rare", "element": "风",
        "title": "纸上谈兵", "weapon_type": "扇",
        "base": {"attack": 240, "defense": 180, "health": 850, "speed": 82, "critical": 0.07},
        "growth": {"attack": 22, "defense": 16, "health": 85, "speed": 6, "critical": 0.002},
        "skill": {"name": "纸上谈兵", "damage": 36, "element": "风", "type": "theory",
                  "description": "理论强于实践，造成36%伤害，但自身防御降低10%"},
        "ultimate": {"name": "拒谏", "damage": 120, "element": "风", "type": "reckless",
                     "description": "对全体造成120%伤害，但自身受到10%最大生命反噬"},
        "passive": {"name": "言过其实", "description": "技能伤害提升20%，但受到伤害增加15%"},
        "story": "字幼常，蜀汉参军。失街亭，被诸葛亮挥泪斩之。"
    },
    "关索": {
        "faction": "shu", "quality": "rare", "element": "火",
        "title": "花关索", "weapon_type": "刀",
        "base": {"attack": 290, "defense": 200, "health": 980, "speed": 82, "critical": 0.09},
        "growth": {"attack": 26, "defense": 18, "health": 98, "speed": 6, "critical": 0.003},
        "skill": {"name": "关家刀法", "damage": 42, "element": "火", "type": "attack",
                  "description": "继承家传刀法，造成42%伤害"},
        "ultimate": {"name": "花关索", "damage": 135, "element": "火", "type": "charm_attack",
                     "description": "对单体造成135%伤害，10%概率迷惑"},
        "passive": {"name": "将门之后", "description": "关羽在场上时，全属性提升15%"},
        "story": "关羽之子，随诸葛亮南征孟获，英勇善战。"
    },
    "鲍三娘": {
        "faction": "shu", "quality": "rare", "element": "水",
        "title": "女将", "weapon_type": "刀",
        "base": {"attack": 280, "defense": 200, "health": 950, "speed": 85, "critical": 0.08},
        "growth": {"attack": 25, "defense": 18, "health": 95, "speed": 7, "critical": 0.003},
        "skill": {"name": "女将之勇", "damage": 40, "element": "水", "type": "attack",
                  "description": "巾帼不让须眉，造成40%伤害"},
        "ultimate": {"name": "连斩", "damage": 130, "element": "水", "type": "chain",
                     "description": "对单体造成130%伤害，击杀后追击50%伤害"},
        "passive": {"name": "关索之妻", "description": "关索在场上时，攻击力提升20%"},
        "story": "关索之妻，鲍家庄之女，武艺高强，随夫君南征。"
    },
    "陈宫": {
        "faction": "qun", "quality": "epic", "element": "水",
        "title": "谋士", "weapon_type": "扇",
        "base": {"attack": 250, "defense": 190, "health": 900, "speed": 85, "critical": 0.08},
        "growth": {"attack": 23, "defense": 17, "health": 90, "speed": 6, "critical": 0.003},
        "skill": {"name": "智谋", "damage": 38, "element": "水", "type": "strategy",
                  "description": "智计百出，造成38%伤害，降低目标20%怒气"},
        "ultimate": {"name": "不事二主", "damage": 125, "element": "水", "type": "loyalty",
                     "description": "对全体造成125%伤害，吕布在场上时伤害提升30%"},
        "passive": {"name": "忠义", "description": "为吕布分担20%伤害"},
        "story": "字公台，吕布谋士。辅佐吕布但不被重用。白门楼拒不降曹，从容赴死。"
    },
    "高顺": {
        "faction": "qun", "quality": "rare", "element": "金",
        "title": "陷阵营", "weapon_type": "枪",
        "base": {"attack": 320, "defense": 260, "health": 1200, "speed": 78, "critical": 0.08},
        "growth": {"attack": 29, "defense": 23, "health": 120, "speed": 6, "critical": 0.003},
        "skill": {"name": "陷阵", "damage": 44, "element": "金", "type": "break",
                  "description": "陷阵营冲锋，造成44%伤害，破甲25%"},
        "ultimate": {"name": "攻无不克", "damage": 140, "element": "金", "type": "siege",
                     "description": "对前排造成140%伤害，无视30%防御"},
        "passive": {"name": "忠诚", "description": "为吕布分担15%伤害，吕布在场上时攻击提升15%"},
        "story": "吕布麾下猛将，统陷阵营，攻无不克。忠心耿耿，随吕布赴死。"
    },
    "曹冲": {
        "faction": "wei", "quality": "rare", "element": "水",
        "title": "神童", "weapon_type": "扇",
        "base": {"attack": 220, "defense": 175, "health": 820, "speed": 88, "critical": 0.08},
        "growth": {"attack": 20, "defense": 16, "health": 82, "speed": 7, "critical": 0.003},
        "skill": {"name": "称象", "damage": 34, "element": "水", "type": "smart",
                  "description": "聪明过人，造成34%伤害，降低目标15%全属性"},
        "ultimate": {"name": "神童之智", "damage": 115, "element": "水", "type": "debuff_all",
                     "description": "对全体造成115%伤害，降低全体20%防御"},
        "passive": {"name": "早慧", "description": "战斗开始时，己方全体获得10%怒气"},
        "story": "字仓舒，曹操之子。称象成名，少年神童。不幸早夭，年仅13。"
    },
    "蔡文姬": {
        "faction": "qun", "quality": "epic", "element": "水",
        "title": "才女", "weapon_type": "琴",
        "base": {"attack": 210, "defense": 170, "health": 830, "speed": 85, "critical": 0.06},
        "growth": {"attack": 19, "defense": 15, "health": 83, "speed": 6, "critical": 0.002},
        "skill": {"name": "胡笳十八拍", "damage": 32, "element": "水", "type": "heal_debuff",
                  "description": "琴音疗伤，造成32%伤害，恢复己方全体12%生命"},
        "ultimate": {"name": "悲愤诗", "damage": 110, "element": "水", "type": "control",
                     "description": "对全体造成110%伤害，25%概率悲伤（无法行动）1回合"},
        "passive": {"name": "才女", "description": "每回合恢复己方全体6%生命"},
        "story": "名琰，蔡邕之女。才女，胡笳十八拍。被匈奴掳走，曹操重金赎回。"
    },
    "张春华": {
        "faction": "wei", "quality": "epic", "element": "雷",
        "title": "毒后", "weapon_type": "扇",
        "base": {"attack": 260, "defense": 190, "health": 900, "speed": 88, "critical": 0.09},
        "growth": {"attack": 24, "defense": 17, "health": 90, "speed": 7, "critical": 0.003},
        "skill": {"name": "绝情", "damage": 38, "element": "雷", "type": "ruthless",
                  "description": "心狠手辣，造成38%伤害，降低目标15%治疗效果"},
        "ultimate": {"name": "死士", "damage": 130, "element": "雷", "type": "assassin",
                     "description": "对单体造成130%伤害，对治疗者额外造成50%伤害"},
        "passive": {"name": "冷酷", "description": "司马懿在场上时，全属性提升15%"},
        "story": "司马懿之妻，司马师司马昭之母。心狠手辣，曾亲手杀婢女。"
    },
    "黄月英": {
        "faction": "shu", "quality": "epic", "element": "雷",
        "title": "机关术", "weapon_type": "杖",
        "base": {"attack": 230, "defense": 180, "health": 850, "speed": 82, "critical": 0.08},
        "growth": {"attack": 21, "defense": 16, "health": 85, "speed": 6, "critical": 0.003},
        "skill": {"name": "木牛流马", "damage": 36, "element": "雷", "type": "mechanical",
                  "description": "机关术，造成36%伤害，召唤木牛流马协战1回合"},
        "ultimate": {"name": "诸葛连弩", "damage": 125, "element": "雷", "type": "multi_shot",
                     "description": "对随机敌人发动5次25%伤害"},
        "passive": {"name": "巧匠", "description": "诸葛亮在场上时，技能伤害提升25%"},
        "story": "诸葛亮之妻，精通机关术。木牛流马、诸葛连弩皆有她的功劳。"
    },

    # ==================== 晋国武将 ====================
    "司马师": {
        "faction": "jin", "quality": "legendary", "element": "雷",
        "title": "景帝", "weapon_type": "剑",
        "base": {"attack": 350, "defense": 290, "health": 1250, "speed": 95, "critical": 0.10},
        "growth": {"attack": 30, "defense": 25, "health": 125, "speed": 7, "critical": 0.004},
        "skill": {"name": "权谋之刃", "damage": 48, "element": "雷", "type": "control_attack",
                  "description": "造成48%伤害，20%概率沉默目标2回合"},
        "ultimate": {"name": "废立之威", "damage": 145, "element": "雷", "type": "fear",
                     "description": "对全体造成145%伤害，使敌方减速30%持续2回合"},
        "passive": {"name": "深沉有略", "description": "生命值高于50%时，攻击力提升25%"},
        "story": "字子元，司马懿长子。承父业，废曹芳，平毌丘俭、文钦之叛。在位期间奠定司马氏代魏基础。"
    },
    "司马昭": {
        "faction": "jin", "quality": "mythic", "element": "雷",
        "title": "文帝", "weapon_type": "剑",
        "base": {"attack": 420, "defense": 300, "health": 1350, "speed": 100, "critical": 0.12},
        "growth": {"attack": 36, "defense": 26, "health": 135, "speed": 8, "critical": 0.005},
        "skill": {"name": "篡位之谋", "damage": 52, "element": "雷", "type": "debuff_attack",
                  "description": "造成52%伤害，降低目标30%防御2回合"},
        "ultimate": {"name": "司马昭之心", "damage": 175, "element": "雷", "type": "execute",
                     "description": "对全体造成175%伤害，生命低于40%的目标额外受到50%伤害"},
        "passive": {"name": "路人皆知", "description": "击杀目标后，自身攻击力提升20%，可叠加3次"},
        "story": "字子上，司马师之弟。弑曹髦，灭蜀汉。'司马昭之心，路人所知也'，为子司马炎代魏立晋奠定基础。"
    },
    "司马炎": {
        "faction": "jin", "quality": "mythic", "element": "风",
        "title": "晋武帝", "weapon_type": "剑",
        "base": {"attack": 380, "defense": 350, "health": 1500, "speed": 85, "critical": 0.08},
        "growth": {"attack": 32, "defense": 30, "health": 150, "speed": 6, "critical": 0.003},
        "skill": {"name": "一统天下", "damage": 50, "element": "风", "type": "buff_attack",
                  "description": "造成50%伤害，提升己方全体20%攻击力2回合"},
        "ultimate": {"name": "天命归晋", "damage": 165, "element": "风", "type": "buff_all",
                     "description": "对敌方全体造成165%伤害，恢复己方全体20%生命，提升全属性15%"},
        "passive": {"name": "受命于天", "description": "场上每阵亡一个敌方武将，全属性提升10%"},
        "story": "字安世，司马昭之子。代魏建晋，灭东吴，结束三国鼎立，统一天下。开创太康之治。"
    },
    "杜预": {
        "faction": "jin", "quality": "legendary", "element": "土",
        "title": "杜武库", "weapon_type": "枪",
        "base": {"attack": 360, "defense": 280, "health": 1200, "speed": 90, "critical": 0.10},
        "growth": {"attack": 31, "defense": 24, "health": 120, "speed": 7, "critical": 0.004},
        "skill": {"name": "破竹之势", "damage": 50, "element": "土", "type": "pierce",
                  "description": "造成50%伤害，对减速目标额外造成30%伤害"},
        "ultimate": {"name": "灭吴之策", "damage": 155, "element": "土", "type": "aoe",
                     "description": "对敌方全体造成155%伤害，击退行动条40%"},
        "passive": {"name": "左传癖", "description": "每次攻击有30%概率追加一次50%伤害的攻击"},
        "story": "字元凯，西晋名将学者。灭吴统一天下的统帅之一。博学多才，人称'杜武库'。著有《春秋左氏传集解》。"
    },
    "羊祜": {
        "faction": "jin", "quality": "legendary", "element": "风",
        "title": "羊叔子", "weapon_type": "剑",
        "base": {"attack": 320, "defense": 320, "health": 1400, "speed": 88, "critical": 0.06},
        "growth": {"attack": 27, "defense": 28, "health": 140, "speed": 6, "critical": 0.002},
        "skill": {"name": "怀柔之策", "damage": 42, "element": "风", "type": "heal_attack",
                  "description": "造成42%伤害，恢复己方全体10%生命"},
        "ultimate": {"name": "边境遗爱", "damage": 130, "element": "风", "type": "buff_all",
                     "description": "对敌方全体造成130%伤害，己方全体获得护盾（自身最大生命20%）"},
        "passive": {"name": "仁德服敌", "description": "回合结束时，恢复己方全体5%生命"},
        "story": "字叔子，西晋战略家。镇守襄阳十年，与吴将陆抗以德相交，遗策灭吴。'堕泪碑'传颂千古。"
    },
    "王濬": {
        "faction": "jin", "quality": "epic", "element": "水",
        "title": "楼船将军", "weapon_type": "弓",
        "base": {"attack": 280, "defense": 200, "health": 1000, "speed": 92, "critical": 0.10},
        "growth": {"attack": 25, "defense": 18, "health": 100, "speed": 7, "critical": 0.004},
        "skill": {"name": "楼船破浪", "damage": 45, "element": "水", "type": "aoe",
                  "description": "造成45%伤害，对水属性目标额外造成20%伤害"},
        "ultimate": {"name": "千艘齐发", "damage": 140, "element": "水", "type": "multi_hit",
                     "description": "对随机敌人发动4次35%伤害"},
        "passive": {"name": "顺流而下", "description": "速度高于目标时，技能伤害提升20%"},
        "story": "字士治，西晋名将。建造楼船，率水军顺江而下灭吴。'王濬楼船下益州，金陵王气黯然收'。"
    },
    "邓艾": {
        "faction": "jin", "quality": "legendary", "element": "土",
        "title": "邓征西", "weapon_type": "枪",
        "base": {"attack": 370, "defense": 270, "health": 1150, "speed": 88, "critical": 0.10},
        "growth": {"attack": 32, "defense": 23, "health": 115, "speed": 7, "critical": 0.004},
        "skill": {"name": "奇袭阴平", "damage": 50, "element": "土", "type": "charge",
                  "description": "造成50%伤害，无视20%防御"},
        "ultimate": {"name": "偷渡剑阁", "damage": 160, "element": "土", "type": "assassin",
                     "description": "对单体造成160%伤害，对生命低于50%的目标必暴击"},
        "passive": {"name": "屯田之策", "description": "每回合恢复自身10%生命，前2回合减伤20%"},
        "story": "字士载，三国末期魏将。偷渡阴平，灭蜀汉。'期思陂'屯田备粮，胸怀大志，口吃而才高。"
    },
    "钟会": {
        "faction": "jin", "quality": "epic", "element": "雷",
        "title": "钟士季", "weapon_type": "剑",
        "base": {"attack": 290, "defense": 220, "health": 950, "speed": 95, "critical": 0.12},
        "growth": {"attack": 26, "defense": 19, "health": 95, "speed": 8, "critical": 0.005},
        "skill": {"name": "篡逆之谋", "damage": 46, "element": "雷", "type": "debuff_attack",
                  "description": "造成46%伤害，降低目标25%攻击力2回合"},
        "ultimate": {"name": "谋反之乱", "damage": 135, "element": "雷", "type": "confusion",
                     "description": "对全体造成135%伤害，20%概率使目标混乱2回合"},
        "passive": {"name": "野心家", "description": "击杀目标后，获得30%攻击力加成，持续2回合"},
        "story": "字士季，魏将。与邓艾灭蜀后谋反，自立为西曹掾，旋即被杀。'志大才疏，自立难成'。"
    },
    "卫瓘": {
        "faction": "jin", "quality": "rare", "element": "土",
        "title": "卫伯玉", "weapon_type": "剑",
        "base": {"attack": 220, "defense": 200, "health": 850, "speed": 78, "critical": 0.06},
        "growth": {"attack": 19, "defense": 18, "health": 85, "speed": 6, "critical": 0.002},
        "skill": {"name": "稳守", "damage": 35, "element": "土", "type": "shield",
                  "description": "造成35%伤害，为自身添加15%生命护盾"},
        "ultimate": {"name": "平蜀监军", "damage": 110, "element": "土", "type": "debuff_all",
                     "description": "对全体造成110%伤害，降低目标20%攻击2回合"},
        "passive": {"name": "执法严明", "description": "对混乱/恐惧目标额外造成25%伤害"},
        "story": "字伯玉，魏晋名臣。监军平蜀，设计擒杀邓艾、钟会。后官至司空，为贾后所杀。"
    },
    "陈骞": {
        "faction": "jin", "quality": "epic", "element": "土",
        "title": "陈休渊", "weapon_type": "枪",
        "base": {"attack": 270, "defense": 250, "health": 1050, "speed": 80, "critical": 0.06},
        "growth": {"attack": 24, "defense": 22, "health": 105, "speed": 6, "critical": 0.002},
        "skill": {"name": "稳攻", "damage": 42, "element": "土", "type": "normal",
                  "description": "造成42%伤害，附带10%减速效果"},
        "ultimate": {"name": "三公之威", "damage": 130, "element": "土", "type": "aoe",
                     "description": "对敌方前排造成130%伤害，降低20%防御2回合"},
        "passive": {"name": "厚重", "description": "防御力高于目标时，受到伤害降低15%"},
        "story": "字休渊，魏晋名将。与司马氏交好，官至大司马，位列三公。沉厚有智谋。"
    },

    # ==================== 群雄补充武将 ====================
    "公孙瓒": {
        "faction": "qun", "quality": "epic", "element": "风",
        "title": "白马将军", "weapon_type": "枪",
        "base": {"attack": 290, "defense": 220, "health": 1050, "speed": 105, "critical": 0.10},
        "growth": {"attack": 26, "defense": 19, "health": 105, "speed": 8, "critical": 0.004},
        "skill": {"name": "白马义从", "damage": 46, "element": "风", "type": "charge",
                  "description": "造成46%伤害，速度高于目标时额外造成20%伤害"},
        "ultimate": {"name": "幽州铁骑", "damage": 140, "element": "风", "type": "multi_hit",
                     "description": "对随机敌人发动3次47%伤害"},
        "passive": {"name": "白马义士", "description": "速度提升15%，闪避率提升10%"},
        "story": "字伯珪，东汉末年群雄。统帅白马义从，威震塞外。与袁绍争冀州，败而自焚。刘备同门师兄。"
    },
    "马腾": {
        "faction": "qun", "quality": "epic", "element": "土",
        "title": "西凉太守", "weapon_type": "枪",
        "base": {"attack": 280, "defense": 240, "health": 1100, "speed": 88, "critical": 0.08},
        "growth": {"attack": 25, "defense": 21, "health": 110, "speed": 7, "critical": 0.003},
        "skill": {"name": "西凉铁骑", "damage": 45, "element": "土", "type": "charge",
                  "description": "造成45%伤害，20%概率眩晕目标1回合"},
        "ultimate": {"name": "父子兵", "damage": 135, "element": "土", "type": "aoe",
                     "description": "对敌方全体造成135%伤害，马超在场时伤害提升30%"},
        "passive": {"name": "汉室忠臣", "description": "对魏国武将额外造成20%伤害"},
        "story": "字寿成，马超之父。西凉军阀，与韩遂结义后反目。受曹操诱调入京被杀。汉伏波将军马援之后。"
    },
    "韩遂": {
        "faction": "qun", "quality": "rare", "element": "土",
        "title": "西凉军阀", "weapon_type": "枪",
        "base": {"attack": 230, "defense": 200, "health": 900, "speed": 80, "critical": 0.06},
        "growth": {"attack": 20, "defense": 18, "health": 90, "speed": 6, "critical": 0.002},
        "skill": {"name": "西凉叛军", "damage": 38, "element": "土", "type": "normal",
                  "description": "造成38%伤害，降低目标10%速度"},
        "ultimate": {"name": "联军反叛", "damage": 115, "element": "土", "type": "aoe",
                     "description": "对全体造成115%伤害，30%概率使目标混乱1回合"},
        "passive": {"name": "背信弃义", "description": "攻击被减益目标时额外造成15%伤害"},
        "story": "字文约，西凉军阀。与马腾结义又反目，多次起兵反曹。最终兵败被杀。"
    },
    "刘表": {
        "faction": "qun", "quality": "rare", "element": "风",
        "title": "荆州牧", "weapon_type": "剑",
        "base": {"attack": 200, "defense": 240, "health": 1100, "speed": 70, "critical": 0.04},
        "growth": {"attack": 17, "defense": 21, "health": 110, "speed": 5, "critical": 0.001},
        "skill": {"name": "荆州自守", "damage": 35, "element": "风", "type": "shield",
                  "description": "造成35%伤害，为自身添加20%生命护盾"},
        "ultimate": {"name": "八俊之名", "damage": 110, "element": "风", "type": "buff_all",
                     "description": "对敌方造成110%伤害，提升己方全体20%防御2回合"},
        "passive": {"name": "坐谈客耳", "description": "受到伤害时，10%概率获得护盾"},
        "story": "字景升，汉室宗亲。荆州牧，治下千里肃清。'坐谈客耳'，曹操评其无雄才。刘备曾投靠。"
    },
    "刘璋": {
        "faction": "qun", "quality": "rare", "element": "土",
        "title": "益州牧", "weapon_type": "剑",
        "base": {"attack": 180, "defense": 250, "health": 1150, "speed": 65, "critical": 0.03},
        "growth": {"attack": 15, "defense": 22, "health": 115, "speed": 5, "critical": 0.001},
        "skill": {"name": "益州自守", "damage": 32, "element": "土", "type": "shield",
                  "description": "造成32%伤害，提升己方全体15%防御2回合"},
        "ultimate": {"name": "蜀道难", "damage": 100, "element": "土", "type": "debuff_all",
                     "description": "对全体造成100%伤害，降低目标20%速度2回合"},
        "passive": {"name": "暗弱", "description": "生命低于50%时，受到伤害降低15%"},
        "story": "字季玉，益州牧。性宽柔无威，'暗弱'。迎刘备入蜀反被所夺，迁于公安。"
    },
    "张鲁": {
        "faction": "qun", "quality": "rare", "element": "雷",
        "title": "五斗米道", "weapon_type": "杖",
        "base": {"attack": 200, "defense": 200, "health": 1000, "speed": 78, "critical": 0.05},
        "growth": {"attack": 18, "defense": 18, "health": 100, "speed": 6, "critical": 0.002},
        "skill": {"name": "符水治病", "damage": 30, "element": "雷", "type": "heal",
                  "description": "造成30%伤害，恢复己方全体15%生命"},
        "ultimate": {"name": "鬼道", "damage": 105, "element": "雷", "type": "confusion",
                     "description": "对全体造成105%伤害，25%概率混乱目标1回合"},
        "passive": {"name": "义舍", "description": "回合开始时，恢复己方全体5%生命"},
        "story": "字公祺，五斗米道首领。汉中割据三十年，政教合一。降曹后封镇南将军。"
    },
    "袁术": {
        "faction": "qun", "quality": "epic", "element": "土",
        "title": "仲家帝", "weapon_type": "剑",
        "base": {"attack": 250, "defense": 220, "health": 1100, "speed": 75, "critical": 0.06},
        "growth": {"attack": 22, "defense": 19, "health": 110, "speed": 6, "critical": 0.002},
        "skill": {"name": "伪帝之怒", "damage": 42, "element": "土", "type": "debuff_attack",
                  "description": "造成42%伤害，降低目标20%攻击2回合"},
        "ultimate": {"name": "骄奢淫逸", "damage": 125, "element": "土", "type": "aoe",
                     "description": "对全体造成125%伤害，附带灼烧效果"},
        "passive": {"name": "四世三公", "description": "在场时，己方群雄武将攻击力提升10%"},
        "story": "字公路，袁绍之弟。淮南称帝，建号仲家。骄奢淫逸，众叛亲离，呕血而亡。"
    },
    "陶谦": {
        "faction": "qun", "quality": "rare", "element": "风",
        "title": "徐州牧", "weapon_type": "剑",
        "base": {"attack": 170, "defense": 230, "health": 1000, "speed": 68, "critical": 0.03},
        "growth": {"attack": 15, "defense": 20, "health": 100, "speed": 5, "critical": 0.001},
        "skill": {"name": "三让徐州", "damage": 30, "element": "风", "type": "heal",
                  "description": "造成30%伤害，恢复己方全体10%生命"},
        "ultimate": {"name": "丹阳兵", "damage": 100, "element": "风", "type": "normal",
                     "description": "对全体造成100%伤害，提升己方全体15%速度2回合"},
        "passive": {"name": "仁厚", "description": "受到攻击时，10%概率为攻击者恢复5%生命"},
        "story": "字恭祖，徐州牧。三让徐州于刘备。黄巾之乱时保境安民，丹阳兵闻名天下。"
    },
    "孔融": {
        "faction": "qun", "quality": "rare", "element": "风",
        "title": "孔北海", "weapon_type": "书",
        "base": {"attack": 170, "defense": 180, "health": 850, "speed": 75, "critical": 0.04},
        "growth": {"attack": 15, "defense": 16, "health": 85, "speed": 6, "critical": 0.002},
        "skill": {"name": "名士之风", "damage": 32, "element": "风", "type": "debuff_attack",
                  "description": "造成32%伤害，降低目标15%攻击2回合"},
        "ultimate": {"name": "让梨", "damage": 95, "element": "风", "type": "buff_all",
                     "description": "对敌方造成95%伤害，提升己方全体20%防御2回合"},
        "passive": {"name": "建安七子", "description": "每回合恢复己方智力型武将8%生命"},
        "story": "字文举，孔子二十世孙。北海相，'建安七子'之首。让梨传佳话，因触怒曹操被杀。"
    },
    "张绣": {
        "faction": "qun", "quality": "epic", "element": "风",
        "title": "北地枪王", "weapon_type": "枪",
        "base": {"attack": 300, "defense": 220, "health": 1050, "speed": 95, "critical": 0.12},
        "growth": {"attack": 27, "defense": 19, "health": 105, "speed": 8, "critical": 0.005},
        "skill": {"name": "百鸟朝凤", "damage": 48, "element": "风", "type": "pierce",
                  "description": "造成48%伤害，无视25%防御"},
        "ultimate": {"name": "宛城之乱", "damage": 145, "element": "风", "type": "assassin",
                     "description": "对单体造成145%伤害，对曹营武将额外造成40%伤害"},
        "passive": {"name": "胡车儿", "description": "速度提升15%，暴击率提升8%"},
        "story": "张济之侄，北地枪王。宛城之乱杀曹操长子曹昂、爱将典韦。后降曹，从征乌桓途中身亡。"
    },
    "颜良文丑": {
        "faction": "qun", "quality": "epic", "element": "土",
        "title": "河北双雄", "weapon_type": "斧",
        "base": {"attack": 320, "defense": 260, "health": 1200, "speed": 80, "critical": 0.10},
        "growth": {"attack": 28, "defense": 22, "health": 120, "speed": 6, "critical": 0.004},
        "skill": {"name": "勇冠三军", "damage": 50, "element": "土", "type": "normal",
                  "description": "造成50%伤害，对关羽额外受到50%伤害（与技能描述绑定）"},
        "ultimate": {"name": "河北之雄", "damage": 150, "element": "土", "type": "aoe",
                     "description": "对敌方前排造成150%伤害，附带15%减速"},
        "passive": {"name": "双雄合璧", "description": "在场时，每有一个群雄武将，攻击力提升8%"},
        "story": "袁绍麾下两员猛将。颜良文丑，勇冠三军，为袁绍统一河北立下赫赫战功。皆死于关羽刀下。"
    },

    # ==================== 蜀国补充 ====================
    "糜竺": {
        "faction": "shu", "quality": "rare", "element": "风",
        "title": "安汉将军", "weapon_type": "书",
        "base": {"attack": 170, "defense": 200, "health": 950, "speed": 70, "critical": 0.04},
        "growth": {"attack": 15, "defense": 18, "health": 95, "speed": 5, "critical": 0.002},
        "skill": {"name": "巨富资助", "damage": 30, "element": "风", "type": "buff_all",
                  "description": "造成30%伤害，提升己方全体15%攻击2回合"},
        "ultimate": {"name": "妹嫁皇叔", "damage": 95, "element": "风", "type": "heal",
                     "description": "对敌方造成95%伤害，恢复己方全体20%生命"},
        "passive": {"name": "散财养士", "description": "回合开始时，恢复己方全体5%生命"},
        "story": "字子仲，徐州巨富。妹嫁刘备即糜夫人。倾家荡产资助刘备，官至安汉将军，位在诸葛亮之上。"
    },
    "孙乾": {
        "faction": "shu", "quality": "rare", "element": "风",
        "title": "秉忠将军", "weapon_type": "书",
        "base": {"attack": 160, "defense": 180, "health": 850, "speed": 72, "critical": 0.03},
        "growth": {"attack": 14, "defense": 16, "health": 85, "speed": 5, "critical": 0.001},
        "skill": {"name": "外交之才", "damage": 28, "element": "风", "type": "debuff_attack",
                  "description": "造成28%伤害，降低目标15%攻击2回合"},
        "ultimate": {"name": "联吴抗曹", "damage": 90, "element": "风", "type": "buff_all",
                     "description": "对敌方造成90%伤害，提升己方全体15%速度2回合"},
        "passive": {"name": "忠贞", "description": "生命低于30%时，受到伤害降低25%"},
        "story": "字公祐，刘备早期谋士。多次出使外交，促成刘备与各诸侯联盟。"
    },
    "邓芝": {
        "faction": "shu", "quality": "rare", "element": "风",
        "title": "车骑将军", "weapon_type": "剑",
        "base": {"attack": 210, "defense": 210, "health": 950, "speed": 80, "critical": 0.05},
        "growth": {"attack": 19, "defense": 19, "health": 95, "speed": 6, "critical": 0.002},
        "skill": {"name": "使吴之命", "damage": 35, "element": "风", "type": "normal",
                  "description": "造成35%伤害，附带10%减速"},
        "ultimate": {"name": "蜀吴同盟", "damage": 110, "element": "风", "type": "buff_all",
                     "description": "对敌方造成110%伤害，恢复己方全体15%生命"},
        "passive": {"name": "刚直", "description": "受到暴击时，10%概率反弹50%伤害"},
        "story": "字伯苗，蜀汉重臣。出使东吴重建联盟，孙权重之。官至车骑将军。"
    },
    "张翼": {
        "faction": "shu", "quality": "rare", "element": "土",
        "title": "左车骑将军", "weapon_type": "枪",
        "base": {"attack": 230, "defense": 220, "health": 1000, "speed": 78, "critical": 0.06},
        "growth": {"attack": 21, "defense": 19, "health": 100, "speed": 6, "critical": 0.002},
        "skill": {"name": "北伐先锋", "damage": 38, "element": "土", "type": "normal",
                  "description": "造成38%伤害，提升自身10%攻击2回合"},
        "ultimate": {"name": "蜀汉末将", "damage": 115, "element": "土", "type": "aoe",
                     "description": "对敌方前排造成115%伤害"},
        "passive": {"name": "忠义", "description": "诸葛亮在场时，全属性提升10%"},
        "story": "字伯恭，蜀汉后期主将。多次随姜维北伐。蜀亡后降钟会，死于乱军。"
    },

    # ==================== 魏国补充 ====================
    "曹真": {
        "faction": "wei", "quality": "epic", "element": "土",
        "title": "大将军", "weapon_type": "枪",
        "base": {"attack": 270, "defense": 260, "health": 1150, "speed": 80, "critical": 0.06},
        "growth": {"attack": 24, "defense": 23, "health": 115, "speed": 6, "critical": 0.002},
        "skill": {"name": "镇军之策", "damage": 42, "element": "土", "type": "shield",
                  "description": "造成42%伤害，为自身添加15%生命护盾"},
        "ultimate": {"name": "拒亮之策", "damage": 130, "element": "土", "type": "debuff_all",
                     "description": "对全体造成130%伤害，降低目标15%攻击2回合"},
        "passive": {"name": "宗室", "description": "受到伤害时，10%概率反弹25%伤害"},
        "story": "字子丹，曹魏宗室名将。多次抵御诸葛亮北伐。识破诸葛亮诈退之计，病亡于军中。"
    },
    "曹休": {
        "faction": "wei", "quality": "epic", "element": "风",
        "title": "千里驹", "weapon_type": "枪",
        "base": {"attack": 280, "defense": 220, "health": 1050, "speed": 92, "critical": 0.10},
        "growth": {"attack": 25, "defense": 19, "health": 105, "speed": 7, "critical": 0.004},
        "skill": {"name": "千里奔袭", "damage": 46, "element": "风", "type": "charge",
                  "description": "造成46%伤害，速度高于目标时额外造成15%伤害"},
        "ultimate": {"name": "东线督帅", "damage": 135, "element": "风", "type": "multi_hit",
                     "description": "对随机敌人发动3次45%伤害"},
        "passive": {"name": "曹家千里驹", "description": "速度提升10%，暴击率提升5%"},
        "story": "字文烈，曹魏宗室。'千里驹'之称，镇守东线。石亭之败后背痈发作而亡。"
    },
    "郝昭": {
        "faction": "wei", "quality": "epic", "element": "土",
        "title": "陈仓守将", "weapon_type": "弓",
        "base": {"attack": 240, "defense": 290, "health": 1100, "speed": 70, "critical": 0.05},
        "growth": {"attack": 21, "defense": 25, "health": 110, "speed": 5, "critical": 0.002},
        "skill": {"name": "陈仓坚守", "damage": 38, "element": "土", "type": "shield",
                  "description": "造成38%伤害，为自身添加20%生命护盾"},
        "ultimate": {"name": "火箭守城", "damage": 125, "element": "火", "type": "aoe",
                     "description": "对敌方前排造成125%伤害，附带灼烧效果"},
        "passive": {"name": "铁壁", "description": "受到远程攻击时，伤害降低20%"},
        "story": "字伯道，曹魏名将。陈仓以千余人抵御诸葛亮数万大军数十日，名震天下。病亡于战后。"
    },
    "郭淮": {
        "faction": "wei", "quality": "epic", "element": "土",
        "title": "雍州刺史", "weapon_type": "枪",
        "base": {"attack": 250, "defense": 250, "health": 1100, "speed": 80, "critical": 0.05},
        "growth": {"attack": 22, "defense": 22, "health": 110, "speed": 6, "critical": 0.002},
        "skill": {"name": "雍凉镇守", "damage": 40, "element": "土", "type": "normal",
                  "description": "造成40%伤害，附带10%减速"},
        "ultimate": {"name": "西线统帅", "damage": 125, "element": "土", "type": "aoe",
                     "description": "对敌方前排造成125%伤害，降低20%攻击2回合"},
        "passive": {"name": "稳如泰山", "description": "生命低于50%时，受到伤害降低20%"},
        "story": "字伯济，曹魏西线统帅。镇守雍凉三十余年，抵御蜀汉北伐。"
    },
    "夏侯霸": {
        "faction": "wei", "quality": "epic", "element": "火",
        "title": "右将军", "weapon_type": "枪",
        "base": {"attack": 290, "defense": 220, "health": 1050, "speed": 88, "critical": 0.10},
        "growth": {"attack": 26, "defense": 19, "health": 105, "speed": 7, "critical": 0.004},
        "skill": {"name": "夏侯枪法", "damage": 46, "element": "火", "type": "normal",
                  "description": "造成46%伤害，15%概率灼烧目标"},
        "ultimate": {"name": "降蜀之将", "damage": 140, "element": "火", "type": "aoe",
                     "description": "对全体造成140%伤害，附带灼烧效果"},
        "passive": {"name": "逃亡之路", "description": "生命低于30%时，速度提升30%"},
        "story": "字仲权，夏侯渊之子。司马氏篡魏后逃亡蜀汉，姜维重之。后随姜维北伐。"
    },

    # ==================== 吴国补充 ====================
    "程普": {
        "faction": "wu", "quality": "epic", "element": "火",
        "title": "程公", "weapon_type": "矛",
        "base": {"attack": 270, "defense": 250, "health": 1150, "speed": 78, "critical": 0.06},
        "growth": {"attack": 24, "defense": 22, "health": 115, "speed": 6, "critical": 0.002},
        "skill": {"name": "老将之威", "damage": 42, "element": "火", "type": "normal",
                  "description": "造成42%伤害，附带10%灼烧"},
        "ultimate": {"name": "江东元勋", "damage": 130, "element": "火", "type": "aoe",
                     "description": "对敌方前排造成130%伤害，附带灼烧效果"},
        "passive": {"name": "副都督", "description": "每回合恢复5%生命，前2回合减伤15%"},
        "story": "字德谋，江东三代老臣。右都督，赤壁之战主战派之一。使一条铁脊蛇矛。"
    },
    "祖茂": {
        "faction": "wu", "quality": "rare", "element": "土",
        "title": "双刀将", "weapon_type": "刀",
        "base": {"attack": 240, "defense": 200, "health": 950, "speed": 88, "critical": 0.08},
        "growth": {"attack": 21, "defense": 18, "health": 95, "speed": 7, "critical": 0.003},
        "skill": {"name": "双刀流", "damage": 40, "element": "土", "type": "multi_hit",
                  "description": "造成2次20%伤害"},
        "ultimate": {"name": "替主脱险", "damage": 120, "element": "土", "type": "sacrifice",
                     "description": "对单体造成120%伤害，为孙坚挡下一次攻击"},
        "passive": {"name": "忠勇", "description": "孙坚在场时，攻击力提升15%"},
        "story": "字大荣，孙坚爱将。使双刀。汜水关前以红头巾引开华雄，为孙坚脱险，力战而亡。"
    },
    "蒋钦": {
        "faction": "wu", "quality": "rare", "element": "水",
        "title": "荡寇将军", "weapon_type": "弓",
        "base": {"attack": 230, "defense": 200, "health": 950, "speed": 85, "critical": 0.08},
        "growth": {"attack": 21, "defense": 18, "health": 95, "speed": 7, "critical": 0.003},
        "skill": {"name": "水战精锐", "damage": 40, "element": "水", "type": "normal",
                  "description": "造成40%伤害，对火属性目标额外造成20%伤害"},
        "ultimate": {"name": "濡须督", "damage": 120, "element": "水", "type": "aoe",
                     "description": "对敌方前排造成120%伤害，附带10%减速"},
        "passive": {"name": "节俭", "description": "受到伤害时，10%概率获得10怒气"},
        "story": "字公奕，江东名将。与周泰、陈武齐名。水战精锐，镇守濡须口。"
    },
    "徐盛": {
        "faction": "wu", "quality": "epic", "element": "土",
        "title": "安东将军", "weapon_type": "弓",
        "base": {"attack": 260, "defense": 240, "health": 1050, "speed": 80, "critical": 0.08},
        "growth": {"attack": 23, "defense": 21, "health": 105, "speed": 6, "critical": 0.003},
        "skill": {"name": "疑城之计", "damage": 42, "element": "土", "type": "shield",
                  "description": "造成42%伤害，为己方全体添加10%生命护盾"},
        "ultimate": {"name": "百里疑城", "damage": 130, "element": "土", "type": "debuff_all",
                     "description": "对全体造成130%伤害，降低目标20%攻击2回合"},
        "passive": {"name": "坚守", "description": "受到远程攻击时，伤害降低15%"},
        "story": "字文向，东吴名将。曹丕伐吴时筑百里疑城退敌。'魏军惧而退'，名震江东。"
    },
    "诸葛瑾": {
        "faction": "wu", "quality": "epic", "element": "水",
        "title": "大将军", "weapon_type": "书",
        "base": {"attack": 200, "defense": 230, "health": 1100, "speed": 78, "critical": 0.04},
        "growth": {"attack": 18, "defense": 20, "health": 110, "speed": 6, "critical": 0.002},
        "skill": {"name": "外交之才", "damage": 35, "element": "水", "type": "debuff_attack",
                  "description": "造成35%伤害，降低目标15%攻击2回合"},
        "ultimate": {"name": "吴蜀同盟", "damage": 110, "element": "水", "type": "buff_all",
                     "description": "对敌方造成110%伤害，恢复己方全体15%生命"},
        "passive": {"name": "温厚", "description": "回合结束时，恢复己方全体5%生命"},
        "story": "字子瑜，诸葛亮之兄，东吴重臣。孙权称帝后官至大将军。为人温厚诚信，深受信任。"
    },
    "张昭": {
        "faction": "wu", "quality": "epic", "element": "风",
        "title": "张公", "weapon_type": "书",
        "base": {"attack": 180, "defense": 200, "health": 1000, "speed": 75, "critical": 0.04},
        "growth": {"attack": 16, "defense": 18, "health": 100, "speed": 6, "critical": 0.002},
        "skill": {"name": "名士之辩", "damage": 32, "element": "风", "type": "debuff_attack",
                  "description": "造成32%伤害，降低目标20%攻击2回合"},
        "ultimate": {"name": "内政之才", "damage": 100, "element": "风", "type": "buff_all",
                     "description": "对敌方造成100%伤害，提升己方全体20%防御2回合"},
        "passive": {"name": "托孤之臣", "description": "孙权在场时，全属性提升10%"},
        "story": "字子布，东吴重臣。孙策托孤之臣，'内事不决问张昭'。赤壁主降派代表。"
    },
    "顾雍": {
        "faction": "wu", "quality": "epic", "element": "土",
        "title": "顾丞相", "weapon_type": "书",
        "base": {"attack": 170, "defense": 220, "health": 1050, "speed": 72, "critical": 0.03},
        "growth": {"attack": 15, "defense": 19, "health": 105, "speed": 5, "critical": 0.001},
        "skill": {"name": "丞相之策", "damage": 32, "element": "土", "type": "buff_all",
                  "description": "造成32%伤害，提升己方全体15%防御2回合"},
        "ultimate": {"name": "举国同心", "damage": 100, "element": "土", "type": "buff_all",
                     "description": "对敌方造成100%伤害，恢复己方全体15%生命"},
        "passive": {"name": "稳重", "description": "受到伤害时，10%概率获得护盾"},
        "story": "字元叹，东吴丞相。蔡邕弟子，为相十九年，举措适当。'顾雍不言，言必有中'。"
    },
    "曹纯": {
        "faction": "wei", "quality": "epic", "element": "风",
        "title": "虎豹骑督", "weapon_type": "枪",
        "base": {"attack": 270, "defense": 220, "health": 1050, "speed": 95, "critical": 0.10},
        "growth": {"attack": 24, "defense": 19, "health": 105, "speed": 8, "critical": 0.004},
        "skill": {"name": "虎豹冲锋", "damage": 46, "element": "风", "type": "charge",
                  "description": "造成46%伤害，速度高于目标时额外造成15%伤害"},
        "ultimate": {"name": "虎豹骑突袭", "damage": 140, "element": "风", "type": "multi_hit",
                     "description": "对随机敌人发动3次47%伤害"},
        "passive": {"name": "虎豹督", "description": "速度提升15%，暴击率提升5%"},
        "story": "字子和，曹仁之弟。统领曹魏精锐虎豹骑，南皮斩袁谭，白狼山擒蹋顿。"
    },

    # ==================== 普通武将扩充（common品质） ====================
    "潘凤": {
        "faction": "qun", "quality": "common", "element": "土",
        "title": "无双上将", "weapon_type": "斧",
        "base": {"attack": 150, "defense": 120, "health": 600, "speed": 60, "critical": 0.05},
        "growth": {"attack": 12, "defense": 10, "health": 60, "speed": 4, "critical": 0.002},
        "skill": {"name": "上将之威", "damage": 25, "element": "土", "type": "normal",
                  "description": "造成25%伤害"},
        "ultimate": {"name": "无双", "damage": 80, "element": "土", "type": "normal",
                     "description": "对单体造成80%伤害"},
        "passive": {"name": "我上将潘凤", "description": "无特殊效果"},
        "story": "韩馥麾下'无双上将'，被华雄斩杀。'吾有上将潘凤，可斩华雄'，千古笑谈。"
    },
    "邢道荣": {
        "faction": "qun", "quality": "common", "element": "土",
        "title": "零陵上将", "weapon_type": "斧",
        "base": {"attack": 140, "defense": 130, "health": 580, "speed": 58, "critical": 0.04},
        "growth": {"attack": 11, "defense": 11, "health": 58, "speed": 4, "critical": 0.002},
        "skill": {"name": "吹牛", "damage": 22, "element": "土", "type": "normal",
                  "description": "造成22%伤害，自身攻击力下降5%"},
        "ultimate": {"name": "我乃邢道荣", "damage": 75, "element": "土", "type": "normal",
                     "description": "对单体造成75%伤害"},
        "passive": {"name": "虚张声势", "description": "生命低于50%时，速度降低10%"},
        "story": "零陵刘度部将。'我乃零陵上将邢道荣'，被诸葛亮智擒，诈降后欲反，被赵云一枪刺死。"
    },
    "刘三刀": {
        "faction": "qun", "quality": "common", "element": "火",
        "title": "三刀流", "weapon_type": "刀",
        "base": {"attack": 160, "defense": 100, "health": 550, "speed": 70, "critical": 0.08},
        "growth": {"attack": 13, "defense": 8, "health": 55, "speed": 5, "critical": 0.003},
        "skill": {"name": "三刀流", "damage": 28, "element": "火", "type": "multi_hit",
                  "description": "造成3次10%伤害"},
        "ultimate": {"name": "我部将刘三刀", "damage": 85, "element": "火", "type": "multi_hit",
                     "description": "对单体造成3次28%伤害"},
        "passive": {"name": "部将", "description": "暴击率提升5%"},
        "story": "网络三国梗人物。'我部将刘三刀，三刀之内必斩吕布'，结果被吕布一戟刺死。"
    },
    "俞涉": {
        "faction": "qun", "quality": "common", "element": "土",
        "title": "骁将", "weapon_type": "枪",
        "base": {"attack": 140, "defense": 110, "health": 570, "speed": 62, "critical": 0.04},
        "growth": {"attack": 11, "defense": 9, "health": 57, "speed": 4, "critical": 0.002},
        "skill": {"name": "骁勇", "damage": 23, "element": "土", "type": "normal",
                  "description": "造成23%伤害"},
        "ultimate": {"name": "拼死一战", "damage": 78, "element": "土", "type": "normal",
                     "description": "对单体造成78%伤害"},
        "passive": {"name": "忠勇", "description": "无特殊效果"},
        "story": "袁术麾下骁将，被华雄斩杀。'吾有上将俞涉'，不到三回合被斩。"
    },
    "管亥": {
        "faction": "qun", "quality": "common", "element": "土",
        "title": "黄巾将", "weapon_type": "刀",
        "base": {"attack": 165, "defense": 130, "health": 650, "speed": 60, "critical": 0.05},
        "growth": {"attack": 13, "defense": 11, "health": 65, "speed": 4, "critical": 0.002},
        "skill": {"name": "黄巾乱", "damage": 26, "element": "土", "type": "normal",
                  "description": "造成26%伤害"},
        "ultimate": {"name": "蛾贼", "damage": 82, "element": "土", "type": "aoe",
                     "description": "对敌方前排造成82%伤害"},
        "passive": {"name": "黄巾", "description": "对官军武将额外造成5%伤害"},
        "story": "黄巾军首领之一，统十万众寇北海。太史慈突围求援刘备，管亥被关羽所斩。"
    },
    "裴元绍": {
        "faction": "qun", "quality": "common", "element": "土",
        "title": "黄巾将", "weapon_type": "矛",
        "base": {"attack": 145, "defense": 120, "health": 600, "speed": 62, "critical": 0.04},
        "growth": {"attack": 12, "defense": 10, "health": 60, "speed": 4, "critical": 0.002},
        "skill": {"name": "落草", "damage": 23, "element": "土", "type": "normal",
                  "description": "造成23%伤害"},
        "ultimate": {"name": "劫掠", "damage": 78, "element": "土", "type": "normal",
                     "description": "对单体造成78%伤害"},
        "passive": {"name": "山贼", "description": "击杀目标时，10%概率获得额外金币"},
        "story": "原黄巾军，后落草卧牛山。与赵云冲突，被误杀。"
    },
    "麴义": {
        "faction": "qun", "quality": "common", "element": "土",
        "title": "先登", "weapon_type": "弓",
        "base": {"attack": 170, "defense": 110, "health": 580, "speed": 65, "critical": 0.08},
        "growth": {"attack": 14, "defense": 9, "health": 58, "speed": 5, "critical": 0.003},
        "skill": {"name": "先登死士", "damage": 28, "element": "土", "type": "normal",
                  "description": "造成28%伤害，对骑兵额外造成15%伤害"},
        "ultimate": {"name": "八百先登", "damage": 88, "element": "土", "type": "aoe",
                     "description": "对敌方前排造成88%伤害"},
        "passive": {"name": "先登", "description": "对骑兵武将额外造成10%伤害"},
        "story": "袁绍麾下大将。先登营大破公孙瓒白马义从。后因恃功骄纵被袁绍所杀。"
    },

    # ==================== 蜀国普通武将 ====================
    "刘封": {
        "faction": "shu", "quality": "common", "element": "土",
        "title": "副军师", "weapon_type": "剑",
        "base": {"attack": 170, "defense": 140, "health": 650, "speed": 70, "critical": 0.05},
        "growth": {"attack": 14, "defense": 12, "health": 65, "speed": 5, "critical": 0.002},
        "skill": {"name": "副军", "damage": 26, "element": "土", "type": "normal",
                  "description": "造成26%伤害"},
        "ultimate": {"name": "敢死", "damage": 85, "element": "土", "type": "normal",
                     "description": "对单体造成85%伤害，自身受到10%反伤"},
        "passive": {"name": "养子", "description": "刘备在场时，全属性提升5%"},
        "story": "刘备养子。有武勇，不救关羽致其败亡。诸葛亮虑其刚猛难御，劝刘备赐死。"
    },
    "孟达": {
        "faction": "shu", "quality": "common", "element": "风",
        "title": "反复", "weapon_type": "剑",
        "base": {"attack": 160, "defense": 130, "health": 620, "speed": 70, "critical": 0.05},
        "growth": {"attack": 13, "defense": 11, "health": 62, "speed": 5, "critical": 0.002},
        "skill": {"name": "反复无常", "damage": 25, "element": "风", "type": "normal",
                  "description": "造成25%伤害，10%概率自身眩晕1回合"},
        "ultimate": {"name": "叛降", "damage": 82, "element": "风", "type": "normal",
                     "description": "对单体造成82%伤害"},
        "passive": {"name": "三姓家奴", "description": "每次攻击有5%概率使自身混乱"},
        "story": "原刘璋部将，迎刘备入蜀。关羽败亡后降魏，又欲降蜀，被司马懿斩杀。"
    },
    "糜芳": {
        "faction": "shu", "quality": "common", "element": "风",
        "title": "南郡太守", "weapon_type": "剑",
        "base": {"attack": 130, "defense": 130, "health": 600, "speed": 60, "critical": 0.03},
        "growth": {"attack": 11, "defense": 11, "health": 60, "speed": 4, "critical": 0.001},
        "skill": {"name": "怯懦", "damage": 22, "element": "风", "type": "normal",
                  "description": "造成22%伤害"},
        "ultimate": {"name": "叛变", "damage": 75, "element": "风", "type": "debuff_attack",
                     "description": "对单体造成75%伤害，降低目标15%攻击"},
        "passive": {"name": "背主", "description": "受到伤害时，10%概率使己方随机武将减防10%"},
        "story": "糜竺之弟，刘备妻弟。关羽麾下镇守江陵，因惧关羽追责降吴，致关羽败亡。后回蜀被罚。"
    },
    "傅士仁": {
        "faction": "shu", "quality": "common", "element": "风",
        "title": "公安守将", "weapon_type": "剑",
        "base": {"attack": 135, "defense": 125, "health": 590, "speed": 60, "critical": 0.03},
        "growth": {"attack": 11, "defense": 10, "health": 59, "speed": 4, "critical": 0.001},
        "skill": {"name": "怯战", "damage": 22, "element": "风", "type": "normal",
                  "description": "造成22%伤害"},
        "ultimate": {"name": "献城", "damage": 75, "element": "风", "type": "normal",
                     "description": "对单体造成75%伤害"},
        "passive": {"name": "背义", "description": "受到伤害时，10%概率降低自身10%防御"},
        "story": "关羽麾下公安守将。与糜芳一同降吴，致关羽败走麦城。后回蜀被罚。"
    },

    # ==================== 魏国普通武将 ====================
    "夏侯杰": {
        "faction": "wei", "quality": "common", "element": "土",
        "title": "曹将", "weapon_type": "枪",
        "base": {"attack": 130, "defense": 110, "health": 560, "speed": 55, "critical": 0.02},
        "growth": {"attack": 11, "defense": 9, "health": 56, "speed": 4, "critical": 0.001},
        "skill": {"name": "胆小", "damage": 20, "element": "土", "type": "normal",
                  "description": "造成20%伤害"},
        "ultimate": {"name": "惊吓", "damage": 70, "element": "土", "type": "normal",
                     "description": "对单体造成70%伤害"},
        "passive": {"name": "胆寒", "description": "受到暴击时，10%概率自身眩晕1回合"},
        "story": "曹操部将。长坂坡被张飞一声怒吼惊得肝胆俱裂，坠马而亡。"
    },
    "秦琪": {
        "faction": "wei", "quality": "common", "element": "土",
        "title": "守关将", "weapon_type": "刀",
        "base": {"attack": 155, "defense": 120, "health": 590, "speed": 62, "critical": 0.04},
        "growth": {"attack": 12, "defense": 10, "health": 59, "speed": 4, "critical": 0.002},
        "skill": {"name": "守关", "damage": 24, "element": "土", "type": "normal",
                  "description": "造成24%伤害"},
        "ultimate": {"name": "拦路", "damage": 78, "element": "土", "type": "normal",
                     "description": "对单体造成78%伤害"},
        "passive": {"name": "无礼", "description": "无特殊效果"},
        "story": "夏侯惇部将，守黄河渡口。被关羽过五关斩六将时所斩。"
    },
    "孔秀": {
        "faction": "wei", "quality": "common", "element": "土",
        "title": "东岭关守将", "weapon_type": "枪",
        "base": {"attack": 150, "defense": 115, "health": 570, "speed": 60, "critical": 0.03},
        "growth": {"attack": 12, "defense": 10, "health": 57, "speed": 4, "critical": 0.001},
        "skill": {"name": "守关", "damage": 23, "element": "土", "type": "normal",
                  "description": "造成23%伤害"},
        "ultimate": {"name": "阻拦", "damage": 76, "element": "土", "type": "normal",
                     "description": "对单体造成76%伤害"},
        "passive": {"name": "执拗", "description": "无特殊效果"},
        "story": "曹操部将，守东岭关。关羽千里走单骑时第一关所斩之将。"
    },

    # ==================== 吴国普通武将 ====================
    "贾华": {
        "faction": "wu", "quality": "common", "element": "土",
        "title": "吴将", "weapon_type": "刀",
        "base": {"attack": 145, "defense": 120, "health": 580, "speed": 62, "critical": 0.04},
        "growth": {"attack": 12, "defense": 10, "health": 58, "speed": 4, "critical": 0.002},
        "skill": {"name": "护卫", "damage": 23, "element": "土", "type": "normal",
                  "description": "造成23%伤害"},
        "ultimate": {"name": "决死", "damage": 76, "element": "土", "type": "normal",
                     "description": "对单体造成76%伤害"},
        "passive": {"name": "忠勇", "description": "无特殊效果"},
        "story": "东吴部将。刘备入吴招亲时，与丁奉一同奉周瑜之命埋伏，欲杀刘备，为孙权所阻。"
    },
    "马忠": {
        "faction": "wu", "quality": "common", "element": "土",
        "title": "擒羽将", "weapon_type": "弓",
        "base": {"attack": 155, "defense": 110, "health": 560, "speed": 65, "critical": 0.06},
        "growth": {"attack": 13, "defense": 9, "health": 56, "speed": 5, "critical": 0.002},
        "skill": {"name": "埋伏", "damage": 25, "element": "土", "type": "normal",
                  "description": "造成25%伤害，10%概率眩晕目标"},
        "ultimate": {"name": "擒王", "damage": 80, "element": "土", "type": "normal",
                     "description": "对单体造成80%伤害"},
        "passive": {"name": "伏击", "description": "暴击率提升5%"},
        "story": "潘璋部将。在临沮擒获关羽父子。后为糜芳、傅士仁所刺杀。"
    },
    "范疆": {
        "faction": "wu", "quality": "common", "element": "土",
        "title": "张飞部将", "weapon_type": "刀",
        "base": {"attack": 135, "defense": 110, "health": 560, "speed": 60, "critical": 0.03},
        "growth": {"attack": 11, "defense": 9, "health": 56, "speed": 4, "critical": 0.001},
        "skill": {"name": "怨望", "damage": 22, "element": "土", "type": "normal",
                  "description": "造成22%伤害"},
        "ultimate": {"name": "暗杀", "damage": 75, "element": "土", "type": "assassin",
                     "description": "对单体造成75%伤害，对睡眠/眩晕目标必暴击"},
        "passive": {"name": "叛逆", "description": "对己方张飞额外造成30%伤害"},
        "story": "张飞部将。因限期完不成白旗白甲之命，与张达夜刺张飞，投奔东吴。"
    },
    "张达": {
        "faction": "wu", "quality": "common", "element": "土",
        "title": "张飞部将", "weapon_type": "刀",
        "base": {"attack": 140, "defense": 115, "health": 570, "speed": 60, "critical": 0.03},
        "growth": {"attack": 12, "defense": 10, "health": 57, "speed": 4, "critical": 0.001},
        "skill": {"name": "怨怒", "damage": 23, "element": "土", "type": "normal",
                  "description": "造成23%伤害"},
        "ultimate": {"name": "夜刺", "damage": 78, "element": "土", "type": "assassin",
                     "description": "对单体造成78%伤害，对睡眠/眩晕目标必暴击"},
        "passive": {"name": "叛逆", "description": "对己方张飞额外造成30%伤害"},
        "story": "张飞部将。与范疆夜刺张飞，携张飞首级投奔东吴。后孙权送还，被张苞所杀。"
    }
}

# ============================================================
# 武将羁绊扩展
# ============================================================
HERO_BONDS_EXPANDED = {
    "taoyuan": {
        "name": "桃园结义", "heroes": ["刘备", "关羽", "张飞"],
        "effect": {"type": "damage_bonus", "value": 0.3, "description": "攻击+30%"},
        "description": "桃园三结义，不求同年同月同日生，但求同年同月同日死"
    },
    "five_tigers": {
        "name": "五虎上将", "heroes": ["关羽", "张飞", "赵云", "马超", "黄忠"],
        "effect": {"type": "crit_bonus", "value": 0.2, "description": "暴击+20%"},
        "description": "蜀汉五虎上将，天下无敌"
    },
    "liang_zhou": {
        "name": "卧龙凤雏", "heroes": ["诸葛亮", "庞统"],
        "effect": {"type": "skill_damage", "value": 0.35, "description": "技能伤害+35%"},
        "description": "卧龙凤雏，得一可安天下"
    },
    "c_brothers": {
        "name": "曹氏父子", "heroes": ["曹操", "曹丕"],
        "effect": {"type": "hp_bonus", "value": 0.25, "description": "生命+25%"},
        "description": "曹家父子，文武双全"
    },
    "jiang_dong": {
        "name": "江东二乔", "heroes": ["大乔", "小乔"],
        "effect": {"type": "heal_bonus", "value": 0.3, "description": "治疗效果+30%"},
        "description": "江东二乔，国色天香"
    },
    "sun_family": {
        "name": "孙氏父子", "heroes": ["孙坚", "孙策", "孙权"],
        "effect": {"type": "speed_bonus", "value": 0.25, "description": "速度+25%"},
        "description": "江东孙氏，猛虎一脉"
    },
    "wei_five": {
        "name": "五子良将", "heroes": ["张辽", "徐晃", "张郃", "于禁", "乐进"],
        "effect": {"type": "all_bonus", "value": 0.15, "description": "全属性+15%"},
        "description": "魏国五子良将，战功赫赫"
    },
    "sima_family": {
        "name": "司马家族", "heroes": ["司马懿", "张春华", "曹丕"],
        "effect": {"type": "skill_damage", "value": 0.25, "description": "技能伤害+25%"},
        "description": "司马家族，权倾天下"
    },
    "huo_shao": {
        "name": "火烧赤壁", "heroes": ["周瑜", "黄盖", "诸葛亮"],
        "effect": {"type": "fire_damage", "value": 0.4, "description": "火属性伤害+40%"},
        "description": "赤壁之战，火烧曹军百万"
    },
    "hebei_four": {
        "name": "河北四庭柱", "heroes": ["颜良", "文丑"],
        "effect": {"type": "attack_bonus", "value": 0.2, "description": "攻击+20%"},
        "description": "袁绍麾下四大将"
    },
    "nv_jiang": {
        "name": "巾帼英雄", "heroes": ["祝融", "鲍三娘", "貂蝉"],
        "effect": {"type": "dodge_bonus", "value": 0.15, "description": "闪避+15%"},
        "description": "巾帼不让须眉"
    },
    "shen_yi": {
        "name": "神医", "heroes": ["华佗", "黄月英"],
        "effect": {"type": "heal_bonus", "value": 0.4, "description": "治疗效果+40%"},
        "description": "神医与机关巧匠"
    },
    "lv_bu_group": {
        "name": "吕布势力", "heroes": ["吕布", "貂蝉", "陈宫", "高顺"],
        "effect": {"type": "attack_bonus", "value": 0.25, "description": "攻击+25%"},
        "description": "飞将势力，天下无双"
    },
    "qi_xiong": {
        "name": "群雄逐鹿", "heroes": ["董卓", "袁绍", "吕布"],
        "effect": {"type": "damage_reduction", "value": 0.1, "description": "伤害减免+10%"},
        "description": "群雄割据，逐鹿中原"
    },
    "shu_later": {
        "name": "蜀汉后期", "heroes": ["姜维", "廖化", "王平"],
        "effect": {"type": "defense_bonus", "value": 0.2, "description": "防御+20%"},
        "description": "蜀汉后期栋梁"
    },
    "guan_family": {
        "name": "关氏一族", "heroes": ["关羽", "关平", "关兴", "关索"],
        "effect": {"type": "crit_damage", "value": 0.3, "description": "暴击伤害+30%"},
        "description": "关家刀法，代代相传"
    },
    "zhang_family": {
        "name": "张氏父子", "heroes": ["张飞", "张苞"],
        "effect": {"type": "hp_bonus", "value": 0.2, "description": "生命+20%"},
        "description": "猛虎一脉，父传子承"
    },
    "nan_zheng": {
        "name": "南征军团", "heroes": ["诸葛亮", "魏延", "关索", "鲍三娘", "严颜"],
        "effect": {"type": "speed_bonus", "value": 0.15, "description": "速度+15%"},
        "description": "诸葛亮南征军团"
    },
    "sima_three": {
        "name": "司马三父子", "heroes": ["司马懿", "司马师", "司马昭"],
        "effect": {"type": "skill_damage", "value": 0.3, "description": "技能伤害+30%"},
        "description": "司马父子三人，权倾魏室"
    },
    "jin_generals": {
        "name": "灭晋三杰", "heroes": ["杜预", "羊祜", "王濬"],
        "effect": {"type": "damage_bonus", "value": 0.25, "description": "攻击+25%"},
        "description": "西晋灭吴三大统帅"
    },
    "deng_zhong_conspiracy": {
        "name": "灭蜀双雄", "heroes": ["邓艾", "钟会"],
        "effect": {"type": "attack_bonus", "value": 0.2, "description": "攻击+20%"},
        "description": "邓艾偷渡阴平，钟会攻破剑阁"
    },
    "wei_celebrities": {
        "name": "建安名士", "heroes": ["孔融", "陈宫", "贾诩"],
        "effect": {"type": "skill_damage", "value": 0.2, "description": "技能伤害+20%"},
        "description": "汉末名士智谋集团"
    },
    "wu_celebrities": {
        "name": "东吴四英杰", "heroes": ["周瑜", "鲁肃", "吕蒙", "陆逊"],
        "effect": {"type": "all_bonus", "value": 0.15, "description": "全属性+15%"},
        "description": "东吴四代都督，文武兼备"
    },
    "liu_family": {
        "name": "刘氏父子", "heroes": ["刘备", "刘封"],
        "effect": {"type": "hp_bonus", "value": 0.15, "description": "生命+15%"},
        "description": "刘备父子"
    },
    "huang_jin": {
        "name": "黄巾起义", "heroes": ["张角", "管亥", "裴元绍"],
        "effect": {"type": "damage_bonus", "value": 0.15, "description": "攻击+15%"},
        "description": "苍天已死，黄天当立"
    },
    "wei_zong_shi": {
        "name": "曹魏宗室", "heroes": ["夏侯惇", "夏侯渊", "曹仁", "曹真", "曹休"],
        "effect": {"type": "defense_bonus", "value": 0.2, "description": "防御+20%"},
        "description": "曹魏宗室名将，世代镇守四方"
    },
    "wu_cheng_xiang": {
        "name": "东吴文武", "heroes": ["张昭", "诸葛瑾", "顾雍"],
        "effect": {"type": "all_bonus", "value": 0.1, "description": "全属性+10%"},
        "description": "东吴文臣集团"
    },
    "shu_xiao_jiang": {
        "name": "蜀汉小将", "heroes": ["关平", "关兴", "张苞", "刘封"],
        "effect": {"type": "attack_bonus", "value": 0.15, "description": "攻击+15%"},
        "description": "蜀汉新生代战将"
    },
    "jin_emperor": {
        "name": "晋初三帝", "heroes": ["司马师", "司马昭", "司马炎"],
        "effect": {"type": "all_bonus", "value": 0.2, "description": "全属性+20%"},
        "description": "晋初三帝，奠定一统"
    },
    "meng_huo_zhu_rong": {
        "name": "南蛮王夫妇", "heroes": ["孟获", "祝融"],
        "effect": {"type": "attack_bonus", "value": 0.2, "description": "攻击+20%"},
        "description": "南蛮王与火神之女"
    },
    "xian_di": {
        "name": "先登死士", "heroes": ["麴义", "颜良文丑"],
        "effect": {"type": "damage_bonus", "value": 0.15, "description": "攻击+15%"},
        "description": "河北悍将"
    },
    "jiang_dong_tiger": {
        "name": "江东猛虎", "heroes": ["孙坚", "祖茂", "程普", "黄盖", "韩当"],
        "effect": {"type": "hp_bonus", "value": 0.2, "description": "生命+20%"},
        "description": "孙坚旧部，江东元勋"
    },
    "wu_ze_i": {
        "name": "东吴十二虎臣", "heroes": ["甘宁", "周泰", "凌统", "蒋钦", "徐盛", "丁奉"],
        "effect": {"type": "all_bonus", "value": 0.15, "description": "全属性+15%"},
        "description": "东吴十二虎臣，江东砥柱"
    },
    "shu_qi_xiong": {
        "name": "蜀汉七雄", "heroes": ["关羽", "张飞", "赵云", "马超", "黄忠", "魏延", "姜维"],
        "effect": {"type": "damage_bonus", "value": 0.2, "description": "攻击+20%"},
        "description": "蜀汉七大名将"
    },
    "san_gu_mao_lu": {
        "name": "三顾茅庐", "heroes": ["刘备", "诸葛亮"],
        "effect": {"type": "damage_bonus", "value": 0.2, "description": "攻击+20%"},
        "extra_effects": {"hp_bonus": 0.15},
        "special": "诸葛亮技能冷却减少50%",
        "description": "刘备诚心请诸葛亮出山"
    },
    "guo_wu_guan": {
        "name": "过五关斩六将", "heroes": ["关羽"],
        "effect": {"type": "damage_bonus", "value": 0.25, "description": "攻击+25%"},
        "extra_effects": {"crit_bonus": 0.15},
        "special": "对敌方后排造成额外伤害",
        "requirement": 1,
        "description": "关羽千里走单骑，过五关斩六将"
    },
    "chang_ban_po": {
        "name": "长坂坡", "heroes": ["赵云"],
        "effect": {"type": "dodge_bonus", "value": 0.2, "description": "闪避+20%"},
        "extra_effects": {"damage_reduction": 0.15},
        "special": "生命值低于30%时闪避率翻倍",
        "requirement": 1,
        "description": "赵云在长坂坡七进七出"
    },
    "kong_cheng_ji": {
        "name": "空城计", "heroes": ["诸葛亮"],
        "effect": {"type": "dodge_bonus", "value": 0.15, "description": "闪避+15%"},
        "special": "开场时敌方全体攻击力降低20%",
        "requirement": 1,
        "description": "诸葛亮空城退敌"
    },
    "lv_bu_diao_chan": {
        "name": "吕布貂蝉", "heroes": ["吕布", "貂蝉"],
        "effect": {"type": "damage_bonus", "value": 0.35, "description": "攻击+35%"},
        "extra_effects": {"crit_bonus": 0.2},
        "special": "吕布攻击时必定暴击",
        "description": "英雄美人，乱世佳话"
    },
    "sima_yi_alone": {
        "name": "隐忍司马懿", "heroes": ["司马懿"],
        "effect": {"type": "damage_reduction", "value": 0.2, "description": "伤害减免+20%"},
        "special": "受到致命伤害时有30%概率不死",
        "requirement": 1,
        "description": "隐忍一生，最终夺权"
    },
    "qun_xiong_zhu_lu": {
        "name": "十八路诸侯", "heroes": ["袁绍", "袁术", "公孙瓒", "刘表", "陶谦"],
        "effect": {"type": "damage_reduction", "value": 0.1, "description": "伤害减免+10%"},
        "description": "讨董十八路诸侯"
    },
    "guan_zhang_ma_huang_zhao": {
        "name": "蜀汉四将军", "heroes": ["关羽", "张飞", "马超", "黄忠", "赵云"],
        "effect": {"type": "crit_bonus", "value": 0.15, "description": "暴击+15%"},
        "description": "前后左右四将军"
    },
    "guan_hai": {
        "name": "黄巾余党", "heroes": ["管亥", "裴元绍", "廖化", "周仓"],
        "effect": {"type": "hp_bonus", "value": 0.1, "description": "生命+10%"},
        "description": "黄巾余部归附蜀汉"
    },
    "wei_xian_deng": {
        "name": "虎豹骑", "heroes": ["夏侯渊", "曹纯", "曹真", "张辽"],
        "effect": {"type": "speed_bonus", "value": 0.2, "description": "速度+20%"},
        "description": "曹魏精锐虎豹骑统帅"
    }
}

# ============================================================
# 物品数据库 - 消耗品、材料
# ============================================================
ITEMS_DATABASE = {
    # 药水类
    "小回春丹": {"type": "consumable", "rarity": "common", "icon": "💊",
               "effect": {"heal": 200}, "description": "恢复200生命值", "price": 50, "stack": 99},
    "回春丹": {"type": "consumable", "rarity": "rare", "icon": "💊",
              "effect": {"heal": 800}, "description": "恢复800生命值", "price": 200, "stack": 99},
    "大回春丹": {"type": "consumable", "rarity": "epic", "icon": "💊",
                "effect": {"heal": 3000}, "description": "恢复3000生命值", "price": 800, "stack": 99},
    "九转还魂丹": {"type": "consumable", "rarity": "legendary", "icon": "💊",
                  "effect": {"heal": 10000, "revive": True}, "description": "恢复10000生命，可复活阵亡武将", "price": 5000, "stack": 10},
    "回怒丹": {"type": "consumable", "rarity": "rare", "icon": "🔥",
              "effect": {"rage": 50}, "description": "恢复50点怒气", "price": 150, "stack": 99},
    "大回怒丹": {"type": "consumable", "rarity": "epic", "icon": "🔥",
                "effect": {"rage": 100}, "description": "满怒气", "price": 500, "stack": 50},
    "洗髓丹": {"type": "consumable", "rarity": "epic", "icon": "🌀",
              "effect": {"reset_attr": True}, "description": "重置武将属性分配", "price": 1000, "stack": 10},
    "突破丹": {"type": "consumable", "rarity": "legendary", "icon": "⭐",
              "effect": {"breakthrough": True}, "description": "突破武将等级上限", "price": 3000, "stack": 10},

    # 卷轴类
    "经验卷轴": {"type": "consumable", "rarity": "common", "icon": "📜",
               "effect": {"exp": 1000}, "description": "增加1000经验", "price": 100, "stack": 99},
    "大经验卷轴": {"type": "consumable", "rarity": "rare", "icon": "📜",
                  "effect": {"exp": 5000}, "description": "增加5000经验", "price": 400, "stack": 99},
    "超级经验卷轴": {"type": "consumable", "rarity": "epic", "icon": "📜",
                    "effect": {"exp": 20000}, "description": "增加20000经验", "price": 1500, "stack": 50},
    "技能升级卷轴": {"type": "consumable", "rarity": "epic", "icon": "📜",
                    "effect": {"skill_upgrade": True}, "description": "升级武将技能等级", "price": 2000, "stack": 20},
    "觉醒卷轴": {"type": "consumable", "rarity": "legendary", "icon": "📜",
                "effect": {"awaken": True}, "description": "觉醒武将隐藏力量", "price": 8000, "stack": 5},

    # 材料类
    "精铁": {"type": "material", "rarity": "common", "icon": "🔩",
             "description": "基础锻造材料", "price": 20, "stack": 999},
    "玄铁": {"type": "material", "rarity": "rare", "icon": "🔩",
             "description": "高级锻造材料", "price": 100, "stack": 999},
    "陨铁": {"type": "material", "rarity": "epic", "icon": "🔩",
             "description": "天外陨铁，锻造神兵的材料", "price": 500, "stack": 99},
    "龙鳞": {"type": "material", "rarity": "legendary", "icon": "🐲",
             "description": "龙之鳞片，锻造传说装备的材料", "price": 2000, "stack": 50},
    "凤羽": {"type": "material", "rarity": "legendary", "icon": "🔥",
             "description": "凤凰之羽，附魔材料", "price": 2000, "stack": 50},
    "麒麟血": {"type": "material", "rarity": "mythic", "icon": "🩸",
               "description": "麒麟之血，神话材料", "price": 10000, "stack": 10},

    # 宝石类
    "攻击宝石": {"type": "gem", "rarity": "rare", "icon": "💎",
                "effect": {"attack": 50}, "description": "镶嵌后增加攻击力", "price": 300, "stack": 99},
    "防御宝石": {"type": "gem", "rarity": "rare", "icon": "💎",
                "effect": {"defense": 50}, "description": "镶嵌后增加防御力", "price": 300, "stack": 99},
    "生命宝石": {"type": "gem", "rarity": "rare", "icon": "💎",
                "effect": {"health": 200}, "description": "镶嵌后增加生命值", "price": 300, "stack": 99},
    "速度宝石": {"type": "gem", "rarity": "rare", "icon": "💎",
                "effect": {"speed": 10}, "description": "镶嵌后增加速度", "price": 300, "stack": 99},
    "暴击宝石": {"type": "gem", "rarity": "epic", "icon": "💎",
                "effect": {"critical": 0.05}, "description": "镶嵌后增加暴击率", "price": 800, "stack": 50},
    "全属性宝石": {"type": "gem", "rarity": "legendary", "icon": "💎",
                  "effect": {"all": 0.05}, "description": "镶嵌后增加全属性5%", "price": 3000, "stack": 20},

    # 特殊道具
    "改名卡": {"type": "special", "rarity": "rare", "icon": "📝",
              "description": "修改武将名称", "price": 500, "stack": 10},
    "扩位卡": {"type": "special", "rarity": "rare", "icon": "📦",
              "description": "扩展武将仓库位置", "price": 1000, "stack": 10},
    "传送符": {"type": "special", "rarity": "common", "icon": "🌀",
              "description": "快速传送至已探索地点", "price": 50, "stack": 99},
    "遁地符": {"type": "special", "rarity": "rare", "icon": "🌀",
              "description": "从战斗中逃跑", "price": 100, "stack": 99},
    "双倍经验符": {"type": "special", "rarity": "rare", "icon": "✨",
                  "effect": {"exp_multiplier": 2.0, "duration": 3600},
                  "description": "1小时内获得双倍经验", "price": 500, "stack": 10},
    "双倍掉落符": {"type": "special", "rarity": "epic", "icon": "✨",
                  "effect": {"drop_multiplier": 2.0, "duration": 3600},
                  "description": "1小时内掉落翻倍", "price": 1000, "stack": 10},

    # 食物类（新增）
    "肉干": {"type": "consumable", "rarity": "common", "icon": "🍖",
            "effect": {"heal": 100, "rage": 10}, "description": "恢复100生命和10怒气", "price": 30, "stack": 99},
    "美酒": {"type": "consumable", "rarity": "common", "icon": "🍶",
            "effect": {"rage": 30, "attack_bonus": 0.05}, "description": "恢复30怒气，攻击+5%（1战）",
            "price": 80, "stack": 99},
    "女儿红": {"type": "consumable", "rarity": "rare", "icon": "🍶",
              "effect": {"rage": 60, "attack_bonus": 0.1}, "description": "恢复60怒气，攻击+10%（1战）",
              "price": 250, "stack": 50},
    "八珍糕": {"type": "consumable", "rarity": "epic", "icon": "🍱",
              "effect": {"heal": 500, "rage": 30, "all_bonus": 0.05},
              "description": "恢复500生命30怒气，全属性+5%（1战）", "price": 600, "stack": 30},
    "蟠桃": {"type": "consumable", "rarity": "legendary", "icon": "🍑",
              "effect": {"heal": 5000, "rage": 100, "exp": 5000},
              "description": "西王母蟠桃，恢复5000生命100怒气，获得5000经验",
              "price": 3000, "stack": 5},
    "人参果": {"type": "consumable", "rarity": "mythic", "icon": "🍑",
              "effect": {"heal": 20000, "rage": 100, "revive": True, "all_bonus": 0.1},
              "description": "五庄观人参果，回满生命，复活阵亡武将，全属性+10%（3战）",
              "price": 15000, "stack": 1},

    # 武将经验药水（新增）
    "武将经验药水": {"type": "consumable", "rarity": "common", "icon": "🧪",
                   "effect": {"hero_exp": 500}, "description": "武将获得500经验", "price": 80, "stack": 99},
    "高级经验药水": {"type": "consumable", "rarity": "rare", "icon": "🧪",
                   "effect": {"hero_exp": 2500}, "description": "武将获得2500经验", "price": 300, "stack": 99},
    "超级经验药水": {"type": "consumable", "rarity": "epic", "icon": "🧪",
                   "effect": {"hero_exp": 10000}, "description": "武将获得10000经验", "price": 1200, "stack": 50},
    "神级经验药水": {"type": "consumable", "rarity": "legendary", "icon": "🧪",
                   "effect": {"hero_exp": 50000}, "description": "武将获得50000经验", "price": 5000, "stack": 10},

    # 进阶丹药（新增）
    "进阶丹": {"type": "consumable", "rarity": "rare", "icon": "💊",
              "effect": {"evolve": True}, "description": "武将品质进阶", "price": 1500, "stack": 10},
    "觉醒丹": {"type": "consumable", "rarity": "legendary", "icon": "💊",
              "effect": {"awaken": True}, "description": "武将觉醒，开启隐藏力量", "price": 6000, "stack": 5},
    "升星丹": {"type": "consumable", "rarity": "epic", "icon": "⭐",
              "effect": {"star_up": True}, "description": "武将升星", "price": 2500, "stack": 10},
    "转生丹": {"type": "consumable", "rarity": "mythic", "icon": "💫",
              "effect": {"rebirth": True}, "description": "武将转生", "price": 20000, "stack": 1},

    # 战斗道具（新增）
    "火攻计": {"type": "consumable", "rarity": "rare", "icon": "🔥",
              "effect": {"skill_damage": 200, "element": "火"},
              "description": "对敌全体造成200点火属性伤害", "price": 200, "stack": 50},
    "水淹计": {"type": "consumable", "rarity": "rare", "icon": "🌊",
              "effect": {"skill_damage": 200, "element": "水"},
              "description": "对敌全体造成200点水属性伤害", "price": 200, "stack": 50},
    "落雷符": {"type": "consumable", "rarity": "epic", "icon": "⚡",
              "effect": {"skill_damage": 500, "element": "雷"},
              "description": "对敌全体造成500点雷属性伤害", "price": 800, "stack": 20},
    "封印符": {"type": "consumable", "rarity": "epic", "icon": "🔒",
              "effect": {"silence": True, "duration": 2},
              "description": "沉默敌方全体2回合", "price": 1000, "stack": 10},

    # 装备强化材料（新增）
    "强化石": {"type": "material", "rarity": "common", "icon": "🪨",
              "description": "装备强化基础材料", "price": 30, "stack": 999},
    "精炼石": {"type": "material", "rarity": "rare", "icon": "🪨",
              "description": "装备精炼材料", "price": 150, "stack": 999},
    "突破石": {"type": "material", "rarity": "epic", "icon": "🪨",
              "description": "装备突破材料", "price": 600, "stack": 99},
    "神炼石": {"type": "material", "rarity": "legendary", "icon": "🪨",
              "description": "神级装备强化材料", "price": 3000, "stack": 50},
    "天工石": {"type": "material", "rarity": "mythic", "icon": "🪨",
              "description": "传说天工开物之石", "price": 15000, "stack": 10},

    # 神兽材料（新增）
    "白虎牙": {"type": "material", "rarity": "legendary", "icon": "🐯",
              "description": "白虎之牙，锻造神兵", "price": 3000, "stack": 30},
    "朱雀羽": {"type": "material", "rarity": "legendary", "icon": "🦅",
              "description": "朱雀之羽，附魔材料", "price": 3000, "stack": 30},
    "玄武甲": {"type": "material", "rarity": "legendary", "icon": "🐢",
              "description": "玄武之甲，防御材料", "price": 3000, "stack": 30},
    "青龙鳞": {"type": "material", "rarity": "mythic", "icon": "🐲",
              "description": "青龙之鳞，神话材料", "price": 12000, "stack": 10},
    "麒麟角": {"type": "material", "rarity": "mythic", "icon": "🦄",
              "description": "麒麟之角，至高材料", "price": 15000, "stack": 5},

    # 高级宝石（新增）
    "破甲宝石": {"type": "gem", "rarity": "epic", "icon": "💎",
                "effect": {"armor_pierce": 0.15}, "description": "无视15%防御", "price": 1000, "stack": 50},
    "吸血宝石": {"type": "gem", "rarity": "epic", "icon": "💎",
                "effect": {"life_steal": 0.1}, "description": "攻击吸血10%", "price": 1000, "stack": 50},
    "反伤宝石": {"type": "gem", "rarity": "epic", "icon": "💎",
                "effect": {"reflect": 0.15}, "description": "反伤15%", "price": 1000, "stack": 50},
    "命中宝石": {"type": "gem", "rarity": "rare", "icon": "💎",
                "effect": {"accuracy": 0.1}, "description": "命中率+10%", "price": 400, "stack": 99},
    "闪避宝石": {"type": "gem", "rarity": "epic", "icon": "💎",
                "effect": {"dodge": 0.08}, "description": "闪避率+8%", "price": 800, "stack": 50},
    "怒气宝石": {"type": "gem", "rarity": "legendary", "icon": "💎",
                "effect": {"rage_per_turn": 10}, "description": "每回合恢复10怒气", "price": 2500, "stack": 20},

    # 礼包类（新增）
    "新手大礼包": {"type": "special", "rarity": "epic", "icon": "🎁",
                  "effect": {"bundle": "newbie"}, "description": "新手必备，包含多种资源",
                  "price": 1000, "stack": 1},
    "高级招募令x10": {"type": "special", "rarity": "epic", "icon": "🎁",
                    "effect": {"recruit_ticket": 10, "tier": "advanced"},
                    "description": "10张高级招募令", "price": 4500, "stack": 1},
    "传说招募令x10": {"type": "special", "rarity": "legendary", "icon": "🎁",
                    "effect": {"recruit_ticket": 10, "tier": "legendary"},
                    "description": "10张传说招募令", "price": 18000, "stack": 1},
    "资源大礼包": {"type": "special", "rarity": "epic", "icon": "🎁",
                  "effect": {"bundle": "resources"}, "description": "大量基础资源",
                  "price": 2000, "stack": 1}
}

# ============================================================
# 装备数据库扩展
# ============================================================
EQUIPMENT_DATABASE = {
    # 武器类
    "铁剑": {"type": "weapon", "rarity": "common", "icon": "⚔️",
             "stats": {"attack": 30}, "level_req": 1, "price": 100,
             "description": "普通铁制长剑"},
    "青铜剑": {"type": "weapon", "rarity": "common", "icon": "⚔️",
               "stats": {"attack": 60}, "level_req": 5, "price": 300,
               "description": "青铜铸造的剑"},
    "钢剑": {"type": "weapon", "rarity": "rare", "icon": "⚔️",
             "stats": {"attack": 120, "critical": 0.03}, "level_req": 10, "price": 800,
             "description": "精钢打造"},
    "青釭剑": {"type": "weapon", "rarity": "epic", "icon": "⚔️",
               "stats": {"attack": 250, "critical": 0.08, "speed": 10}, "level_req": 20, "price": 3000,
               "description": "削铁如泥的宝剑"},
    "七星宝刀": {"type": "weapon", "rarity": "legendary", "icon": "⚔️",
                "stats": {"attack": 500, "critical": 0.15, "speed": 20}, "level_req": 35, "price": 10000,
                "description": "镶嵌七星的宝刀"},
    "双股剑": {"type": "weapon", "rarity": "legendary", "icon": "⚔️",
               "stats": {"attack": 450, "defense": 100, "health": 300}, "level_req": 30, "price": 8000,
               "description": "刘备的雌雄双股剑"},
    "倚天剑": {"type": "weapon", "rarity": "mythic", "icon": "⚔️",
               "stats": {"attack": 800, "critical": 0.2, "speed": 30, "leadership": 100},
               "level_req": 50, "price": 30000,
               "description": "曹操佩剑，号令天下"},
    "青龙偃月刀": {"type": "weapon", "rarity": "mythic", "icon": "⚔️",
                  "stats": {"attack": 900, "critical": 0.25, "health": 500},
                  "level_req": 50, "price": 50000,
                  "description": "关羽神兵，武圣之刀"},
    "丈八蛇矛": {"type": "weapon", "rarity": "mythic", "icon": "⚔️",
                 "stats": {"attack": 850, "health": 800, "defense": 200},
                 "level_req": 50, "price": 45000,
                 "description": "张飞神兵"},
    "方天画戟": {"type": "weapon", "rarity": "mythic", "icon": "⚔️",
                 "stats": {"attack": 1000, "critical": 0.3, "speed": 50},
                 "level_req": 50, "price": 60000,
                 "description": "吕布神兵，天下无双"},

    # 防具类
    "布衣": {"type": "armor", "rarity": "common", "icon": "🛡️",
             "stats": {"defense": 20}, "level_req": 1, "price": 80,
             "description": "普通布衣"},
    "皮甲": {"type": "armor", "rarity": "common", "icon": "🛡️",
             "stats": {"defense": 50, "health": 100}, "level_req": 5, "price": 250,
             "description": "皮革护甲"},
    "铁甲": {"type": "armor", "rarity": "rare", "icon": "🛡️",
             "stats": {"defense": 120, "health": 300}, "level_req": 10, "price": 700,
             "description": "铁制铠甲"},
    "锁子甲": {"type": "armor", "rarity": "epic", "icon": "🛡️",
               "stats": {"defense": 250, "health": 600, "speed": 5}, "level_req": 20, "price": 2500,
               "description": "精细锁甲"},
    "黄金甲": {"type": "armor", "rarity": "legendary", "icon": "🛡️",
               "stats": {"defense": 450, "health": 1200, "speed": 10}, "level_req": 35, "price": 8000,
               "description": "皇家黄金铠甲"},
    "九龙甲": {"type": "armor", "rarity": "mythic", "icon": "🛡️",
               "stats": {"defense": 800, "health": 2000, "defense_percent": 0.1},
               "level_req": 50, "price": 30000,
               "description": "九龙护体，刀枪不入"},

    # 头盔类
    "皮帽": {"type": "helmet", "rarity": "common", "icon": "⛑️",
             "stats": {"defense": 15, "health": 50}, "level_req": 1, "price": 60,
             "description": "皮革帽子"},
    "铁盔": {"type": "helmet", "rarity": "rare", "icon": "⛑️",
             "stats": {"defense": 80, "health": 200}, "level_req": 10, "price": 500,
             "description": "铁制头盔"},
    "将军盔": {"type": "helmet", "rarity": "epic", "icon": "⛑️",
               "stats": {"defense": 180, "health": 500, "critical": 0.03}, "level_req": 20, "price": 2000,
               "description": "将军头盔"},
    "紫金冠": {"type": "helmet", "rarity": "legendary", "icon": "⛑️",
               "stats": {"defense": 350, "health": 1000, "attack": 100}, "level_req": 35, "price": 7000,
               "description": "紫金打造的王冠"},

    # 饰品类
    "玉佩": {"type": "accessory", "rarity": "rare", "icon": "💎",
             "stats": {"health": 200, "speed": 5}, "level_req": 10, "price": 400,
             "description": "温润玉佩"},
    "虎符": {"type": "accessory", "rarity": "epic", "icon": "💎",
             "stats": {"attack": 100, "leadership": 50}, "level_req": 20, "price": 1500,
             "description": "调兵虎符"},
    "传国玉玺": {"type": "accessory", "rarity": "mythic", "icon": "💎",
                 "stats": {"all": 0.1, "leadership": 200, "health": 1000},
                 "level_req": 50, "price": 50000,
                 "description": "受命于天，既寿永昌"},

    # 靴子类
    "草鞋": {"type": "boots", "rarity": "common", "icon": "👢",
             "stats": {"speed": 5}, "level_req": 1, "price": 40,
             "description": "刘备早年编草鞋"},
    "皮靴": {"type": "boots", "rarity": "common", "icon": "👢",
             "stats": {"speed": 15, "defense": 10}, "level_req": 5, "price": 150,
             "description": "皮制靴子"},
    "追风靴": {"type": "boots", "rarity": "epic", "icon": "👢",
               "stats": {"speed": 50, "dodge": 0.05}, "level_req": 20, "price": 2000,
               "description": "追风逐电"},
    "神行靴": {"type": "boots", "rarity": "legendary", "icon": "👢",
               "stats": {"speed": 100, "dodge": 0.1, "attack": 50}, "level_req": 35, "price": 6000,
               "description": "日行千里"},

    # 书籍类
    "孙子兵法": {"type": "book", "rarity": "legendary", "icon": "📖",
                 "stats": {"skill_damage": 0.2, "leadership": 100}, "level_req": 30, "price": 8000,
                 "description": "兵法圣典"},
    "六韬": {"type": "book", "rarity": "epic", "icon": "📖",
             "stats": {"skill_damage": 0.15, "defense": 100}, "level_req": 20, "price": 2000,
             "description": "姜子牙兵法"},
    "三略": {"type": "book", "rarity": "epic", "icon": "📖",
             "stats": {"skill_damage": 0.12, "attack": 100}, "level_req": 20, "price": 2000,
             "description": "黄石公兵法"},
    "遁甲天书": {"type": "book", "rarity": "mythic", "icon": "📖",
                 "stats": {"skill_damage": 0.3, "all": 0.05}, "level_req": 50, "price": 30000,
                 "description": "左慈仙书"},

    # 新增武器（专属神兵）
    "龙胆亮银枪": {"type": "weapon", "rarity": "mythic", "icon": "⚔️",
                  "stats": {"attack": 880, "critical": 0.2, "speed": 40, "dodge": 0.05},
                  "level_req": 50, "price": 48000,
                  "description": "赵云神兵，龙胆亮银"},
    "虎头湛金枪": {"type": "weapon", "rarity": "legendary", "icon": "⚔️",
                  "stats": {"attack": 550, "critical": 0.12, "speed": 25},
                  "level_req": 40, "price": 12000,
                  "description": "马超神兵"},
    "丈八蛇矛": {"type": "weapon", "rarity": "mythic", "icon": "⚔️",
                 "stats": {"attack": 850, "health": 800, "defense": 200},
                 "level_req": 50, "price": 45000,
                 "description": "张飞神兵（重定义）"},
    "古锭刀": {"type": "weapon", "rarity": "epic", "icon": "⚔️",
              "stats": {"attack": 280, "critical": 0.1, "speed": 15},
              "level_req": 25, "price": 3500,
              "description": "孙坚佩刀"},
    "松纹古定剑": {"type": "weapon", "rarity": "epic", "icon": "⚔️",
                  "stats": {"attack": 270, "defense": 80, "speed": 10},
                  "level_req": 25, "price": 3500,
                  "description": "名匠锻造"},
    "九凤刀": {"type": "weapon", "rarity": "legendary", "icon": "⚔️",
              "stats": {"attack": 480, "critical": 0.18, "speed": 30},
              "level_req": 35, "price": 9000,
              "description": "九凤朝阳之刀"},

    # 新增防具
    "吞兽铠": {"type": "armor", "rarity": "epic", "icon": "🛡️",
              "stats": {"defense": 280, "health": 700, "attack": 50},
              "level_req": 25, "price": 3000,
              "description": "吞兽之铠"},
    "明光铠": {"type": "armor", "rarity": "legendary", "icon": "🛡️",
              "stats": {"defense": 500, "health": 1300, "speed": 15, "defense_percent": 0.05},
              "level_req": 40, "price": 9000,
              "description": "明光铠，反射如镜"},
    "天蚕宝甲": {"type": "armor", "rarity": "mythic", "icon": "🛡️",
                "stats": {"defense": 900, "health": 2200, "defense_percent": 0.15, "dodge": 0.05},
                "level_req": 50, "price": 35000,
                "description": "天蚕丝所织，刀枪不入"},

    # 新增头盔
    "鱼鳞盔": {"type": "helmet", "rarity": "rare", "icon": "⛑️",
              "stats": {"defense": 100, "health": 250},
              "level_req": 15, "price": 700,
              "description": "鱼鳞甲之盔"},
    "兽面盔": {"type": "helmet", "rarity": "epic", "icon": "⛑️",
              "stats": {"defense": 200, "health": 550, "attack": 50},
              "level_req": 25, "price": 2500,
              "description": "兽面吞头铠"},
    "凤翅盔": {"type": "helmet", "rarity": "legendary", "icon": "⛑️",
              "stats": {"defense": 380, "health": 1100, "speed": 20},
              "level_req": 40, "price": 7500,
              "description": "凤翅展翼之盔"},
    "九霄冠": {"type": "helmet", "rarity": "mythic", "icon": "⛑️",
              "stats": {"defense": 700, "health": 1800, "all": 0.05, "leadership": 100},
              "level_req": 50, "price": 28000,
              "description": "九霄云外之冠"},

    # 新增饰品
    "龙形玉佩": {"type": "accessory", "rarity": "epic", "icon": "💎",
                "stats": {"health": 400, "attack": 80, "speed": 10},
                "level_req": 25, "price": 2500,
                "description": "龙形玉佩"},
    "和氏璧": {"type": "accessory", "rarity": "mythic", "icon": "💎",
              "stats": {"all": 0.15, "leadership": 250, "health": 1500, "rage_per_turn": 5},
              "level_req": 50, "price": 60000,
              "description": "和氏之璧，价值连城"},
    "九锡": {"type": "accessory", "rarity": "mythic", "icon": "💎",
             "stats": {"all": 0.1, "leadership": 200, "attack": 300, "defense": 300},
             "level_req": 50, "price": 50000,
             "description": "天子赐予九锡之礼"},
    "五彩神石": {"type": "accessory", "rarity": "legendary", "icon": "💎",
                "stats": {"all": 0.05, "health": 800, "rage_per_turn": 3},
                "level_req": 40, "price": 12000,
                "description": "女娲补天遗石"},

    # 新增靴子
    "草鞋": {"type": "boots", "rarity": "common", "icon": "👢",
             "stats": {"speed": 5}, "level_req": 1, "price": 40,
             "description": "刘备早年编草鞋"},
    "战靴": {"type": "boots", "rarity": "rare", "icon": "👢",
             "stats": {"speed": 30, "defense": 30, "health": 100},
             "level_req": 15, "price": 600,
             "description": "战场之靴"},
    "踏雪靴": {"type": "boots", "rarity": "legendary", "icon": "👢",
               "stats": {"speed": 90, "dodge": 0.08, "attack": 60, "defense": 60},
               "level_req": 40, "price": 7500,
               "description": "踏雪无痕"},
    "凌空靴": {"type": "boots", "rarity": "mythic", "icon": "👢",
               "stats": {"speed": 150, "dodge": 0.15, "attack": 100},
               "level_req": 50, "price": 28000,
               "description": "凌空飞行之靴"},

    # 新增书籍
    "战国策": {"type": "book", "rarity": "rare", "icon": "📖",
              "stats": {"skill_damage": 0.08, "attack": 50},
              "level_req": 15, "price": 700,
              "description": "战国纵横之策"},
    "吴子兵法": {"type": "book", "rarity": "epic", "icon": "📖",
                "stats": {"skill_damage": 0.12, "defense": 80},
                "level_req": 20, "price": 2000,
                "description": "吴起兵法"},
    "司马法": {"type": "book", "rarity": "epic", "icon": "📖",
              "stats": {"skill_damage": 0.12, "leadership": 50},
              "level_req": 20, "price": 2000,
              "description": "司马穰苴兵法"},
    "孟德新书": {"type": "book", "rarity": "legendary", "icon": "📖",
                "stats": {"skill_damage": 0.18, "leadership": 80, "attack": 80},
                "level_req": 30, "price": 7000,
                "description": "曹操所著兵法"},
    "太公兵法": {"type": "book", "rarity": "mythic", "icon": "📖",
                "stats": {"skill_damage": 0.25, "leadership": 150, "all": 0.03},
                "level_req": 50, "price": 25000,
                "description": "姜子牙六韬"},

    # 新增专属饰品（武将专属）
    "的卢马": {"type": "accessory", "rarity": "legendary", "icon": "🐎",
              "stats": {"speed": 80, "dodge": 0.1, "health": 500},
              "level_req": 30, "price": 9000,
              "description": "刘备坐骑，的卢跃檀溪"},
    "赤兔马": {"type": "accessory", "rarity": "mythic", "icon": "🐎",
              "stats": {"speed": 120, "attack": 200, "dodge": 0.05},
              "level_req": 50, "price": 35000,
              "description": "人中吕布，马中赤兔"},
    "绝影": {"type": "accessory", "rarity": "legendary", "icon": "🐎",
             "stats": {"speed": 90, "dodge": 0.12, "health": 600},
             "level_req": 35, "price": 8000,
             "description": "曹操坐骑，绝影无影"},
    "爪黄飞电": {"type": "accessory", "rarity": "legendary", "icon": "🐎",
                "stats": {"speed": 100, "attack": 100, "dodge": 0.08},
                "level_req": 35, "price": 8000,
                "description": "曹操坐骑，爪黄飞电"}
}

# 套装效果
SET_BONUSES = {
    "wu_sheng_set": {
        "name": "武圣套装", "items": ["青龙偃月刀", "九龙甲", "紫金冠", "神行靴"],
        "bonus": {2: {"attack": 200}, 3: {"critical": 0.1}, 4: {"attack_percent": 0.3}},
        "description": "武圣关羽套装"
    },
    "fei_jiang_set": {
        "name": "飞将套装", "items": ["方天画戟", "黄金甲", "紫金冠", "传国玉玺"],
        "bonus": {2: {"attack": 300}, 3: {"speed": 30}, 4: {"all": 0.1}},
        "description": "飞将吕布套装"
    },
    "long_jiang_set": {
        "name": "常胜套装", "items": ["青釭剑", "锁子甲", "追风靴", "玉佩"],
        "bonus": {2: {"speed": 50}, 3: {"dodge": 0.1}, 4: {"attack_percent": 0.25}},
        "description": "常胜将军赵云套装"
    },
    "di_wang_set": {
        "name": "帝王套装", "items": ["倚天剑", "九龙甲", "紫金冠", "传国玉玺"],
        "bonus": {2: {"leadership": 200}, 3: {"all": 0.08}, 4: {"all": 0.15}},
        "description": "帝王之套装"
    },
    "fei_jiang_lvbu_set": {
        "name": "飞将吕布套装", "items": ["方天画戟", "天蚕宝甲", "九霄冠", "赤兔马"],
        "bonus": {2: {"attack": 400}, 3: {"critical": 0.15, "speed": 50}, 4: {"all": 0.2}},
        "description": "吕布全套神装，天下无双"
    },
    "wu_sheng_guan_set": {
        "name": "武圣关羽套装加强", "items": ["青龙偃月刀", "天蚕宝甲", "九霄冠", "踏雪靴"],
        "bonus": {2: {"attack": 500, "critical": 0.05}, 3: {"attack_percent": 0.3, "speed": 30},
                  4: {"all": 0.15, "critical": 0.1}},
        "description": "武圣关羽全套神装"
    },
    "chang_sheng_zhao_set": {
        "name": "常胜赵云套装加强", "items": ["龙胆亮银枪", "明光铠", "凤翅盔", "凌空靴"],
        "bonus": {2: {"speed": 80, "dodge": 0.1}, 3: {"attack": 300, "critical": 0.15},
                  4: {"all": 0.15, "dodge": 0.15}},
        "description": "赵云常胜套装全套"
    },
    "jin_wu_set": {
        "name": "晋武套装", "items": ["倚天剑", "天蚕宝甲", "九霄冠", "和氏璧"],
        "bonus": {2: {"leadership": 300}, 3: {"all": 0.1, "rage_per_turn": 5},
                  4: {"all": 0.2, "leadership": 300}},
        "description": "晋武帝司马炎套装"
    },
    "meng_jiang_set": {
        "name": "孟将套装", "items": ["虎头湛金枪", "明光铠", "兽面盔", "战靴"],
        "bonus": {2: {"attack": 250, "speed": 30}, 3: {"critical": 0.1, "attack_percent": 0.2},
                  4: {"all": 0.1, "speed": 50}},
        "description": "锦马超套装"
    },
    "huo_zhi_zhu_set": {
        "name": "火之主套装", "items": ["九凤刀", "吞兽铠", "凤翅盔", "五彩神石"],
        "bonus": {2: {"attack": 300, "critical": 0.08}, 3: {"attack_percent": 0.25, "critical": 0.05},
                  4: {"all": 0.12, "critical": 0.15}},
        "description": "火神祝融之套装"
    },
    "zhi_zun_set": {
        "name": "至尊套装", "items": ["七星宝刀", "天蚕宝甲", "九霄冠", "九锡"],
        "bonus": {2: {"leadership": 250, "attack": 200}, 3: {"all": 0.1, "leadership": 150},
                  4: {"all": 0.2, "leadership": 400}},
        "description": "天子至尊套装"
    },
    "wen_chen_set": {
        "name": "文臣套装", "items": ["太公兵法", "明光铠", "紫金冠", "和氏璧"],
        "bonus": {2: {"skill_damage": 0.2, "leadership": 150},
                  3: {"skill_damage": 0.3, "all": 0.05},
                  4: {"skill_damage": 0.5, "all": 0.15}},
        "description": "谋士文臣套装"
    }
}

def get_hero_by_name(name):
    """根据名字获取武将数据"""
    return HERO_DATABASE.get(name)

def get_heroes_by_faction(faction):
    """根据阵营获取武将列表"""
    return {name: data for name, data in HERO_DATABASE.items() if data.get("faction") == faction}

def get_heroes_by_quality(quality):
    """根据品质获取武将列表"""
    return {name: data for name, data in HERO_DATABASE.items() if data.get("quality") == quality}

def get_hero_count():
    """获取武将总数"""
    return len(HERO_DATABASE)

def get_random_hero(quality=None, faction=None):
    """随机获取武将"""
    pool = HERO_DATABASE
    if quality:
        pool = {k: v for k, v in pool.items() if v.get("quality") == quality}
    if faction:
        pool = {k: v for k, v in pool.items() if v.get("faction") == faction}
    if not pool:
        return None
    return random.choice(list(pool.keys()))

def get_item_by_name(name):
    """根据名字获取物品数据"""
    return ITEMS_DATABASE.get(name)

def get_equipment_by_name(name):
    """根据名字获取装备数据"""
    return EQUIPMENT_DATABASE.get(name)

def get_all_items():
    """获取所有物品"""
    return ITEMS_DATABASE

def get_all_equipment():
    """获取所有装备"""
    return EQUIPMENT_DATABASE

# ============================================================
# 被动技能效果注册表
# ============================================================
# 替代脆弱的关键字解析，使用结构化效果定义
# 效果类型说明：
# - heal_self: 每回合恢复自身百分比生命
# - heal_all: 每回合恢复己方全体百分比生命
# - crit_bonus: 暴击率加成
# - crit_damage: 暴击伤害加成（额外倍数）
# - dodge_bonus: 闪避率加成
# - shield_chance: 获得护盾的概率
# - shield_amount: 护盾固定值（若未指定则为max_hp的百分比）
# - hp_based_attack: 基于生命值的攻击加成系数
# - lifesteal_on_kill: 击杀目标时恢复生命的百分比
# - lifesteal_on_crit: 暴击时恢复生命的百分比
# - damage_reduction: 伤害减免百分比
# - speed_bonus: 速度加成百分比
# - speed_damage_bonus: 速度高于目标时额外伤害
# - counter_chance: 被攻击时反击概率
# - counter_damage: 反击伤害系数
# - death_buff: 队友阵亡时全属性提升
# - skill_reset_chance: 技能命中时重置冷却概率
# - ally_buff: 特定队友在场时的属性加成
# ============================================================
PASSIVE_EFFECTS = {
    "仁德之心": {
        "heal_all": 0.05
    },
    "武圣之威": {
        "crit_bonus": 0.2,
        "crit_damage": 1.0,
        "lifesteal_on_kill": 0.2
    },
    "万人之敌": {
        "hp_based_attack": 0.4
    },
    "一身是胆": {
        "dodge_bonus": 0.15,
        "shield_chance": 0.2
    },
    "西凉之魂": {
        "speed_damage_bonus": 0.2
    },
    "老当益壮": {
        "crit_damage": 0.5
    },
    "神机妙算": {
        "skill_cd_buff": 0.3
    },
    "连环之策": {
        "chaos_chance": 0.25
    },
    "桀骜不驯": {
        "counter_chance": 0.2,
        "counter_damage": 0.5
    },
    "继承遗志": {
        "death_buff": 0.2
    },
    "奇谋百出": {
        "skill_reset_chance": 0.2
    },
    "忠孝两全": {
        "ally_buff": {"关羽": {"attack": 0.15, "defense": 0.15}}
    },
    "将门虎子": {
        "lifesteal_on_crit": 0.05
    },
    "燕人咆哮": {
        "fear_chance": 0.3,
        "fear_duration": 1
    },
    "威震华夏": {
        "damage_reduction": 0.15,
        "attack_bonus": 0.1
    },
    "常胜将军": {
        "dodge_bonus": 0.2,
        "hp_regen": 0.03
    },
    "卧龙之才": {
        "skill_damage_bonus": 0.25,
        "mana_regen": 0.1
    },
    "凤雏涅槃": {
        "sacrifice_damage": 0.3,
        "team_damage_reduction": 0.2
    },
    "魏武雄风": {
        "team_attack_bonus": 0.1,
        "hp_bonus": 0.1
    },
    "鬼才": {
        "skill_crit_bonus": 0.2,
        "aoe_damage_bonus": 0.15
    },
    "虎痴": {
        "defense_bonus": 0.2,
        "hp_based_defense": 0.3
    },
    "古之恶来": {
        "counter_damage": 0.8,
        "damage_reduction": 0.2
    },
    "威震逍遥津": {
        "speed_bonus": 0.15,
        "pierce_bonus": 0.2
    },
    "锦帆贼": {
        "stealth_chance": 0.3,
        "backstab_bonus": 0.5
    },
    "大都督": {
        "fire_damage_bonus": 0.3,
        "burn_chance": 0.25
    },
    "小霸王": {
        "rage_gain_bonus": 0.5,
        "attack_bonus_low_hp": 0.3
    },
    "碧眼儿": {
        "team_defense_bonus": 0.15,
        "heal_bonus": 0.2
    },
    "国色天香": {
        "charm_chance": 0.4,
        "team_damage_bonus": 0.1
    },
    "飞将": {
        "attack_bonus": 0.3,
        "speed_bonus": 0.2,
        "aoe_range_bonus": 1
    },
    "人中吕布": {
        "all_bonus": 0.25
    }
}

def _auto_generate_passive_effects():
    """自动为未定义被动效果的武将生成效果"""
    for hero_name, hero_data in HERO_DATABASE.items():
        passive_name = hero_data.get("passive_name", "")
        passive_description = hero_data.get("passive_description", "")
        
        if passive_name and passive_name not in PASSIVE_EFFECTS:
            effects = {}
            
            desc = passive_description
            
            if "恢复" in desc or "回血" in desc:
                if "全体" in desc:
                    effects["heal_all"] = 0.05
                else:
                    effects["heal_self"] = 0.05
            
            if "暴击" in desc:
                effects["crit_bonus"] = 0.2
            
            if "闪避" in desc:
                effects["dodge_bonus"] = 0.15
            
            if "护盾" in desc:
                if "概率" in desc:
                    effects["shield_chance"] = 0.2
                else:
                    effects["shield_amount"] = 100
            
            if "攻击力提升" in desc or "攻击提升" in desc:
                effects["hp_based_attack"] = 0.4
            
            if "击杀" in desc and "恢复" in desc:
                effects["lifesteal_on_kill"] = 0.2
            
            if "伤害减免" in desc or "减伤" in desc:
                effects["damage_reduction"] = 0.1
            
            if "速度" in desc and "提升" in desc:
                effects["speed_bonus"] = 0.1
            
            if "防御" in desc and "提升" in desc:
                effects["defense_bonus"] = 0.15
            
            if "生命" in desc and "提升" in desc:
                effects["hp_bonus"] = 0.15
            
            if "全属性" in desc or "所有属性" in desc:
                effects["all_bonus"] = 0.1
            
            if effects:
                PASSIVE_EFFECTS[passive_name] = effects

_auto_generate_passive_effects()

TACTICAL_SKILLS = {
    "zhuge_liang": {
        "name": "空城计",
        "description": "诸葛亮的独门绝技，使敌人不敢进攻",
        "effects": {"enemy_fear": True, "damage_reduction": 0.5},
        "cooldown": 5
    },
    "zhou_yu": {
        "name": "火烧赤壁",
        "description": "周瑜的火攻绝技，对敌人造成大量伤害",
        "effects": {"fire_damage": 500, "burning": True},
        "cooldown": 6
    },
    "sima_yi": {
        "name": "隐忍",
        "description": "司马懿的隐忍绝技，蓄力后爆发",
        "effects": {"power_up": 0.5, "next_attack_double": True},
        "cooldown": 4
    },
    "guanyu": {
        "name": "武圣降临",
        "description": "关羽的终极绝技，提升所有属性",
        "effects": {"attack_bonus": 0.3, "defense_bonus": 0.3, "speed_bonus": 0.2},
        "cooldown": 5
    },
    "zhangfei": {
        "name": "怒吼",
        "description": "张飞的怒吼，震慑敌人",
        "effects": {"enemy_stun": True, "attack_bonus": 0.2},
        "cooldown": 4
    },
    "zhaoyun": {
        "name": "七进七出",
        "description": "赵云的冲锋绝技，无视敌人防御",
        "effects": {"armor_penetration": 0.5, "speed_bonus": 0.5},
        "cooldown": 5
    },
    "machao": {
        "name": "西凉铁骑",
        "description": "马超的骑兵绝技，快速攻击",
        "effects": {"speed_bonus": 0.5, "attack_bonus": 0.2},
        "cooldown": 4
    },
    "huangzhong": {
        "name": "百步穿杨",
        "description": "黄忠的箭术绝技，远程高伤害",
        "effects": {"ranged_damage": 800, "crit_chance": 0.5},
        "cooldown": 5
    },
    "liubei": {
        "name": "仁德",
        "description": "刘备的仁德绝技，恢复队友生命",
        "effects": {"heal_all": 500, "team_buff": 0.1},
        "cooldown": 5
    },
    "caocao": {
        "name": "乱世枭雄",
        "description": "曹操的枭雄绝技，压制敌人",
        "effects": {"enemy_debuff": 0.2, "attack_bonus": 0.2},
        "cooldown": 5
    },
    "sunquan": {
        "name": "江东之主",
        "description": "孙权的统领绝技，强化水军",
        "effects": {"team_defense": 0.2, "water_bonus": 0.3},
        "cooldown": 5
    },
    "lvbu": {
        "name": "人中吕布",
        "description": "吕布的最强绝技，无人能挡",
        "effects": {"attack_bonus": 0.5, "crit_damage": 0.5, "invincible": True},
        "cooldown": 6
    },
    "dianwei": {
        "name": "恶来",
        "description": "典韦的狂暴绝技，舍身护主",
        "effects": {"damage_reduction": 0.8, "taunt": True},
        "cooldown": 5
    },
    "xu_chu": {
        "name": "虎痴",
        "description": "许褚的勇猛绝技，越战越勇",
        "effects": {"attack_bonus_per_hp": 0.5, "hp_bonus": 500},
        "cooldown": 4
    },
    "zhenji": {
        "name": "洛神",
        "description": "甄姬的魅惑绝技，迷惑敌人",
        "effects": {"enemy_confusion": True, "team_heal": 300},
        "cooldown": 4
    },
    "diaochan": {
        "name": "倾国倾城",
        "description": "貂蝉的魅惑绝技，使敌人内讧",
        "effects": {"enemy_friendly_fire": True, "team_buff": 0.15},
        "cooldown": 5
    },
    "xiaoqiao": {
        "name": "琴音",
        "description": "小乔的琴音绝技，安抚队友",
        "effects": {"team_heal": 400, "team_defense": 0.15},
        "cooldown": 4
    },
    "daqiao": {
        "name": "水镜",
        "description": "大乔的水镜绝技，反射伤害",
        "effects": {"damage_reflect": 0.3, "team_buff": 0.1},
        "cooldown": 5
    },
    "guojia": {
        "name": "鬼才",
        "description": "郭嘉的计谋绝技，料事如神",
        "effects": {"skill_damage": 0.5, "cooldown_reduction": 2},
        "cooldown": 4
    },
    "xunyu": {
        "name": "王佐之才",
        "description": "荀彧的辅助绝技，强化队友",
        "effects": {"team_all_bonus": 0.2, "mana_regen": 200},
        "cooldown": 5
    },
    "xunyou": {
        "name": "谋主",
        "description": "荀攸的谋略绝技，削弱敌人",
        "effects": {"enemy_all_debuff": 0.2, "silence": True},
        "cooldown": 4
    },
    "贾诩": {
        "name": "毒士",
        "description": "贾诩的毒计绝技，持续伤害",
        "effects": {"poison_damage": 200, "enemy_debuff": 0.15},
        "cooldown": 4
    },
    "chengong": {
        "name": "忠义",
        "description": "陈宫的忠义绝技，舍身取义",
        "effects": {"damage_reduction": 0.5, "team_buff": 0.1},
        "cooldown": 5
    },
    "zhangliao": {
        "name": "威震逍遥津",
        "description": "张辽的冲锋绝技，威震敌胆",
        "effects": {"aoe_damage": 400, "enemy_fear": True},
        "cooldown": 5
    },
    "zhangxun": {
        "name": "八百破十万",
        "description": "张勋的勇猛绝技，以少胜多",
        "effects": {"attack_bonus": 0.5, "defense_bonus": 0.3},
        "cooldown": 5
    },
    "lejin": {
        "name": "先登",
        "description": "乐进的先锋绝技，率先破敌",
        "effects": {"first_strike": True, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "yujin": {
        "name": "持重",
        "description": "于禁的防守绝技，固若金汤",
        "effects": {"damage_reduction": 0.4, "team_defense": 0.15},
        "cooldown": 5
    },
    "xuande": {
        "name": "白马将军",
        "description": "公孙瓒的骑兵绝技，快速突击",
        "effects": {"speed_bonus": 0.5, "ranged_attack": True},
        "cooldown": 4
    },
    "yuanben": {
        "name": "四世三公",
        "description": "袁绍的名门绝技，声势浩大",
        "effects": {"team_attack": 0.2, "aoe_damage": 300},
        "cooldown": 5
    },
    "taishici": {
        "name": "勇冠三军",
        "description": "太史慈的勇猛绝技，双戟无敌",
        "effects": {"dual_wield": True, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "ganjiang": {
        "name": "锦帆贼",
        "description": "甘宁的水战绝技，来去如风",
        "effects": {"water_bonus": 0.5, "speed_bonus": 0.3},
        "cooldown": 4
    },
    "huanggai": {
        "name": "苦肉计",
        "description": "黄盖的牺牲绝技，诈降破敌",
        "effects": {"self_damage": 300, "enemy_damage": 800},
        "cooldown": 6
    },
    "lingtong": {
        "name": "破贼",
        "description": "凌统的近战绝技，破阵杀敌",
        "effects": {"armor_penetration": 0.3, "attack_bonus": 0.2},
        "cooldown": 4
    },
    "luomeng": {
        "name": "白衣渡江",
        "description": "吕蒙的奇袭绝技，偷渡破城",
        "effects": {"stealth": True, "backstab": True},
        "cooldown": 5
    },
    "shuxiang": {
        "name": "火烧连营",
        "description": "陆逊的火攻绝技，焚烧敌军",
        "effects": {"fire_damage": 600, "burning": True},
        "cooldown": 6
    },
    "zhugejin": {
        "name": "稳重",
        "description": "诸葛瑾的防守绝技，稳重如山",
        "effects": {"damage_reduction": 0.3, "team_defense": 0.1},
        "cooldown": 5
    },
    "zhangheng": {
        "name": "木牛流马",
        "description": "张衡的机关绝技，运送粮草",
        "effects": {"resource_bonus": 0.3, "heal_all": 200},
        "cooldown": 6
    },
    "weiyan": {
        "name": "奇袭",
        "description": "魏延的奇袭绝技，出其不意",
        "effects": {"stealth": True, "attack_bonus": 0.5},
        "cooldown": 5
    },
    "jiangwei": {
        "name": "北伐",
        "description": "姜维的北伐绝技，勇往直前",
        "effects": {"attack_bonus": 0.3, "defense_bonus": 0.2},
        "cooldown": 5
    },
    "fa_zheng": {
        "name": "奇谋",
        "description": "法正的奇谋绝技，料敌先机",
        "effects": {"skill_damage": 0.4, "cooldown_reduction": 1},
        "cooldown": 4
    },
    "peng_tong": {
        "name": "蛮王",
        "description": "孟获的蛮族绝技，力大无穷",
        "effects": {"attack_bonus": 0.4, "hp_bonus": 800},
        "cooldown": 5
    },
    "zhurong": {
        "name": "祝融",
        "description": "祝融夫人的火神绝技，火焰攻击",
        "effects": {"fire_damage": 400, "burning": True},
        "cooldown": 4
    },
    "kongming": {
        "name": "借东风",
        "description": "诸葛亮的呼风唤雨绝技",
        "effects": {"weather_control": True, "team_buff": 0.2},
        "cooldown": 6
    },
    "jiangdong": {
        "name": "江东子弟",
        "description": "孙策的统领绝技，江东儿郎",
        "effects": {"team_attack": 0.25, "speed_bonus": 0.2},
        "cooldown": 5
    },
    "sunjian": {
        "name": "江东猛虎",
        "description": "孙坚的勇猛绝技，猛虎下山",
        "effects": {"attack_bonus": 0.4, "defense_bonus": 0.1},
        "cooldown": 4
    },
    "sunce": {
        "name": "小霸王",
        "description": "孙策的霸王绝技，势不可挡",
        "effects": {"attack_bonus": 0.5, "crit_chance": 0.3},
        "cooldown": 5
    },
    "wuzhangyuan": {
        "name": "七星灯",
        "description": "诸葛亮的续命绝技",
        "effects": {"resurrect": True, "hp_restore": 0.5},
        "cooldown": 8
    },
    "mulan": {
        "name": "代父从军",
        "description": "花木兰的巾帼绝技",
        "effects": {"attack_bonus": 0.3, "defense_bonus": 0.3, "speed_bonus": 0.2},
        "cooldown": 5
    },
    "hua_mulan": {
        "name": "巾帼英雄",
        "description": "花木兰的变身绝技",
        "effects": {"transform": True, "all_bonus": 0.2},
        "cooldown": 5
    },
    "huangdi": {
        "name": "炎黄血脉",
        "description": "黄帝的血脉绝技",
        "effects": {"all_bonus": 0.5, "immortal": True},
        "cooldown": 8
    },
    "yao": {
        "name": "禅让",
        "description": "尧帝的仁德绝技",
        "effects": {"team_heal": 1000, "team_buff": 0.3},
        "cooldown": 6
    },
    "shun": {
        "name": "孝德",
        "description": "舜帝的孝道绝技",
        "effects": {"damage_reduction": 0.5, "team_defense": 0.3},
        "cooldown": 6
    },
    "yu": {
        "name": "治水",
        "description": "大禹的治水绝技",
        "effects": {"water_control": True, "aoe_damage": 600},
        "cooldown": 6
    },
    "tangyao": {
        "name": "唐尧",
        "description": "唐尧的圣德绝技",
        "effects": {"team_all_bonus": 0.3, "heal_all": 800},
        "cooldown": 6
    },
    "yushun": {
        "name": "虞舜",
        "description": "虞舜的圣明绝技",
        "effects": {"damage_reduction": 0.6, "team_buff": 0.2},
        "cooldown": 6
    },
    "xiaoyu": {
        "name": "夏禹",
        "description": "夏禹的伟业绝技",
        "effects": {"aoe_damage": 800, "water_bonus": 0.5},
        "cooldown": 7
    },
    "zhuanxu": {
        "name": "高阳",
        "description": "颛顼的帝王绝技",
        "effects": {"all_bonus": 0.4, "crit_chance": 0.3},
        "cooldown": 6
    },
    "diqiao": {
        "name": "高辛",
        "description": "帝喾的仁德绝技",
        "effects": {"team_heal": 600, "team_buff": 0.25},
        "cooldown": 5
    },
    "huangong": {
        "name": "共工",
        "description": "共工的水神绝技",
        "effects": {"water_damage": 800, "flood": True},
        "cooldown": 6
    },
    "zhurong_shen": {
        "name": "祝融火神",
        "description": "祝融的火神绝技",
        "effects": {"fire_damage": 800, "burning": True},
        "cooldown": 6
    },
    "gonggong": {
        "name": "水神",
        "description": "共工的水神绝技",
        "effects": {"water_damage": 600, "aoe_damage": 400},
        "cooldown": 5
    },
    "wuxian": {
        "name": "巫族",
        "description": "巫族的神秘绝技",
        "effects": {"dark_damage": 500, "debuff": True},
        "cooldown": 5
    },
    "fuxi": {
        "name": "伏羲",
        "description": "伏羲的创世绝技",
        "effects": {"all_bonus": 0.5, "skill_damage": 0.5},
        "cooldown": 7
    },
    "nvwa": {
        "name": "女娲",
        "description": "女娲的补天绝技",
        "effects": {"resurrect_all": True, "heal_all": 1000},
        "cooldown": 8
    },
    "suiren": {
        "name": "燧人",
        "description": "燧人的取火绝技",
        "effects": {"fire_damage": 600, "burning": True},
        "cooldown": 5
    },
    "youchao": {
        "name": "有巢",
        "description": "有巢的筑巢绝技",
        "effects": {"damage_reduction": 0.5, "hp_bonus": 1000},
        "cooldown": 6
    },
    "shangtang": {
        "name": "商汤",
        "description": "商汤的仁德绝技",
        "effects": {"team_heal": 800, "team_buff": 0.3},
        "cooldown": 6
    },
    "zhouwen": {
        "name": "周文王",
        "description": "周文王的仁德绝技",
        "effects": {"team_all_bonus": 0.3, "mana_regen": 300},
        "cooldown": 6
    },
    "zhouwu": {
        "name": "周武王",
        "description": "周武王的伐纣绝技",
        "effects": {"attack_bonus": 0.4, "aoe_damage": 500},
        "cooldown": 6
    },
    "jiangziya": {
        "name": "太公兵法",
        "description": "姜子牙的兵法绝技",
        "effects": {"skill_damage": 0.5, "cooldown_reduction": 2},
        "cooldown": 5
    },
    "wuding": {
        "name": "武丁",
        "description": "武丁的中兴绝技",
        "effects": {"attack_bonus": 0.4, "defense_bonus": 0.2},
        "cooldown": 5
    },
    "pan_geng": {
        "name": "盘庚",
        "description": "盘庚的迁都绝技",
        "effects": {"resource_bonus": 0.5, "team_buff": 0.2},
        "cooldown": 6
    },
    "liuwang": {
        "name": "纣王",
        "description": "纣王的暴君绝技",
        "effects": {"attack_bonus": 0.5, "hp_bonus": 800},
        "cooldown": 5
    },
    "daji": {
        "name": "妲己",
        "description": "妲己的妖媚绝技",
        "effects": {"enemy_confusion": True, "team_buff": 0.2},
        "cooldown": 5
    },
    "huangfeihu": {
        "name": "黄飞虎",
        "description": "黄飞虎的武成王绝技",
        "effects": {"attack_bonus": 0.4, "defense_bonus": 0.2},
        "cooldown": 5
    },
    "yinshang": {
        "name": "殷商",
        "description": "殷商的王朝绝技",
        "effects": {"team_attack": 0.3, "team_defense": 0.2},
        "cooldown": 6
    },
    "xizhou": {
        "name": "西周",
        "description": "西周的王朝绝技",
        "effects": {"team_buff": 0.3, "heal_all": 600},
        "cooldown": 6
    },
    "qinhuang": {
        "name": "秦始皇",
        "description": "秦始皇的统一绝技",
        "effects": {"all_bonus": 0.5, "aoe_damage": 600},
        "cooldown": 7
    },
    "liubang": {
        "name": "汉高祖",
        "description": "刘邦的帝王绝技",
        "effects": {"team_buff": 0.3, "heal_all": 800},
        "cooldown": 6
    },
    "xiangyu": {
        "name": "项羽",
        "description": "项羽的霸王绝技",
        "effects": {"attack_bonus": 0.6, "hp_bonus": 1000},
        "cooldown": 6
    },
    "zhangliang": {
        "name": "张良",
        "description": "张良的谋略绝技",
        "effects": {"skill_damage": 0.5, "cooldown_reduction": 2},
        "cooldown": 5
    },
    "hanxin": {
        "name": "韩信",
        "description": "韩信的兵仙绝技",
        "effects": {"attack_bonus": 0.4, "armor_penetration": 0.3},
        "cooldown": 5
    },
    "lvbu_changshan": {
        "name": "常山赵子龙",
        "description": "赵云的常山绝技",
        "effects": {"speed_bonus": 0.5, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "guanyu_yunchang": {
        "name": "关云长",
        "description": "关羽的云长绝技",
        "effects": {"attack_bonus": 0.4, "defense_bonus": 0.3},
        "cooldown": 5
    },
    "zhangfei_yide": {
        "name": "张翼德",
        "description": "张飞的翼德绝技",
        "effects": {"attack_bonus": 0.5, "taunt": True},
        "cooldown": 4
    },
    "zhugekongming": {
        "name": "诸葛孔明",
        "description": "诸葛亮的孔明绝技",
        "effects": {"skill_damage": 0.5, "team_buff": 0.2},
        "cooldown": 5
    },
    "caocaomengde": {
        "name": "曹孟德",
        "description": "曹操的孟德绝技",
        "effects": {"attack_bonus": 0.3, "skill_damage": 0.3},
        "cooldown": 5
    },
    "sunquanchongmou": {
        "name": "孙仲谋",
        "description": "孙权的仲谋绝技",
        "effects": {"team_defense": 0.3, "heal_all": 600},
        "cooldown": 5
    },
    "zhouyu_gongjin": {
        "name": "周公瑾",
        "description": "周瑜的公瑾绝技",
        "effects": {"skill_damage": 0.4, "fire_damage": 500},
        "cooldown": 5
    },
    "machao_wenhou": {
        "name": "马孟起",
        "description": "马超的孟起绝技",
        "effects": {"speed_bonus": 0.5, "attack_bonus": 0.4},
        "cooldown": 4
    },
    "huangzhong_hansheng": {
        "name": "黄汉升",
        "description": "黄忠的汉升绝技",
        "effects": {"ranged_damage": 800, "crit_chance": 0.5},
        "cooldown": 5
    },
    "xuhuang_gongming": {
        "name": "徐晃",
        "description": "徐晃的公明绝技",
        "effects": {"defense_bonus": 0.3, "damage_reduction": 0.2},
        "cooldown": 5
    },
    "zhanghe_yigong": {
        "name": "张郃",
        "description": "张郃的儁乂绝技",
        "effects": {"speed_bonus": 0.4, "attack_bonus": 0.2},
        "cooldown": 4
    },
    "li Dian": {
        "name": "李典",
        "description": "李典的曼成绝技",
        "effects": {"defense_bonus": 0.3, "team_defense": 0.1},
        "cooldown": 5
    },
    "wangping": {
        "name": "王平",
        "description": "王平的子均绝技",
        "effects": {"defense_bonus": 0.3, "damage_reduction": 0.15},
        "cooldown": 5
    },
    "zhangyi": {
        "name": "张仪",
        "description": "张仪的连横绝技",
        "effects": {"skill_damage": 0.4, "debuff": True},
        "cooldown": 5
    },
    "suqin": {
        "name": "苏秦",
        "description": "苏秦的合纵绝技",
        "effects": {"team_buff": 0.3, "cooldown_reduction": 1},
        "cooldown": 5
    },
    "guiguzi": {
        "name": "鬼谷子",
        "description": "鬼谷子的神秘绝技",
        "effects": {"skill_damage": 0.6, "all_bonus": 0.3},
        "cooldown": 6
    },
    "sunbin": {
        "name": "孙膑",
        "description": "孙膑的兵法绝技",
        "effects": {"skill_damage": 0.4, "armor_penetration": 0.3},
        "cooldown": 5
    },
    "pangjuan": {
        "name": "庞涓",
        "description": "庞涓的兵法绝技",
        "effects": {"attack_bonus": 0.4, "debuff": True},
        "cooldown": 5
    },
    "hanfeizi": {
        "name": "韩非子",
        "description": "韩非子的法家绝技",
        "effects": {"skill_damage": 0.3, "team_buff": 0.2},
        "cooldown": 5
    },
    "lisi": {
        "name": "李斯",
        "description": "李斯的法家绝技",
        "effects": {"resource_bonus": 0.4, "team_buff": 0.15},
        "cooldown": 5
    },
    "mengtian": {
        "name": "蒙恬",
        "description": "蒙恬的筑长城绝技",
        "effects": {"defense_bonus": 0.4, "damage_reduction": 0.2},
        "cooldown": 5
    },
    "mengchong": {
        "name": "蒙冲",
        "description": "蒙冲的水军绝技",
        "effects": {"water_bonus": 0.5, "speed_bonus": 0.3},
        "cooldown": 4
    },
    "zhaoxiangwang": {
        "name": "秦昭襄王",
        "description": "秦昭襄王的帝王绝技",
        "effects": {"all_bonus": 0.3, "team_buff": 0.2},
        "cooldown": 6
    },
    "weizhaowang": {
        "name": "魏昭王",
        "description": "魏昭王的帝王绝技",
        "effects": {"attack_bonus": 0.3, "team_attack": 0.15},
        "cooldown": 5
    },
    "zhuzhuangwang": {
        "name": "楚庄王",
        "description": "楚庄王的帝王绝技",
        "effects": {"attack_bonus": 0.4, "defense_bonus": 0.2},
        "cooldown": 5
    },
    "yanzhwang": {
        "name": "燕昭王",
        "description": "燕昭王的帝王绝技",
        "effects": {"team_buff": 0.3, "resource_bonus": 0.3},
        "cooldown": 5
    },
    "qinzhuangxiangwang": {
        "name": "秦庄襄王",
        "description": "秦庄襄王的帝王绝技",
        "effects": {"all_bonus": 0.25, "heal_all": 500},
        "cooldown": 5
    },
    "wangjian": {
        "name": "王翦",
        "description": "王翦的名将绝技",
        "effects": {"attack_bonus": 0.4, "aoe_damage": 400},
        "cooldown": 5
    },
    "li xin": {
        "name": "李信",
        "description": "李信的名将绝技",
        "effects": {"speed_bonus": 0.4, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "zhanghan": {
        "name": "章邯",
        "description": "章邯的名将绝技",
        "effects": {"defense_bonus": 0.4, "damage_reduction": 0.2},
        "cooldown": 5
    },
    "chenshe": {
        "name": "陈胜",
        "description": "陈胜的起义绝技",
        "effects": {"attack_bonus": 0.3, "team_buff": 0.2},
        "cooldown": 5
    },
    "wu_gui": {
        "name": "吴广",
        "description": "吴广的起义绝技",
        "effects": {"defense_bonus": 0.3, "team_defense": 0.2},
        "cooldown": 5
    },
    "xianglijiang": {
        "name": "项梁",
        "description": "项梁的名将绝技",
        "effects": {"attack_bonus": 0.3, "team_attack": 0.2},
        "cooldown": 5
    },
    "fan_zeng": {
        "name": "范增",
        "description": "范增的谋士绝技",
        "effects": {"skill_damage": 0.4, "debuff": True},
        "cooldown": 5
    },
    "chenping": {
        "name": "陈平",
        "description": "陈平的谋士绝技",
        "effects": {"skill_damage": 0.3, "cooldown_reduction": 1},
        "cooldown": 5
    },
    "xiahouying": {
        "name": "夏侯婴",
        "description": "夏侯婴的名将绝技",
        "effects": {"speed_bonus": 0.4, "defense_bonus": 0.2},
        "cooldown": 4
    },
    "xiahouyuan": {
        "name": "夏侯渊",
        "description": "夏侯渊的名将绝技",
        "effects": {"speed_bonus": 0.5, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "xiahou_dun": {
        "name": "夏侯惇",
        "description": "夏侯惇的名将绝技",
        "effects": {"attack_bonus": 0.3, "hp_regen": 0.1},
        "cooldown": 5
    },
    "cao_ren": {
        "name": "曹仁",
        "description": "曹仁的名将绝技",
        "effects": {"defense_bonus": 0.4, "damage_reduction": 0.2},
        "cooldown": 5
    },
    "cao_hong": {
        "name": "曹洪",
        "description": "曹洪的名将绝技",
        "effects": {"hp_bonus": 800, "damage_reduction": 0.15},
        "cooldown": 5
    },
    "wang_yang": {
        "name": "王洋",
        "description": "王洋的神秘绝技",
        "effects": {"all_bonus": 0.3, "skill_damage": 0.3},
        "cooldown": 5
    },
    "chen_ming": {
        "name": "陈明",
        "description": "陈明的神秘绝技",
        "effects": {"attack_bonus": 0.3, "defense_bonus": 0.3},
        "cooldown": 5
    },
    "zhang_jian": {
        "name": "张健",
        "description": "张健的神秘绝技",
        "effects": {"speed_bonus": 0.4, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "liu_yi": {
        "name": "刘毅",
        "description": "刘毅的神秘绝技",
        "effects": {"skill_damage": 0.4, "cooldown_reduction": 1},
        "cooldown": 5
    },
    "yuan_yong": {
        "name": "袁勇",
        "description": "袁勇的神秘绝技",
        "effects": {"attack_bonus": 0.4, "crit_chance": 0.3},
        "cooldown": 5
    },
    "li_wu": {
        "name": "李武",
        "description": "李武的神秘绝技",
        "effects": {"defense_bonus": 0.4, "hp_bonus": 600},
        "cooldown": 5
    },
    "zhao_bao": {
        "name": "赵宝",
        "description": "赵宝的神秘绝技",
        "effects": {"speed_bonus": 0.5, "dodge_chance": 0.3},
        "cooldown": 4
    },
    "sun_feng": {
        "name": "孙锋",
        "description": "孙锋的神秘绝技",
        "effects": {"skill_damage": 0.3, "heal_bonus": 0.3},
        "cooldown": 5
    },
    "zhou_bo": {
        "name": "周波",
        "description": "周波的神秘绝技",
        "effects": {"attack_bonus": 0.3, "defense_bonus": 0.2},
        "cooldown": 5
    },
    "wu_jie": {
        "name": "吴杰",
        "description": "吴杰的神秘绝技",
        "effects": {"all_bonus": 0.2, "team_buff": 0.15},
        "cooldown": 5
    },
    "zheng_wei": {
        "name": "郑伟",
        "description": "郑伟的神秘绝技",
        "effects": {"attack_bonus": 0.3, "speed_bonus": 0.2},
        "cooldown": 4
    },
    "wang_hua": {
        "name": "王华",
        "description": "王华的神秘绝技",
        "effects": {"defense_bonus": 0.3, "hp_regen": 0.1},
        "cooldown": 5
    },
    "xu_qing": {
        "name": "徐青",
        "description": "徐青的神秘绝技",
        "effects": {"skill_damage": 0.35, "mana_regen": 200},
        "cooldown": 5
    },
    "chen_liang": {
        "name": "陈亮",
        "description": "陈亮的神秘绝技",
        "effects": {"attack_bonus": 0.35, "crit_chance": 0.2},
        "cooldown": 5
    },
    "huang_yi": {
        "name": "黄毅",
        "description": "黄毅的神秘绝技",
        "effects": {"defense_bonus": 0.35, "damage_reduction": 0.15},
        "cooldown": 5
    },
    "lin_fei": {
        "name": "林飞",
        "description": "林飞的神秘绝技",
        "effects": {"speed_bonus": 0.45, "dodge_chance": 0.25},
        "cooldown": 4
    },
    "tang_jun": {
        "name": "唐军",
        "description": "唐军的神秘绝技",
        "effects": {"skill_damage": 0.4, "heal_bonus": 0.25},
        "cooldown": 5
    },
    "xue_feng": {
        "name": "薛峰",
        "description": "薛峰的神秘绝技",
        "effects": {"attack_bonus": 0.4, "speed_bonus": 0.25},
        "cooldown": 4
    },
    "he_yong": {
        "name": "何勇",
        "description": "何勇的神秘绝技",
        "effects": {"defense_bonus": 0.4, "hp_bonus": 500},
        "cooldown": 5
    },
    "luo_wei": {
        "name": "罗伟",
        "description": "罗伟的神秘绝技",
        "effects": {"all_bonus": 0.25, "team_buff": 0.2},
        "cooldown": 5
    },
    "guo_qing": {
        "name": "郭庆",
        "description": "郭庆的神秘绝技",
        "effects": {"skill_damage": 0.35, "cooldown_reduction": 1},
        "cooldown": 5
    },
    "fang_liang": {
        "name": "方亮",
        "description": "方亮的神秘绝技",
        "effects": {"attack_bonus": 0.35, "defense_bonus": 0.25},
        "cooldown": 5
    },
    "ding_jun": {
        "name": "丁军",
        "description": "丁军的神秘绝技",
        "effects": {"speed_bonus": 0.4, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "xiang_yi": {
        "name": "项毅",
        "description": "项毅的神秘绝技",
        "effects": {"skill_damage": 0.4, "hp_regen": 0.1},
        "cooldown": 5
    },
    "liang_jun": {
        "name": "梁军",
        "description": "梁军的神秘绝技",
        "effects": {"attack_bonus": 0.3, "crit_damage": 0.3},
        "cooldown": 5
    },
    "zhang_wei": {
        "name": "张伟",
        "description": "张伟的神秘绝技",
        "effects": {"defense_bonus": 0.3, "damage_reduction": 0.2},
        "cooldown": 5
    },
    "peng_fei": {
        "name": "彭飞",
        "description": "彭飞的神秘绝技",
        "effects": {"speed_bonus": 0.5, "attack_bonus": 0.25},
        "cooldown": 4
    },
    "yuan_liang": {
        "name": "袁亮",
        "description": "袁亮的神秘绝技",
        "effects": {"skill_damage": 0.35, "team_buff": 0.2},
        "cooldown": 5
    },
    "sun_wei": {
        "name": "孙伟",
        "description": "孙伟的神秘绝技",
        "effects": {"attack_bonus": 0.3, "defense_bonus": 0.3},
        "cooldown": 5
    },
    "zhao_feng": {
        "name": "赵锋",
        "description": "赵锋的神秘绝技",
        "effects": {"speed_bonus": 0.4, "dodge_chance": 0.2},
        "cooldown": 4
    },
    "liu_jun": {
        "name": "刘军",
        "description": "刘军的神秘绝技",
        "effects": {"skill_damage": 0.4, "heal_bonus": 0.25},
        "cooldown": 5
    },
    "wu_qing": {
        "name": "吴青",
        "description": "吴青的神秘绝技",
        "effects": {"attack_bonus": 0.35, "speed_bonus": 0.2},
        "cooldown": 4
    },
    "song_liang": {
        "name": "宋亮",
        "description": "宋亮的神秘绝技",
        "effects": {"defense_bonus": 0.35, "hp_bonus": 600},
        "cooldown": 5
    },
    "yang_fei": {
        "name": "杨飞",
        "description": "杨飞的神秘绝技",
        "effects": {"speed_bonus": 0.45, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "chen_jun": {
        "name": "陈军",
        "description": "陈军的神秘绝技",
        "effects": {"skill_damage": 0.35, "cooldown_reduction": 1},
        "cooldown": 5
    },
    "zhou_qing": {
        "name": "周庆",
        "description": "周庆的神秘绝技",
        "effects": {"attack_bonus": 0.4, "defense_bonus": 0.2},
        "cooldown": 5
    },
    "wu_feng": {
        "name": "吴锋",
        "description": "吴锋的神秘绝技",
        "effects": {"speed_bonus": 0.5, "crit_chance": 0.25},
        "cooldown": 4
    },
    "zheng_jun": {
        "name": "郑军",
        "description": "郑军的神秘绝技",
        "effects": {"skill_damage": 0.4, "team_buff": 0.2},
        "cooldown": 5
    },
    "wang_liang": {
        "name": "王亮",
        "description": "王亮的神秘绝技",
        "effects": {"attack_bonus": 0.35, "defense_bonus": 0.3},
        "cooldown": 5
    },
    "xu_jun": {
        "name": "徐军",
        "description": "徐军的神秘绝技",
        "effects": {"speed_bonus": 0.4, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "chen_yong": {
        "name": "陈勇",
        "description": "陈勇的神秘绝技",
        "effects": {"skill_damage": 0.4, "hp_regen": 0.1},
        "cooldown": 5
    },
    "huang_feng": {
        "name": "黄锋",
        "description": "黄锋的神秘绝技",
        "effects": {"attack_bonus": 0.4, "speed_bonus": 0.25},
        "cooldown": 4
    },
    "lin_jun": {
        "name": "林军",
        "description": "林军的神秘绝技",
        "effects": {"defense_bonus": 0.4, "damage_reduction": 0.15},
        "cooldown": 5
    },
    "tang_liang": {
        "name": "唐亮",
        "description": "唐亮的神秘绝技",
        "effects": {"all_bonus": 0.25, "team_buff": 0.2},
        "cooldown": 5
    },
    "xue_qing": {
        "name": "薛青",
        "description": "薛青的神秘绝技",
        "effects": {"skill_damage": 0.35, "cooldown_reduction": 1},
        "cooldown": 5
    },
    "he_liang": {
        "name": "何亮",
        "description": "何亮的神秘绝技",
        "effects": {"attack_bonus": 0.35, "defense_bonus": 0.25},
        "cooldown": 5
    },
    "luo_feng": {
        "name": "罗峰",
        "description": "罗峰的神秘绝技",
        "effects": {"speed_bonus": 0.4, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "guo_jun": {
        "name": "郭军",
        "description": "郭军的神秘绝技",
        "effects": {"skill_damage": 0.4, "hp_regen": 0.1},
        "cooldown": 5
    },
    "fang_jun": {
        "name": "方军",
        "description": "方军的神秘绝技",
        "effects": {"attack_bonus": 0.3, "crit_damage": 0.3},
        "cooldown": 5
    },
    "ding_liang": {
        "name": "丁亮",
        "description": "丁亮的神秘绝技",
        "effects": {"defense_bonus": 0.3, "damage_reduction": 0.2},
        "cooldown": 5
    },
    "xiang_wei": {
        "name": "项伟",
        "description": "项伟的神秘绝技",
        "effects": {"speed_bonus": 0.5, "attack_bonus": 0.25},
        "cooldown": 4
    },
    "liang_wei": {
        "name": "梁伟",
        "description": "梁伟的神秘绝技",
        "effects": {"skill_damage": 0.35, "team_buff": 0.2},
        "cooldown": 5
    },
    "zhang_feng": {
        "name": "张锋",
        "description": "张锋的神秘绝技",
        "effects": {"attack_bonus": 0.3, "defense_bonus": 0.3},
        "cooldown": 5
    },
    "peng_wei": {
        "name": "彭伟",
        "description": "彭伟的神秘绝技",
        "effects": {"speed_bonus": 0.4, "dodge_chance": 0.2},
        "cooldown": 4
    },
    "yuan_wei": {
        "name": "袁伟",
        "description": "袁伟的神秘绝技",
        "effects": {"skill_damage": 0.4, "heal_bonus": 0.25},
        "cooldown": 5
    },
    "sun_qing": {
        "name": "孙庆",
        "description": "孙庆的神秘绝技",
        "effects": {"attack_bonus": 0.35, "speed_bonus": 0.2},
        "cooldown": 4
    },
    "zhao_wei": {
        "name": "赵伟",
        "description": "赵伟的神秘绝技",
        "effects": {"defense_bonus": 0.35, "hp_bonus": 600},
        "cooldown": 5
    },
    "liu_liang": {
        "name": "刘亮",
        "description": "刘亮的神秘绝技",
        "effects": {"speed_bonus": 0.45, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "wu_jun": {
        "name": "吴军",
        "description": "吴军的神秘绝技",
        "effects": {"skill_damage": 0.35, "cooldown_reduction": 1},
        "cooldown": 5
    },
    "song_jun": {
        "name": "宋军",
        "description": "宋军的神秘绝技",
        "effects": {"attack_bonus": 0.4, "defense_bonus": 0.2},
        "cooldown": 5
    },
    "yang_jun": {
        "name": "杨军",
        "description": "杨军的神秘绝技",
        "effects": {"speed_bonus": 0.5, "crit_chance": 0.25},
        "cooldown": 4
    },
    "chen_qing": {
        "name": "陈庆",
        "description": "陈庆的神秘绝技",
        "effects": {"skill_damage": 0.4, "team_buff": 0.2},
        "cooldown": 5
    },
    "zhou_wei": {
        "name": "周伟",
        "description": "周伟的神秘绝技",
        "effects": {"attack_bonus": 0.35, "defense_bonus": 0.3},
        "cooldown": 5
    },
    "wu_wei": {
        "name": "吴伟",
        "description": "吴伟的神秘绝技",
        "effects": {"speed_bonus": 0.4, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "zheng_liang": {
        "name": "郑亮",
        "description": "郑亮的神秘绝技",
        "effects": {"skill_damage": 0.4, "hp_regen": 0.1},
        "cooldown": 5
    },
    "wang_feng": {
        "name": "王锋",
        "description": "王锋的神秘绝技",
        "effects": {"attack_bonus": 0.4, "speed_bonus": 0.25},
        "cooldown": 4
    },
    "xu_liang": {
        "name": "徐亮",
        "description": "徐亮的神秘绝技",
        "effects": {"defense_bonus": 0.4, "damage_reduction": 0.15},
        "cooldown": 5
    },
    "chen_wei": {
        "name": "陈伟",
        "description": "陈伟的神秘绝技",
        "effects": {"all_bonus": 0.25, "team_buff": 0.2},
        "cooldown": 5
    },
    "huang_wei": {
        "name": "黄伟",
        "description": "黄伟的神秘绝技",
        "effects": {"skill_damage": 0.35, "cooldown_reduction": 1},
        "cooldown": 5
    },
    "lin_wei": {
        "name": "林伟",
        "description": "林伟的神秘绝技",
        "effects": {"attack_bonus": 0.35, "defense_bonus": 0.25},
        "cooldown": 5
    },
    "tang_wei": {
        "name": "唐伟",
        "description": "唐伟的神秘绝技",
        "effects": {"speed_bonus": 0.4, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "xue_wei": {
        "name": "薛伟",
        "description": "薛伟的神秘绝技",
        "effects": {"skill_damage": 0.4, "hp_regen": 0.1},
        "cooldown": 5
    },
    "he_wei": {
        "name": "何伟",
        "description": "何伟的神秘绝技",
        "effects": {"attack_bonus": 0.3, "crit_damage": 0.3},
        "cooldown": 5
    },
    "luo_wei": {
        "name": "罗伟",
        "description": "罗伟的神秘绝技",
        "effects": {"defense_bonus": 0.3, "damage_reduction": 0.2},
        "cooldown": 5
    },
    "guo_wei": {
        "name": "郭伟",
        "description": "郭伟的神秘绝技",
        "effects": {"speed_bonus": 0.5, "attack_bonus": 0.25},
        "cooldown": 4
    },
    "fang_wei": {
        "name": "方伟",
        "description": "方伟的神秘绝技",
        "effects": {"skill_damage": 0.35, "team_buff": 0.2},
        "cooldown": 5
    },
    "ding_wei": {
        "name": "丁伟",
        "description": "丁伟的神秘绝技",
        "effects": {"attack_bonus": 0.3, "defense_bonus": 0.3},
        "cooldown": 5
    },
    "xiang_liang": {
        "name": "项亮",
        "description": "项亮的神秘绝技",
        "effects": {"speed_bonus": 0.4, "dodge_chance": 0.2},
        "cooldown": 4
    },
    "liang_liang": {
        "name": "梁亮",
        "description": "梁亮的神秘绝技",
        "effects": {"skill_damage": 0.4, "heal_bonus": 0.25},
        "cooldown": 5
    },
    "zhang_wei": {
        "name": "张伟",
        "description": "张伟的神秘绝技",
        "effects": {"attack_bonus": 0.35, "speed_bonus": 0.2},
        "cooldown": 4
    },
    "peng_liang": {
        "name": "彭亮",
        "description": "彭亮的神秘绝技",
        "effects": {"defense_bonus": 0.35, "hp_bonus": 600},
        "cooldown": 5
    },
    "yuan_liang": {
        "name": "袁亮",
        "description": "袁亮的神秘绝技",
        "effects": {"speed_bonus": 0.45, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "sun_wei": {
        "name": "孙伟",
        "description": "孙伟的神秘绝技",
        "effects": {"skill_damage": 0.35, "cooldown_reduction": 1},
        "cooldown": 5
    },
    "zhao_liang": {
        "name": "赵亮",
        "description": "赵亮的神秘绝技",
        "effects": {"attack_bonus": 0.4, "defense_bonus": 0.2},
        "cooldown": 5
    },
    "liu_wei": {
        "name": "刘伟",
        "description": "刘伟的神秘绝技",
        "effects": {"speed_bonus": 0.5, "crit_chance": 0.25},
        "cooldown": 4
    },
    "wu_liang": {
        "name": "吴亮",
        "description": "吴亮的神秘绝技",
        "effects": {"skill_damage": 0.4, "team_buff": 0.2},
        "cooldown": 5
    },
    "song_wei": {
        "name": "宋伟",
        "description": "宋伟的神秘绝技",
        "effects": {"attack_bonus": 0.35, "defense_bonus": 0.3},
        "cooldown": 5
    },
    "yang_wei": {
        "name": "杨伟",
        "description": "杨伟的神秘绝技",
        "effects": {"speed_bonus": 0.4, "attack_bonus": 0.3},
        "cooldown": 4
    },
    "chen_liang": {
        "name": "陈亮",
        "description": "陈亮的神秘绝技",
        "effects": {"skill_damage": 0.4, "hp_regen": 0.1},
        "cooldown": 5
    },
    "zhou_liang": {
        "name": "周亮",
        "description": "周亮的神秘绝技",
        "effects": {"attack_bonus": 0.4, "speed_bonus": 0.25},
        "cooldown": 4
    },
    "wu_liang": {
        "name": "吴亮",
        "description": "吴亮的神秘绝技",
        "effects": {"defense_bonus": 0.4, "damage_reduction": 0.15},
        "cooldown": 5
    },
    "zheng_wei": {
        "name": "郑伟",
        "description": "郑伟的神秘绝技",
        "effects": {"all_bonus": 0.25, "team_buff": 0.2},
        "cooldown": 5
    }
}