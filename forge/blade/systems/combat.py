#Various utilities for managing combat, including hit/damage

from pdb import set_trace as T

import numpy as np
from forge.blade.systems import skill as Skill

def level(skills):
   hp = skills.constitution.level
   defense = skills.defense.level
   melee = skills.melee.level
   ranged = skills.range.level
   mage   = skills.mage.level
   
   base = 0.25*(defense + hp)
   final = np.floor(base + 0.5*max(melee, ranged, mage))
   return final

def attack(entity, targ, skill):
   attackLevel  = skill.level
   defenseLevel = targ.skills.defense.level + targ.loadout.defense
   skill = skill.__class__.__name__

   #1 dmg on a miss, max hit on success
   dmg = 1
   if np.random.rand() < accuracy(attackLevel, defenseLevel):
      dmg = damage(skill, attackLevel, entity.resources, entity.config)
      
   entity.applyDamage(dmg, skill.lower())
   targ.receiveDamage(entity, dmg)
   return dmg

#Compute maximum damage roll
def damage(skill, level, resources, config):
   # pseudo-smithing
   mult = min(resources.ore.val + 1, 1.5)
   resources.ore.decrement(1)
   if skill == 'Melee':
      return np.floor((5 + level * config.MELEE_MULT) * mult)
   if skill == 'Range':
      return np.floor((3 + level * config.RANGE_MULT) * mult)
   if skill == 'Mage':
      return np.floor((1 + level * config.MAGE_MULT) * mult)

#Compute maximum attack or defense roll (same formula)
#Max attack 198 - min def 1 = 197. Max 198 - max 198 = 0
#REMOVE FACTOR OF 2 FROM ATTACK AFTER IMPLEMENTING WEAPONS
def accuracy(attkLevel, defLevel):
   return 0.5 + (2*attkLevel - defLevel) / 197

def danger(config, pos, full=False):
   cent = config.TERRAIN_SIZE // 2

   #Distance from center
   R   = int(abs(pos[0] - cent + 0.5))
   C   = int(abs(pos[1] - cent + 0.5))
   mag = max(R, C)

   #Distance from border terrain to center
   if config.INVERT_WILDERNESS:
      R   = cent - R - config.TERRAIN_BORDER
      C   = cent - C - config.TERRAIN_BORDER
      mag = min(R, C)

   #Normalize
   norm = mag / (cent - config.TERRAIN_BORDER)

   if full:
      return norm, mag
   return norm
      
def wilderness(config, pos):
   norm, raw = danger(config, pos, full=True)
   wild      = int(100 * norm) - 1

   if not config.WILDERNESS:
      return 99
   if wild < config.WILDERNESS_MIN:
      return -1
   if wild > config.WILDERNESS_MAX:
      return config.WILDERNESS_MAX

   return wild
