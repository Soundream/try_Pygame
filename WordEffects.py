from TeamLogic import *
from colors import *
from GeneralSettings import *

withAnimation = True


def drawSurroundings(screen, text, position, text_surface, font=None, in_center=False):
    if not font:
        font = FONT(default_font_size+5)
    if in_center:
        text_rect = text_surface.get_rect(center=position)
        c_x, c_y = text_rect.center
    else:
        text_rect = text_surface.get_rect(position)
        c_x, c_y = position
    # 绘制描边
    for dx, dy in offsets:
        if in_center:
            surrounding_rect = text_surface.get_rect(center=(c_x + dx, c_y + dy))
        else:
            surrounding_rect = text_surface.get_rect(c_x + dx, c_y + dy)
        screen.blit(font.render(text, True, BLACK), surrounding_rect)



def draw_unit_info(character, position, font, screen, max_x=0):
    # 背景框宽度设置
    box_width = 210
    box_color = (0, 0, 0, 200)
    x, y = position

    # 准备文字
    attack_logic_translation = {
        "front": "前排",
        "back": "后排",
        "all": "任意位置",
        "none": "不了任何人"
    }

    line2 = []
    if character.str:
        line2.append(f"攻击力: {character.str}")
    if character.int:
        line2.append(f"法强: {character.int}")
    if character.heal:
        line2.append(f"奶量: {character.heal}")
    info_texts = [
        f"  {character.chinese_name}  ",
        f"生命值: {character.maxhp}"
    ] + line2 + [
        f"  偏好站在{attack_logic_translation[character.selfrow]}",
        f"   攻击{attack_logic_translation[character.targetrow]}",
        f""
    ]

    # 自动换行显示描述
    description_lines = wrap_chinese_text(character.chinese_description, font, box_width - 20)
    
    # 计算总行数
    total_lines = len(info_texts) + len(description_lines)
    line_height = 20
    box_height = 10 + total_lines * line_height + 10  # 上下边距为 10 像素

    # 防止框超出屏幕范围
    if max_x:
        x = min(x, max_x - 40 - box_width)
    else:
        x = min(x, screen_width - 10 - box_width)
    y = min(y, screen_height - 40 - box_height)

    # 绘制背景框
    surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    surface.fill(box_color)
    screen.blit(surface, (x, y))

    # 显示基础信息
    for i, text in enumerate(info_texts):
        if i == 0:
            rendered_text = FONT.size(default_font_size+3).render(text, True, WHITE)
            text_rect = rendered_text.get_rect(center=(x + box_width//2, y + 15))
            screen.blit(rendered_text, text_rect)
        else:
            rendered_text = font.render(text, True, WHITE)
            screen.blit(rendered_text, (x + 10, y + 10 + i * line_height))

    # 显示描述信息
    for i, line in enumerate(description_lines):
        rendered_text = font.render(line, True, WHITE)
        screen.blit(rendered_text, (x + 10, y + 10 + (len(info_texts) + i) * line_height))

# 自动换行函数
def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def wrap_chinese_text(text, font, max_width):
    lines = []
    current_line = ""
    for char in text:  # 按字符处理
        test_line = f"{current_line}{char}"  # 测试加入当前字符后的宽度
        if font.size(test_line)[0] <= max_width or char in "，。、！？":  # 如果加入字符后不超过最大宽度
            current_line = test_line
        else:
            lines.append(current_line) 
            current_line = char
    if current_line:
        lines.append(current_line) 
    return lines


class Words:
    def __init__(self, game, animation=None):
        self.word_effects = [] # 存储飘字效果
        self.font = FONT.size(default_font_size+5)

        self.animation = animation
        if game:
            self.game = game
            self.screen = game.screen

        self.recorded_positions = {}

        self.multi_attack = False
        self.voice_inserted = False
        self.initialized = False
    
    def add_text(self, text0, position, color=RED, i=0, time="hit", how="", delay=0, alter_hp=None, show=True):
        if withAnimation:
            # show_time: hit, now, animation done
            text = str(text0)
            text_dict = {
                "text": text,
                "position": position,  # 初始飘字位置
                "orginial_position": tuple(position), # 用于处理多个飘字的位置
                "color": color,  # 飘字颜色
                "follow": i, # 飘字跟随动画
                "show": show,  # 是否显示
                "show_time": time,  # 显示时机
                "timer": default_word_effect_timer,  # 飘字显示帧数
                "distance": 0,  # 飘字漂移距离
                "dealt": False,  # 是否已处理延迟
                "delay": delay,  # 延迟帧数
                "alter_hp": alter_hp,  # 飘字所在单位
                "altered": False,  # 是否已修改hp
                }

            if how == "insert":
                self.word_effects.insert(0, text_dict)
            elif how == "insert-1":
                self.word_effects.insert(-1, text_dict)
            else:
                self.word_effects.append(text_dict)

    def initialize(self):
        # 初始化飘字（待优化）
        if (self.animation.targets and len(self.animation.targets) > 1):
            self.multi_attack = True     
        for effect in self.word_effects[:]:  # 遍历所有飘字
            # 同一个位置有没有多个飘字？
            if not effect["dealt"]:
                effect["dealt"] = True
                if effect["orginial_position"] not in self.recorded_positions:
                    self.recorded_positions[effect["orginial_position"]] = 0
                elif effect["show"] == False:
                    pass # 不显示的飘字不计算额外的延迟，以便和显示的飘字同时修改lockhp
                else:
                    self.recorded_positions[effect["orginial_position"]] += 1
                effect["delay"] += self.recorded_positions[effect["orginial_position"]] * default_delay

    def update(self, effect):
        # 飘字效果更新
        if effect["delay"] > 0:
            effect["delay"] -= 1  # 延迟帧数减少
        else:
            # 动画播放时修改lockhp
            if effect["delay"] <= 0 and effect["timer"] == default_word_effect_timer and effect["alter_hp"] and not effect["altered"]:
                damage = int(float(effect["text"]))
                unit = effect["alter_hp"]
                unit.lockhp += damage
                unit.lockhp = min(max(0, unit.lockhp), unit.maxhp)
                effect["altered"] = True

            effect["distance"] += 0.5  # 飘字漂移距离增加
            effect["timer"] -= 1  # 计时器减少
            if effect["timer"] <= 0:
                self.word_effects.remove(effect)



    def draw(self, effect, font=None, with_surroundings=True, in_center=True):
        if not font:
            font = self.font
        
        if effect["delay"] <= 0 and effect["show"]:
            text_surface = font.render(effect["text"], True, effect["color"])
            position = (effect["position"][0], effect["position"][1] - effect["distance"])
            if in_center:
                text_rect = text_surface.get_rect(center=position)
            else:
                text_rect = text_surface.get_rect(position)
            if with_surroundings:
                drawSurroundings(self.screen, effect["text"], position, text_surface, font, in_center)
            self.screen.blit(text_surface, text_rect)

    def showWordEffects(self, font=None, with_surroundings=True, in_center=True):
        # show_time: hit, now, animation done
        if self.voice_inserted:
            if not self.initialized:
                self.initialize()
                self.initialized = True
                
            if self.word_effects:
                if self.multi_attack:
                    for effect in self.word_effects:
                        if (effect["show_time"] == "now") or \
                            (self.animation.hit_everyone[effect["follow"]] and effect["show_time"] == "hit") or \
                            (self.animation.back_from_every_hit[effect["follow"]] and effect["show_time"] == "back") or \
                            (self.animation.done and effect["show_time"] == "animation done"):
                            self.update(effect)
                            self.draw(effect, font, with_surroundings, in_center)
                else:
                    for effect in self.word_effects:
                        if (effect["show_time"] == "now") or \
                            (self.animation.hit and effect["show_time"] == "hit") or \
                            (self.animation.back and effect["show_time"] == "back") or \
                            (self.animation.done and effect["show_time"] == "animation done"):
                            self.update(effect)
                            self.draw(effect, font, with_surroundings, in_center)
            else:
                self.animation.words_shown = True
        






