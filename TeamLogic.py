from random import randint, sample
from Characters import *
import pygame
from colors import *
from GeneralSettings import *
from WordEffects import *


def fillLines(team, armyList, side):
    while len(armyList) > 0:
        random_unit = armyList[randint(0, len(armyList)-1)]

        if random_unit not in team.front and random_unit not in team.back:
            random_unit.side = side
            if random_unit.selfrow == "front":
                if len(team.front) < team.maxfront:
                    team.front.append(random_unit)
                else:
                    team.back.append(random_unit)
            elif random_unit.selfrow == "back":
                if len(team.back) < team.maxback:
                    team.back.append(random_unit)
                else:
                    team.front.append(random_unit)
            elif random_unit.selfrow == "all":
                if len(team.front) < team.maxfront:
                    team.front.append(random_unit)
                else:
                    team.back.append(random_unit)

        armyList.remove(random_unit)

# 对前排更宽松
def shorterLine(team): 
    if len(team.front) <= len(team.back):
        return team.front, "front"
    else:
        return team.back, "back"
def longerLine(team):
    if len(team.front) > len(team.back):
        return team.front, "back"
    else:
        return team.back, "front"


def appendUnits(team, units, where):
    if type(units) != list:
        units = [units]
    if type(where) != list:
        where = [where]
    side = (team.front+team.back)[0].side
    # 分配位置
    positions = {
        "myTeam": {"front":[[central_line-2*road_width, upper_line+(i+0.5)*road_width] 
                            for i in range(len(team.front), len(team.front)+len(units))],  
                   "back":[[central_line-3*road_width, upper_line+i*road_width]
                           for i in range(len(team.back), len(team.back)+len(units))]},
        "enemy": {"front":[[central_line+2*road_width, upper_line+(i+0.5)*road_width]
                           for i in range(len(team.front), len(team.front)+len(units))], 
                  "back": [[central_line+3*road_width, upper_line+i*road_width]
                           for i in range(len(team.back), len(team.back)+len(units))]}
    }
    colors = {"myTeam": BLUE, "enemy": PURPLE}
    for i, unit in enumerate(units):
        if where[i] == "front":
            unit.position = positions[side]["front"].pop(0)
            unit.original_position = tuple(unit.position)
            unit.actual_row = "front"
            team.front.append(unit)
        else:
            unit.position = positions[side]["back"].pop(0)
            unit.original_position = tuple(unit.position)
            unit.actual_row = "back"
            team.back.append(unit)
        unit.move() # 将rect对应到position
        unit.color = colors[side]
        unit.side = side
        unit.team = team


def buildArmy(team, units, side, from_list=True):
    if from_list:
        units_with_preference = [i for i in units if i.selfrow != "all"]
        units_without_preference = [i for i in units if i.selfrow == "all"]
        fillLines(team, units_with_preference, side)
        fillLines(team, units_without_preference, side)


    # 分配位置
    positions = {
        "myTeam": {"front":[[central_line-2*road_width, upper_line+(i+0.5)*road_width] 
                            for i in range(team.maxfront)], 
                   "back":[[central_line-3*road_width, upper_line+i*road_width]
                           for i in range(team.maxback)]},
        "enemy": {"front":[[central_line+2*road_width, upper_line+(i+0.5)*road_width]
                           for i in range(team.maxfront)], 
                  "back": [[central_line+3*road_width, upper_line+i*road_width]
                           for i in range(team.maxback)]}
    }
    colors = {"myTeam": BLUE, "enemy": PURPLE}
    for unit in team.front:
        unit.position = positions[side]["front"].pop(0)
        unit.original_position = tuple(unit.position)
        unit.actual_row = "front"
        unit.move() # 将rect对应到position
        unit.color = colors[side]
        unit.side = side
        unit.team = team
    for unit in team.back:
        unit.position = positions[side]["back"].pop(0)
        unit.original_position = tuple(unit.position)
        unit.actual_row = "back"
        unit.move()
        unit.color = colors[side]
        unit.side = side
        unit.team = team

    # 分配其他本队记忆 （敌队记忆在setGame中）
    for unit in team.front + team.back:
        if unit.name in ("ArchMage", "Sniper"):
            unit.others = [member for member in (team.front + team.back) if member != unit]



class Team:
    def __init__(self, units):
        self.doubleattack = 0
        self.maxfront = len(units) // 2 - 1 if len(units) > 7 else 3
        self.front = []
        self.maxback = self.maxfront + 3
        self.back = []

        # 追踪器
        self.wholeTeamTracker = [] # 全队行动追踪器
        self.towers = [] # 建筑
        self.skeletons = [] # 骷髅
        # 动画追踪器
        self.aimedTargets = [] # 被狙击手瞄准的目标

        self.font = default_font
        self.unit_size = 4/5 * road_width

    def reset(self, side):
        for member in self.front + self.back:
            member.die()
        # 替换为新实例
        self.front = [member.reset() for member in self.front and member.name != "Skeleton"]
        self.back = [member.reset() for member in self.back and member.name != "Skeleton"]
        # 初始化计数器
        self.doubleattack = 0
        self.aimedTargets = []
        self.wholeTeamTracker = []
        # 重新分配位置
        buildArmy(self, None, side, from_list=False)


    def drawAimedTarget(self, c_x2, c_y2, surface, color):
        pygame.draw.circle(surface, color, (c_x2, c_y2), 12, 4)
        rect1 = pygame.Rect(0, 0, 30, 4)
        rect1.center = (c_x2, c_y2)
        pygame.draw.rect(surface, color, rect1)
        rect2 = pygame.Rect(0, 0, 4, 30)
        rect2.center = (c_x2, c_y2)
        pygame.draw.rect(surface, color, rect2)

    def drawShield(self, c_x2, c_y2, surface, color):
        pygame.draw.circle(surface, color, (c_x2, c_y2), 12, 4)
        rect1 = pygame.Rect(0, 0, 30, 4)
        rect1.center = (c_x2, c_y2)
        pygame.draw.rect(surface, color, rect1)
        rect2 = pygame.Rect(0, 0, 4, 30)
        rect2.center = (c_x2, c_y2)
        pygame.draw.rect(surface, color, rect2)


    def draw(self, screen):
        for member in (self.front + self.back):
            member.move()
            # 绘制单位
            pygame.draw.rect(screen, member.color, member.rect)
            
            unit_position = tuple(member.position)
            # 绘制血条，使用动画血条，而不是真实血条
            hpLocation = (unit_position[0]-unit_size//2, unit_position[1] - unit_size//2 - 13)
            pygame.draw.rect(screen, RED, (*hpLocation, self.unit_size, 13))
            pygame.draw.rect(screen, GREEN, (*hpLocation, self.unit_size * (member.lockhp / member.maxhp), 13))

            # 绘制蓝条
            manaLocation = (unit_position[0]-unit_size//2, unit_position[1] - unit_size//2 - 5)
            if member.mana:
                pygame.draw.rect(screen, DARK_BLUE, (*manaLocation, self.unit_size * (member.mana / member.maxmana), 5))

            # 绘制全队行动追踪器
            if member in self.wholeTeamTracker:
                rect = pygame.Rect(0, 0, unit_size, unit_size)
                rect.center = tuple(member.position)
                pygame.draw.rect(screen, BLACK, rect, 5)

            # 此时在动画上单位还存活
            if member.alive or (not member.alive and (member.lockhp > 0 or member.unplayed_anima)):
                # 绘制单位的特殊状态
                if member.special_status:
                    member.drawSpecialStatus(screen)
                
                # 绘制宠物
                if member.attachment:
                    for i, attachment in enumerate(member.attachment):
                        attachment.draw(screen, i)

                # 绘制守护
                if member.shield > 0:
                    member.drawShieldWithSurroundings(screen)    

                # 绘制单位名字    
                unit_name = self.font.render(member.chinese_name, True, WHITE)  # 白色文字
                text_rect = unit_name.get_rect(center=unit_position) 
                drawSurroundings(screen, member.chinese_name, unit_position, unit_name, self.font, True) # 描边
                screen.blit(unit_name, text_rect)

                # 指示瞄准的目标
                if member in self.aimedTargets:
                    c_x2, c_y2 = member.position
                    # c_x2, c_y2 = c_x2-unit_size//2, c_y2-unit_size//2+12
                    for dx, dy in offsets:
                        self.drawAimedTarget(c_x2+dx, c_y2+dy, screen, BLACK)
                    self.drawAimedTarget(c_x2, c_y2, screen, MID_RED)

            # 死亡名字
            else:
                member.special_status = False
                unit_name = self.font.render(member.dead_name, True, RED)
                text_rect = unit_name.get_rect(center=unit_position)  
                drawSurroundings(screen, member.dead_name, unit_position, unit_name, self.font, True) 
                screen.blit(unit_name, text_rect)  
            # 绘制完后，每一帧都设置各个单位的没有未播放动画，留给动画部分更新属性
            member.unplayed_anima = False



def randAliveAll(team0): # return a random member in the team that is alive
    #But we assume that someone must be alive in the team
    if randint(0,1):
        return randAliveBack(team0)
    else:
        return randAliveFront(team0)
    

def AliveAll(team0, exclude=None, exclude_names=(), exclude_types=()):
    return [unit for unit in team0.front+team0.back 
            if unit.alive and unit != exclude and 
            unit.name not in exclude_names and 
            all(not isinstance(unit, exclude_type) for exclude_type in exclude_types)]


def randAliveSeveral(team0, n, exclude=None):
    # 获取所有活着的单位
    alive_units = AliveAll(team0, exclude=None)
    
    # 如果活着的单位不足 n 个，返回所有单位
    if len(alive_units) <= n:
        return alive_units
    
    # 随机选择 n 个单位
    return sample(alive_units, n)



def randAliveFront(team0): # return a random member in the team that is alive
    #But we assume that someone must be alive in the team
    n = len(team0.front)
    if allDead(team0.front) or n == 0:
        return randAliveBack(team0)
    else:
        r = randint(0,n-1)
        return team0.front[r] if team0.front[r].alive else randAliveFront(team0)


def randAliveBack(team0): # return a random member in the team that is alive
    #But we assume that someone must be alive in the team
    n = len(team0.back)
    if allDead(team0.back) or n == 0:
        return randAliveFront(team0)
    else:
        r = randint(0,n-1)
        return team0.back[r] if team0.back[r].alive else randAliveBack(team0)


def nearbyAlive(team0, target, nearby=1, exclude=False): # return alive members next to it
    if target.actual_row == "front":
        the_row = team0.front
    elif target.actual_row == "back":
        the_row = team0.back

    i = the_row.index(target)
    targets = []
    for j in range(i-nearby, i+nearby+1):
        if j < 0 or j >= len(the_row):
            continue
        if exclude and the_row[j] == target:
            continue
        if the_row[j].alive:
            targets.append(the_row[j])
    return targets



def randDeath(team0):
    if randint(0,1):
        return randDeathBack(team0)
    else:
        return randDeathFront(team0)


def randDeathFront(team0): 
    n = len(team0.front)
    if allAlive(team0.front) or n == 0:
        return randDeathBack(team0)
    else:
        r = randint(0,n-1)
        return team0.front[r] if not team0.front[r].alive else randDeathFront(team0)


def randDeathBack(team0): 
    n = len(team0.back)
    if allAlive(team0.back) or n == 0:
        return randDeathFront(team0)
    else:
        r = randint(0,n-1)
        return team0.back[r] if not team0.back[r].alive else randDeathBack(team0)




def Damaged(team0, who="one"): 
    damaged_ones = []
    for i in team0.front + team0.back:
        if i.hp < i.maxhp and i.alive:
            damaged_ones.append(i)
    if damaged_ones == []:
        return False
    else:
        if who == "one":
            r = randint(0,len(damaged_ones)-1)
            return damaged_ones[r]
        elif who == "all":
            return damaged_ones
        else:
            return False


def deadCount(team0,where="all"):
    if type(team0) == list:
        team = team0
    else:
        if where == "front":
            team = team0.front
        elif where == "back":
            team = team0.back
        elif where == "all":
            team = team0.front + team0.back
    count = 0
    for i in team:
        if not i.alive:
            count += 1
    return count



def allDead(team0, where="all"): # Check if all the team is dead
    if type(team0) == list:
        team = team0
    else:
        if where == "front":
            team = team0.front
        elif where == "back":
            team = team0.back
        elif where == "all":
            team = team0.front + team0.back
    for i in team:
        if i.alive:
            return False
    return True

def allAlive(team0, where="all"):# Check if all the team is alive
    if type(team0) == list:
        team = team0
    else:
        if where == "front":
            team = team0.front
        elif where == "back":
            team = team0.back
        elif where == "all":
            team = team0.front + team0.back
    for i in team:
        if not i.alive:
            return False
    return True




