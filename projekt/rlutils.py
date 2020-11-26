from pdb import set_trace as T
import numpy as np

import ray.rllib.agents.ppo.ppo as ppo
from ray.rllib.policy.sample_batch import DEFAULT_POLICY_ID


class EvoPPOTrainer(ppo.PPOTrainer):
   '''Small utility class on top of RLlib's base trainer'''
   def __init__(self, env, path, config):
      super().__init__(env=env, config=config)
      self.saveDir = path
      self.n_epoch = 0

   def save(self):
      '''Save model to file. Note: RLlib does not let us chose save paths'''
      savedir = super().save(self.saveDir)
      with open('experiment/path.txt', 'w') as f:
         f.write(savedir)
      print('Saved to: {}'.format(savedir))
      return savedir

   def restore(self, model):
      '''Restore model from path'''
      if model is None:
         print('Training from scratch...')
         return
      if model == 'current':
         with open('experiment/path.txt') as f:
            path = f.read().splitlines()[0]
      else:
         path = 'experiment/{}/checkpoint'.format(model)

      print('Loading from: {}'.format(path))
      super().restore(path)

   def policyID(self, idx):
      return 'policy_{}'.format(idx)

   def model(self, policyID):
      model = self.get_policy(policyID).model
     #print('sending evo trainer model to gpu\n')
#     model.cuda()
      return self.get_policy(policyID).model

   def defaultModel(self):
      return self.model(self.policyID(0))

   def train(self, 
      #maps
      ):
     
#     self.maps = maps
     stats = super().train()
     self.save()

     nSteps = stats['info']['num_steps_trained']
     print('Epoch: {}, Samples: {}'.format(self.n_epoch, nSteps))
     hist = stats['hist_stats']
     for key, stat in hist.items():
        if len(stat) == 0 or key == 'map_fitness':
           continue

        print('{}:: Total: {:.4f}, N: {:.4f}, Mean: {:.4f}, Std: {:.4f}, Min: {:.4f}, Max: {:.4f}'.format(
              key, np.sum(stat), len(stat), np.mean(stat), np.std(stat), np.min(stat), np.max(stat)))
       #if key == 'map_fitness':
       #    print('DEBUG MAP FITNESS PRINTOUT')
       #    print(hist[key])
        hist[key] = []
   
     self.n_epoch += 1
     return stats

   def reset(self, new_remote_workers):
      print('sane reset evoTrainer \n')
      print(self.workers.local_worker, self.workers.remote_workers)
      self.workers.reset(new_remote_workers)
#     raise Exception


class SanePPOTrainer(ppo.PPOTrainer):
   '''Small utility class on top of RLlib's base trainer'''
   def __init__(self, env, path, config):
      super().__init__(env=env, config=config)
      self.saveDir = path

   def save(self):
      '''Save model to file. Note: RLlib does not let us chose save paths'''
      savedir = super().save(self.saveDir)
      with open('experiment/path.txt', 'w') as f:
         f.write(savedir)
      print('Saved to: {}'.format(savedir))
      return savedir

   def restore(self, model):
      '''Restore model from path'''
      if model is None:
         print('Training from scratch...')
         return
      if model == 'current':
         with open('experiment/path.txt') as f:
            path = f.read().splitlines()[0]
      else:
         path = 'experiment/{}/checkpoint'.format(model)

      print('Loading from: {}'.format(path))
      super().restore(path)

   def policyID(self, idx):
      return 'policy_{}'.format(idx)

   def model(self, policyID):
      return self.get_policy(policyID).model

   def defaultModel(self):
      return self.model(self.policyID(0))

   def train(self):
      '''Train forever, printing per epoch'''
      epoch = 0
      while True:
          stats = super().train()
          self.save()

          nSteps = stats['info']['num_steps_trained']
          print('Epoch: {}, Samples: {}'.format(epoch, nSteps))
          hist = stats['hist_stats']
          for key, stat in hist.items():
             if len(stat) == 0:
                continue

             print('{}:: Total: {:.4f}, N: {:.4f}, Mean: {:.4f}, Std: {:.4f}, Min: {:.4f}, Max: {:.4f}'.format(
                   key, np.sum(stat), len(stat), np.mean(stat), np.std(stat), np.min(stat), np.max(stat)))
             hist[key] = []
       
          epoch += 1
