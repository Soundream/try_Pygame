from random import randint
from Characters import *
import pygame
from colors import *
from GeneralSettings import *
from WordEffects import *
from TeamLogic import *
from createChar import *

debug = False

class chooseMyTeam:
    def __init__(self, outside):
        self.font = FONT.size(20)
        self.normalColor = BLUE
        self.hoverColor = NOT_THAT_GREEN
        self.mouse_pos = (0,0)

        self.enemy = None
        self.massMinions = False

        self.outside = outside
        self.screen = outside.screen
        self.clock = outside.clock
        self.button_size = outside.game.unit_size
        self.road_width = outside.game.road_width

        self.nCharType = nCharType
        self.team_as_list = []
        self.unit_ints = []
        self.minCost = 100
        
        self.stage = 1
        self.word_effects = []
        # 购买的按钮位置
        self.buttons = [
            pygame.Rect((50 + (i%4)*self.road_width, 220 + (i//4)*self.road_width), 
                        (self.button_size, self.button_size))
            for i in range(self.nCharType)
            ]
        self.characters = [createChar(i+1)[0] for i in range(self.nCharType)]
        self.counts = [0] * self.nCharType

        # 图鉴按钮
        self.wiki_start = 400
        self.wiki_width = screen_width - self.wiki_start
        self.wiki_button = pygame.Rect((800, 50), (80, 50)) # 进入图鉴后同一个位置显示退出图鉴
        self.wiki = self.buildWiki()
        self.inWiki = False
        self.scroll = {key: 0 for key in range(self.nCharType)}

    def buildWiki(self):
        wiki = {}
        with open("characterWiki.txt", "r", encoding="utf-8") as file:
            lines = file.readlines()
            current_char = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line[0] != "-":
                    char_name = line
                    wiki[char_name] = []
                    current_char = char_name
                else:
                    wiki[current_char].append(line)
        return wiki
                    
    def wrapWikiText(self, lines, font, width):
        description = []
        for line in lines:
            text = wrap_chinese_text(line, font, width)
            for subtext in text:
                if subtext[:2] != "- ":
                    subtext = "  " + subtext
                subtext = " " + subtext    
                description.append(subtext)
        return description


    def drawWiki(self, screen, character, character_i):
        char_name = character.name
        char_info = self.wiki[char_name]

        # 显示名字
        min_y = 100
        position = (self.wiki_start + self.wiki_width//2, min_y)
        name_font = FONT.size(30)
        text_surface = name_font.render(character.chinese_name, True, character.themeColor)
        drawSurroundings(screen, character.chinese_name, position, text_surface, font=name_font, in_center=True)
        text_rect = text_surface.get_rect(center=position)
        screen.blit(text_surface,text_rect)

        font = FONT.size(20)
        # 显示描述信息
        description_lines = self.wrapWikiText(char_info, font, self.wiki_width - 40)
        extra_blanks = 0
        for i, line in enumerate(description_lines[self.scroll[character_i]:]):
            if line[:3] == " - ":
                extra_blanks += 1
            rendered_text = font.render(line, True, BLACK)
            screen.blit(rendered_text, (self.wiki_start, min_y + 10 + i*25 + extra_blanks*10))


    def randomRest(self, massMinions):
        while self.outside.gold >= minCost:
            tempChar, unit_int = createChar(randint(1,nCharType))
            if self.outside.gold >= tempChar.cost:
                if massMinions and tempChar.cost >= 2*minCost:
                    continue
                self.outside.gold -= tempChar.cost
                self.counts[unit_int-1] += 1 # 这里counts是列表，从0开始

                self.team_as_list.append(tempChar)
                self.unit_ints.append(unit_int)     
    
    def clearAll(self, clearGold=True, show_text=True):
        self.team_as_list = []
        self.unit_ints = []
        self.counts = [0] * self.nCharType
        if clearGold:
            self.outside.gold = self.outside.allowedGold
        if show_text:
            self.add_text("已清空招募名单", (280,120), NOT_THAT_YELLOW)


    def updateWordEffect(self):
        # 用一个字典存储每个 x 坐标上的已分配偏移量
        offset_map = {}

        for effect in self.word_effects[:]:  # 遍历所有飘字
            # 同一个位置有没有多个飘字？
            if not effect["dealt"]:
                effect["dealt"] = True
                if tuple(effect["position"]) not in offset_map:
                    offset_map[tuple(effect["position"])] = 0
                else:
                    offset_map[tuple(effect["position"])] += 1
                effect["delay"] = offset_map[tuple(effect["position"])] * 20

            if effect["delay"] > 0:
                effect["delay"] -= 1
                continue
            else:
                effect["position"][1] -= 1  # 飘字向上漂移
                effect["timer"] -= 1  # 计时器减少
                if effect["timer"] <= 0:
                    self.word_effects.remove(effect)
    

    def add_text(self, text0, position, color=RED):
        text = str(text0)
        self.word_effects.append({
            "text": text,
            "position": [position[0] + 10, position[1] - 20],  # 初始飘字位置
            "color": color,  # 飘字颜色
            "timer": 60,  # 飘字显示帧数
            "dealt": False,  # 是否处理延迟
            "delay": 0  # 延迟帧数
        })


    def draw(self):
        enemy_display = FONT.size(default_font_size+7).render(f"即将面对的敌人：", True, BLACK)
        self.screen.blit(enemy_display, (500, 25))
        if self.enemy:
            self.enemy.draw(self.screen)

        if self.inWiki:
            overlay = pygame.Surface((self.wiki_width, screen_height), pygame.SRCALPHA)
            overlay.fill((*NOT_THAT_WHITE, 220))  # RGBA: 最后一个参数是透明度 (0=完全透明, 255=完全不透明)
            self.screen.blit(overlay, (self.wiki_start, 0))
            self.outside.drawButton("返回", self.wiki_button) 
        else:
            # 绘制图鉴入口
            self.outside.drawButton("图鉴", self.wiki_button)            

        self.updateWordEffect()

        # 绘制选将区域
        for i, button in enumerate(self.buttons):
            if button.collidepoint(self.mouse_pos):
                pygame.draw.rect(self.screen, self.hoverColor, button)
            else:
                pygame.draw.rect(self.screen, self.normalColor, button)
            # 绘制单位名字
            unit_name = self.font.render(self.characters[i].chinese_name, True, WHITE)  # 白色文字
            text_rect = unit_name.get_rect(center=(button.center))  # 确保文字在矩形中心
            c_x, c_y = text_rect.center
            for dx, dy in offsets:
                text_rect2 = unit_name.get_rect(center=(c_x + dx, c_y + dy))
                self.screen.blit(self.font.render(self.characters[i].chinese_name, True, BLACK), 
                            text_rect2)
            self.screen.blit(unit_name, text_rect)  # 将名字渲染到矩形中心

            # 绘制价格
            c_x, c_y = button.center[0] + unit_size//2-3, button.center[1] + unit_size//2-3
            unit_cost = self.font.render(f"-{self.characters[i].cost}", True, NOT_THAT_YELLOW)
            text_rect3 = unit_cost.get_rect(bottomright=(c_x, c_y)) 
            for dx, dy in offsets:
                text_rect4 = unit_cost.get_rect(bottomright=(c_x + dx, c_y + dy))
                self.screen.blit(self.font.render(f"-{self.characters[i].cost}", True, BLACK), 
                            text_rect4)
            self.screen.blit(unit_cost, text_rect3)           

            # 绘制计数器
            c_x2, c_y2 = button.center
            if self.counts[i] > 0:
                pygame.draw.circle(self.screen, BLACK, (c_x2+self.button_size//2, c_y2-self.button_size//2), 12)
                text_surface = self.font.render(f"{self.counts[i]}", True, RED)
                text_rect = text_surface.get_rect(center=(c_x2+self.button_size//2, c_y2-self.button_size//2))
                self.screen.blit(text_surface, text_rect)

        # 绘制可购买单位介绍
        for i, button in enumerate(self.buttons):
            if button.collidepoint(self.mouse_pos):
                if self.inWiki:
                    draw_unit_info(self.characters[i], (button.center), self.font, self.screen, self.wiki_start)
                    self.drawWiki(self.screen, self.characters[i], i)
                else:
                    draw_unit_info(self.characters[i], (button.center), self.font, self.screen)
        # 绘制敌方备战单位介绍    
        for member in (self.enemy.front + self.enemy.back):
            if member.rect.collidepoint(self.mouse_pos) and not self.inWiki:
                draw_unit_info(member, (member.rect.center), self.font, self.screen)              

        # 更新飘字
        for effect in self.word_effects:
            if effect["delay"] <= 0:
                text_surface = self.font.render(effect["text"], True, effect["color"])
                c1_x, c1_y = effect["position"]
                for dx, dy in offsets:
                    self.screen.blit(self.font.render(effect["text"], True, BLACK), 
                                    (c1_x + dx, c1_y + dy))
                self.screen.blit(text_surface, (c1_x, c1_y))


    def readRecord(self, myTeamRecord):
        self.unit_ints = myTeamRecord
        self.team_as_list = []
        self.counts = [0] * self.nCharType
        if myTeamRecord:
            for i in myTeamRecord:
                tempChar, __ = createChar(i)
                if self.outside.gold >= tempChar.cost:
                    self.outside.gold -= tempChar.cost
                    self.counts[i-1] += 1
                    self.team_as_list.append(tempChar)

    # 事件处理
    def Choose(self):
        self.outside.myTeam_all = self.team_as_list

        self.mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.outside.running = False
                pygame.quit()
            else:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # 左键点击购买
                    if event.button == 1:  
                        for i, button in enumerate(self.buttons):
                            if button.collidepoint(self.mouse_pos):
                                tempChar, __ = createChar(i+1)
                                if self.outside.gold >= tempChar.cost:
                                    self.outside.gold -= tempChar.cost
                                    self.counts[i] += 1
                                    self.add_text(-tempChar.cost, (280,120), NOT_THAT_YELLOW)
                                    self.team_as_list.append(tempChar)
                                    self.unit_ints.append(i+1)
                                else:
                                    self.add_text("金币不足", button, NOT_THAT_YELLOW)

                        # 提前确认和摆烂随机
                        if self.outside.buttonStage2["提前进入战斗"].collidepoint(self.mouse_pos):   
                            if self.team_as_list:
                                self.outside.stage2confirmed = True
                            else:
                                self.add_text("请至少招募一个单位", (280,120), NOT_THAT_YELLOW)
                        elif self.outside.buttonStage2["剩下的随机选完"].collidepoint(self.mouse_pos):
                            if self.outside.gold >= minCost:
                                self.randomRest(self.massMinions)
                            else:
                                self.clearAll()

                        # 打开图鉴模式
                        if self.wiki_button.collidepoint(self.mouse_pos):
                            self.inWiki = not self.inWiki

                    # 右键点击出售
                    elif event.button == 3:
                        for i, button in enumerate(self.buttons):
                            if button.collidepoint(self.mouse_pos):
                                if self.counts[i] > 0:  # 确保玩家有该类型单位可出售
                                    self.counts[i] -= 1
                                    self.outside.gold += self.characters[i].cost  # 增加金币
                                    self.add_text(f"+{self.characters[i].cost}", (280, 120), NOT_THAT_YELLOW)
                                    # 从 team_as_list 中移除一个对应单位
                                    for unit in self.team_as_list:
                                        if unit.chinese_name == self.characters[i].chinese_name:
                                            self.team_as_list.remove(unit)
                                            self.unit_ints.remove(i+1)
                                            break
                                else:
                                    self.add_text("没有单位可供出售", button, NOT_THAT_YELLOW)

                    # 滚轮滚动调整wiki显示
                    elif event.button == 4:  
                        for i, button in enumerate(self.buttons):
                            if button.collidepoint(self.mouse_pos):
                                self.scroll[i] = max(0, self.scroll[i]-1)
                    elif event.button == 5:
                        for i, button in enumerate(self.buttons):
                            if button.collidepoint(self.mouse_pos):
                                self.scroll[i] += 1

