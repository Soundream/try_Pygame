import pygame
from colors import *
from GeneralSettings import *
from WordEffects import *


class BlankAnimation:
    def __init__(self, game, attacker):
        self.hit = False
        self.back = False
        self.done = False

        self.attacker = attacker
        self.target = None
        self.targets = []

        self.words_shown = False
        self.words = Words(game, self)
        self.words.voice_inserted = True

        self.delay = -999
        self.draw_now = False

    def update(self):
        self.hit = True
        self.back = True
        if self.words_shown:
            self.done = True

    def draw(self, screen):
        if self.delay > 0:
            self.delay -= 1
            return
        if not self.done:
            self.update()
            self.words.showWordEffects()
        

class RecoverMana(BlankAnimation):
    def __init__(self, game, attacker, tempRecovery, silent=0): # silent=0,1,2
        super().__init__(game, attacker)
        self.attacker = attacker

        # silent=2时什么都不显示，silent=1时显示飘字不显示语音，silent=0时显示全部
        if silent in (0,1):
            self.words.add_text(self.attacker.chinese_mana_voice, self.attacker.position, color=LIGHT_BLUE, i=0, time="now")
        if silent == 0:
            self.words.add_text(f"+{tempRecovery}", self.attacker.position, color=LIGHT_BLUE, i=0, time="now")
        self.words.voice_inserted = True



class FightBack(BlankAnimation):
    def __init__(self, game, attacker, target, damage):
        super().__init__(game, attacker)
        self.attacker = attacker
        self.target = target
        self.targets = [target]
        self.tracker = self.attacker.be_hit_count

        self.words.add_text(f"-{damage}", target.position, color=MID_RED, i=0, time="hit", alter_hp=self.target)
        self.words.add_text(f"受到反击", target.position, color=MID_RED, i=0, time="hit", how="insert")
        self.words.voice_inserted = True
    
    def update(self):
        self.hit = self.attacker.be_hit[self.tracker]
        if self.hit:
            self.hit = True
            self.back = True
        if self.words_shown:
            self.done = True



class GeneralOneTargetAttack(BlankAnimation):
    def __init__(self, game, attacker, target, damage):
        super().__init__(game, attacker)
        self.size = game.unit_size
        self.speed = default_speed

        self.attacker = attacker
        self.damage = damage
        self.voice_initialized = False

        if type(target)!=list:
            self.target = target
            self.targets = [target]
            # 加入受击指示
            self.target.be_hit.append(False)
            self.target.be_hit_count += 1
            self.tracker = (self.target.be_hit_count,)
        elif len(target) == 1:
            self.target = target[0]
            self.targets = target

            self.target.be_hit.append(False)
            self.target.be_hit_count += 1
            self.tracker = (self.target.be_hit_count,)
        else:
            self.target = None
            self.targets = target
            self.tracker = []

            for target0 in self.targets:
                target0.be_hit.append(False)
                target0.be_hit_count += 1
                self.tracker.append(target0.be_hit_count)
            self.tracker = tuple(self.tracker)
    

class HitAttack(GeneralOneTargetAttack):
    def __init__(self, game, attacker, target, damage, hit_again=False):
        super().__init__(game, attacker, target, damage)
        self.back_position = None

        self.original_attacker_position = tuple(self.attacker.original_position)
        self.hit_again = hit_again

        if damage > 0:
            self.words.add_text(f"-{damage}", target.position, color=MID_RED, i=0, time="hit", alter_hp=self.target)
        elif damage < 0:
            self.words.add_text(f"+{-damage}", target.position, color=GREEN, i=0, time="hit", alter_hp=self.target)
        
        if target.name in ("Sniper",):
            self.words.add_text(target.chinese_be_interrupted_voice, target.position, color=WHITE, i=0, time="hit")

        self.words.voice_inserted = True
    
    def itemFlying(self):
        # 计算目标位置与当前位置的方向向量
        dx = self.target.position[0] - self.attacker.position[0]
        dy = self.target.position[1] - self.attacker.position[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5  # 计算两点间距离

        if not self.attacker.rect.colliderect(self.target.rect):
            # 计算单位方向向量
            direction_x = dx / distance
            direction_y = dy / distance

            # 更新位置，沿直线移动
            self.attacker.position[0] += round(direction_x * self.speed)
            self.attacker.position[1] += round(direction_y * self.speed)
        else:
            # 到达目标位置，返回 True
            return True
        return False
    
    def turnBack(self):
        if not self.back_position:
            # 记录一个回位位置
            if not self.hit_again:
                # 正常要退回原位
                self.back_position = self.original_attacker_position
            else:
                # 在多重攻击中，退回半步，随即进行下一次攻击
                b_r = 2 # 退回倍率1/2
                dx0 = self.original_attacker_position[0] - self.attacker.position[0]
                dy0 = self.original_attacker_position[1] - self.attacker.position[1]

                self.back_position = [self.attacker.position[0] + dx0 // b_r, 
                                      self.attacker.position[1] + dy0 // b_r]

        # 计算目标位置与当前位置的方向向量
        dx = self.back_position[0] - self.attacker.position[0]
        dy = self.back_position[1] - self.attacker.position[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5  # 计算两点间距离
    
        if tuple(self.attacker.position) != self.back_position and distance > default_speed:
            # 计算单位方向向量
            direction_x = dx / distance
            direction_y = dy / distance

            # 更新位置，沿直线移动
            self.attacker.position[0] += round(direction_x * self.speed)
            self.attacker.position[1] += round(direction_y * self.speed)
        else:
            # 到达目标位置
            if not self.hit_again:
                # 不继续攻击的话就记录当前位置作为下一次攻击的回位位置
                self.attacker.original_attacker_position = tuple(self.attacker.position)
            return True
        return False
        

    def update(self):
        if not self.done:
            if not self.hit:
                self.hit = self.itemFlying()
            if self.hit and not self.back:
                self.target.be_hit[self.tracker[0]] = True
                self.back = self.turnBack()
            if self.hit and self.back and not self.hit_again:
                self.attacker.position = list(self.original_attacker_position)
            if self.hit and self.back and self.words_shown:
                self.done = True



class MagicAttack(GeneralOneTargetAttack):
    def __init__(self, game, attacker, target, damage, category="damage"):
        super().__init__(game, attacker, target, damage)

        self.speed = round(1.2 * default_speed)
        self.size = game.unit_size // 6

        self.damage = damage
        self.category = category
        if self.category == "damage":
            self.color = BLACK
        elif self.category == "heal":
            self.color = GREEN
        else:
            self.color = BLACK

        self.font = FONT.size(default_font_size+5)
        self.moving_rect = pygame.Rect(*self.attacker.position, self.size*2, self.size*2)
    
    def voiceInitialize(self):
        # 伤害飘字
        if self.damage > 0:
            if self.category == "damage":
                self.words.add_text(f"-{self.damage}", self.target.position, color=MID_RED, i=0, time="hit", alter_hp=self.target)
            elif self.category == "heal":
                self.words.add_text(f"+{self.damage}", self.target.position, color=GREEN, i=0, time="hit", alter_hp=self.target)



    def itemFlying(self):
        item = self.moving_rect

        dx = self.target.position[0] - item.centerx
        dy = self.target.position[1] - item.centery
        distance = (dx ** 2 + dy ** 2) ** 0.5  # 计算两点间距离

        if not item.colliderect(self.target.rect):
            # 计算单位方向向量
            direction_x = dx / distance
            direction_y = dy / distance

            # 更新位置，沿直线移动
            item.x += round(direction_x * self.speed)
            item.y += round(direction_y * self.speed)
        else:
            # 到达目标位置，返回 True
            return True
        return False
    
    def update(self):
        if not self.hit:
            self.hit = self.itemFlying()
        else:
            self.target.be_hit[self.tracker[0]] = True
            self.back = True
        if self.hit and self.back and self.words_shown:
            self.done = True

    def draw(self,screen):
        if not self.voice_initialized:
            try:
                self.voiceInitialize()
                self.voice_initialized = True
            except AttributeError:
                print("AttributeError")
                pass
            finally:
                self.words.voice_inserted = True
        
        if self.delay > 0:
            self.delay -= 1
            return
        
        if not self.done:
            self.update()
            self.words.showWordEffects()
            if not self.hit:
                pygame.draw.circle(screen, self.color, self.moving_rect.center, self.size)
            


class MutliMagicAttack(MagicAttack):
    def __init__(self, game, attacker, target, damage, category="damage"):
        super().__init__(game, attacker, target, damage, category)
        self.game = game
        self.animations = []
        self.target = None
        self.targets = target
        self.targets_count = len(target)

        self.hit = False
        self.hit_everyone = [False] * self.targets_count
        self.back = False
        self.back_from_every_hit = [False] * self.targets_count
        self.words_shown = False
        self.words_shown_everyone = [False] * self.targets_count

        if type(damage) == list:
            # 防错
            if len(damage) != self.targets_count:
                raise ValueError("Damage list length not equal to target list length")
            # 逐一填充animations
            self.animations = [MagicAttack(self.game, self.attacker, target0, damage[i], self.category) for i, target0 in enumerate(self.targets)]

        else:
            # 简单统一处理
            self.animations = [MagicAttack(self.game, self.attacker, target0, damage, self.category) for target0 in self.targets]


    def voiceInitialize(self):
        pass


    def update(self):
        if not self.done:
            for i, animation in enumerate(self.animations):
                if animation.hit:
                    self.targets[i].be_hit[self.tracker[i]] = True
                    self.hit_everyone[i] = True
                    self.back_from_every_hit[i] = True
                if animation.words_shown:
                    self.words_shown_everyone[i] = True
            if all(self.hit_everyone):
                self.hit = True
                self.back = True
            if self.hit and self.back and self.words_shown and all(self.words_shown_everyone):
                self.done = True

    def draw(self,screen):
        if not self.voice_initialized:
            try:
                self.voiceInitialize()
                self.voice_initialized = True
            except AttributeError:
                pass
            finally:
                self.words.voice_inserted = True

        if self.delay > 0:
            self.delay -= 1
            return
        
        if not self.done:
            self.update()
            self.words.showWordEffects()
            for animation in self.animations:
                animation.draw(screen)

class KaboomAttack(MutliMagicAttack):
    def __init__(self, game, attacker, target, damage, category="damage"):
        super().__init__(game, attacker, target, damage, category)
        self.speed = round(0.4 * default_speed)
        self.size = game.unit_size // 4
        self.start_size = game.unit_size // 4
        self.final_size = game.unit_size // 2
        self.font = FONT.size(30)

        self.warning_circle_r = 0 # start from 0, increase by 0.3 each tick, finally reach 1.2 * unit_size

    def voiceInitialize(self):
        # 奥数彗星从召唤者正上方从天而降
        for i in range(self.targets_count):
            self.animations[i].moving_rect = pygame.Rect(self.attacker.position[0]-20, -60, self.size*2, self.size*2)
            self.animations[i].speed = self.speed
            self.animations[i].size = self.size
        # 相关语音
        self.words.add_text(self.attacker.chinese_kaboom_voice, self.attacker.position, color=LIGHT_BLUE, i=0, time="now", how="insert")
        for i in range(self.targets_count):
            self.animations[i].words.add_text(self.attacker.chinese_be_hit_by_kaboom_voice, self.targets[i].position, color=LIGHT_BLUE, i=i, time="hit", how="insert")

            
    def draw(self,screen):
        super().draw(screen)
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        circle_color = (*RED, 100)  # 红色，透明度100

        # 奥数彗星的其他特效
        if not self.done:
            # 慢慢增大彗星的半径
            if self.size < self.final_size:
                self.size += 0.2
                # 比例插值法增大感叹号大小
                progress = (self.size - self.start_size) / (self.final_size - self.start_size)
                self.font = FONT.size(int(30 + progress * 18))            
            # 慢慢增大警示圈的半径
            if self.warning_circle_r < round(unit_size * 0.9):
                self.warning_circle_r += 0.5
            
            for i,animation in enumerate(self.animations):
                # 更新彗星大小
                self.animations[i].size = self.size

                if not animation.hit:
                    # 警示圈特效
                    pygame.draw.circle(overlay, circle_color, animation.target.rect.center, self.warning_circle_r)
            screen.blit(overlay, (0, 0))

            for i,animation in enumerate(self.animations):
                if not animation.hit:
                    # 飞弹的感叹号装饰
                    text_surface = self.font.render("!", True, MID_RED)  # 红色感叹号
                    text_rect = text_surface.get_rect(center=animation.moving_rect.center)  # 居中
                    screen.blit(text_surface, text_rect) 



