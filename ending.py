import pygame
from random import randint
from colors import *
from GeneralSettings import *
from WordEffects import *
from beginning import *
import sys


class ending:
    def __init__(self, game):
        # 动画
        self.game = game
        self.screen = game.screen
        self.clock = game.clock
        
        self.font = FONT.size(default_font_size+5)
        self.normalColor = BLUE
        self.hoverColor = NOT_THAT_GREEN

        self.mouse_pos = None
        self.confirmed = False

        self.timer=0

        self.buttons = {
            # button_text: button_rect
            "重新战斗": pygame.Rect((200, 200), (150, 50)),
            " 下一局（+500金）":pygame.Rect((560, 200), (230, 50)), 
            "调整阵容":pygame.Rect((200, 300), (150, 50)),
            "直面自我":pygame.Rect((600, 300), (150, 50)), 
            "返回主菜单":pygame.Rect((200, 400), (150, 50)),
            "退出游戏":  pygame.Rect((600, 400), (150, 50)),                
        }

    # 通用按钮函数
    def drawButton(self, button_text, button_rect):
        # 绘制按钮
        if button_rect.collidepoint(self.mouse_pos):
            pygame.draw.rect(self.screen, self.hoverColor, button_rect)
        else:
            pygame.draw.rect(self.screen, self.normalColor, button_rect)

        # 绘制说明文字
        text_surface = self.font.render(button_text, True, WHITE)
        position = button_rect.center
        text_rect = text_surface.get_rect(center=position)
        drawSurroundings(self.screen, button_text, position, text_surface, self.font, in_center=True)
        self.screen.blit(text_surface, text_rect)

    # 所有按钮功能
    # 重新战斗
    def resetBattle(self):
        self.game.reset()
        self.game.myTeam.reset("myTeam")
        self.game.enemy.reset("enemy")
        self.game.runFromAllSet()

    # 下一局（+500金）
    def newGame(self):
        self.game.reset()
        self.game.gold += 500
        self.game.runFromScratch(myTeamRecord = self.game.myTeamArmyList)

    # 调整阵容
    def faceEnemy(self):
        self.game.reset()
        self.game.enemy.reset("enemy")
        self.game.myTeam = None
        self.game.myTeamArmyList = []
        self.game.runFromSetEnemy()

    # 直面自我
    def faceYourself(self):
        self.game.enemy = self.game.myTeam
        self.game.enemyArmyList = self.game.myTeamArmyList
        self.faceEnemy()

    # 返回主菜单
    def returnToMenu(self):
        self.game.reset()
        self.game.runFromScratch()

    # 退出游戏
    def exitGame(self):
        pygame.quit()
        sys.exit()


    def drawEndOfBattle(self, endOfBattle):
        # 结算语句
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((*NOT_THAT_WHITE, 180)) # 结算界面底色
        self.screen.blit(overlay, (0, 0))

        line1 = self.game.endOfBattleFont.render(self.game.endOfBattle, True, ORANGE)
        line1_rect = line1.get_rect(center=(screen_width//2, screen_height//2))
        self.screen.blit(line1, line1_rect)
    
        
        # 绘制按钮
        for button_text, button_rect in self.buttons.items():
            if button_text == " 下一局（+500金）" and self.game.endOfBattle == " 撤退！":
                rect = pygame.Rect((0,0), (150, 50))
                rect.center = button_rect.center
                self.drawButton("跳过动画", rect)
            elif button_text == " 下一局（+500金）" and self.game.endOfBattle == " 失败！":
                pass
            else:
                self.drawButton(button_text, button_rect)

    def update(self):
        self.timer+=1
        self.mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and self.timer > 20:  # 左键按下状态
            self.timer = 0
            for button_text, button_rect in self.buttons.items():
                if button_rect.collidepoint(self.mouse_pos):
                    if button_text == "重新战斗":
                        self.resetBattle()
                    elif button_text == "调整阵容":
                        self.faceEnemy()
                    elif button_text == "直面自我":  
                        self.faceYourself()
                    elif button_text == " 下一局（+500金）":
                        if self.game.endOfBattle == " 胜利！":
                            self.newGame()
                        elif self.game.endOfBattle == " 撤退！":
                            self.game.jumpToEnd(self.game.mode)
                            continue
                        elif self.game.endOfBattle == "失败！":
                            continue
                    elif button_text == "返回主菜单":
                        self.returnToMenu()
                    elif button_text == "退出游戏":
                        self.exitGame()
                    
                    self.confirmed = True
        
        self.drawEndOfBattle(self.game.endOfBattle)
        if self.confirmed:
            return None
        



