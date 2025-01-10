from random  import randint, sample
from TeamLogic import *
import pygame
from colors import *
from animation import *
from GeneralSettings import *
from WordEffects import *
from testDamage import *



def dprint(s):
    if printActionDescription:
        print(s)


def rollDice(xdx="1d6"):
    x, dx = xdx.split("d")
    x, dx = int(x), int(dx)
    return sum([randint(1, int(dx)) for _ in range(int(x))])


# 用于绘制角色矩形内部的一个镂空矩形，显示持续性True/False特殊状态
def drawInsideRect(surface, position, color, width=5):
    rect = pygame.Rect(0, 0, unit_size*3//4, unit_size*3//4)
    rect.center = tuple(position)
    pygame.draw.rect(surface, color, rect, width)


# 用于绘制竖在角色前面的护盾
def drawShield(unit, surface):
    shields = {
        1: (unit_size*5//4, unit_size//2+6),
        2: (unit_size*4//4, unit_size//2+14),
        3: (unit_size*3//4, unit_size//2+22)
    }

    # 绘制被守护的单位的护盾
    for i in range(1, unit.shield+1):
        x, y = unit.position[0] + (2*(unit.side=="myTeam")-1) * shields[i][1], unit.position[1]
        rect = pygame.Rect(0, 0, 3, shields[i][0])
        # 描边
        for dx, dy in offsets:
            rect.center = (x+dx, y+dy)
            pygame.draw.rect(surface, BLACK, rect)
        rect.center = (x, y)
        pygame.draw.rect(surface, NOT_THAT_YELLOW, rect)


# Constants for Mage Type        
manaCost = 20
manaRecovery = 30

attack_logic = {
    "front": randAliveFront,
    "back": randAliveBack,
    "all": randAliveAll
}


class Character(object):
    def __init__(self):
        # general status
        self.name = ''
        self.chinese_name = ''
        self.dead_name = '似了'
        self.maxhp, self.hp, self.lockhp = [99999] * 3
        self.cost = 999999        
        self.act_times = 0

        # general tracker
        self.poisoned = 0
        self.attachment = []
        self.under_whose_protection = None
        self.shield = 0
        self.side = ""
        self.team = None

        # personal status
        self.str = 0
        self.maxmana, self.mana = [0] * 2
        self.int = 0
        self.heal = 0
        self.alive = True
        self.cannot_be_poisoned = False
        self.melee = False          

        # personal description-like info
        self.actual_row = "none"
        self.selfrow = "all"
        self.targetrow = "none"

        # animation info
        self.themeColor = WHITE
        self.special_status = False # 记录有没有需要显示的特殊状态
        self.unplayed_anima = False
        self.be_hit = []
        self.be_hit_count = -1
        self.position = [0,0]
        self.original_position = (0,0)
        self.rect = None
        self.color = BLUE

        # description & voice
        self.description = ""
        self.chinese_description = ""
        self.attack_voice = ""
        self.chinese_attack_voice = ""


    @classmethod
    def reset(cls): 
        # 彻底重置角色状态
        return cls() 


    def move(self):
        # 角色绘图位置的移动
        self.rect = pygame.Rect(0, 0, unit_size, unit_size)
        self.rect.center = tuple(self.position)


    def act(self,myTeam,enemy, game):
        return
    

    def new_turn(self):
        # 新回合，回合内状态的初始化
        self.act_times += 1


    def die(self):
        # 死亡后的归零数值
        self.hp = 0
        self.mana = 0
        self.poisoned = 0
        self.act_times = 0
        self.alive = False
        self.shield = 0 
        self.checkShield()

        if self.attachment:
            for attached in self.attachment[:]:
                attached.lose_attach()

        dprint(self.name + ' died!')


    def check(self):
        # for debug
        print(f"{self.name} {'is' if self.alive else 'is not'} alive, with hp {self.hp} and lockhp {self.lockhp}.")
    

    def drawSpecialStatus(self, surface):
        pass

    def drawShieldWithSurroundings(self, surface):
        drawShield(self, surface)
    
    def checkShield(self):
        # 守护归零则剔除
        if self.shield == 0 and self.under_whose_protection:
            self.under_whose_protection.protecting.remove(self)
            self.under_whose_protection = None


    def fightBack(self, attacker, game, times=1/2): # 通用反击倍率1/2
        # 先检查守护和替代反击，有的话跳过自己的反击
        if self.under_whose_protection and self.under_whose_protection.alive:
            damage = self.under_whose_protection.fightBack(attacker, game)
            damage = testDamage(self.under_whose_protection, attacker, damage)
            self.checkShield()
            return damage
        
        # 再检查自己的反击
        if self.str > 0 and self.melee and self.alive:
            damage = self.str * times
            damage = testDamage(self, attacker, damage)
            dprint(self.name + ' fight back!')
            attacker.gotHurt(damage)
            return damage


    def actWithPoison(self,myTeam,enemy,game):
        if self.poisoned:
            self.poisoned -= 1
            damage = min(self.maxhp // 5, 400)
            damage = testDamage(None, self, damage, type="poison")
            self.gotHurt(damage, type="poison")

            dprint(self.name + ' is poisoned!')
            animates = BlankAnimation(game, self)
            animates.words.add_text(f"-{damage}", self.position, color=GREEN, i=0, time="now", alter_hp=self)
            game.animations.append(animates)
        if self.alive:
            self.act_times -= 1
            self.act(myTeam,enemy,game)


    def loseMana(self, tempCost = manaCost):
        tempCost = round(tempCost)
        self.mana = min(max(0, self.mana-tempCost), self.maxmana)


    def gotHurt(self, damage, type="normal"):
        # gotHurt没有动画
        if self.hp <= 0:
            return None
        if damage < 0 and type=="normal":
            type = "heal"

        if damage >= self.hp:
            excess = damage - self.hp
            self.die()
            return excess
        else:
            self.hp = min(self.hp - damage, self.maxhp)
            if damage > 0:
                dprint(self.name + f' hurt with remaining hp {self.hp}.')
            else:
                dprint(self.name + f' healed with remaining hp {self.hp}.')



class Fighter(Character):
    def __init__(self):
        super().__init__()
        self.name = 'Fighter'
        self.chinese_name = '战士'
        self.maxhp, self.hp, self.lockhp = [1200] * 3
        self.str = 120
        self.cost = 100
        self.selfrow = "front"
        self.targetrow = "front"
        self.melee = True

        self.description = "Typical Fighter. Melee."
        self.chinese_description = "标准的战士身材。只能攻击前排单位，受到近战攻击可反击。"

    def act(self,myTeam,enemy,game, voices=None):
        target = attack_logic[self.targetrow](enemy)
        damage = self.str
        damage = testDamage(self, target, damage)

        dprint(f'{self.name} Hurt enemy {target.name} by damage {damage}.')
        target.gotHurt(damage)
        fightBackDamage = target.fightBack(self, game) # fightBack已经包含了testDamage

        animates = HitAttack(game, self, target, damage)
        if voices:
            for voice in voices:
                animates.words.add_text(*voice)
        game.animations.append(animates)

        if fightBackDamage:
            animates2 = FightBack(game, target, self, fightBackDamage)
            game.animations.append(animates2)

        return target
  

class Mage(Character):
    def __init__(self):
        super().__init__()
        self.name = 'Mage'
        self.chinese_name = '法师'
        self.maxmana, self.mana = [50] * 2
        self.maxhp, self.hp, self.lockhp = [800] * 3
        self.cost = 200
        self.int = 400
        self.selfrow = "back"
        self.targetrow = "all"

        self.description = "Use Mana to Strike Hard."
        self.chinese_description = "标准的法师身材。消耗20法力造成高额单体伤害。"

        self.attack_voice = "Magic Missile!"
        self.chinese_attack_voice = " 魔法飞弹！"
        self.mana_voice = "Recover Mana"
        self.chinese_mana_voice = "清晰术"

    def cast(self, myTeam, enemy, game, voices=None):
        self.mana -= manaCost
        target = attack_logic[self.targetrow](enemy)
        damage = self.int
        damage = testDamage(self, target, damage)
        target.gotHurt(damage)

        dprint(f'{self.name} Strike enemy {target.name} with spell')
        animates = MagicAttack(game, self, target, damage, "damage")
        if voices:
            for voice in voices:
                animates.words.add_text(*voice)
        else:
            if hasattr(self, "chinese_attack_voice"):
                animates.words.add_text(self.chinese_attack_voice, self.position, color=WHITE, i=0, time="now", how="insert")
        game.animations.append(animates)

        return target
    
    def recoverMana(self, game, tempRecovery = manaRecovery, silent=0):
        tempRecovery = round(tempRecovery)
        self.mana += min(tempRecovery, self.maxmana-self.mana)

        dprint(f'Mana recover to {self.mana}.')
        animates = RecoverMana(game, self, tempRecovery, silent)
        game.animations.append(animates)


    def act(self, myTeam, enemy, game, voices=None):
        if self.mana < manaCost:
            self.recoverMana(game)
        else:
            return self.cast(myTeam, enemy,game, voices)


class Berserker(Fighter):
    def __init__(self):
        super().__init__()
        self.name = 'Berserker'
        self.chinese_name = '狂战士'
        self.maxhp, self.hp, self.lockhp = [1500] * 3
        self.str = 150
        self.cost = 250
        self.anger = False
        self.themeColor = RED

        self.description = "Double STR When HP Is Low."
        self.chinese_description = "生命值低于50%时，进入狂暴模式，攻击力翻倍，且攻击可回血。"
        # 图鉴：可以回到高于50%血且不解除狂暴状态；死亡永久失去狂暴能力。

        self.berserk_voice = "Berserk!"
        self.chinese_berserk_voice = " 狂暴！"
        self.berserk_attack_voice = "War!"
        self.chinese_berserk_attack_voice = "战争热诚"

    def die(self):
        super().die()
        # 死亡后，即使复活狂战士也不再有狂暴能力
        if self.anger:
            self.str = self.str // 2
        self.anger = False
    
    def drawSpecialStatus(self, surface):
        if self.anger:
            drawInsideRect(surface, self.position, self.themeColor)
 
    def act(self, myTeam, enemy, game):
        if (not self.anger) and (0 < self.hp <= 0.5*self.maxhp):
            self.str *= 2
            self.anger = True
            self.special_status = True

            dprint('Berserk mode! Attack double!')
            animates = BlankAnimation(game, self)
            animates.words.add_text(self.chinese_berserk_voice, self.position, color=RED, i=0, time="now", how="insert")
            game.animations.append(animates)
        if self.anger:
            self.gotHurt(-self.maxhp//10)
            super().act(myTeam, enemy, game, 
                        voices=[(self.chinese_berserk_attack_voice, self.position, RED, 0, "hit", "insert", 0, None), 
                                (f"+{self.maxhp//10}", self.position, GREEN, 0, "hit", "", 0, self)])
        # voices=[(text0, position, color=RED, i=0, time="hit", how="", delay=0, alter_hp=None)]
        else:
            super().act(myTeam, enemy, game)
        

class ArchMage(Mage):
    def __init__(self):
        super().__init__()
        self.name = 'ArchMage'
        self.chinese_name = '奥数大法师'
        self.cost = 600
        self.others = []
        self.special_status = True

        self.description = "Cast a Big Spell When He Is the Only One."
        self.chinese_description = "当一方只有大法师一人存活时，立即消耗全部法力，引导奥数彗星攻击敌方全体单位。"

        self.mana_voice = "Random Recover"
        self.chinese_mana_voice = "不稳定高阶清晰术"
        self.kaboom_voice = "Cast KABOOM"
        self.chinese_kaboom_voice = "！吟唱 奥数彗星！"
        self.kaboom_ready_voice = "KABOOM Ready"
        self.chinese_kaboom_ready_voice = "已沟通奥数魔网"
        self.be_hit_by_kaboom_voice = "! KABOOOM !"
        self.chinese_be_hit_by_kaboom_voice = " 彗星坠落！"

        self.kaboomSpell = True
    
    def die(self):
        super().die()
        self.kaboomSpell = False


    def drawSpecialStatus(self, surface):
        if self.kaboomSpell:
            drawInsideRect(surface, self.position, DARK_BLUE)


    def kaboom(self,enemy,game):
        damage = []
        kaboom_damage = round(self.int * (self.mana/manaCost))

        targets = [potential_target 
                   for potential_target in (enemy.front + enemy.back) 
                   if potential_target.alive]
        for i, target in enumerate(targets):
            damage0 = testDamage(self, target, kaboom_damage, type="kaboom")
            damage.append(damage0)
            target.gotHurt(damage0)
        # 释放完毕设置疲劳状态
        self.mana = 0
        self.kaboomSpell = False
        self.special_status = False

        dprint(f'Cast KABOOOOOOM! (Damage {kaboom_damage}) to every enemy!')
        animates = KaboomAttack(game, self, targets, damage)
        game.animations.append(animates)


    def checkKaboom(self,game):
        if self.mana == self.maxmana and self.kaboomSpell==False:
            self.kaboomSpell = True
            self.special_status = True

            dprint(f'KABOOM Ready')
            animates = BlankAnimation(game, self)
            animates.words.add_text(self.chinese_kaboom_ready_voice, self.position, color=LIGHT_BLUE, i=0, time="now", delay=60)
            game.animations.append(animates)


    def recoverMana(self,game):
        super().recoverMana(game, tempRecovery = randint(6, 12) * manaRecovery // 6)
        self.checkKaboom(game)


    def act(self,myTeam,enemy,game):
        self.checkKaboom(game)
        if self.mana >= manaCost and allDead(self.others) and self.kaboomSpell:
            self.kaboom(enemy,game)
        else:
            super().act(myTeam, enemy,game)


class Necromancer(Mage):
    def __init__(self):
        super().__init__()
        self.name = 'Necromancer'
        self.chinese_name = '通灵师'
        self.cost = 400
        self.int = 400
        self.themeColor = GREEN

        self.description = "Revive the Dead."
        self.chinese_description = "消耗40法力值，以一半生命值复活一名已经阵亡的队友。"
        # 图鉴：复活的队友蓝条为0

        self.heal_voice = "! Revive !"
        self.chinese_heal_voice = " 死者苏生！"
        self.be_revived_voice = "Revived"
        self.chinese_be_revived_voice = "堂堂复活"

    def revive(self, game, myTeam):
        dead_one = randDeath(myTeam)
        # 尽量不复活attachment
        trial = 0
        while trial < 10 and isinstance(dead_one, Attachment):
            dead_one = randDeath(myTeam)
            trial += 1

        dead_one.hp = dead_one.maxhp // 2
        dead_one.alive = True

        # 对复活低质量单位有补偿
        tempCost = dead_one.cost / 5
        self.loseMana(min(tempCost, manaCost*2))

        dprint(f'Revive member {dead_one.name} with hp {dead_one.maxhp // 2}.')
        animates = MagicAttack(game, self, dead_one, 0, "heal")
        animates.words.add_text(self.chinese_be_revived_voice, dead_one.position, color=GREEN, i=0, time="hit", how="insert")
        animates.words.add_text(f"+{dead_one.maxhp // 2}", dead_one.position, color=GREEN, i=0, time="hit", alter_hp=dead_one)
        game.animations.append(animates)

        return dead_one


    def act(self,myTeam,enemy,game):
        if not allAlive(myTeam):
            if self.mana >= manaCost * 2:
                self.revive(game, myTeam)
            else:
                self.recoverMana(game)
        else:
            super().act(myTeam, enemy,game)


class Ranger(Fighter, Mage):
    def __init__(self):
        super().__init__()
        self.name = 'Ranger'
        self.chinese_name = '法师游骑兵'
        self.maxhp = 1000
        self.hp = 1000
        self.lockhp = self.hp
        self.str = 100
        self.int = 300
        self.cost = 150
        self.selfrow = "all"
        self.targetrow = "all"

        self.description = "Both a Fighter And a Mage."
        self.chinese_description = "50%几率随机进行近战或远程法术攻击。近战攻击只能攻击前排单位，但是可以回蓝。"

    def act(self, myTeam, enemy,game):
        if randint(1,6)>3:
            self.targetrow = "all"
            Mage.act(self, myTeam, enemy,game)
        else:
            self.targetrow = "front"
            Mage.recoverMana(self, game, tempRecovery=manaCost//2, silent = 1)
            Fighter.act(self, myTeam, enemy,game)


class Assassin(Fighter):
    def __init__(self):
        super().__init__()
        self.name = 'Assassin'
        self.chinese_name = '刺客'
        self.maxhp, self.hp, self.lockhp = [800] * 3
        self.cost = 200
        self.str = 80
        self.dagger = 3
        self.special_status = True
        self.themeColor = GREEN
        self.targetrow = "all"

        self.description = "Poisoned Dagger. Can Critic When Preparing."
        self.chinese_description = "使用毒匕首攻击，最多让三个目标中毒，此后需要准备两回合以再次上毒。"
        # 图鉴：可攻击后排单位。使用毒匕首攻击，附带3层毒，目标行动时受到20%生命值的毒伤。匕首没有涂毒时，行动两回合以准备一层毒，此时有20%几率暴击。

        self.attack_voice = "Poison Ready"
        self.chinese_attack_voice = " 淬毒！"
        self.be_poisoned_voice = "Poisoned"
        self.chinese_be_poisoned_voice = "中毒"

    def die(self):
        super().die()
        self.dagger = 0

    def drawSpecialStatus(self, surface):
        c_x, c_y = self.position
        pygame.draw.circle(surface, BLACK, (c_x-unit_size//2, c_y+unit_size//2 - 12), 15)
        text = FONT.size(default_font_size).render(f"{int(self.dagger)}", True, GREEN)
        text_rect = text.get_rect(center=(c_x-unit_size//2, c_y+unit_size//2 - 12))
        surface.blit(text, text_rect)

    def act(self, myTeam, enemy, game):
        self.special_status = True
        target = attack_logic[self.targetrow](enemy)
        # 带毒攻击
        if self.dagger >= 1 and target.cannot_be_poisoned == False:
            self.dagger -= 1
            damage = self.str
            damage = testDamage(self, target, damage)
            target.poisoned = 3
            target.gotHurt(damage)
            fightBackDamage = target.fightBack(self, game)

            animates = HitAttack(game, self, target, damage)
            animates.words.add_text(self.chinese_be_poisoned_voice, target.position, color=GREEN, i=0, time="hit")
            game.animations.append(animates)

            if fightBackDamage:
                animates2 = FightBack(game, target, self, fightBackDamage)
                game.animations.append(animates2)
        # 普通攻击
        else:
            # 涂毒需要准备一回合
            self.dagger += 0.5
            if self.dagger == 1:
                animates = BlankAnimation(game, self)
                animates.words.add_text(self.chinese_attack_voice, self.position, color=GREEN, i=0, time="now", how="insert")
                game.animations.append(animates)

            if not randint(0,4): # 20%暴击
                damage = self.str * 2
                damage = testDamage(self, target, damage)
                target.gotHurt(damage)
                fightBackDamage = target.fightBack(self, game)

                animates = HitAttack(game, self, target, damage)
                animates.words.add_text(chinese_critical_voice, target.position, color=MID_RED, i=0, time="hit", how="insert-1")
                game.animations.append(animates)

                if fightBackDamage:
                    animates2 = FightBack(game, target, self, fightBackDamage)
                    game.animations.append(animates2)

            else:
                super().act(myTeam, enemy, game)
        return target



class Bard(Character):
    def __init__(self):
        super().__init__()
        self.name = 'Bard'
        self.chinese_name = '吟游诗人'
        self.maxhp = 800
        self.hp = 800
        self.lockhp = self.hp
        self.cost = 100
        self.selfrow = "all"
        self.themeColor = NOT_THAT_YELLOW

        self.description = "Boost Morale But Doesn't Attack."
        self.chinese_description = "不能进行攻击，但是吟唱战歌可以让下一位角色连续行动两次。"

        self.attack_voice = "Do~Re~Mi"
        self.chinese_attack_voice = " 战鼓擂动！"

    def act(self,myTeam,enemy,game):
        myTeam.doubleattack += 1

        dprint(f'do~re~mi, {self.name} is singing!')
        animates = BlankAnimation(game, self)
        animates.words.add_text(self.chinese_attack_voice, self.position, color=self.themeColor, i=0, time="now", how="insert")
        game.animations.append(animates)
        

class Paladin(Fighter, Mage):
    def __init__(self):
        super().__init__()
        self.name = 'Paladin'
        self.chinese_name = '圣骑士'
        self.maxhp, self.hp, self.lockhp = [2000] * 3
        self.str = 200
        self.int = 150
        self.cost = 300
        self.themeColor = ORANGE
        self.special_status = True
        self.to_be_forgiven = True

        self.description = "Deal Additional Melee Damage with Mana."
        self.chinese_description = "使用信仰力量护佑自身或附魔武器，可消耗10法力造成额外伤害。受到牧师的回复效果翻倍。"

        self.attack_voice = "Holy Slash!"
        self.chinese_attack_voice = " 至圣斩！"
        self.double_attack_voice = "Justice!"
        self.chinese_double_attack_voice = "邪佞无处遁身"
        self.mana_voice = "Blessed by the Light"
        self.chinese_mana_voice = "重获神恩"
        self.no_mana_voice = "Losing Connection with the Belief"
        self.chinese_no_mana_voice = "无法继续借用神力"
        self.forgived_from_death_voice = "Forgived"
        self.chinese_forgived_from_death_voice = "免于一死"


    def die(self):
        if self.mana > 0 and self.to_be_forgiven:
            self.loseMana(manaCost)
            self.to_be_forgiven = False
            self.hp = 1
            dprint(self.name + ' was forgived.')
        else:
            super().die()
            self.str = 150
            self.to_be_forgiven = False


    def drawSpecialStatus(self, surface):
        if self.to_be_forgiven and self.mana:
            drawInsideRect(surface, self.position, ORANGE)


    def strike(self,myTeam,enemy,game):
        target = attack_logic[self.targetrow](enemy)
        # 对手血量较高时可触发2次
        times = 1
        if self.mana > manaCost // 2:
            times += 1
        if self.hp < target.hp:
            times += 1
        self.loseMana(manaCost * times // 2)
        damage = self.str + max(self.int, 0.2*target.hp) * (times-1)
        damage = testDamage(self, target, damage)

        target.gotHurt(damage)
        fightBackDamage = target.fightBack(self, game)

        # 坚守信仰，蓝条归零后不能发动至圣斩，但是攻击力提升50
        if self.mana <= 0:
            self.mana = 0
            self.str += 50 

        dprint(f'Holy Slash! {self.name} Strike enemy {target.name} by damage {damage}.')
        animates = HitAttack(game, self, target, damage)
        if times >= 2:
            animates.words.add_text(self.chinese_double_attack_voice, target.position, color=ORANGE, i=0, time="now", how="insert")
        elif times == 1:
            animates.words.add_text(self.chinese_attack_voice, target.position, color=ORANGE, i=0, time="hit", how="insert")
        if self.mana == 0:
            dprint(self.name + " " + self.no_mana_voice)
            animates.words.add_text(self.chinese_no_mana_voice, self.position, color=ORANGE, i=0, time="back")
        game.animations.append(animates)

        if fightBackDamage:
            animates2 = FightBack(game, target, self, fightBackDamage)
            game.animations.append(animates2)


    def act(self,myTeam,enemy,game):
        # 清除中毒状态
        self.poisoned = 0
        # 法力满时重获神恩
        if self.mana == self.maxmana:
            self.to_be_forgiven = True
            self.special_status = True

        if self.mana < manaCost // 2:
            Fighter.act(self, myTeam, enemy,game)
        else:
            self.strike(myTeam, enemy,game)


class Archer(Fighter):
    def __init__(self):
        super().__init__()
        self.name = 'Archer'
        self.chinese_name = '弓箭手'
        self.str = 100
        self.maxhp, self.hp, self.lockhp = [1000] * 3
        self.cost = 100
        self.selfrow = "back"
        self.targetrow = "all"
        self.melee = False

        self.description = "Typical Archer, Attacking from Range."
        self.chinese_description = "标准的射手身材。远程攻击利于对抗[最前排]和[满血]单位，这两个弱点可叠加。"
        # 图鉴：远程攻击在瞄准满血单位时造成200%伤害，从后排攻击前排时造成120%伤害，可叠加。如果前排死完了，后排打后排也有加成。

        self.attack_voice = "Shoot!"
        self.chinese_attack_voice = " 射击！"


    def act(self,myTeam,enemy,game):
        target = attack_logic[self.targetrow](enemy)
        # 有条件的伤害倍率
        damage = self.str
        if target in enemy.front and self in myTeam.back:
            damage *= 1.2 # 后排打前排
        elif target in enemy.back and allDead(enemy, where="front") and self in myTeam.back:
            damage *= 1.2 # 或者前排死完了，后排打后排也有加成
        if target.hp == target.maxhp:
            damage *= 2 # 打满血单位伤害翻倍
        damage = testDamage(self, target, damage)
        target.gotHurt(damage)

        dprint(f'Archer Hurt enemy {target.name} by damage {damage} from range.')
        animates = MagicAttack(game, self, target, damage, "damage")
        if damage > self.str:
            animates.words.add_text(chinese_critical_voice, target.position, color=MID_RED, i=0, time="hit", how="insert-1")
        animates.words.add_text(self.chinese_attack_voice, self.position, color=WHITE, i=0, time="now", how="insert")
        game.animations.append(animates)


class Cleric(Mage, Bard):
    def __init__(self):
        super().__init__()
        self.name = 'Cleric'
        self.chinese_name = '牧师'
        self.int = 200
        self.heal = 300
        self.cost = 300
        self.maxmana, self.mana = [80] * 2
        self.themeColor = ORANGE

        self.description = "Heal the Wounded."
        self.chinese_description = "友方受伤时，有概率治疗一名或全体队友，对同样有信仰的圣骑士效果翻倍。没有队友受伤时，有概率使用圣光攻击敌人或合唱圣歌鼓舞士气。"
        # 图鉴：有更高的初始法力值。可能治疗一名队友并用自己的蓝给对方回蓝，也可能治疗友方全体单位，但治疗量减半且不回蓝。

        self.heal_voice = " Heal!"
        self.chinese_heal_voice = " 愈合！"
        self.heal_mana_voice = "Mana Recover"
        self.chinese_heal_mana_voice = "清明"
        self.heal_all_voice = "! Heal All !"
        self.chinese_heal_all_voice = "！全体治疗！"

    def healone(self,myTeam,game):
        target = Damaged(myTeam, who="one")
        # 对圣骑士效果翻倍
        times = 2 if target.name == "Paladin" else 1
        heal = self.heal*times
        # 对40%以下血量的单位治疗效果提升50%
        if target.hp / target.maxhp < 0.4:
            heal *= 1.5
        # 最终结算
        heal = testDamage(self, target, heal, type="heal")
        target.gotHurt(-heal)

        dprint(f'Heal member {target.name} by {heal}.')
        animates = MagicAttack(game, self, target, heal, "heal")
        animates.words.add_text(self.chinese_heal_voice, self.position, color=GREEN, i=0, time="now", how="insert")
        game.animations.append(animates)
        
        # 单体治疗可以回蓝，但是不能给自己回蓝
        if target.maxmana and target is not self:
            tempRecovery = min(manaRecovery*times//2, target.maxmana-target.mana)
            if tempRecovery:
                target.mana += tempRecovery
                tempCost = min(tempRecovery/times//2, self.mana)
                # 实际上是把自己的蓝传给对方，自己要扣除
                if tempCost:
                    self.mana -= tempCost

                dprint(f'Member {target.name} mana recover by {tempRecovery}.')
                dprint(f'As a cost, Cleric mana lose {tempCost}.')
                if times == 2: # 圣骑士
                    animates2 = RecoverMana(game, target, manaRecovery//2)
                else:
                    animates2 = RecoverMana(game, target, manaRecovery//2, silent=2)
                    animates2.words.add_text(self.chinese_heal_mana_voice, target.position, color=ORANGE, i=0, time="now", how="insert")
                game.animations.append(animates2)


    def healall(self,myTeam,game):
        targets = Damaged(myTeam, who="all")
        # 全体治疗不回蓝，治疗量打折
        heal = []
        heal_base = round(max(self.heal/4, self.heal/len(targets)))
        # 查看倍率
        for target in targets:
            times = 2 if target.name == "Paladin" else 1 # 对圣骑士效果翻倍
            if target.hp / target.maxhp < 0.4: # 对40%以下血量的单位治疗效果提升50%
                times *= 1.5

            heal0 = testDamage(self, target, heal_base*times, type="heal")
            heal.append(heal0)
            target.gotHurt(-heal0)

        dprint(f'Cleric heals all wounds.')
        animates = MutliMagicAttack(game, self, targets, heal, "heal")
        animates.words.add_text(self.chinese_heal_all_voice, self.position, color=GREEN, i=0, time="now", how="insert")
        game.animations.append(animates)


    def act(self,myTeam,enemy,game):
        if self.mana >= manaCost and Damaged(myTeam, who="all"):
            dice = randint(1,len(Damaged(myTeam, who="all"))+3)
            # 受伤人数少时更高概率进行单体治疗
            if dice <= 4:
                self.healone(myTeam,game)
            else:
                self.healall(myTeam,game)
            self.mana -= manaCost
        else:

            # 没有受伤队友时，有概率使用Mage或Bard的攻击
            dice = rollDice("1d6")
            if self.mana < manaCost:
                self.recoverMana(game, tempRecovery = round(manaRecovery*1.5))
            elif dice <= 3:
                self.attack_voice = " Light!"
                self.chinese_attack_voice = " 圣光！"
                self.cast(myTeam, enemy,game, 
                          voices=[(self.chinese_attack_voice, self.position, ORANGE, 0, "now", "insert")])
                # voices=[(text0, position, color=RED, i=0, time="hit", how="", delay=0, alter_hp=None)]
            else:
                self.attack_voice = "Choral Hymn"
                self.chinese_attack_voice = "合唱圣歌"            
                Bard.act(self, myTeam, enemy, game)


class HellConqueror(Fighter, Mage):
    def __init__(self):
        super().__init__()
        self.name = 'HellConqueror'
        self.chinese_name = '魔狱征服者'
        self.dead_name = '炼狱'
        self.maxhp, self.hp, self.lockhp = [4000] * 3
        self.str = 400
        self.int = 0
        self.cost = 1500
        self.percentage_defense_buff = 0.1 # 减伤10%
        self.selfrow = "front"
        self.targetrow = "all"
        self.themeColor = HELL_RED

        self.channeling = False # 正在引导
        self.power = False # 引导的灭世之力
        self.killing = 0 # 凯旋状态
        self.max_killing = 2 # 最多一回合奖励两动

        self.description = "Strike with His Incredible Sword and Infernal Magma Combined."
        self.chinese_description = "用地狱深处的罪恶之火浇灌剑身,他将带来最终的杀戮。"\
            "攻击造成范围斩杀伤害，成功斩杀时，凯旋，并获得一个额外的回合。"
        
        self.attack_voice = "Infernal Magma"
        self.chinese_attack_voice = "焚天之焰"
        self.mana_voice = "Feeling the Hell"
        self.chinese_mana_voice = "罪业之力聚于此地"
        self.channel_voice = "Channeling Flame from Hell"
        self.chinese_channel_voice = "地狱之火重返吾身"
        self.power_voice = "Power of the End"
        self.chinese_power_voice1 = " 灭世之力！"
        self.chinese_power_voice2 = "启动炼狱心脏发动机"
        self.no_mana_voice = "Hell Flame Exhausted"
        self.chinese_no_mana_voice = "炼狱将熄"
        self.killing_voice = "Killing Spree"
        self.chinese_killing_voice1 = "生啖其肉"
        self.chinese_killing_voice2 = "捉魂夺魄"
        self.be_killed_voice = "Burnt"
        self.chinese_be_killed_voice1 = "烈焰焚身"
        self.chinese_be_killed_voice2 = "灵魂溃散"
        self.chinese_be_killed_voice3 = "无暇入殓"

    def new_turn(self):
        super().new_turn()
        self.killing=0 # 重置计数器

    def die(self):
        super().die()
        self.channeling = False
        self.power = False
        self.str = 400
        self.maxhp = max(1000, self.maxhp-1000)
        self.lockhp = min(self.lockhp, self.maxhp)
        self.track_round = 0
        self.percentage_defense_buff = 0.1

    def fightBack(self, attacker, game, times=1/5):
        return Fighter.fightBack(self, attacker, game, times)

        
    def drawSpecialStatus(self, surface):
        c_x, c_y = self.position
        c_x = c_x-unit_size//2
        c_y = c_y+unit_size//2 - 12
        pygame.draw.circle(surface, BLACK, (c_x, c_y), 15)
        if self.str < 1000:
            text = FONT.size(default_font_size-3).render(f"{self.str}", True, RED)
        else:
            text = FONT.size(default_font_size-6).render(f"{self.str}", True, RED)
        text_rect = text.get_rect(center=(c_x, c_y))
        surface.blit(text, text_rect)


    def channel(self, game):
        self.track_round = game.round
        self.mana -= manaCost
        self.percentage_defense_buff = 0.3
        self.channeling = True

        dprint(self.name + ' is channelling!')
        animates = BlankAnimation(game, self)
        animates.words.add_text(self.chinese_channel_voice, self.position, color=HELL_RED, i=0, time="now")
        game.animations.append(animates)

    def strike(self,myTeam,enemy,game):
        if self.mana >= manaCost // 2:
            self.mana -= manaCost // 2
            target0 = attack_logic[self.targetrow](enemy)
            # 造成斩杀伤害，在目标30%血量时达到最高两倍伤害
            hpLeft = 1 - ((max(target0.hp / target0.maxhp, 0.3) - 0.3) / 0.7)
            damage = testDamage(self, target0, self.str * (1 + hpLeft))

            animates = HitAttack(game, self, target0, damage)
            # 对最多三个单位造成群体伤害
            for target in nearbyAlive(enemy, target0):
                animates.words.add_text(self.chinese_attack_voice, target.position, color=HELL_RED, i=0, time="hit", how="insert")
                if target == target0:
                    dprint(f'Hell Conqueror Strike enemy {target.name} by damage {damage}.')
                    target.gotHurt(damage)
                    fightBackDamage = target.fightBack(self, game)
                    if fightBackDamage:
                        animates2 = FightBack(game, target, self, fightBackDamage)
                        game.animations.append(animates2)
                else:
                    # 副目标受到一半伤害且不能反击
                    dprint(f'And enemy {target.name} by damage {damage//2}.')
                    target.gotHurt(damage//2)
                    animates.words.add_text(f"-{damage//2}", target.position, color=MID_RED, i=0, time="hit", alter_hp=target)
                
                # 成功斩杀触发凯旋和连杀，回蓝不展示
                if self.alive:
                    if target.hp == 0:
                        lostHp, lostMana = self.maxhp - self.hp, self.maxmana - self.mana
                        self.gotHurt(-(lostHp//4))
                        self.mana += min(lostMana//4, self.maxmana-self.mana)
                        self.str += 50
                        if self.killing < self.max_killing:
                            self.killing += 1
                            self.act_times += 1
                        
                        if randint(0,1):
                            animates.words.add_text(self.chinese_killing_voice1, self.position, color=HELL_RED, i=0, time="hit")
                        else:
                            animates.words.add_text(self.chinese_killing_voice2, self.position, color=HELL_RED, i=0, time="hit")
                        if lostHp > 0:
                            animates.words.add_text(f"+{lostHp//4}", self.position, color=GREEN, i=0, time="hit", alter_hp=self)
                        
                        randVoice = randint(1,3)
                        if randVoice == 1:
                            animates.words.add_text(self.chinese_be_killed_voice1, target.position, color=HELL_RED, i=0, time="hit")
                        elif randVoice == 2:
                            animates.words.add_text(self.chinese_be_killed_voice2, target.position, color=HELL_RED, i=0, time="hit")
                        elif randVoice == 3:
                            animates.words.add_text(self.chinese_be_killed_voice3, target.position, color=HELL_RED, i=0, time="hit")

            # 力量耗尽
            if self.mana < manaCost // 2:
                self.mana = 0
                self.power = False
                self.act_times = 0
                dprint(f"{self.name} {self.no_mana_voice}")
                animates.words.add_text(self.chinese_no_mana_voice, self.position, color=HELL_RED, i=0, time="back")
            game.animations.append(animates)

    # 优先回蓝，有蓝就引导神力，一回合后回血回蓝，且具有AOE斩杀能力，斩杀成功回血回蓝，斩杀一次需要10法力值，即最多连续空斩5次
    def act(self,myTeam,enemy,game):
        if self.channeling:
            self.channeling = False
            self.percentage_defense_buff = 0.1
            self.power = True
            # 引导完毕加攻击力，回蓝回血，并增加行动次数
            bonus_times = (game.round - self.track_round) // 2
            self.track_round = 0
            self.str += 50 * bonus_times
            self.gotHurt(-self.str * 2)
            self.mana += min(manaRecovery, self.maxmana-self.mana)
            self.act_times += min(bonus_times//2, 2)
            self.special_status = True

            # 加上各种语音
            animates = BlankAnimation(game, self)
            if randint(0,1):
                animates.words.add_text(self.chinese_power_voice1, self.position, color=HELL_RED, i=0, time="now")
            else:
                animates.words.add_text(self.chinese_power_voice2, self.position, color=HELL_RED, i=0, time="now")
            if bonus_times:
                animates.words.add_text(f"引导{bonus_times}回合", self.position, color=HELL_RED, i=0, time="now", how="insert")
                animates.words.add_text(f"+{50 * bonus_times}", self.position, color=HELL_RED, i=0, time="now")
                animates.words.add_text(f"+{self.str * 2}", self.position, color=GREEN, i=0, time="now", alter_hp=self)
            game.animations.append(animates)
            
        if self.power:
            self.strike(myTeam,enemy,game)
        else:
            if self.mana < manaCost:
                self.recoverMana(game)
            else:
                self.channel(game)



class Shieldguard(Fighter):
    def __init__(self):
        super().__init__()
        self.name = 'Shieldguard'
        self.chinese_name = '塔盾兵'
        self.str = 100
        self.maxhp, self.hp, self.lockhp = [2500] * 3
        self.cost = 300
        self.protecting = []
        self.special_status = True
        self.percentage_defense_buff = 0.8 # 常驻减伤20%，首次受到伤害减伤80%
        self.themeColor = NOT_THAT_YELLOW

        self.description = "A Tank with High Defense, can protect others."
        self.chinese_description = "拥有高血量，高减伤，高反击，并且可以守护其他单位。"
        # 图鉴：守护周围两个和随机三个目标（重叠时不叠加），守护时可以分担伤害并反击

        self.protect_voice = "Protect My Allies"
        self.chinese_protect_voice = "加固防线"
        self.be_protected_voice = "Be Protected"
        self.chinese_be_protected_voice = "守护"
        self.attack_voice = "Shield Strike"
        self.chinese_attack_voice = "护盾猛击"

    def gotHurt(self, damage, type="normal"):
        excess_damage = super().gotHurt(damage, type)
        if self.percentage_defense_buff == 0.8:
            self.shield = 0
            self.percentage_defense_buff = 0.2
            self.checkShield()
        return excess_damage

    # 全额反击倍率
    def fightBack(self, attacker, game, times=1):
        # 自己不能被守护
        if self.alive:
            damage = self.str * times
            damage = testDamage(self, attacker, damage)
            self.str += 25 # 反击后回合内攻击力提升
            dprint(self.name + ' fight back!')
            attacker.gotHurt(damage)
            return damage
        

    def new_turn(self):
        super().new_turn()
        self.str = 100
        self.take_shield_stirke = False


    def drawSpecialStatus(self, surface):
        # 减伤圈
        width = round(self.percentage_defense_buff*20)
        drawInsideRect(surface, self.position, self.themeColor, width)
        # 攻击力
        c_x, c_y = self.position
        c_x = c_x-unit_size//2
        c_y = c_y+unit_size//2 - 12
        pygame.draw.circle(surface, BLACK, (c_x, c_y), 15)
        text = FONT.size(default_font_size-3).render(f"{self.str}", True, RED)
        text_rect = text.get_rect(center=(c_x, c_y))
        surface.blit(text, text_rect)


    def die(self):
        super().die()
        self.str = 100
        for unit in self.protecting:
            unit.under_whose_protection = None
            unit.shield = 0
        self.protecting = []
        self.percentage_defense_buff = 0.2


    def protect(self, myTeam, enemy, game, count):
        # 每次刷新判定自己周围两个
        potential_targets = nearbyAlive(myTeam, self, nearby=1)
        # 再加上指定数量的随机单位，优先后排
        alive_units = [unit for unit in myTeam.back if unit.alive and 
                       unit.name != 'Shieldguard' and unit not in potential_targets]
        if len(alive_units) < count:
            alive_units += [unit for unit in myTeam.front if unit.alive and 
                            unit.name != 'Shieldguard' and unit not in potential_targets]
        # 加一层防错
        potential_targets += sample(alive_units, min(count, len(alive_units)))

        dprint(self.name + ' is protecting!')
        animates = BlankAnimation(game, self)
        animates.words.add_text(self.chinese_protect_voice, self.position, color=self.themeColor, i=0, time="now")
        
        if self.protecting:
            tracker = sum([unit.shield for unit in self.protecting])
        else:
            tracker = 0

        # 修改守护追踪器
        for target in potential_targets:
            # 不能覆盖其他盾卫的守护效果
            if target.under_whose_protection and target.under_whose_protection != self:
                continue
            # 只能刷新自己的守护
            if target not in self.protecting:
                self.protecting.append(target)
            target.under_whose_protection = self
            target.shield = 3
            # 刷新自己的减伤，并显示语音
            if target == self:
                self.checkShield()
            else:
                animates.words.add_text(self.chinese_be_protected_voice, target.position, color=self.themeColor, i=0, time="now")
        
        # 如果实际上没有增加护盾的话，就不算一次行动，立即释放盾击
        if tracker == sum([unit.shield for unit in self.protecting]):
            self.shieldStrike(myTeam, enemy, game)
        else:
            game.animations.append(animates)


    def shieldStrike(self,myTeam,enemy,game):
        # 和Fighter的区别是，伤害额外增加了守护单位数的增益，且不受反击
        target = attack_logic[self.targetrow](enemy)
        damage = self.str*self.shield + 50*len(self.protecting)
        damage = testDamage(self, target, damage)
        target.gotHurt(damage)
        
        self.shield = 0
        self.checkShield()
        for unit in self.protecting:
            unit.shield -= 1
            unit.checkShield()

        dprint(f'{self.name} Hurt enemy {target.name} with Shield by damage {damage}.')
        animates = HitAttack(game, self, target, damage)
        animates.words.add_text(self.chinese_attack_voice, target.position, color=self.themeColor, i=0, time="hit", how="insert-1")
        game.animations.append(animates)

        return target


    def checkShield(self):
        super().checkShield()
        # 有护盾时减伤翻倍
        if self.shield:
            self.percentage_defense_buff = max(0.4, self.percentage_defense_buff)
        else:
            self.percentage_defense_buff = 0.2


    def act(self,myTeam,enemy,game):
        # 优先守护，有的话概率盾击，或者增加两个守护
        if not self.protecting:
            self.protect(myTeam, enemy, game, 3)
        else:
            dice = rollDice("1d6")
            if dice > 4 and self.shield:
                self.shieldStrike(myTeam, enemy, game)
            else:
                self.protect(myTeam, enemy, game, 2)



class Sniper(Archer):
    def __init__(self):
        super().__init__()
        self.name = 'Sniper'
        self.chinese_name = '神箭手'
        self.str = 300
        self.cost = 400
        self.channeling = False
        self.aimedTarget = None
        self.special_status = True
        self.track_round = 0
        self.maxammo = 3
        self.ammo = self.maxammo
        self.focus_base = 0
        self.focus = 0

        self.description = "Very very advanced archer, dealing much more damage but needed to aim first."
        self.chinese_description = "掌握神力的弓箭手，乘风而行，有许多连带动作。雄鹰帮助他在瞄准后锁定目标，风神赐福的箭矢让他能造成更高伤害。"
        
        self.reload_voice = "Reload"
        self.chinese_reload_voice = "凝聚风神赐福"
        self.aim_voice = "Aiming"
        self.chinese_aim_voice1 = "乘风之鹰赐予我视野"
        self.chinese_aim_voice2 = "风之印记凝于其身"
        self.be_interrupted_voice = "Aiming Interrupted"
        self.chinese_be_interrupted_voice = "仓皇撤离"
        self.blessed_attack_voice = "God's Breath"
        self.chinese_blessed_attack_voice = "风神之息"
        self.last_ammo_voice = "Fierce Wind"
        self.chinese_last_ammo_voice = "狂风怒号"
        self.last_ammo_voice_another_target = "Invovled in the Wind"
        self.chinese_last_ammo_voice_another_target = "席卷"     


    def die(self):
        super().die()
        self.ammo = 0
        self.maxammo = 3
        self.focus_base = 0
        self.focus = 0
        self.track_round = 0
        if self.aimedTarget:
            self.enemy.aimedTargets.remove(self.aimedTarget)
            self.aimedTarget = None


    def fightBack(self, attacker, game):
        # 受到守护时不会受到影响
        damage = super().fightBack(attacker, game)
        if damage:
            return damage
        
        # 否则近战攻击打断瞄准，远程攻击减少专注
        if self.aimedTarget and attacker.melee:
            self.enemy.aimedTargets.remove(self.aimedTarget)
            self.aimedTarget = None
            self.focus = min(self.focus, self.focus_base)
            self.track_round = 0
            self.channeling = False
        elif not attacker.melee:
            self.focus = max(0, self.focus-1)
        


    def drawSpecialStatus(self, surface):
        c_x, c_y = self.position
        c_x, c_y = c_x-unit_size//2, c_y+unit_size//2 - 12
        pygame.draw.circle(surface, BLACK, (c_x, c_y), 15)
        pygame.draw.circle(surface, BLACK, (c_x+12, c_y), 15)

        text = FONT.size(default_font_size).render(f"{self.ammo}-{self.focus}", True, WHITE)
        text_rect = text.get_rect(center=(c_x+5, c_y))
        surface.blit(text, text_rect)


    def aim(self, enemy, game):
        self.channeling = True
        # 记录空过回合数
        if self.track_round == 0:
            self.track_round = game.round
        self.focus = min(self.focus, self.focus_base)
        self.aimedTarget = attack_logic[self.targetrow](enemy)
        enemy.aimedTargets.append(self.aimedTarget)

        # 附带动作：装填
        if self.maxammo == 1: # 完全体时不再视作附带动作
            self.reload(game, silent=False)
        else:
            self.reload(game, silent=True)

        dprint(self.name + ' is aiming!')
        animates = BlankAnimation(game, self)
        if randint(0,1):
            animates.words.add_text(self.chinese_aim_voice1, self.position, color=WHITE, i=0, time="now")
        else:
            animates.words.add_text(self.chinese_aim_voice2, self.position, color=WHITE, i=0, time="now")
        game.animations.append(animates)


    def reload(self, game, silent=False):
        # 记录空过回合数
        if self.track_round == 0:
            self.track_round = game.round
        # 重新装填
        if self.ammo == 0:
            self.ammo = self.maxammo
            # 强制进入下一回合
            self.focus_base += self.act_times
            self.focus = max(self.focus+self.act_times, self.focus_base)
            self.act_times = 0
            # 如果装填不是瞄准的连带动作，增加专注
            if not silent:
                self.focus_base += 1
                self.focus += 1

                dprint(self.name + ' is reloading!')
                animates = BlankAnimation(game, self)
                animates.words.add_text(self.chinese_reload_voice, self.position, color=WHITE, i=0, time="now")
                
                # 附带动作：用专注疗伤
                if self.focus >= 3 and self.maxhp - self.hp >= 200:
                    self.focus -= 2
                    self.gotHurt(-200)
                    animates.words.add_text("+200", self.position, color=GREEN, i=0, time="now", alter_hp=self)
                elif self.focus >= 2 and self.maxhp - self.hp >= 100:
                    self.focus -= 1
                    self.gotHurt(-100)
                    animates.words.add_text("+100", self.position, color=GREEN, i=0, time="now", alter_hp=self)
                
                game.animations.append(animates)


    # 瞄准完毕的攻击
    def blessedArrow(self, myTeam, enemy, game):
        target = self.aimedTarget
        # 基于弓箭手的伤害倍率
        damage = self.str
        if target in enemy.front and self in myTeam.back:
            damage *= 1.2
        elif target in enemy.back and allDead(enemy, where="front") and self in myTeam.back:
            damage *= 1.2

        # 基于专注和子弹数的伤害倍率
        self.ammo -= 1
        self.focus += 1
        damage *= 0.8 + 0.2 * self.focus
        if self.ammo == 0:
            # 最后一箭额外造成目标15%已损失生命值的斩杀伤害
            damage += round(0.15 * (target.maxhp- target.hp))

        damage = testDamage(self, target, damage)
        # 溢出伤害
        excess_damage = target.gotHurt(damage)
        # 击杀奖励：减少最大子弹数，增加基础专注
        if target.hp == 0:
            self.maxammo = max(1, self.maxammo-1)
            self.focus_base += 1 # 需要装填才能获得实际收益
            self.enemy.aimedTargets.remove(self.aimedTarget) # 击杀后解除瞄准
            self.aimedTarget = None
        # 溢出的伤害连带攻击随机后排目标
        if self.ammo == 0 and excess_damage and (target in enemy.front or allDead(enemy, where="front")) and not allDead(enemy, where="back"):
            target2 = randAliveBack(enemy)
            if target2:
                excess_damage = testDamage(self, target2, excess_damage)
                target2.gotHurt(excess_damage//2)

        dprint(f'Sniper Hurt enemy {target.name} by damage {damage} from range.')
        animates = MagicAttack(game, self, target, damage, "damage")
        animates.words.add_text(self.chinese_blessed_attack_voice, self.position, color=WHITE, i=0, time="now", how="insert")
        animates.words.add_text(f"专注{self.focus}", self.position, color=WHITE, i=0, time="now")
        if self.ammo == 0:
            animates.words.add_text(self.chinese_last_ammo_voice, target.position, color=WHITE, i=0, time="hit", how="insert")
            if excess_damage and (target in enemy.front or allDead(enemy, where="front")) and not allDead(enemy, where="back"):
                dprint(f'Sniper also Hurt enemy {target2.name} by damage {excess_damage} from range.')
                animates.words.add_text(self.chinese_last_ammo_voice_another_target, target2.position, color=WHITE, i=0, time="hit")
                animates.words.add_text(f"-{excess_damage//2}", target2.position, color=MID_RED, i=0, time="hit",alter_hp=target2)
        game.animations.append(animates)

    def act(self,myTeam,enemy,game):
        self.special_status = True
        # 队友死完了的话，只能仓促射击
        if allDead(self.others):
            if self.aimedTarget:
                self.enemy.aimedTargets.remove(self.aimedTarget)
                self.aimedTarget = None
            self.str = max(100, self.str//2) # 攻击力越来越低
            self.str += self.focus * 25
            super().act(myTeam, enemy, game)
        else:
            if self.aimedTarget and (self.aimedTarget.alive == False or self.aimedTarget not in (enemy.front+enemy.back)):
                # 重新瞄准，叠加瞄准回合数收益
                self.enemy.aimedTargets.remove(self.aimedTarget)
                self.aimedTarget = None

            if not self.aimedTarget:
                self.aim(enemy, game)
            elif self.ammo == 0:
                self.reload(game)
            else:
                if self.channeling:
                    # 基于空过回合数的专注收益
                    self.focus_base += (game.round - self.track_round) // 8
                    self.focus += (game.round - self.track_round) // 4
                    self.act_times += (game.round - self.track_round) // 8
                    self.track_round = 0
                    self.channeling = False
                # 射出附魔箭
                self.blessedArrow(myTeam, enemy, game)



class Longbowman(Archer):
    def __init__(self):
        super().__init__()
        self.name = 'Longbowman'
        self.chinese_name = '长弓兵'
        self.str = 50
        self.cost = 250
        self.selfrow = "back"
        self.targetrow = "back"

        self.description = "Attacking up to 3 units in the back row for 3 times."
        self.chinese_description = "发射箭雨对后排最多三个敌人造成三次伤害。"
        # 图鉴：每次箭雨伤害独立计算伤害，总伤害3*(0.8~1.3)*攻击力。

        self.attack_voice = "Arrow Rain"
        self.chinese_attack_voice = " 箭雨！"


    def act(self,myTeam,enemy,game):
        # 攻击后排站在一起的最多三个单位
        target0 = attack_logic[self.targetrow](enemy)
        targets = nearbyAlive(enemy, target0)
        counts = len(targets)
        
        dprint(f'{self.name} is triggering Arrow Rain to {" & ".join([target.name for target in targets])}!')
        # 连续射3次
        for j in range(3):
            damage = []
            for target in targets:
                damage0 = testDamage(self, target, self.str*(0.7+0.1*rollDice("1d6")))
                damage.append(damage0)
                target.gotHurt(damage0)

            animates = MutliMagicAttack(game, self, targets, damage, "damage")
            game.animations.append(animates)



class Spearman(Fighter):
    def __init__(self):
        super().__init__()
        self.name = 'Spearman'
        self.chinese_name = '投矛手'
        self.str = 120
        self.cost = 150
        
        self.spears = 3
        self.spear_targets = []
        self.special_status = True
        self.pickup_spears = False

        self.description = "Carrying 3 spears. Throw spears before melee attack."
        self.chinese_description = "携带了三根长矛。在近战攻击前可以投掷长矛，如果敌人死亡可以从敌人处捡回长矛。"
        # 图鉴：冲锋伤害独立计算伤害，总伤害2*(0.8~1.3)*攻击力。

        self.attack_voice = "Throwing Spears"
        self.chinese_attack_voice = "投掷长矛"

    
    def drawSpecialStatus(self, surface):
        c_x, c_y = self.position
        pygame.draw.circle(surface, BLACK, (c_x-unit_size//2, c_y+unit_size//2 - 12), 15)
        text = FONT.size(default_font_size).render(f"{int(self.spears)}", True, WHITE)
        text_rect = text.get_rect(center=(c_x-unit_size//2, c_y+unit_size//2 - 12))
        surface.blit(text, text_rect)

    
    def throwSpear(self, target, game):
        self.spears -= 1
        damage = testDamage(self, target, self.str*5/6) # 投矛伤害为100，即标准近战120，远程100。
        target.gotHurt(damage)
        self.spear_targets.append(target)

        dprint(f'{self.name} is throwing spear to {target.name}!')
        animates = MagicAttack(game, self, target, damage, "damage")
        animates.words.add_text(self.chinese_attack_voice, self.position, color=WHITE, i=0, time="now", how="insert")
        game.animations.append(animates)


    # 每个回合只能捡一次长矛
    def new_turn(self):
        super().new_turn()
        self.pickup_spears = False
    

    def pickUp(self, enemy):
        pick_up = False
        if self.spear_targets:
            for target in self.spear_targets[:]:
                if target.alive == False or target not in enemy.front+enemy.back:
                    self.spear_targets.remove(target)
                    self.spears += 1
                    self.pickup_spears = True
                    pick_up = True

                    dprint(f'{self.name} picked up a spear!')
        return pick_up


    def act(self,myTeam,enemy,game):
        # 检查投矛的人有没有死，死了的话可以捡回长矛
        if not self.pickup_spears:
            self.pickUp(enemy)

        target = attack_logic[self.targetrow](enemy)
        # 先投矛
        if self.spears > 0:
            self.throwSpear(target, game)
            new_spear = self.pickUp(enemy)
            if new_spear:
                if allDead(enemy):
                    return
                else:
                    # 如果投死了就可以捡回来再投一次
                    target2 = attack_logic[self.targetrow](enemy)
                    self.throwSpear(target2, game)
                    return target2
            
        # 没投死就砍他
        damage = testDamage(self, target, self.str)

        dprint(f'{self.name} Hurt enemy {target.name} by damage {damage}.')
        target.gotHurt(damage)
        fightBackDamage = target.fightBack(self, game)

        animates = HitAttack(game, self, target, damage)
        game.animations.append(animates)

        if fightBackDamage:
            animates2 = FightBack(game, target, self, fightBackDamage)
            game.animations.append(animates2)

        return target
            

class SkeletalSummoner(Mage):
    def __init__(self):
        super().__init__()
        self.name = 'SkeletalSummoner'
        self.chinese_name = '死灵巫祝'
        self.cost = 400
        self.int = 300
        self.themeColor = GREEN
        self.cast_round = True
        self.skeletons = []

        self.description = "Summon 3 skeleton allies."
        self.chinese_description = "召唤3只一起行动的小骷髅。"

        self.summon_voice = "skeleton"
        self.chinese_summon_voice = "骨骼已组装"


    def die(self):
        super().die()
        for skeleton in self.skeletons[:]:
            skeleton.die()
            skeleton.lockhp = 0
        self.skeletons = []


    def cast(self, myTeam, enemy, game, voice):
        if self.cast_round:
            super().cast(myTeam, enemy, game, voice)
            super().recoverMana(game, tempRecovery = 10, silent=2)
        else:
            self.summoneSkeleton(game, myTeam)
        self.cast_round = not self.cast_round


    def summoneSkeleton(self, game, myTeam):
        count = 3
        # 正常召唤三个
        __, line_indicator = shorterLine(myTeam)
        skeletons = [Skeleton() for i in range(3)]
        self.skeletons.extend(skeletons)
        appendUnits(myTeam, skeletons ,  
            ["front", "back", line_indicator])
        myTeam.skeletons.extend(skeletons)

        # 有人死亡可以加强召唤
        for lst2 in [myTeam.front, myTeam.back]:
            for i, unit in enumerate(lst2):
                if i % 2 and unit.alive == False:
                    skeleton = Skeleton()
                    skeleton.replace(unit)
                    lst2[i] = skeleton
                    self.skeletons.append(skeleton)
                    myTeam.skeletons.append(skeleton)

        dprint(f'{self.name} summoned {count} skeleton allies!')
        animates = BlankAnimation(game, self)
        animates.words.add_text(f"{count}{self.chinese_summon_voice}", self.position, color=self.themeColor, i=0, time="now", how="insert")
        game.animations.append(animates)       





class Skeleton(Fighter):
    def __init__(self):
        super().__init__()
        self.name = 'Skeleton'
        self.chinese_name = '小骷髅'
        self.maxhp, self.hp, self.lockhp = [50] * 3
        self.str = 50
        self.cost = 5
        self.acted = False
        self.themeColor = WHITE

        self.description = "Typical Skeleton"
        self.chinese_description = "标准的骷髅，但是会一起行动。"


    def skeleton_act(self, myTeam, enemy, game):
        super().act(myTeam, enemy, game)

    
    def new_turn(self):
        super().new_turn()
        self.acted = False

    
    def fightBack(self, attacker, game):
        pass
    

    def replace(self, unit):
        self.position = unit.position
        self.original_position = tuple(unit.position)
        self.actual_row = unit.actual_row
        self.move() # 将rect对应到position
        self.color = unit.color
        self.side = unit.side
        self.team = unit.team


    def act(self,myTeam,enemy,game):
        for skeleton in myTeam.skeletons:
            if (not allDead(enemy)) and skeleton.alive and skeleton.acted == False:
                skeleton.skeleton_act(myTeam, enemy, game)
                self.acted = True
                if game.mode == 4: # 全队行动
                    if skeleton in game.myTeam.wholeTeamTracker:
                        game.myTeam.wholeTeamTracker.remove(skeleton)
                    elif skeleton in game.enemy.wholeTeamTracker:
                        game.enemy.wholeTeamTracker.remove(skeleton)




class Attachment(Character): # 新的角色类型：attachment
    def __init__(self):
        super().__init__()
        self.ex_master = None
        self.master = None
        self.percentage_damage_buff = 0
        self.percentage_defense_buff = 0
        self.fixed_damage_buff = 0
        self.fixed_defense_buff = 0
        self.selfrow = "all"
        self.targetrow = "none"

        self.attach_voice = ""
        self.chinese_attach_voice = ""


    def draw(self, surface, i):
        if self.master:
            rect = pygame.Rect(0, 0, unit_size//2, unit_size//2)
            c_x = self.master.position[0]+unit_size//4+10+10*i
            c_y = self.master.position[1]+unit_size//4+10+10*i
            rect.center = (c_x, c_y)
            pygame.draw.rect(surface, self.color, rect)

            font = FONT.size(default_font_size)
            unit_name = font.render(self.chinese_name, True, WHITE)  # 白色文字
            text_rect = unit_name.get_rect(center=(c_x, c_y)) 
            drawSurroundings(surface, self.chinese_name, (c_x, c_y), unit_name, font, True) # 描边
            surface.blit(unit_name, text_rect)


    def die(self):
        super().die()
        if self.master:
            self.lose_attach()
        if self.actual_row == "front" and self not in self.team.front:
            self.team.front.append(self)
        elif self.actual_row == "back" and self not in self.team.back:
            self.team.back.append(self)


    def lose_attach(self):
        self.master.attachment.remove(self)
        self.master = None
        if self.actual_row == "front":
            self.team.front.append(self)
        elif self.actual_row == "back":
            self.team.back.append(self)


    def findMaster(self, myTeam, game=None, master=None):
        self.shield = 0
        self.checkShield()

        if not master:
            # 附身队友
            alive_units = AliveAll(myTeam, exclude=self)
            if alive_units:
                master = sample(alive_units, 1)[0]
            else:
                master = None

        if master:
            # 记录上一个master
            self.ex_master = self.master
            if self.ex_master:
                self.ex_master.attachment.remove(self)

            # 更新master
            self.master = master
            self.master.attachment.append(self)

            # 从主要成员中剔除
            if self.actual_row == "front" and self in myTeam.front:
                myTeam.front.remove(self)
            if self.actual_row == "back" and self in myTeam.back:
                myTeam.back.remove(self)

            # 附身以后把自己的attachment都一起附身给队友
            for attachment in self.attachment:
                attachment.master = self.master
                self.master.attachment.append(attachment)
            self.attachment = []

            dprint(f'{self.name} attached to {self.master.name}.')
            if game and hasattr(self, 'chinese_attach_voice') and self.chinese_attach_voice:
                animations = BlankAnimation(game, self)
                animations.words.add_text(self.chinese_attach_voice, self.position, color=WHITE, i=0, time="now")
                game.animations.append(animations)

        else:
            # 没有队友时死亡
            self.lockhp=0
            self.die()

            dprint(f'{self.name} has no one to attach to and died.')
            if hasattr(self, 'chinese_lose_attach_voice') and self.chinese_lose_attach_voice:
                animations = BlankAnimation(game, self)
                animations.words.add_text(self.chinese_lose_attach_voice, self.position, color=WHITE, i=0, time="now")
                game.animations.append(animations)
            
    
class Cat(Attachment): 
    def __init__(self):
        super().__init__()
        self.name = 'Cat'
        self.chinese_name = '小猫'
        self.maxhp, self.hp, self.lockhp = [9] * 3 # 每次受到伤害最多为1
        self.cost = 50
        self.str = 0
        self.dead_name = "跑掉了"

        self.fixed_damage_buff = 50
        self.fixed_defense_buff = 50

        self.description = "Cute Cat. An Attachment."
        self.chinese_description = "小猫有9条命（可以最多承受9次伤害）。它没有行动能力，只能为附身的队友增幅造成的伤害，或减少受到的伤害。没有队友可以附身时会直接跑掉。"
        # 图鉴：小猫在master受到伤害时会尝试逃跑（仍然减伤），如果逃跑前后master不变，则受到一点伤害

        self.attach_voice = "Meow~"
        self.chinese_attach_voice = " 喵呜！"
        self.lose_attach_voice = "Purr~"
        self.chinese_lose_attach_voice = "嘤嘤嘤"


    def lose_attach(self):
        super().lose_attach()
        self.gotHurt(1)
        self.lockhp = self.hp


    def act(self,myTeam,enemy,game):
        self.findMaster(myTeam, game)
    
    

class Dog(Attachment): 
    def __init__(self):
        super().__init__()
        self.name = 'Dog'
        self.chinese_name = '狗勾'
        self.maxhp, self.hp, self.lockhp = [500] * 3
        self.cost = 50
        self.str = 50
        self.dead_name = "跑掉了"
        self.selfrow = "front"
        self.targetrow = "front"

        self.special_status = True
        self.themeColor = RED
        self.melee = True
        self.attachable = True
        self.required_power = 300
        self.percentage_damage_buff = 0.2

        self.description = "Cute Cat. An Attachment."
        self.chinese_description = "小狗会尝试附身队友提供20%伤害增幅，但是，如果队友比自己弱，则改而自己上去咬人。场上只有狗勾时有可能产生狗王。"

        self.attach_voice = "Woof~"
        self.chinese_attach_voice = " 嗷呜！"
        self.lose_attach_voice = "Whine~"
        self.chinese_lose_attach_voice = "夹着尾巴跑了"


    def die(self):
        super().die()
        self.str = 50
        self.required_power = 300
        self.fixed_damage_buff = 0
        self.fixed_defense_buff = 0
        self.attachable = True
        self.name = 'Dog'
        self.chinese_name = '狗勾'
        self.themeColor = RED


    def drawSpecialStatus(self, surface):
        if not self.attachable:
            drawInsideRect(surface, self.position, self.themeColor)
        if self.str > 50:
            c_x, c_y = self.position
            c_x = c_x-unit_size//2
            c_y = c_y+unit_size//2 - 12
            pygame.draw.circle(surface, BLACK, (c_x, c_y), 15)
            text = FONT.size(default_font_size-3).render(f"{self.str}", True, RED)
            text_rect = text.get_rect(center=(c_x, c_y))
            surface.blit(text, text_rect)

    
    def gotHurt(self, damage, type="normal"):
        excess_damage = super().gotHurt(damage, type)
        self.str += 25
        return excess_damage




    def act(self,myTeam,enemy,game):
        alive_units = AliveAll(myTeam, exclude=self, exclude_names=("Cat", "Dog"))
        if alive_units and self.attachable:
            master = sample(alive_units, 1)[0]
        else:
            master = None
        # 有master时，如果master攻击力过低，则自己咬人，如果自己血比较少，就抱大腿
        if master:
            if max(master.str, master.int) < self.required_power - (self.maxhp - self.hp):
                self.required_power -= 50
                Fighter.act(self, myTeam, enemy, game)
                self.str += 25
            else:
                self.findMaster(myTeam, game, master)

        else:
            # 没有可附身的单位时，强壮的变成狗王，弱小的直接死亡
            if self.str >= 150 or self.attachable == False:
                if self.attachable:
                    if "HellConqueror" in [unit.name for unit in myTeam.front+myTeam.back]:
                        self.str += 50
                        self.name = 'Hellhound'
                        self.chinese_name = "地狱犬"
                        self.themeColor = HELL_RED
                    else:
                        self.str += 50
                        self.name = 'King of Dogs'
                        self.chinese_name = "狗王" # 狗王可以被狗附身
                    self.attachable = False
                else:
                    attached_dogs = [unit for unit in self.attachment if unit.name == 'Dog']
                    self.fixed_damage_buff = min(25 * len(attached_dogs), 100)
                    self.fixed_defense_buff = min(25 * len(attached_dogs), 100)
                Fighter.act(self, myTeam, enemy, game)
            else:
                # 不够强壮的小狗在没有队友时死亡
                self.lockhp=0
                self.die()

                dprint(f'{self.name} has no one to attach to and died.')
                if hasattr(self, 'chinese_lose_attach_voice') and self.chinese_lose_attach_voice:
                    animations = BlankAnimation(game, self)
                    animations.words.add_text(self.chinese_lose_attach_voice, self.position, color=WHITE, i=0, time="now")
                    game.animations.append(animations)



class Tower(Character):
    def __init__(self):
        super().__init__()
        self.dead_name = "坍塌"
        self.percent_defense_buff = 0.1
        self.melee = False
        self.cannot_be_poisoned = True
        self.driver = None
        self.selfrow = "front"
        self.targetrow = "all"

        self.attach_voice = "Coordinated Attack"
        self.chinese_attach_voice = "协同攻击"

    
    def allocateDriver(self, game, myTeam, ):
        driver = randAliveBack()
        if driver:
            self.driver = driver
            self.hp += driver.hp//2
            self.lockhp += driver.hp//2



    def gotHurt(self, damage, type="normal"):
        return super().gotHurt(damage, type)


    def die(self):
        super().die()
        if self.driver:
            self.driver.die()
            self.driver = None


    def act(self, myTeam, enemy, game):
        if self.driver.alive==False:
            self.driver=None
        if not self.driver and AliveAll(myTeam, exclude=self, exclude_names=(), exclude_types=(Tower,)):
            self.allocateDriver(game, myTeam)



class CoastalDefenseArtillery():
    def __init__(self):
        super().__init__()
        self.name = 'CoastalDefenseArtillery'
        self.chinese_name = '岸防炮'
        self.maxhp, self.hp, self.lockhp = [1500] * 3
        self.cost = 200
        self.str = 10
        self.percentage_defense_buff = 0.2

        self.description = "Cute Cat. An Attachment."
        self.chinese_description = "小狗会尝试附身队友提供20%伤害增幅，但是，如果队友比自己弱，则改而自己上去咬人。场上只有狗勾时有可能产生狗王。"

        self.attach_voice = "Woof~"
        self.chinese_attach_voice = " 嗷呜！"
        self.lose_attach_voice = "Whine~"
        self.chinese_lose_attach_voice = "夹着尾巴跑了"


