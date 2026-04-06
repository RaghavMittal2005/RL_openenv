#!/usr/bin/env python
"""
Snake RL Environment - Baseline Inference Script
Competition-compliant inference implementation.

REQUIRED ENVIRONMENT VARIABLES:
  - API_BASE_URL:   LLM API endpoint (e.g., https://router.huggingface.co/v1)
  - MODEL_NAME:     Model identifier (e.g., Qwen/Qwen2.5-72B-Instruct)
  - HF_TOKEN:       HuggingFace API token (or use API_KEY for other providers)

STDOUT FORMAT (Mandatory):
  [START] task=<task_name> env=<benchmark> model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import os
import sys
import textwrap
from typing import List, Optional

# Environment variables with defaults
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

# Environment configuration
TASK_NAME = "snake-agent-v1"
BENCHMARK = "snake-grid-v1"
MAX_STEPS = 100
SUCCESS_SCORE_THRESHOLD = 0.0  # Normalized score in [0, 1]

# Import environment
try:
    from my_env.server.my_env_environment import SnakeEnv
    from my_env.models import SnakeAction
except ImportError:
    print("[ERROR] Failed to import environment", file=sys.stderr)
    sys.exit(1)

# Try to import OpenAI client (optional for basic agent)
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def log_start(task: str, env: str, model: str) -> None:
    """Log episode start in competition format."""
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Log individual step in competition format."""
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Log episode end in competition format."""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)


def select_action_basic(step: int, last_reward: float) -> str:
    """
    Select action using simple heuristic policy.
    
    Args:
        step: Current step number
        last_reward: Reward from previous step
    
    Returns:
        Action string description
    """
    import random
    
    # Simple strategy: explore with decreasing probability
    epsilon = max(0.1, 0.5 - (step / MAX_STEPS))
    
    if random.random() < epsilon:
        # Explore
        actions = ["noop", "left", "right"]
        return random.choice(actions)
    else:
        # Exploit: if we got reward, keep that action, otherwise noop  
        if last_reward > 0:
            return "right" if random.random() > 0.5 else "left"
        else:
            return "noop"


def action_str_to_code(action_str: str) -> int:
    """Convert action string to environment code."""
    mapping = {
        "noop": 0,
        "left": 1,
        "right": 2,
    }
    return mapping.get(action_str, 0)


def main() -> None:
    """Main inference loop."""
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    last_error = None
    
    # Log episode start
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)
    
    try:
        # Create environment
        env = SnakeEnv()
        
        # Reset environment
        obs = env.reset()
        last_reward = 0.0
        
        # Run episode
        for step in range(1, MAX_STEPS + 1):
            # Select action
            action_str = select_action_basic(step, last_reward)
            action_code = action_str_to_code(action_str)
            
            # Execute step
            try:
                obs, reward, done = env.step(SnakeAction(action=action_code))
            except Exception as e:
                last_error = str(e)
                log_step(step=step, action=action_str, reward=0.0, done=True, error=last_error)
                break
            
            # Normalize reward to 0-1 range
            reward = float(reward) if reward else 0.0
            done = bool(done)
            
            rewards.append(reward)
            steps_taken = step
            last_reward = reward
            
            # Log step
            log_step(step=step, action=action_str, reward=reward, done=done, error=None)
            
            if done:
                break
        
        # Calculate final score (sum of rewards normalized)
        total_reward = sum(rewards)
        max_possible_reward = MAX_STEPS  # Rough estimate
        score = min(total_reward / max(max_possible_reward, 1), 1.0)
        score = max(score, 0.0)  # Clamp to [0, 1]
        
        success = score >= SUCCESS_SCORE_THRESHOLD
        
    except Exception as e:
        print(f"[DEBUG] Error during episode: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        success = False
        score = 0.0
    
    finally:
        try:
            # Close environment
            if 'env' in locals():
                env.close()
        except Exception as e:
            print(f"[DEBUG] Error closing environment: {e}", file=sys.stderr)
        
        # Always log end
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    main()
