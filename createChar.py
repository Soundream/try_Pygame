
from Characters import *
from random import randint
from TeamLogic import *
from colors import *
from GeneralSettings import *
from WordEffects import *

characters = [
    Fighter, 
    Assassin,
    Berserker, 
    Shieldguard,
    Paladin,
    HellConqueror,

    Dog,
    Bard, 
    Ranger,
    Spearman,

    Mage, 
    Cleric,
    Necromancer, 
    SkeletalSummoner,
    ArchMage, 
        
    Archer, 
    Longbowman,
    Sniper, 
    
    Cat,
    Skeleton,
    ]

def createChar(i):
    return characters[i-1](), i
    

def createRandTeam(gold, massMinions = False):
    team = []
    unit_ints = []
    while gold >= minCost:
        tempChar, unit_int = createChar(randint(1,nCharType))
        if gold >= tempChar.cost:
            if massMinions:
                if tempChar.cost > 2*minCost or tempChar.cost < minCost:
                    continue
            gold -= tempChar.cost
            team.append(tempChar)
            unit_ints.append(unit_int)       
    return team, unit_ints








