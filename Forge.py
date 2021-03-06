'''Main file for the neural-mmo/projekt demo

/projeckt will give you a basic sense of the training
loop, infrastructure, and IO modules for handling input 
and output spaces. From there, you can either use the 
prebuilt IO networks in PyTorch to start training your 
own models immediately or hack on the environment'''

#My favorite debugging macro
from pdb import set_trace as T

from fire import Fire
import sys

import numpy as np
import torch

import ray
from ray import rllib

from forge.ethyr.torch import utils

import projekt
from projekt import realm, rlutils

#Instantiate a new environment
def createEnv(config):
   map_arr = config['map_arr']
   return projekt.Realm(map_arr, config)

#Map agentID to policyID -- requires config global
def mapPolicy(agentID):
   return 'policy_{}'.format(agentID % config.NPOLICIES)

#Generate RLlib policies
def createPolicies(config):
   obs      = projekt.realm.observationSpace(config)
   atns     = projekt.realm.actionSpace(config)
   policies = {}

   for i in range(config.NPOLICIES):
      params = {
            "agent_id": i,
            "obs_space_dict": obs,
            "act_space_dict": atns}
      key           = mapPolicy(i)
      policies[key] = (None, obs, atns, params)

   return policies

if __name__ == '__main__':
   #Setup ray
   torch.set_num_threads(1)
   ray.init()
   
   #Built config with CLI overrides
   config = projekt.Config()
   if len(sys.argv) > 1:
      sys.argv.insert(1, 'override')
      Fire(config)

   #RLlib registry
   rllib.models.ModelCatalog.register_custom_model(
         'test_model', projekt.Policy)
   ray.tune.registry.register_env("custom", createEnv)

   #Create policies
   policies  = createPolicies(config)


   map_arr = np.zeros((120, 120), dtype=int)

   #Instantiate monolithic RLlib Trainer object.
   trainer = rlutils.SanePPOTrainer(
         env="custom", path='experiment', config={
      'num_workers': 1,
      'num_gpus': 1,
      'num_envs_per_worker': 1,
      'train_batch_size': 4000,
      'rollout_fragment_length': 100,
      'sgd_minibatch_size': 128,
      'num_sgd_iter': 1,
      'use_pytorch': True,
      'horizon': np.inf,
      'soft_horizon': False, 
      'no_done_at_end': False,
      'env_config': {
         'config': config,
         'map_arr': map_arr,
      },
      'multiagent': {
         "policies": policies,
         "policy_mapping_fn": mapPolicy
      },
      'model': {
         'custom_model': 'test_model',
         'custom_options': {'config': config}
      },
   })

   #Print model size
   utils.modelSize(trainer.defaultModel())
   trainer.restore(config.MODEL)
  #torch._C._cuda_init()
#  trainer.defaultModel().cuda()

   if config.RENDER:
      env = createEnv({'config': config,
                        'map_arr': map_arr})
      projekt.Evaluator(trainer, env, map_arr, config).run()
   else:
      trainer.train()
