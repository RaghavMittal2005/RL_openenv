# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the My Env Environment.

This module creates an HTTP server that exposes the MyEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception:
    try:
        from openenv.env_server.http_server import create_app
    except Exception:
        try:
            # Try importing just the openenv package to verify it's installed
            import openenv
            print("openenv is installed but create_app import failed, creating minimal FastAPI app")
            from fastapi import FastAPI
            from fastapi.middleware.cors import CORSMiddleware
            
            def create_app(env_class, action_class, observation_class, env_name="env", **kwargs):
                """Minimal create_app implementation"""
                app = FastAPI(title=env_name)
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
                
                # Store for lazy initialization
                env_instances = {}
                
                @app.post("/reset")
                def reset():
                    try:
                        # Create new environment for this session
                        env = env_class()
                        obs = env.reset()
                        # Store environment instance
                        env_instances["current"] = env
                        result = obs.dict() if hasattr(obs, 'dict') else obs
                        return {"observation": result}
                    except Exception as e:
                        print(f"Error in /reset: {e}")
                        return {"error": str(e)}, 500
                
                @app.post("/step")
                def step(action: action_class):
                    try:
                        env = env_instances.get("current")
                        if not env:
                            return {"error": "Environment not initialized, call /reset first"}, 400
                        
                        obs, reward, done = env.step(action)
                        result = obs.dict() if hasattr(obs, 'dict') else obs
                        return {
                            "observation": result,
                            "reward": float(reward),
                            "done": bool(done)
                        }
                    except Exception as e:
                        print(f"Error in /step: {e}")
                        return {"error": str(e)}, 500
                
                @app.get("/state")
                def state():
                    return {"status": "running"}
                
                @app.get("/schema")
                def schema():
                    try:
                        return {
                            "action_schema": action_class.schema() if hasattr(action_class, 'schema') else {},
                            "observation_schema": observation_class.schema() if hasattr(observation_class, 'schema') else {}
                        }
                    except Exception as e:
                        print(f"Error in /schema: {e}")
                        return {"error": str(e)}, 500
                
                return app
        except Exception as e:
            raise ImportError(
                f"Failed to import or create FastAPI app: {e}"
            ) from e

# Resolve model/environment imports in all execution contexts (module, script, uv run, python -m)
try:
    from my_env.models import SnakeAction as MyAction, SnakeObservation as MyObservation
    from my_env.server.my_env_environment import SnakeEnv as MyEnvironment
except Exception:
    try:
        from ..models import SnakeAction as MyAction, SnakeObservation as MyObservation
        from .my_env_environment import SnakeEnv as MyEnvironment
    except Exception:
        from models import SnakeAction as MyAction, SnakeObservation as MyObservation
        from server.my_env_environment import SnakeEnv as MyEnvironment


# Create the app with web interface and README integration
app = create_app(
    MyEnvironment,
    MyAction,
    MyObservation,
    env_name="my_env",
    max_concurrent_envs=1,  # increase this number to allow more concurrent WebSocket sessions
)


def main(host: str = "127.0.0.1", port: int = 8000):
    """
    Entry point for direct execution via uv run or python -m.

    This function enables running the server without Docker:
        uv run --project . server
        uv run --project . server --port 8001
        python -m my_env.server.app

    Args:
        host: Host address to bind to (default: "0.0.0.0")
        port: Port number to listen on (default: 8000)

    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn my_env.server.app:app --workers 4
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
