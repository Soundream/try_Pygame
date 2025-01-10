
# type: normal, heal, kaboom, poison
def testDamage(attacker, target, originalDamage, type="normal"):
    damage = round(originalDamage)
    if damage < 0 and type in ("normal", "heal"):
        damage = -damage
        type = "heal"
    
    # 小猫不过检定
    if target.name == "Cat":
        if type == "heal":
            return -1
        else:
            return 1

    # 毒伤害和治疗不过检定
    if type in ("poison", "heal"):
        return round(damage)


    # 其他伤害过检定
    # 先查看有没有百分比加伤减伤
    if attacker:
        if hasattr(attacker, "percentage_damage_buff") and attacker.percentage_damage_buff:
            damage *= 1 + attacker.percentage_damage_buff
        damage = attachmentBuff(attacker, damage, "percentage_damage_buff")

    if hasattr(target, "percentage_defense_buff") and target.percentage_defense_buff:
        damage *= 1 - target.percentage_defense_buff
    damage = attachmentBuff(target, damage, "percentage_defense_buff")

    # 再查看有没有固定加伤减伤
    if attacker:
        if hasattr(attacker, "fixed_damage_buff") and attacker.fixed_damage_buff:
            damage += attacker.fixed_damage_buff
        damage = attachmentBuff(attacker, damage, "fixed_damage_buff")

    if hasattr(target, "fixed_defense_buff") and target.fixed_defense_buff:
        damage -= target.fixed_defense_buff
    damage = attachmentBuff(target, damage, "fixed_defense_buff")
    
    # 普通伤害受到shield减伤，每次减少50点。kaboom伤害不受shield减伤。
    if type=="normal" and target.shield > 0:
        if damage > target.hp:
            damage -= 50 * target.shield
            target.shield = 0
            target.checkShield()
        else:
            damage -= 50
            target.shield -= 1
            target.checkShield()

    return max(1,round(damage))




cal_buff = {
    "percentage_damage_buff": lambda damage, buff: damage * (1 + buff),
    "percentage_defense_buff": lambda damage, buff: damage * (1 - buff),
    "fixed_damage_buff": lambda damage, buff: damage + buff,
    "fixed_defense_buff": lambda damage, buff: damage - buff,
    }


def attachmentBuff(attacker, damage, buff_type):
    # 同类buff后续只有25%收益
    if attacker.attachment:
        attachments = []
        for attachment1 in attacker.attachment:
            if getattr(attachment1, buff_type):
                if attachment1.name not in attachments:
                    attachments.append(attachment1.name)
                    damage = cal_buff[buff_type](damage, getattr(attachment1, buff_type))
                else:
                    damage = cal_buff[buff_type](damage, getattr(attachment1, buff_type)/4)

                # 如果伤者身上有小猫，小猫会尝试逃跑
                if attachment1.name == "Cat" and buff_type == "fixed_defense_buff":
                    attachment1.findMaster(attachment1.team, game=None, master=None)
                    # 逃跑失败会扣血
                    if attachment1.master == attachment1.ex_master:
                        attachment1.gotHurt(1)
                        attachment1.lockhp -= 1
    return damage
                    




