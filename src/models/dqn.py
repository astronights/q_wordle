import gym
import sys
from src.models.base_model import BaseModel
from stable_baselines3.common.env_util import make_vec_env
from ..config import WIN_REWARD, LOSE_REWARD

import numpy as np
from stable_baselines3 import DQN

from ..envs.qwordle3 import QWordle3

class DQNModel(BaseModel):

    def __init__(self, config = None):
        super().__init__(config)
        self.epsilon = config['epsilon']
        self.gamma = config['gamma']
        self.alpha = config['alpha']
        self.games_solved = []

    def train(self, iter = 100):
        self.games_solved = []
        env = gym.make("QWordle3-v0")
        model = DQN(
            "MlpPolicy", 
            env,
            gamma=self.gamma, 
            learning_rate=self.alpha,
            learning_starts=10000,
            buffer_size=6*iter,
            exploration_fraction=self.epsilon,
            exploration_final_eps=0.5,
            target_update_interval=1000,
            train_freq=1,
            verbose=1,
        )
        try:
            model.learn(total_timesteps=6*iter, log_interval=1)
        except KeyboardInterrupt:
            pass
        counter = 0
        rewards = model.replay_buffer.rewards
        for reward in rewards:
            if reward[0] == 30:
                self.games_solved.append(counter)
            if reward[0] == WIN_REWARD or reward[0] == LOSE_REWARD:
                counter += 1
        # print(model.q_net)
        model.save("wordle_dqn")
        return model

    def test(self, verbose=True):

        model = DQN.load("wordle_dqn")

        env = QWordle3()
        obs = env.reset()
        done = False
        while not done:
            action, _states = model.predict(obs)
            obs, rewards, done, res = env.step(action)
            if(verbose):
                env.render()
        if(verbose):
            print(res)
        return(res)