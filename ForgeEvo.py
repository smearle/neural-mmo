import os
import pickle
import sys
# My favorite debugging macro
from pdb import set_trace as T

import ray
import torch
from fire import Fire
from ray import rllib

import projekt
from evolution.evolver import init_evolver
from pcg import get_tile_data
TILE_TYPES, TILE_PROBS = get_tile_data(griddly=False)
from projekt import rllib_wrapper

'''Main file for the neural-mmo/projekt demo

/projeckt will give you a basic sense of the training
loop, infrastructure, and IO modules for handling input
and output spaces. From there, you can either use the
prebuilt IO networks in PyTorch to start training your
own models immediately or hack on the environment'''

# Instantiate a new environment

def createEnv(config):
#   map_arr = config['map_arr']

    return rllib_wrapper.RLLibEnv(#map_arr,
            config)

# Map agentID to policyID -- requires config global

def mapPolicy(agentID):
    return 'policy_{}'.format(agentID % config.NPOLICIES)


# Generate RLlib policies

def createPolicies(config):
    obs = rllib_wrapper.observationSpace(config)
    atns = rllib_wrapper.actionSpace(config)
    policies = {}

    for i in range(config.NPOLICIES):
        params = {"agent_id": i, "obs_space_dict": obs, "act_space_dict": atns}
        key = mapPolicy(i)
        policies[key] = (None, obs, atns, params)

    return policies

#@ray.remote
#class Counter:
#   ''' When using rllib trainer to train and simulate on evolved maps, this global object will be
#   responsible for providing unique indexes to parallel environments.'''
#   def __init__(self, config):
#      self.count = 0
#   def get(self):
#      self.count += 1
#
#      if self.count == config.N_EVO_MAPS:
#          self.count = 0
#
#      return self.count
#   def set(self, i):
#      self.count = i - 1

@ray.remote
class Counter:
   ''' When using rllib trainer to train and simulate on evolved maps, this global object will be
   responsible for providing unique indexes to parallel environments.'''
   def __init__(self, config):
      self.count = 0
      self.idxs = None

   def get(self):

      if not self.idxs:
         # Then we are doing inference and have set the idx directly

         return self.count
      idx = self.idxs[self.count % len(self.idxs)]
      self.count += 1

      return idx

   def set(self, i):
      # For inference
      self.count = i

   def set_idxs(self, idxs):
      self.count = 0
      self.idxs = idxs

#@ray.remote
#class Stats:
#   def __init__(self, config):
#      self.stats = {}
#      self.mults = {}
#      self.spawn_points = {}
#      self.config = config
#   def add(self, stats, mapIdx):
#      if config.RENDER:
##        print(self.headers)
##        print(stats)
#         calc_differential_entropy(stats, verbose=True)
#
#         return
#
#      if mapIdx not in self.stats or 'skills' not in self.stats[mapIdx]:
#         self.stats[mapIdx] = stats
#      else:
#         for (k, v) in stats.items():
#             if k in self.stats:
#                 self.stats[k].append(v)
#             else:
#                 self.stats[k] = [stats[k]]
#   def get(self):
#      return self.stats
#   def reset(self):
#      self.stats = {}
#   def add_mults(self, g_hash, mults):
#      self.mults[g_hash] = mults
#   def get_mults(self, g_hash):
#      if g_hash not in self.mults:
#         return None
#
#      return self.mults[g_hash]
#   def add_spawn_points(self, g_hash, spawn_points):
#      self.spawn_points[g_hash] = spawn_points
#   def get_spawn_points(self, g_hash):
#      return self.spawn_points[g_hash]



if __name__ == '__main__':
   # Setup ray
#  torch.set_num_threads(1)
   torch.set_num_threads(torch.get_num_threads())
   ray.init()


   global config

   config = projekt.config.EvoNMMO()
#  config = projekt.config.Griddly()

   # Built config with CLI overrides
   if len(sys.argv) > 1:
       sys.argv.insert(1, 'override')
       Fire(config)


   # on the driver
   counter = Counter.options(name="global_counter").remote(config)
#  stats = Stats.options(name="global_stats").remote(config)

   # RLlib registry
   rllib.models.ModelCatalog.register_custom_model('test_model',
                                                   rllib_wrapper.Policy)
   ray.tune.registry.register_env("custom", createEnv)

 # save_path = 'evo_experiment/skill_entropy_life'
 # save_path = 'evo_experiment/scratch'
 # save_path = 'evo_experiment/skill_ent_0'

   save_path = os.path.join('evo_experiment', '{}'.format(config.EVO_DIR))

   if not os.path.isdir(save_path):
       os.mkdir(save_path)

   try:
      evolver_path = os.path.join(save_path, 'evolver')
      with open(evolver_path, 'rb') as save_file:
         evolver = pickle.load(save_file)

         print('loading evolver from save file')
      # change params on reload here
      evolver.config.RENDER = config.RENDER
      evolver.config.TERRAIN_RENDER = config.TERRAIN_RENDER
      evolver.config.NENT = config.NENT
      evolver.config.MODEL = 'reload'
      evolver.reloading = True
      evolver.epoch_reloaded = evolver.n_epoch
      evolver.restore(trash_trainer=True)
      if config.RENDER:
         evolver.config.INFER_IDX = config.INFER_IDX
      if evolver.MAP_ELITES:
         evolver.load()

   except FileNotFoundError as e:
      print(e)
      print('Cannot load; missing evolver and/or model checkpoint. Evolving from scratch.')

      evolver = init_evolver(save_path,
                            createEnv,
                            None,  # init the trainer in evolution script
                            config,
                            n_proc=   config.N_PROC,
                            n_pop=    config.N_EVO_MAPS,
                            )
#  print(torch.__version__)

#  print(torch.cuda.current_device())
#  print(torch.cuda.device(0))
#  print(torch.cuda.device_count())
#  print(torch.cuda.get_device_name(0))
#  print(torch.cuda.is_available())
#  print(torch.cuda.current_device())

   if config.RENDER:
      evolver.infer()
   else:
      evolver.evolve()