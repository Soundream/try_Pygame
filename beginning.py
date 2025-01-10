import pygame
from random import randint
from colors import *
from GeneralSettings import *
from chooseMyTeam import *


# 展示游戏模式及图鉴
#  游戏模式：混战模式、轮流行动模式、回合模式
#  回合模式：自动回合、手动回合
#  图鉴

class beginning:
    def __init__(self, game):
        # 动画
        self.game = game
        self.screen = game.screen
        self.clock = game.clock
        self.font = FONT.size(default_font_size)
        self.normalColor = BLUE
        self.hoverColor = NOT_THAT_GREEN
        self.mouse_pos = None

        self.button_size = game.unit_size
        self.road_width = game.road_width

        # 主体逻辑
        self.allowedGold = game.gold # 金币总量限制器
        self.gold = game.gold # 金币追踪器
        self.stage = 1
        self.newEnemy = True

        # 队伍
        self.nCharType = nCharType
        self.myTeam = None
        self.enemy = None
        self.enemyArmyList = []
        self.enemy_created = False
        self.choosing = chooseMyTeam(self)
        self.myTeam_all = self.choosing.team_as_list
        self.myTeamArmyList = self.choosing.unit_ints

        # 按钮 stage1
        self.buttonStage1 = {
            # button_text: button_rect
            "自动进入下一回合": pygame.Rect((150, 200), (200, 80)),
            "手动进入下一回合": pygame.Rect((450, 200), (200, 80)),

            "自选目标模式": pygame.Rect((100, 300), (200, 80)),
            "随机轮流行动": pygame.Rect((350, 300), (200, 80)),
            "团队行动模式": pygame.Rect((600, 300), (200, 80)),

            "精挑细选": pygame.Rect((150, 500), (200, 100)),
            "随机组队": pygame.Rect((450, 500), (200, 100)),
        }
        self.line1 = 0 # 0 1
        self.line2 = 4 # 2 3 4
        self.line3 = 5 # 5 6
        # 割草模式按钮
        self.massMinions = game.massMinions
        self.massMinionsRect = pygame.Rect((750, 400), (120, 50))
        self.massMinionsIndicator = pygame.Rect((750-50, 400), (50, 50))
        # 难度选择
        self.difficulty = game.difficulty
        # 确认按钮
        self.stage1confirm = pygame.Rect((700, 500), (100, 100))
        self.stage1confirmed = False
        
        # 按钮 stage2
        self.buttonStage2 = {
            "提前进入战斗": pygame.Rect((50, 150), (200, 60)),
            # "提前进入战斗"
            "剩下的随机选完": pygame.Rect((280, 150), (200, 60)),
            # "清空，重选"
        }

        self.stage2confirmed = False
        self.ask_to_confirm = False

    def resetGold(self):
        self.allowedGold = self.game.gold
        self.gold = self.game.gold

    # 通用按钮函数
    def drawButton(self, button_text, button_rect, font=None, color=()):
        if not font:
            font = FONT.size(default_font_size+5)
        if color == "reverse":
            color = (self.hoverColor, self.normalColor)
        elif color == "hover":
            color = (self.hoverColor, self.hoverColor)       
        elif not color:
            color = (self.normalColor, self.hoverColor)
        # 绘制按钮
        if button_rect.collidepoint(self.mouse_pos):
            pygame.draw.rect(self.screen, color[1], button_rect)
        else:
            pygame.draw.rect(self.screen, color[0], button_rect)

        # 绘制说明文字
        text_surface = font.render(button_text, True, WHITE)
        position = button_rect.center
        text_rect = text_surface.get_rect(center=position)
        drawSurroundings(self.screen, button_text, position, text_surface, font, in_center=True)
        self.screen.blit(text_surface, text_rect)

    # 随机生成敌方队伍
    def randomEnemy(self, gold):
        enemy_all, self.enemyArmyList = createRandTeam(gold, self.massMinions)
        self.enemy = Team(enemy_all)
        buildArmy(self.enemy, enemy_all, "enemy")
        self.choosing.enemy = self.enemy

    # 随机生成我方整支队伍
    def randomMyTeam(self, gold):
        myTeam_all, self.myTeamArmyList = createRandTeam(gold, self.massMinions)
        self.myTeam = Team(myTeam_all)
        buildArmy(self.myTeam, myTeam_all, "myTeam")


    def draw(self):
        # 绘制游戏元素
        self.screen.fill(NOT_THAT_WHITE)

        # 绘制金币
        gold_I_have = FONT.size(30).render(f"持有金币：{self.gold}", True, NOT_THAT_YELLOW)
        for dx, dy in offsets:
            self.screen.blit(FONT.size(30).render(f"持有金币：{self.gold}", True, BLACK), 
                             (100 + dx, 100 + dy))
        self.screen.blit(gold_I_have, (100, 100))

        # 按阶段进行主体绘制
        if self.stage == 1:
            # 游戏标题
            title = " 对对碰 v2.0"
            title_surface = FONT.size(60).render(title, True, WHITE)
            title_position = (screen_width//2, screen_height//6)
            title_rect = title_surface.get_rect(center=title_position)
            drawSurroundings(self.screen, title, title_position, title_surface, FONT.size(60), in_center=True)
            self.screen.blit(title_surface, title_rect)

            # 绘制割草模式按钮
            self.drawButton("割草模式", self.massMinionsRect)
            pygame.draw.rect(self.screen, BLACK, self.massMinionsIndicator, 4)
            if self.massMinions:
                self.game.massMinions = True
                inside_rect = pygame.Rect((0,0), (30, 30))
                inside_rect.center = self.massMinionsIndicator.center
                pygame.draw.rect(self.screen, RED, inside_rect)
            else:
                self.game.massMinions = False

            # 绘制其他按钮
            for i, (button_text, button_rect) in enumerate(self.buttonStage1.items()):
                if i in (5,6):
                    #最后FONT.size(default_font_size+10)
                    if i==self.line3:
                        self.drawButton(button_text, button_rect, font=FONT.size(default_font_size+5), color="hover")
                    else:
                        self.drawButton(button_text, button_rect, font=FONT.size(default_font_size+5))
                else:
                    if i in (self.line1, self.line2):
                        self.drawButton(button_text, button_rect, color="hover")
                    else:
                        self.drawButton(button_text, button_rect)

            # 绘制确认按钮
            self.drawButton("", self.stage1confirm) # pygame.Rect((700, 500), (100, 100))
            triangle_points = [(710, 510), (710, 590), (790, 550)]  # 三个顶点
            pygame.draw.polygon(self.screen, WHITE, triangle_points)  # 绘制三角形
            
        elif self.stage == 2:

            # 有钱的时候可以随机选，没钱的时候可以清空列表
            if self.gold >= minCost:
                self.drawButton("提前进入战斗", self.buttonStage2["提前进入战斗"])
                self.drawButton("剩下的随机选完", self.buttonStage2["剩下的随机选完"])
            else:
                self.drawButton("确认阵容", self.buttonStage2["提前进入战斗"])
                self.drawButton("清空，重选", self.buttonStage2["剩下的随机选完"])
            self.choosing.draw()

        elif self.stage == 3:
            texting = FONT.size(25).render("双方队伍离开备战区域", True, BLACK)  
            texting_rect = texting.get_rect(center=(400,200))  
            self.screen.blit(texting, texting_rect) 
        
            texting1 = FONT.size(25).render("请点按 左键 或 空格键 进入战役", True, BLACK)  
            texting1_rect = texting1.get_rect(center=(400,300))  
            self.screen.blit(texting1, texting1_rect)  
            
            if self.game.auto == 0:
                texting2 = FONT.size(25).render("动画将自动播放，回合将自动推进", True, BLACK) 
                texting2_rect = texting2.get_rect(center=(400,400))  
                self.screen.blit(texting2, texting2_rect)
            elif self.game.auto == 1:
                texting2 = FONT.size(25).render("并点按 左键 或 空格键 以推进回合", True, BLACK) 
                texting2_rect = texting2.get_rect(center=(400,400))  
                self.screen.blit(texting2, texting2_rect)  

    def update(self, myTeamRecord):
        self.clock = pygame.time.Clock()
        running = True
        while running:
            self.mouse_pos = pygame.mouse.get_pos()
            # stage1
            if self.stage == 1:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        pygame.quit()
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 左键点击
                            # 自主选择和随机选择
                            for i, (_, button_rect) in enumerate(self.buttonStage1.items()):
                                if button_rect.collidepoint(self.mouse_pos):
                                    if i in (0,1): # 
                                        self.line1 = i
                                    elif i in (2,3,4):
                                        self.line2 = i
                                    elif i in (5,6):
                                        self.line3 = i
                            # 割草模式
                            if self.massMinionsRect.collidepoint(self.mouse_pos) or self.massMinionsIndicator.collidepoint(self.mouse_pos):
                                self.massMinions = not self.massMinions
                            # 难度

                            # 确认按钮
                            if self.stage1confirm.collidepoint(self.mouse_pos):
                                self.stage1confirmed = True

                if self.stage1confirmed:
                    self.game.auto = self.line1
                    self.game.mode = self.line2
                    self.game.massMinions = self.massMinions
                    self.game.difficulty = self.difficulty

                    # 生成敌人
                    if self.newEnemy:
                        self.randomEnemy(self.gold+200*(self.difficulty-1))

                    if self.line3 == 5: # 精挑细选
                        self.stage = 2
                    elif self.line3 == 6: # 随机组队
                        self.randomMyTeam(self.gold)
                        self.myTeam_all, self.myTeamArmyList = createRandTeam(self.gold)
                        self.stage = 3
                        self.stage2confirmed = True
                        if not self.myTeam:
                            self.myTeam = Team(self.myTeam_all)
                            buildArmy(self.myTeam, self.myTeam_all, "myTeam")
                        return None

            # stage2
            elif self.stage == 2:
                # 选择我方队伍
                self.choosing.Choose()

                # 提醒确认
                if self.gold <= minCost:
                    if (not self.ask_to_confirm) and self.gold != self.allowedGold:
                        self.ask_to_confirm = True
                        self.choosing.add_text("请确认组建您的队伍", (280, 120), NOT_THAT_YELLOW)
                elif self.gold > minCost and self.ask_to_confirm:
                    self.ask_to_confirm = False # 金额改变时重置

                if self.stage2confirmed:
                    self.myTeamArmyList = self.choosing.unit_ints
                    self.stage = 3

            # stage 3
            elif self.stage == 3:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or \
                    (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):  # 左键或空格键触发攻击
                        if not self.myTeam:
                            self.myTeam = Team(self.myTeam_all)
                            buildArmy(self.myTeam, self.myTeam_all, "myTeam")
                        return None

            self.draw()
            pygame.display.flip()
            self.clock.tick(100)


    # 开始界面
    def beginTheGame(self, newEnemy=True, massMinions = False, myTeamRecord = []):
        self.newEnemy = newEnemy
        self.resetGold()
        self.choosing.clearAll(show_text=False)

        # 读取我方队伍已选记录
        if myTeamRecord:
            self.choosing.readRecord(myTeamRecord)

        self.update(self)











