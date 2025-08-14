import asyncio
import json
import logging
import uuid
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed

from .models import ColonyState


logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, command_url: str = "ws://localhost:8080", 
                 event_url: str = "ws://localhost:8181"):
        self.command_url = command_url
        self.event_url = event_url
        
        self.command_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.event_ws: Optional[websockets.WebSocketClientProtocol] = None
        
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        
        self._running = False
        self._reconnect_delay = 5.0
        self._command_task: Optional[asyncio.Task] = None
        self._event_task: Optional[asyncio.Task] = None
        
    async def connect(self):
        """Establish connections to both WebSocket servers"""
        self._running = True
        self._command_task = asyncio.create_task(self._maintain_command_connection())
        self._event_task = asyncio.create_task(self._maintain_event_connection())
        
    async def disconnect(self):
        """Gracefully disconnect from both servers"""
        self._running = False
        
        if self.command_ws:
            await self.command_ws.close()
        if self.event_ws:
            await self.event_ws.close()
            
        if self._command_task:
            self._command_task.cancel()
        if self._event_task:
            self._event_task.cancel()
            
        # Clear pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()
        
    async def _maintain_command_connection(self):
        """Maintain persistent connection to command server with auto-reconnect"""
        while self._running:
            try:
                logger.info(f"Connecting to command server: {self.command_url}")
                async with websockets.connect(self.command_url) as websocket:
                    self.command_ws = websocket
                    logger.info("Command server connected")
                    
                    await self._handle_command_messages()
                    
            except ConnectionClosed:
                logger.warning("Command server connection closed")
            except Exception as e:
                logger.error(f"Command server error: {e}")
            finally:
                self.command_ws = None
                
            if self._running:
                logger.info(f"Reconnecting to command server in {self._reconnect_delay} seconds...")
                await asyncio.sleep(self._reconnect_delay)
                
    async def _maintain_event_connection(self):
        """Maintain persistent connection to event server with auto-reconnect"""
        while self._running:
            try:
                logger.info(f"Connecting to event server: {self.event_url}")
                async with websockets.connect(self.event_url) as websocket:
                    self.event_ws = websocket
                    logger.info("Event server connected")
                    
                    await self._handle_event_messages()
                    
            except ConnectionClosed:
                logger.warning("Event server connection closed")
            except Exception as e:
                logger.error(f"Event server error: {e}")
            finally:
                self.event_ws = None
                
            if self._running:
                logger.info(f"Reconnecting to event server in {self._reconnect_delay} seconds...")
                await asyncio.sleep(self._reconnect_delay)
                
    async def _handle_command_messages(self):
        """Process incoming messages from command server"""
        async for message in self.command_ws:
            try:
                data = json.loads(message)
                request_id = data.get('requestId')
                
                if request_id and request_id in self.pending_requests:
                    future = self.pending_requests.pop(request_id)
                    if not future.done():
                        future.set_result(data)
                else:
                    logger.warning(f"Received response with unknown requestId: {request_id}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse command response: {e}")
            except Exception as e:
                logger.error(f"Error handling command message: {e}")
                
    async def _handle_event_messages(self):
        """Process incoming messages from event server"""
        async for message in self.event_ws:
            try:
                data = json.loads(message)
                await self.event_queue.put(data)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse event: {e}")
            except Exception as e:
                logger.error(f"Error handling event message: {e}")
                
    async def send_request(self, action: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a request to the command server and wait for response
        
        Args:
            action: The action to perform
            payload: Optional payload data
            
        Returns:
            The response from the server
        """
        if not self.command_ws:
            raise ConnectionError("Not connected to command server")
            
        request_id = str(uuid.uuid4())
        request = {
            "requestId": request_id,
            "action": action,
            "payload": payload or {}
        }
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        try:
            # Send request
            await self.command_ws.send(json.dumps(request))
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=30.0)
            return response
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise TimeoutError(f"Request {request_id} timed out")
        except Exception as e:
            self.pending_requests.pop(request_id, None)
            raise e
            
    # High-level API methods
    
    async def get_state(self) -> ColonyState:
        """Get the current colony state"""
        response = await self.send_request("State.Get")
        return ColonyState.from_dict(response.get('payload', {}))
        
    async def build(self, building_id: str, cell_x: int, cell_y: int) -> bool:
        """
        Place a building at specified cell
        
        Args:
            building_id: The building type ID
            cell_x: X coordinate of the cell
            cell_y: Y coordinate of the cell
            
        Returns:
            True if successful
        """
        response = await self.send_request("Global.Build", {
            "buildingId": building_id,
            "cell": {"x": cell_x, "y": cell_y}
        })
        return response.get('success', False)
        
    async def cancel_build(self, cell_x: int, cell_y: int) -> bool:
        """Cancel building at specified cell"""
        response = await self.send_request("Global.CancelBuild", {
            "cell": {"x": cell_x, "y": cell_y}
        })
        return response.get('success', False)
        
    async def set_priority(self, cell_x: int, cell_y: int, priority: int) -> bool:
        """Set priority for a cell (1-9)"""
        response = await self.send_request("Global.SetPriority", {
            "cell": {"x": cell_x, "y": cell_y},
            "priority": max(1, min(9, priority))
        })
        return response.get('success', False)
        
    async def deploy_blueprint(self, blueprint: Dict[str, Any]) -> bool:
        """
        Deploy a building blueprint
        
        Args:
            blueprint: Blueprint definition containing buildings and their positions
            
        Returns:
            True if successful
        """
        response = await self.send_request("Blueprint.Deploy", blueprint)
        return response.get('success', False)
        
    async def set_speed(self, speed: int) -> bool:
        """
        Set game speed (0=pause, 1=normal, 2=fast, 3=ultra)
        
        Args:
            speed: Speed level (0-3)
            
        Returns:
            True if successful
        """
        response = await self.send_request("Global.SetSpeed", {
            "speed": max(0, min(3, speed))
        })
        return response.get('success', False)
        
    async def pause(self) -> bool:
        """Pause the game"""
        return await self.set_speed(0)
        
    async def resume(self) -> bool:
        """Resume the game at normal speed"""
        return await self.set_speed(1)
        
    async def dig(self, cell_x: int, cell_y: int) -> bool:
        """Mark a cell for digging"""
        response = await self.send_request("Global.Dig", {
            "cell": {"x": cell_x, "y": cell_y}
        })
        return response.get('success', False)
        
    async def cancel_dig(self, cell_x: int, cell_y: int) -> bool:
        """Cancel dig order for a cell"""
        response = await self.send_request("Global.CancelDig", {
            "cell": {"x": cell_x, "y": cell_y}
        })
        return response.get('success', False)
        
    async def get_available_buildings(self) -> list:
        """Get list of available building types"""
        response = await self.send_request("Info.GetBuildings")
        return response.get('payload', {}).get('buildings', [])
        
    async def get_events(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Get next event from the event queue
        
        Args:
            timeout: Maximum time to wait for an event
            
        Returns:
            Event data or None if timeout
        """
        try:
            return await asyncio.wait_for(self.event_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None