from pdb import set_trace as T
import numpy as np

from forge.blade.io.stimulus.hook import StimHook
from forge.blade.io.stimulus.static import Stimulus

def camel(string):
   return string[0].lower() + string[1:]

class Tile(StimHook):
   SERIAL = 1
   def __init__(self, config, mat, r, c, nCounts, tex):
      super().__init__(Stimulus.Tile, config)
      self.r, self.c = r, c
      self.mat = mat()
      self.ents = {}
      self.state = mat()
      self.capacity = self.mat.capacity
      self.tex = tex
      self.terraformable = True

      self.counts = [0 for _ in range(config.NPOP)]

   @property
   def serial(self):
      return self.r, self.c

   def addEnt(self, entID, ent):
      assert entID not in self.ents
      self.ents[entID] = ent

   def delEnt(self, entID):
      assert entID in self.ents
      del self.ents[entID]

   def step(self):
      if (not self.static and 
            np.random.rand() < self.mat.respawnProb):
         self.capacity += 1

      #Try inserting a pass
      if self.static:
         self.state = self.mat

   @property
   def static(self):
      assert self.capacity <= self.mat.capacity
      return self.capacity == self.mat.capacity

   def harvest(self):
      if self.capacity == 0:
         return False
      elif self.capacity <= 1:
         self.state = self.mat.degen()
      self.capacity -= 1
      return True
      return self.mat.dropTable.roll()

   def terraform(self, config, mat):
      super().__init__(Stimulus.Tile, config)
      self.mat = mat()
#     self.capacity = self.mat.capacity
      
  
