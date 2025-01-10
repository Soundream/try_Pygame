import pygame

nCharType = 20 # no. of types of characters you can choose
gold = 600   # Gold for you to recruit characters
difficulty = 1 # 1~5, 5 is the hardest
minCost = 100 # A hack for userChooseTeam()

screen_width, screen_height = 900, 700

central_line = 375
road_width = 90
upper_line = 100
unit_size = 4/5 * road_width # 72

printActionDescription = False
withAnimation = True

default_speed = 8 # 单位攻击时的本体飞行速度
# 飞弹速度为1.2倍飞行速度

default_word_effect_timer = 80
# 默认描边偏移量
offsets = [(-2, 2), (2, -2), (-2, -2), (2, 2), 
           (-2, 0), (2, 0), (0, -2), (0, 2)]

pygame.init()
class FONT:
    def size(font_size):
        return pygame.font.Font("SimHei.ttf", font_size)
# 默认字体字号
default_font_size = 20
default_font = FONT.size(default_font_size)

# 默认延迟帧数
default_delay = 50

# 通用语音
critical_voice = "Critical"
chinese_critical_voice = "暴击"






