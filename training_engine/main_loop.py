import asyncio
import logging
import json
import socket
from typing import Optional, Dict, Any
from datetime import datetime
import pickle

from oni_api_client import ApiClient, ColonyState
from .agents import BaseAgent, RuleBasedAgent, DRLAgent
from .reward_functions import get_reward_function


logger = logging.getLogger(__name__)


class TrainingLoop:
    """Main training loop for AI agents"""
    
    def __init__(self, 
                 agent: BaseAgent,
                 reward_function_name: str = "balanced",
                 gui_host: str = "localhost",
                 gui_port: int = 9999):
        
        self.agent = agent
        self.reward_function = get_reward_function(reward_function_name)
        self.api_client: Optional[ApiClient] = None
        
        # Training state
        self.current_state: Optional[ColonyState] = None
        self.previous_state: Optional[ColonyState] = None
        self.episode_num = 0
        self.step_num = 0
        self.is_training = False
        
        # GUI communication
        self.gui_host = gui_host
        self.gui_port = gui_port
        self.gui_socket: Optional[socket.socket] = None
        
        # Metrics
        self.episode_rewards = []
        self.episode_lengths = []
        self.current_episode_reward = 0.0
        self.current_episode_length = 0
        
    async def initialize(self):
        """Initialize the training loop"""
        logger.info("Initializing training loop...")
        
        # Connect to API
        self.api_client = ApiClient()
        await self.api_client.connect()
        
        # Try to connect to GUI
        try:
            self.gui_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.gui_socket.connect((self.gui_host, self.gui_port))
            self.gui_socket.setblocking(False)
            logger.info(f"Connected to GUI at {self.gui_host}:{self.gui_port}")
        except Exception as e:
            logger.warning(f"Could not connect to GUI: {e}")
            self.gui_socket = None
            
    async def run(self):
        """Main training loop"""
        await self.initialize()
        
        self.is_training = True
        logger.info("Starting training loop...")
        
        try:
            while self.is_training:
                # Wait for state update event
                event = await self.api_client.get_events(timeout=1.0)
                
                if event and event.get('type') == 'State.Update':
                    await self._process_state_update(event.get('payload', {}))
                    
                # Check for GUI commands
                await self._check_gui_commands()
                
        except KeyboardInterrupt:
            logger.info("Training interrupted by user")
        except Exception as e:
            logger.error(f"Training loop error: {e}")
        finally:
            await self.cleanup()
            
    async def _process_state_update(self, state_data: dict):
        """Process a state update from the game"""
        # Convert to ColonyState
        new_state = ColonyState.from_dict(state_data)
        
        # Store previous state
        self.previous_state = self.current_state
        self.current_state = new_state
        
        # Skip first state (no previous state for comparison)
        if self.previous_state is None:
            self.agent.observe(new_state)
            return
            
        # Execute training step
        await self._training_step()
        
    async def _training_step(self):
        """Execute one training step"""
        # 1. Perception - Agent observes current state
        self.agent.observe(self.current_state)
        
        # 2. Decision - Agent decides on action
        action = self.agent.decide_action()
        
        # 3. Action - Execute the action
        if action['action'] != 'noop':
            await self._execute_action(action)
            
        # 4. Reward - Calculate reward
        reward = self.reward_function(self.current_state, self.previous_state)
        
        # 5. Learning - Agent learns from experience
        done = self._check_episode_done()
        self.agent.learn(
            self.previous_state,
            action,
            reward,
            self.current_state,
            done
        )
        
        # Update metrics
        self.current_episode_reward += reward
        self.current_episode_length += 1
        self.step_num += 1
        
        # Send metrics to GUI
        await self._send_metrics_to_gui()
        
        # Check for episode end
        if done:
            await self._end_episode()
            
    async def _execute_action(self, action: Dict[str, Any]):
        """Execute an action through the API"""
        try:
            action_type = action.get('action')
            payload = action.get('payload', {})
            
            if action_type == 'Global.Build':
                await self.api_client.build(
                    payload['buildingId'],
                    payload['cellX'],
                    payload['cellY']
                )
            elif action_type == 'Global.Dig':
                await self.api_client.dig(
                    payload['cellX'],
                    payload['cellY']
                )
            elif action_type == 'Global.SetPriority':
                await self.api_client.set_priority(
                    payload['cellX'],
                    payload['cellY'],
                    payload['priority']
                )
            elif action_type == 'Blueprint.Deploy':
                await self.api_client.deploy_blueprint(payload)
            else:
                # Generic action
                await self.api_client.send_request(action_type, payload)
                
        except Exception as e:
            logger.error(f"Failed to execute action {action}: {e}")
            
    def _check_episode_done(self) -> bool:
        """Check if the current episode should end"""
        # Episode ends if:
        # - All duplicants are dead
        # - Maximum steps reached
        # - Manual reset requested
        
        if not self.current_state.duplicants:
            return True
            
        if self.current_episode_length >= 1000:  # Max steps per episode
            return True
            
        return False
        
    async def _end_episode(self):
        """Handle end of episode"""
        logger.info(f"Episode {self.episode_num} ended. "
                   f"Reward: {self.current_episode_reward:.2f}, "
                   f"Length: {self.current_episode_length}")
        
        # Store metrics
        self.episode_rewards.append(self.current_episode_reward)
        self.episode_lengths.append(self.current_episode_length)
        
        # Reset for next episode
        self.episode_num += 1
        self.current_episode_reward = 0.0
        self.current_episode_length = 0
        self.agent.reset()
        
        # Could trigger game reset here if needed
        # await self.api_client.reset_game()
        
    async def _send_metrics_to_gui(self):
        """Send training metrics to GUI"""
        if not self.gui_socket:
            return
            
        metrics = {
            "episode": self.episode_num,
            "step": self.step_num,
            "reward": self.current_episode_reward,
            "episode_length": self.current_episode_length,
            "avg_reward": sum(self.episode_rewards[-10:]) / min(10, len(self.episode_rewards)) if self.episode_rewards else 0,
            "agent_stats": self.agent.get_stats()
        }
        
        try:
            message = json.dumps(metrics) + "\n"
            self.gui_socket.send(message.encode())
        except Exception as e:
            logger.debug(f"Failed to send metrics to GUI: {e}")
            
    async def _check_gui_commands(self):
        """Check for commands from GUI"""
        if not self.gui_socket:
            return
            
        try:
            data = self.gui_socket.recv(1024)
            if data:
                command = json.loads(data.decode())
                await self._handle_gui_command(command)
        except socket.error:
            pass  # No data available
        except Exception as e:
            logger.debug(f"Error receiving GUI command: {e}")
            
    async def _handle_gui_command(self, command: dict):
        """Handle a command from the GUI"""
        cmd_type = command.get('type')
        
        if cmd_type == 'pause':
            self.is_training = False
            logger.info("Training paused by GUI")
        elif cmd_type == 'resume':
            self.is_training = True
            logger.info("Training resumed by GUI")
        elif cmd_type == 'save_model':
            path = command.get('path', f"model_{self.episode_num}.pkl")
            self.save_agent(path)
        elif cmd_type == 'load_model':
            path = command.get('path')
            if path:
                self.load_agent(path)
                
    def save_agent(self, path: str):
        """Save the agent to disk"""
        try:
            if hasattr(self.agent, 'save'):
                self.agent.save(path)
            else:
                with open(path, 'wb') as f:
                    pickle.dump(self.agent, f)
            logger.info(f"Agent saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save agent: {e}")
            
    def load_agent(self, path: str):
        """Load an agent from disk"""
        try:
            if hasattr(self.agent, 'load'):
                self.agent.load(path)
            else:
                with open(path, 'rb') as f:
                    self.agent = pickle.load(f)
            logger.info(f"Agent loaded from {path}")
        except Exception as e:
            logger.error(f"Failed to load agent: {e}")
            
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up training loop...")
        
        if self.api_client:
            await self.api_client.disconnect()
            
        if self.gui_socket:
            self.gui_socket.close()


async def main():
    """Main entry point for training"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ONI AI Training Engine")
    parser.add_argument('--agent', choices=['rule', 'drl'], default='rule',
                       help='Agent type to use')
    parser.add_argument('--reward', choices=['survival', 'efficiency', 'expansion', 'balanced'],
                       default='balanced', help='Reward function to use')
    parser.add_argument('--gui-host', default='localhost',
                       help='GUI host for metrics')
    parser.add_argument('--gui-port', type=int, default=9999,
                       help='GUI port for metrics')
    
    args = parser.parse_args()
    
    # Create agent
    if args.agent == 'rule':
        agent = RuleBasedAgent()
    else:
        agent = DRLAgent()
        
    # Create and run training loop
    loop = TrainingLoop(
        agent=agent,
        reward_function_name=args.reward,
        gui_host=args.gui_host,
        gui_port=args.gui_port
    )
    
    await loop.run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())