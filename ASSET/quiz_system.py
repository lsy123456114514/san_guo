"""三国知识问答 - 小游戏中心玩法。

规则：
    * 每局随机抽取 10 道三国知识选择题。
    * 答对一题得 1 分，答错不扣分。
    * 结算时按得分发放金元宝，满分额外奖励时间卡。
    * 历史最佳成绩与累计正确率会被保存。
"""

import os
import time
import random

import pygame

from ASSET.game_data import data, save, logger, draw_gradient_bg, get_font
from ASSET import safe_exit

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

COLORS = {
    "bg_dark": (12, 16, 30),
    "bg_light": (24, 30, 52),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 180),
    "accent_blue_light": (100, 149, 237),
    "accent_green": (80, 190, 90),
    "accent_red": (210, 70, 70),
    "text_white": (255, 255, 255),
    "text_gray": (180, 185, 200),
    "panel_bg": (30, 36, 60),
}

QUESTIONS_PER_ROUND = 10
REWARD_PER_CORRECT = 15
FEEDBACK_DELAY = 0.9

# (题目, [四个选项], 正确选项下标)
QUESTIONS = [
    ("《三国演义》中，桃园结义的三位英雄是？",
     ["刘备、关羽、张飞", "曹操、刘备、孙权", "关羽、张飞、赵云", "诸葛亮、周瑜、司马懿"], 0),
    ("三国时期被称为「卧龙」的是谁？",
     ["庞统", "诸葛亮", "司马懿", "徐庶"], 1),
    ("与「卧龙」齐名，被称为「凤雏」的是？",
     ["庞统", "法正", "郭嘉", "荀彧"], 0),
    ("曹操的字是什么？",
     ["玄德", "孟德", "仲谋", "公瑾"], 1),
    ("关羽使用的兵器是？",
     ["丈八蛇矛", "青龙偃月刀", "方天画戟", "双股剑"], 1),
    ("「三顾茅庐」请出的是哪位谋士？",
     ["司马懿", "周瑜", "诸葛亮", "荀彧"], 2),
    ("赤壁之战中，孙刘联军击败的是谁？",
     ["袁绍", "董卓", "曹操", "吕布"], 2),
    ("「既生瑜，何生亮」这句话出自谁之口？",
     ["诸葛亮", "周瑜", "曹操", "鲁肃"], 1),
    ("官渡之战中，曹操击败了哪一方？",
     ["袁绍", "袁术", "刘表", "张绣"], 0),
    ("三国之中，魏国的建立者是？",
     ["曹操", "曹丕", "曹植", "曹叡"], 1),
    ("蜀汉的建立者是？",
     ["刘备", "刘禅", "刘表", "刘璋"], 0),
    ("吴国的建立者是？",
     ["孙坚", "孙策", "孙权", "孙皓"], 2),
    ("关羽「过五关斩六将」是为了寻找谁？",
     ["张飞", "刘备", "曹操", "赵云"], 1),
    ("「空城计」是下列哪位使用的？",
     ["诸葛亮", "司马懿", "周瑜", "姜维"], 0),
    ("白帝城托孤，刘备将刘禅托付给了谁？",
     ["关羽", "诸葛亮", "李严", "赵云"], 1),
    ("赵云在长坂坡救出的婴儿是？",
     ["刘封", "阿斗（刘禅）", "曹冲", "孙亮"], 1),
    ("华容道义释曹操的是哪位将领？",
     ["张飞", "赵云", "关羽", "黄忠"], 2),
    ("「七擒七纵」是诸葛亮平定谁的故事？",
     ["孟获", "张任", "严颜", "马谡"], 0),
    ("「草船借箭」的主角是？",
     ["周瑜", "诸葛亮", "鲁肃", "黄盖"], 1),
    ("貂蝉用连环计离间的是董卓和谁？",
     ["吕布", "李傕", "郭汜", "华雄"], 0),
    ("张辽威震逍遥津，大败的是哪一方？",
     ["曹操", "孙权", "刘备", "袁绍"], 1),
    ("下列哪一位不属于刘备的「五虎上将」？",
     ["关羽", "张飞", "魏延", "马超"], 2),
    ("三国最终统一于哪个朝代？",
     ["魏", "蜀", "吴", "晋"], 3),
    ("「单骑救主」说的是哪位将领？",
     ["张飞", "赵云", "马超", "黄忠"], 1),
]


class Button:
    """简洁的按钮控件。"""

    def __init__(self, text, x, y, width, height, font,
                 normal_color=COLORS["accent_blue"],
                 hover_color=COLORS["accent_blue_light"],
                 text_color=COLORS["text_white"]):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.normal_color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, COLORS["accent_gold"], self.rect, 2, border_radius=10)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        shadow = self.font.render(self.text, True, (0, 0, 0))
        surface.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def hit(self, pos):
        return self.rect.collidepoint(pos)


def draw_title(surface, text, y_pos, screen_width, font_big):
    for offset in range(5, 0, -1):
        alpha = max(0, 50 - offset * 8)
        glow = font_big.render(text, True, (*COLORS["accent_gold"][:3], alpha))
        glow_rect = glow.get_rect(center=(screen_width // 2, y_pos))
        surface.blit(glow, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow, (glow_rect.x + offset, glow_rect.y))
    title = font_big.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    shadow = font_big.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)


def wrap_text(text, font, max_width):
    """按像素宽度对中文文本逐字换行。"""
    lines = []
    current = ""
    for ch in text:
        if font.size(current + ch)[0] <= max_width:
            current += ch
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


class QuizSystem:
    """三国知识问答核心逻辑。"""

    def __init__(self):
        self._ensure_data()
        self.questions = []
        self.index = 0
        self.score = 0
        self.state = "menu"          # menu / playing / feedback / result
        self.feedback = None         # (chosen, correct, is_correct)
        self.feedback_time = 0.0
        self.last_reward = 0
        self.last_bonus = ""

    def _ensure_data(self):
        quiz = data.get("quiz")
        if not isinstance(quiz, dict):
            quiz = {}
        quiz.setdefault("best_score", 0)
        quiz.setdefault("total_played", 0)
        quiz.setdefault("total_correct", 0)
        quiz.setdefault("total_questions", 0)
        data["quiz"] = quiz

    @property
    def stats(self):
        return data["quiz"]

    def accuracy(self):
        total = self.stats["total_questions"]
        if total <= 0:
            return 0.0
        return self.stats["total_correct"] / total * 100

    def start(self):
        count = min(QUESTIONS_PER_ROUND, len(QUESTIONS))
        self.questions = random.sample(QUESTIONS, count)
        self.index = 0
        self.score = 0
        self.feedback = None
        self.last_reward = 0
        self.last_bonus = ""
        self.state = "playing"

    def current_question(self):
        if 0 <= self.index < len(self.questions):
            return self.questions[self.index]
        return None

    def answer(self, choice):
        question = self.current_question()
        if question is None or self.state != "playing":
            return
        correct = question[2]
        is_correct = (choice == correct)
        if is_correct:
            self.score += 1
        self.feedback = (choice, correct, is_correct)
        self.feedback_time = time.time()
        self.state = "feedback"

    def update(self):
        if self.state == "feedback" and time.time() - self.feedback_time >= FEEDBACK_DELAY:
            self.feedback = None
            self.index += 1
            if self.index >= len(self.questions):
                self._finish()
            else:
                self.state = "playing"

    def _finish(self):
        self.state = "result"
        gold = self.score * REWARD_PER_CORRECT
        data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + gold
        self.last_reward = gold

        if self.score == len(self.questions) and self.questions:
            data["resources"]["时间卡"] = data["resources"].get("时间卡", 0) + 1
            self.last_bonus = "完美通关！额外获得 时间卡×1"

        self.stats["total_played"] += 1
        self.stats["total_correct"] += self.score
        self.stats["total_questions"] += len(self.questions)
        if self.score > self.stats["best_score"]:
            self.stats["best_score"] = self.score
        save()


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------

def _draw_center_text(surface, text, font, color, y, screen_width):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(screen_width // 2, y))
    surface.blit(surf, rect)
    return rect


def draw_quiz(screen, system, fonts, option_buttons, menu_buttons):
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    font_big, font_main, font_small = fonts

    draw_title(screen, "三国知识问答", screen_height * 0.09, screen_width, font_big)

    if system.state == "menu":
        stats = system.stats
        y = screen_height * 0.30
        _draw_center_text(screen, f"历史最佳：{stats['best_score']} / {QUESTIONS_PER_ROUND}",
                          font_main, COLORS["accent_gold"], y, screen_width)
        _draw_center_text(screen, f"累计场次：{stats['total_played']}    正确率：{system.accuracy():.1f}%",
                          font_small, COLORS["text_gray"], y + 46, screen_width)
        _draw_center_text(screen, f"每局随机 {QUESTIONS_PER_ROUND} 题，答对一题得 {REWARD_PER_CORRECT} 金元宝",
                          font_small, COLORS["text_gray"], y + 84, screen_width)
        for btn in menu_buttons:
            btn.draw(screen)
        return

    if system.state in ("playing", "feedback"):
        question = system.current_question()
        if question is None:
            return

        _draw_center_text(screen, f"第 {system.index + 1} / {len(system.questions)} 题"
                                  f"    当前得分：{system.score}",
                          font_small, COLORS["accent_blue_light"], screen_height * 0.18, screen_width)

        # 题目面板
        panel = pygame.Rect(60, screen_height * 0.24, screen_width - 120, 120)
        panel_surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*COLORS["panel_bg"], 225), (0, 0, panel.width, panel.height), border_radius=12)
        screen.blit(panel_surf, (panel.x, panel.y))
        pygame.draw.rect(screen, COLORS["accent_gold"], panel, 2, border_radius=12)

        lines = wrap_text(question[0], font_main, panel.width - 40)
        line_y = panel.y + 22
        for line in lines[:3]:
            screen.blit(font_main.render(line, True, COLORS["text_white"]), (panel.x + 20, line_y))
            line_y += font_main.get_height() + 4

        # 选项
        feedback = system.feedback
        for i, btn in enumerate(option_buttons):
            btn.text = f"{'ABCD'[i]}. {question[1][i]}"
            if feedback:
                chosen, correct, _ = feedback
                if i == correct:
                    btn.normal_color = COLORS["accent_green"]
                    btn.hover_color = COLORS["accent_green"]
                elif i == chosen:
                    btn.normal_color = COLORS["accent_red"]
                    btn.hover_color = COLORS["accent_red"]
                else:
                    btn.normal_color = COLORS["accent_blue"]
                    btn.hover_color = COLORS["accent_blue_light"]
            else:
                btn.normal_color = COLORS["accent_blue"]
                btn.hover_color = COLORS["accent_blue_light"]
            btn.draw(screen)

        if feedback and feedback[2]:
            _draw_center_text(screen, "回答正确！", font_main, COLORS["accent_green"],
                              option_buttons[-1].rect.bottom + 30, screen_width)
        elif feedback:
            _draw_center_text(screen, f"回答错误，正确答案是 {'ABCD'[feedback[1]]}",
                              font_main, COLORS["accent_red"],
                              option_buttons[-1].rect.bottom + 30, screen_width)
        return

    # result
    _draw_center_text(screen, "本局结束", font_big, COLORS["accent_gold"],
                      screen_height * 0.26, screen_width)
    _draw_center_text(screen, f"答对 {system.score} / {len(system.questions)} 题",
                      font_main, COLORS["text_white"], screen_height * 0.38, screen_width)
    _draw_center_text(screen, f"获得 {system.last_reward} 金元宝",
                      font_main, COLORS["accent_gold"], screen_height * 0.46, screen_width)
    if system.last_bonus:
        _draw_center_text(screen, system.last_bonus, font_small, COLORS["accent_green"],
                          screen_height * 0.53, screen_width)
    _draw_center_text(screen, f"历史最佳：{system.stats['best_score']}",
                      font_small, COLORS["text_gray"], screen_height * 0.60, screen_width)
    for btn in menu_buttons:
        btn.draw(screen)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    """三国知识问答主函数。"""
    try:
        if not pygame.get_init():
            pygame.init()

        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            screen_width, screen_height = info.current_w, info.current_h
        else:
            resolution = data['settings']['graphics']['resolution']
            try:
                screen_width, screen_height = map(int, resolution.split('x'))
            except (ValueError, AttributeError):
                screen_width, screen_height = 900, 700

        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("三国知识问答")
        clock = pygame.time.Clock()

        font_big = get_font(48)
        font_main = get_font(28)
        font_small = get_font(20)
        fonts = (font_big, font_main, font_small)

        system = QuizSystem()

        # 选项按钮（4 个）
        opt_width = min(680, screen_width - 120)
        opt_height = 52
        opt_x = (screen_width - opt_width) // 2
        opt_y = screen_height * 0.24 + 120 + 30
        option_buttons = []
        for i in range(4):
            y = opt_y + i * (opt_height + 12)
            option_buttons.append(Button("", opt_x, y, opt_width, opt_height, font_small))

        # 菜单按钮（开始 / 返回）
        menu_btn_width = 240
        menu_btn_height = 56
        start_btn = Button("开始答题", (screen_width - menu_btn_width) // 2,
                           screen_height * 0.62, menu_btn_width, menu_btn_height, font_main,
                           normal_color=COLORS["accent_green"])
        menu_buttons = [start_btn]

        back_btn = Button("返回", screen_width - 150, screen_height - 66, 120, 48, font_small)

        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            system.update()

            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            draw_quiz(screen, system, fonts, option_buttons, menu_buttons)

            back_btn.check_hover(mouse_pos)
            back_btn.draw(screen)
            if system.state in ("playing", "feedback"):
                for btn in option_buttons:
                    btn.check_hover(mouse_pos)
            else:
                for btn in menu_buttons:
                    btn.check_hover(mouse_pos)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_btn.hit(event.pos):
                        running = False
                    elif system.state == "playing":
                        for i, btn in enumerate(option_buttons):
                            if btn.hit(event.pos):
                                system.answer(i)
                                break
                    elif system.state in ("menu", "result"):
                        if start_btn.hit(event.pos):
                            system.start()

            clock.tick(60)

        safe_exit("三国知识问答")
    except Exception as e:
        logger.info(f"三国知识问答异常：{str(e)}")
        import traceback
        traceback.print_exc()
        safe_exit("三国知识问答", str(e))


if __name__ == "__main__":
    main()
