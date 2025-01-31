from collections import defaultdict

import numpy as np
import gym
import d4rl

from spirl.utils.general_utils import AttrDict
from spirl.utils.general_utils import ParamDict
from spirl.rl.components.environment import GymEnv


class KitchenEnv(GymEnv):
    """Tiny wrapper around GymEnv for Kitchen tasks."""

    SUBTASKS = [
        "microwave",
        "kettle",
        "slide cabinet",
        "hinge cabinet",
        "bottom burner",
        "light switch",
        "top burner",
        "left hinge cabinet",
    ]

    def __init__(self, *args, **kwargs):
        if args[0]["task"] == "misaligned":
            self.name = "kitchen-mlsh-v0"  # Microwave - Light - Slider - Hinge
        elif args[0]["task"] == "newskill":
            self.name = "kitchen-newskill-v0" # Left Hinge Cabinet
        else:
            self.name = "kitchen-mixed-v0"  # Microwave - Kettle - Bottom Burner - Light

        super().__init__(*args, **kwargs)
        self.id = "kitchen"
        self.observation_space = self._env.observation_space
        self.action_space = self._env.action_space
        self.solved_subtasks = defaultdict(lambda: 0)
        self._t = 0
        self.max_episode_steps = 280

    def _default_hparams(self):
        return super()._default_hparams().overwrite(ParamDict({"name": self.name,}))

    def step(self, *args, **kwargs):
        obs, rew, done, info = super().step(*args, **kwargs)
        self._t += 1
        if self._t >= self.max_episode_steps:
            done = True
        return (
            obs,
            np.float64(rew),
            done,
            self._postprocess_info(info),
        )  # casting reward to float64 is important for getting shape later

    def reset(self):
        self.solved_subtasks = defaultdict(lambda: 0)
        self._t = 0
        return super().reset()

    def get_episode_info(self):
        info = super().get_episode_info()
        info.update(AttrDict(self.solved_subtasks))
        return info

    def _postprocess_info(self, info):
        """Sorts solved subtasks into separately logged elements."""
        completed_subtasks = info.pop("completed_tasks")
        for task in self.SUBTASKS:
            self.solved_subtasks[task] = (
                1 if task in completed_subtasks or self.solved_subtasks[task] else 0
            )
        return info


class NoGoalKitchenEnv(KitchenEnv):
    """Splits off goal from obs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        low, high = self._env.observation_space.low, self._env.observation_space.high
        self.observation_space = gym.spaces.Box(low[:30], high[:30])

    def step(self, *args, **kwargs):
        obs, rew, done, info = super().step(*args, **kwargs)
        obs = obs[: int(obs.shape[0] / 2)]
        return obs, rew, done, info

    def reset(self, *args, **kwargs):
        obs = super().reset(*args, **kwargs)
        return obs[: int(obs.shape[0] / 2)]
