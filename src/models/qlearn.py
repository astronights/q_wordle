from .base_model import BaseModel
from ..strategies.random import RandomStrategy
from ..strategies.highest_ll_strategy import HighestLLStrategy
from ..strategies.highest_ll_smart_strategy import HighestLLSmartStrategy
from ..strategies.fresh_letters_strategy import FreshLettersStrategy
from ..envs.qwordle import QWordle
from ..utils import get_state, word_to_action
from ..config import WORD_LENGTH, GAME_LENGTH

import os
import pickle

import numpy as np
from tqdm import tqdm

class QLearn(BaseModel):
    
    def __init__(self, config = None):
        super().__init__(config)
        self.strategies = []
        self.strategies.extend([RandomStrategy(), HighestLLStrategy(), HighestLLSmartStrategy(), FreshLettersStrategy()])
        if config and 'Q' in config:
            self.Q = config['Q']
            self.epsilon = config['epsilon']
            self.gamma = config['gamma']
            self.alpha = config['alpha']
        else:
            self.Q = np.zeros((WORD_LENGTH+1, WORD_LENGTH+1, GAME_LENGTH+1, len(self.strategies)))
        self.env = QWordle()
        self.games_solved = []

    def update_q(self, q):
        self.Q = q

    def policyFunction(self, state, epsilon):
        action_probabilities = np.ones(len(self.strategies), dtype = float) * epsilon / len(self.strategies)       
        best_action = np.argmax(self.Q[state['green'], state['yellow'], state['step'], :])
        action_probabilities[best_action] += (1.0 - epsilon)
        return action_probabilities
   
    def train(self, iter = 100):
        self.games_solved = []
        num_solved = 0
        for i in tqdm(range(iter)):
            observations = self.env.reset()
            state = get_state(observations['letters'])
            state['step'] = 0 
            done = False
            while(not done):
                action_probabilities = self.policyFunction(state, self.epsilon*(1 - num_solved/iter))
                action_strategy = np.random.choice(np.arange(len(action_probabilities)), p = action_probabilities)
                action = self.strategies[action_strategy].get_action(observations)
                action = word_to_action(action)
                next, reward, done, res = self.env.step(action)
                next_state = get_state(next['letters'])
                next_state['step'] = state['step'] + 1
                next_best_action = np.argmax(self.Q[next_state['green'], next_state['yellow'], next_state['step'],:])
                q_target = reward + self.gamma * self.Q[next_state['green'], next_state['yellow'], next_state['step'], next_best_action]
                self.Q[state['green'], state['yellow'], state['step'], action_strategy] = (self.alpha*q_target) + ((1-self.alpha) * self.Q[state['green'], state['yellow'], state['step'], action_strategy])
                state = next_state
            if(res['solved']):
                num_solved += 1
                self.games_solved.append(i+1)

        pickle.dump({'Q': self.Q}, open('qlearn.pkl', 'wb'))

    def test(self, verbose=True):
        if(os.path.exists('qlearn.pkl')):
            self.Q = pickle.load(open('qlearn.pkl', 'rb'))['Q']
        observations = self.env.reset()
        state = get_state(observations['letters'])
        state['step'] = 0 
        done = False
        while(not done):
            action_probabilities = self.policyFunction(state, 0)
            action_strategy = np.random.choice(np.arange(len(action_probabilities)), p = action_probabilities)
            action = self.strategies[action_strategy].get_action(observations)
            action = word_to_action(action)
            next, _, done, res = self.env.step(action)
            next_state = get_state(next['letters'])
            next_state['step'] = state['step'] + 1
            state = next_state
            if(verbose):
                self.env.render()
        if(verbose):
            print(res)
        return(res)