import pygame
import sys
from Characters import *
from random import randint
from TeamLogic import *
from createChar import *
from animation import *
from colors import *
from GeneralSettings import *
from WordEffects import *
from chooseMyTeam import *
from beginning import *
from ending import *


debug = False


class gameBody:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.clock = pygame.time.Clock()

        self.early_quit = False
        self.battleRunning = True
        self.animations = []
        self.font = default_font

        self.gold = gold
        self.difficulty = 1 # 0~5
        self.massMinions = False
        self.myTeam = None
        self.myTeamArmyList = []
        self.enemy = None
        self.enemyArmyList = []
        self.round = 0
        self.endOfBattle = "暂停"
        self.endOfBattleFont = FONT.size(40)

        self.central_line = central_line
        self.road_width = road_width
        self.upper_line = upper_line
        self.unit_size = unit_size

        self.auto = 0 #  0: auto, 1: press & go
        self.mode = 4 #  2: 指挥官 3: 随机角色 4: 全队行动
        self.mode_dict = {
            2: "随机战斗，自动战斗",
            3: self.takeTurns,
            4: self.takeTurns_wholeTeam,
        }
        self.playing_animations = False


    def reset(self):
        self.round = 0
        self.endOfBattle = "暂停"
        self.early_quit = False
        self.battleRunning = True
    
    def setTeams(self, from_begin=False, newEnemy=True, myTeamRecord = []):
        self.endOfBattle = "暂停"
        if from_begin:
            if not newEnemy:
                self.begin.enemy = self.enemy
                self.begin.choosing.enemy = self.enemy
            self.begin.beginTheGame(newEnemy, myTeamRecord)
            self.myTeam = self.begin.myTeam
            if newEnemy:
                self.enemy = self.begin.enemy

            # 记忆双方阵容
            self.myTeamArmyList = self.begin.myTeamArmyList
            self.enemyArmyList = self.begin.enemyArmyList
        
        # 更新sniper的记忆
        for member in self.myTeam.front+self.myTeam.back:
            if member.name == "Sniper":
                member.enemy = self.enemy
        for member in self.enemy.front+self.enemy.back:
            if member.name == "Sniper":
                member.enemy = self.myTeam

        # 记录回合数并分配先后手
        self.round = 0
        if randint(0,1):
            self.ATurn = True
        else:
            self.ATurn = False


    # 读取阵容记录（不记录具体位置）
    def readTeamRecord(self, side):
        if side == "myTeam":
            myTeam_all = []
            for i in self.myTeamArmyList:
                myTeam_all.append(createChar(i)[0])
            self.myTeam = Team(myTeam_all)
            buildArmy(self.myTeam, myTeam_all, "myTeam")

        elif side == "enemy":
            enemy_all = []
            for i in self.enemyArmyList:
                enemy_all.append(createChar(i)[0])
            self.enemy = Team(enemy_all)
            buildArmy(self.enemy, enemy_all, "enemy")


    def drawAttackSymbol(self):
        # 攻击方提示
        turn_text = self.font.render("正在攻击", True, BLACK)
        text_rect = turn_text.get_rect(center=(
            self.central_line+(4*(self.ATurn)-2)*self.road_width, 
            max(self.upper_line-1.2*self.road_width, 30) # 最小留白值为30
            ))
        self.screen.blit(turn_text, (text_rect))
            

    def drawTeams(self):
        # 绘制游戏元素
        self.screen.fill(NOT_THAT_WHITE)
        self.enemy.draw(self.screen)
        self.myTeam.draw(self.screen) # 我方绘制在上层



    # 游戏模式1：一回合一动
    def drawBattleField(self):
        self.drawTeams()

        # 绘制动画
        if self.animations:
            hit_dict = {}
            anima_dict = {}
            for animation in self.animations:
                if animation.done:
                    self.animations.remove(animation)
                else:
                    # 初始化多个动画的延迟
                    anima_attacker = animation.attacker
                    anima_attacker.unplayed_anima = True
                    if anima_attacker not in anima_dict:
                        anima_dict[anima_attacker] = []
                    anima_dict[anima_attacker].append(animation)
                    if animation.delay < -100:
                        animation.delay = anima_dict[anima_attacker].index(animation) * default_delay
                    if animation.delay > 0:
                        animation.delay -= 1
                    # 同一个角色的多个近战hit动画依次播放
                    if isinstance(animation, HitAttack):
                        # 优化hit_again判断
                        hit_attacker = animation.attacker
                        if hit_attacker not in hit_dict:
                            hit_dict[hit_attacker] = []
                        if not animation.back:
                            hit_dict[hit_attacker].append(animation)
                    # 非hit动画可以直接播放
                    else:
                        animation.draw_now = True

            for hit_attacker in hit_dict: 
                if hit_dict[hit_attacker]:
                    for i, hit_anima in enumerate(hit_dict[hit_attacker]):
                        # 只播放每个单位的第一个hit动画
                        if i == 0:
                            hit_anima.draw_now = True
                        else:
                            hit_anima.draw_now = False
                        # 同一个单位只有最后一个Hit动画的hit_again是False    
                        if i == len(hit_dict[hit_attacker])-1:
                            hit_anima.hit_again = False
                        else:
                            hit_anima.hit_again = True

            for animation in self.animations:
                # 更新上述条件再绘制
                if animation.delay == 0 and animation.draw_now == True:
                    animation.draw(self.screen)
            

    def takeTurns(self):
        if ((not allDead(self.myTeam)) and (not allDead(self.enemy))):
            dprint(" ")
            self.round += 1
            if self.ATurn:
                myTeam = self.myTeam
                enemy = self.enemy
            else:
                myTeam = self.enemy
                enemy = self.myTeam

            # 确定攻击者
            attacker = randAliveAll(myTeam)
            attacker.new_turn()
            teamS = 'Team A' if self.ATurn else 'Team B'
                
            dprint(teamS + f' member {attacker.name} acts')
            if myTeam.doubleattack > 0 and attacker.name != "Bard":
                attacker.act_times += 1
                myTeam.doubleattack -= 1

                animates = BlankAnimation(self, attacker)
                animates.words.add_text("受到鼓舞", attacker.position, color=NOT_THAT_YELLOW, i=0, time="now")
                self.animations.append(animates)
    
            # 结算多重攻击
            while attacker.act_times > 0 and not allDead(enemy):
                attacker.actWithPoison(myTeam,enemy,self)

            # 最后切换回合
            self.ATurn = not self.ATurn

            if allDead(self.enemy):
                self.endOfBattle = " 胜利！"
                self.battleRunning = False
            else:
                self.endOfBattle = " 失败！"
                self.battleRunning = False

    def takeTurns_wholeTeam(self):
        # 更新全队行动指示器
        if self.myTeam.wholeTeamTracker == [] and self.enemy.wholeTeamTracker == []:
            for member in self.myTeam.front + self.myTeam.back:
                if member.alive:
                    self.myTeam.wholeTeamTracker.append(member)
            for member in self.enemy.front + self.enemy.back:
                if member.alive:
                    self.enemy.wholeTeamTracker.append(member)
            # 所有人都行动了则进入下一回合
            self.round += 8 # 回合数奖励固定设置为8 （2x单位数）       

        if ((not allDead(self.myTeam)) and (not allDead(self.enemy))):
            if self.ATurn:
                # 清除已经死了的单位
                self.myTeam.wholeTeamTracker = [member for member in self.myTeam.wholeTeamTracker if member.alive]
                # 调整敌我双方指代
                myTeam = self.myTeam
                enemy = self.enemy
            else:
                self.enemy.wholeTeamTracker = [member for member in self.enemy.wholeTeamTracker if member.alive]
                myTeam = self.enemy
                enemy = self.myTeam

            dprint(" ")
            # 如果本队已经都行动过了，就换对方行动
            # 只有本队还有人没有行动才会随机行动
            if myTeam.wholeTeamTracker:
                # 确定攻击者
                attacker = randAliveAll(myTeam)
                while attacker not in myTeam.wholeTeamTracker:
                    attacker = randAliveAll(myTeam)
                myTeam.wholeTeamTracker.remove(attacker)
                attacker.new_turn()

                teamS = 'Team A' if self.ATurn else 'Team B'
                dprint(teamS + f' member {attacker.name} acts')
                # 检查鼓舞，每个单位一次行动只能受到一次鼓舞
                if myTeam.doubleattack > 0 and attacker.name != "Bard":
                    attacker.act_times += 1
                    myTeam.doubleattack -= 1

                    animates = BlankAnimation(self, attacker)
                    animates.words.add_text("受到鼓舞", attacker.position, color=NOT_THAT_YELLOW, i=0, time="now")
                    self.animations.append(animates)
        
                # 结算多重攻击
                while attacker.act_times > 0 and not allDead(enemy):
                    attacker.actWithPoison(myTeam,enemy,self)

            # 切换回合
            self.ATurn = not self.ATurn

            if allDead(self.enemy):
                self.endOfBattle = " 胜利！"
                self.battleRunning = False
            else:
                self.endOfBattle = " 失败！"
                self.battleRunning = False

    # 游戏模式0：随机战斗，自动战斗
    def autoRunning(self, withAnimation, mode):
        while ((not allDead(self.myTeam)) and (not allDead(self.enemy))):
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.endOfBattle = " 撤退！"
                    self.animations = []
                    self.playing_animations = False
                    self.early_quit = True
                    return None
                
            # 播放完动画自动下一回合
            if (not self.playing_animations) and (not self.early_quit):
                self.mode_dict[mode]()

            if withAnimation:
                if self.animations:
                    self.drawAttackSymbol()
                    self.playing_animations = True
                else:
                    self.playing_animations = False
                self.drawBattleField()
                self.drawAttackSymbol()
                pygame.display.flip()
                self.clock.tick(100)


    # 游戏模式1：随机战斗，鼠标推进回合
    def oneClickOneGo(self, withAnimation, mode):
        while ((not allDead(self.myTeam)) and (not allDead(self.enemy))):
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.endOfBattle = " 撤退！"
                    self.animations = []
                    self.playing_animations = False
                    self.early_quit = True
                    return None
                # 左键或空格键触发攻击    
                elif (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or \
                (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                    self.mode_dict[mode]()

            if withAnimation:
                if self.animations:
                    self.drawAttackSymbol()
                    self.playing_animations = True
                else:
                    self.playing_animations = False
                self.drawBattleField()
                self.drawAttackSymbol()
                pygame.display.flip()
                self.clock.tick(100)
    

    def jumpToEnd(self, mode):
        print("Jump to end")
        while ((not allDead(self.myTeam)) and (not allDead(self.enemy))):
            self.mode_dict[mode]()

        self.animations = [] # 清空动画


    # 游戏主体
    def runBattle(self, withAnimation=True):
        # Return 0 when Team A win and 1 otherwise.
        # There will be no tie

        if self.auto == 0 and self.endOfBattle == "暂停":
            # 游戏模式0：自动战斗
            self.autoRunning(withAnimation, self.mode)
        elif self.auto == 1 and self.endOfBattle == "暂停":
            # 游戏模式1：一回合一动
            self.oneClickOneGo(withAnimation, self.mode)

        # 结算界面
        while True and withAnimation:
            if self.animations:
                self.playing_animations = True
            else:
                self.playing_animations = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.endOfBattle = " 撤退！"
                    self.animations = []
                    self.playing_animations = False
                    self.early_quit = True

            self.drawBattleField()
            # 放完动画就播放结算界面
            if not self.playing_animations:
                self.end.update()
            # 结算界面选择完毕就退出
            if self.end.confirmed:
                return None
            pygame.display.flip()
            self.clock.tick(100)


    # 指南：setTeams(begin): 由begin定义新的myTeam和enemy
    def runFromScratch(self, myTeamRecord = []):
        self.begin = beginning(self)
        if myTeamRecord:
            self.begin.stage = 2
            if self.begin.newEnemy:
                self.begin.randomEnemy(self.gold+200*(self.difficulty-1))
            if self.begin.choosing.enemy == None:
                self.begin.choosing.enemy = self.begin.enemy
        self.end = ending(self)
        self.setTeams(True, True, myTeamRecord)
        self.runBattle(withAnimation)
    
    def runFromSetEnemy(self):
        self.begin = beginning(self)
        self.begin.stage = 2
        self.begin.enemy = self.enemy
        self.end = ending(self)
        self.setTeams(True, newEnemy=False, myTeamRecord =[])
        self.runBattle(withAnimation)
    
    def runFromAllSet(self):
        self.end = ending(self)
        self.setTeams()
        self.runBattle(withAnimation)




            

