# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Snake Environment Implementation.

This module implements the actual Snake game environment for server-side execution.
"""

from typing import Tuple, Any, Dict
import random
import asyncio
import uuid

try:
    from my_env.models import SnakeAction, SnakeObservation
except ImportError:
    from models import SnakeAction, SnakeObservation

try:
    from openenv.core.env_server.types import State
except ImportError:
    # Fallback if State not available
    class State:
        def __init__(self, episode_id=None, step_count=0):
            self.episode_id = episode_id
            self.step_count = step_count


class SnakeEnv:
    """
    Snake Game Environment.
    
    A simple grid-based snake game where the snake moves around a grid
    trying to eat food while avoiding walls and itself.
    """

    def __init__(
        self,
        grid_width: int = 10,
        grid_height: int = 10,
        seed: int = None,
    ):
        """
        Initialize the Snake environment.

        Args:
            grid_width: Width of the game grid (default: 10)
            grid_height: Height of the game grid (default: 10)
            seed: Random seed for reproducibility
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.rng = random.Random(seed)

        # Game state
        self.snake = []
        self.food = None
        self.direction = (1, 0)  # (dx, dy)
        self.next_direction = (1, 0)
        self.episode_score = 0
        self.episode_steps = 0
        self.episode_fruits = 0
        self.alive = True
        self.episode_id = str(uuid.uuid4())
        self._state = State(episode_id=self.episode_id, step_count=0)

    async def reset_async(self) -> SnakeObservation:
        """Async version of reset for OpenEnv compatibility."""
        return self.reset()

    def reset(self) -> SnakeObservation:
        """
        Reset the environment to initial state.

        Returns:
            SnakeObservation: Initial observation
        """
        # Create new episode
        self.episode_id = str(uuid.uuid4())
        self._state = State(episode_id=self.episode_id, step_count=0)
        
        # Initialize snake in the center
        mid_x, mid_y = self.grid_width // 2, self.grid_height // 2
        self.snake = [(mid_x, mid_y), (mid_x - 1, mid_y), (mid_x - 2, mid_y)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.episode_score = 0
        self.episode_steps = 0
        self.episode_fruits = 0
        self.alive = True

        # Spawn first food
        self._spawn_food()

        return self._get_observation()

    def step(self, action: SnakeAction) -> Tuple[SnakeObservation, float, bool]:
        """
        Execute one step of the environment.

        Args:
            action: SnakeAction with action value (0=noop, 1=left, 2=right)

        Returns:
            Tuple of (observation, reward, done)
        """
        # Update direction based on action
        if action.action == 1:  # Turn left
            dx, dy = self.direction
            self.next_direction = (dy, -dx)
        elif action.action == 2:  # Turn right
            dx, dy = self.direction
            self.next_direction = (-dy, dx)
        # else: action == 0 (noop), keep current direction

        self.direction = self.next_direction

        # Move snake
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        reward = 0
        done = False

        # Check wall collision
        if not (0 <= new_head[0] < self.grid_width and 0 <= new_head[1] < self.grid_height):
            self.alive = False
            reward = -1
            done = True
        # Check self collision
        elif new_head in self.snake:
            self.alive = False
            reward = -1
            done = True
        else:
            # Add new head
            self.snake.insert(0, new_head)

            # Check food collision
            if new_head == self.food:
                reward = 1
                self.episode_score += 1
                self.episode_fruits += 1
                self._spawn_food()
            else:
                # Remove tail if no food ate
                self.snake.pop()

        self.episode_steps += 1

        # Episode termination condition (optional: max steps)
        if self.episode_steps >= 1000:
            done = True

        return self._get_observation(), reward, done

    async def step_async(self, action: SnakeAction) -> Tuple[SnakeObservation, float, bool]:
        """Async version of step for OpenEnv compatibility."""
        return self.step(action)

    @property
    def state(self) -> State:
        """Get current environment state."""
        self._state.step_count = self.episode_steps
        return self._state

    def close(self):
        """Close and cleanup the environment."""
        pass

    def _spawn_food(self):
        """Spawn food at a random empty location."""
        while True:
            x = self.rng.randint(0, self.grid_width - 1)
            y = self.rng.randint(0, self.grid_height - 1)
            if (x, y) not in self.snake:
                self.food = (x, y)
                break

    def _get_observation(self) -> SnakeObservation:
        """
        Generate observation from current state.

        Returns:
            SnakeObservation with grid, observation, and episode stats
        """
        # Create grid representation
        grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]

        # Mark snake (head=2, body=1)
        for i, (x, y) in enumerate(self.snake):
            grid[y][x] = 2 if i == 0 else 1

        # Mark food (3)
        if self.food:
            x, y = self.food
            grid[y][x] = 3

        # Create observation (simple version: just use grid as observation)
        observation = [[[float(grid[y][x])] for x in range(self.grid_width)] for y in range(self.grid_height)]

        return SnakeObservation(
            grid=grid,
            observation=observation,
            episode_score=float(self.episode_score),
            episode_steps=self.episode_steps,
            episode_fruits=self.episode_fruits,
            episode_kills=0,
            alive=self.alive,
        )