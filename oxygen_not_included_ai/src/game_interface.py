# Placeholder for game_interface.py
# This module will handle communication with the game.

import asyncio
import websockets
import json
import logging
from websockets.exceptions import ConnectionClosed
from .models import ColonyState, GameEvent

class GameInterface:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.event_handlers = {}
        self.unknown_events = []
        self.current_state: ColonyState | None = None
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        while True:
            try:
                self.websocket = await websockets.connect(self.uri)  # type: ignore
                self.logger.info("Connected to the game server.")
                self.current_state = ColonyState.parse_obj(await self.get_game_state())
                asyncio.create_task(self.listen_for_events())
                break
            except Exception as e:
                self.logger.error(f"Connection failed: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def send_action(self, action):
        while True:
            if not self.websocket:
                await self.connect()
            try:
                await self.websocket.send(json.dumps(action))  # type: ignore
                response = await self.websocket.recv()  # type: ignore
                return json.loads(response)
            except ConnectionClosed as e:
                self.logger.warning(f"Connection closed: {e}. Reconnecting...")
                self.websocket = None
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise

    async def get_game_state(self):
        # In a real implementation, this would request the full game state
        # For now, it's a placeholder.
        while True:
            if not self.websocket:
                await self.connect()
            try:
                await self.websocket.send(json.dumps({"action": "get_state"}))  # type: ignore
                state = await self.websocket.recv()  # type: ignore
                return json.loads(state)
            except ConnectionClosed as e:
                self.logger.warning(f"Connection closed: {e}. Reconnecting...")
                self.websocket = None
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise

    def register_event_handler(self, event_type: str, handler):
        self.event_handlers[event_type] = handler

    async def listen_for_events(self):
        while True:
            if not self.websocket:
                await self.connect()
            try:
                message = await self.websocket.recv()  # type: ignore
                data = json.loads(message)
                if 'EventType' in data:
                    event = GameEvent.parse_obj(data)
                    if event.EventType in self.event_handlers:
                        await self.event_handlers[event.EventType](event)
                    if event.EventType == 'state_delta':
                        self.apply_delta(event.Payload)
                else:
                    self.unknown_events.append(data)
            except ConnectionClosed as e:
                self.logger.warning(f"Connection closed: {e}. Reconnecting...")
                self.websocket = None
                # Refresh full state on reconnect
                if self.websocket:
                    self.current_state = ColonyState.parse_obj(await self.get_game_state())
            except Exception as e:
                self.logger.error(f"Unexpected error in event listener: {e}")

    def apply_delta(self, delta: dict):
        if self.current_state:
            # Simple dict update, assume delta is compatible dict
            current_dict = self.current_state.dict()
            current_dict.update(delta)
            self.current_state = ColonyState.parse_obj(current_dict)

async def main():
    # Example usage
    game_interface = GameInterface("ws://localhost:8080")
    await game_interface.connect()
    # example_action = {"action": "Dig", "params": {"x": 10, "y": 5}}
    # result = await game_interface.send_action(example_action)
    # print(f"Action result: {result}")

if __name__ == "__main__":
    asyncio.run(main())