import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional
from threading import Thread
from queue import Queue, Empty

from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QTimer, QObject
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel, QSpinBox, QComboBox,
    QGroupBox, QSplitter, QTabWidget, QGridLayout, QCheckBox,
    QScrollArea, QMessageBox
)
from PySide6.QtGui import QTextCursor, QFont, QAction

import pyqtgraph as pg

# Import our API client
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oni_api_client import ApiClient, ColonyState


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApiWorkerThread(QThread):
    """Background thread for running asyncio event loop with ApiClient"""
    
    # Signals for thread-safe communication
    state_received = Signal(dict)
    event_received = Signal(dict)
    response_received = Signal(str, dict)
    error_occurred = Signal(str)
    connection_status_changed = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self.client: Optional[ApiClient] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.command_queue = Queue()
        self._running = False
        
    def run(self):
        """Run asyncio event loop in this thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self._running = True
        self.loop.run_until_complete(self._async_main())
        
    async def _async_main(self):
        """Main async function"""
        self.client = ApiClient()
        
        try:
            # Connect to servers
            await self.client.connect()
            self.connection_status_changed.emit(True)
            
            # Start event listener
            event_task = asyncio.create_task(self._listen_events())
            
            # Process commands
            while self._running:
                # Check for commands from GUI
                try:
                    command = self.command_queue.get_nowait()
                    asyncio.create_task(self._process_command(command))
                except Empty:
                    pass
                    
                await asyncio.sleep(0.1)
                
            event_task.cancel()
            
        except Exception as e:
            logger.error(f"API worker error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            await self.client.disconnect()
            self.connection_status_changed.emit(False)
            
    async def _listen_events(self):
        """Listen for events from the API"""
        while self._running:
            event = await self.client.get_events(timeout=1.0)
            if event:
                self.event_received.emit(event)
                
                # Special handling for state updates
                if event.get('type') == 'State.Update':
                    self.state_received.emit(event.get('payload', {}))
                    
    async def _process_command(self, command: dict):
        """Process a command from the GUI"""
        action = command.get('action')
        payload = command.get('payload', {})
        command_id = command.get('id', '')
        
        try:
            if action == 'State.Get':
                state = await self.client.get_state()
                self.response_received.emit(command_id, state.to_dict())
            elif action == 'Global.Build':
                success = await self.client.build(
                    payload['buildingId'],
                    payload['cellX'],
                    payload['cellY']
                )
                self.response_received.emit(command_id, {'success': success})
            elif action == 'Global.SetSpeed':
                success = await self.client.set_speed(payload['speed'])
                self.response_received.emit(command_id, {'success': success})
            elif action == 'Global.Pause':
                success = await self.client.pause()
                self.response_received.emit(command_id, {'success': success})
            elif action == 'Global.Resume':
                success = await self.client.resume()
                self.response_received.emit(command_id, {'success': success})
            elif action == 'Global.Dig':
                success = await self.client.dig(payload['cellX'], payload['cellY'])
                self.response_received.emit(command_id, {'success': success})
            elif action == 'Blueprint.Deploy':
                success = await self.client.deploy_blueprint(payload)
                self.response_received.emit(command_id, {'success': success})
            else:
                # Generic request
                response = await self.client.send_request(action, payload)
                self.response_received.emit(command_id, response)
                
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            self.error_occurred.emit(f"Command {action} failed: {str(e)}")
            
    def send_command(self, action: str, payload: dict = None) -> str:
        """Send a command to be processed"""
        import uuid
        command_id = str(uuid.uuid4())
        self.command_queue.put({
            'id': command_id,
            'action': action,
            'payload': payload or {}
        })
        return command_id
        
    def stop(self):
        """Stop the worker thread"""
        self._running = False


class CommandPanel(QWidget):
    """Left panel for sending commands"""
    
    command_sent = Signal(str, dict)
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Connection status
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        layout.addWidget(self.status_label)
        
        # Game control buttons
        control_group = QGroupBox("Game Control")
        control_layout = QGridLayout()
        
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(0, 3)
        self.speed_spin.setValue(1)
        self.set_speed_btn = QPushButton("Set Speed")
        
        control_layout.addWidget(self.pause_btn, 0, 0)
        control_layout.addWidget(self.resume_btn, 0, 1)
        control_layout.addWidget(QLabel("Speed:"), 1, 0)
        control_layout.addWidget(self.speed_spin, 1, 1)
        control_layout.addWidget(self.set_speed_btn, 1, 2)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Building commands
        build_group = QGroupBox("Building Commands")
        build_layout = QGridLayout()
        
        self.building_combo = QComboBox()
        self.building_combo.addItems([
            "Ladder", "Tile", "Door", "Bed", "ToiletFlush",
            "WashBasin", "Generator", "Battery", "Wire",
            "LiquidPump", "GasPump", "LiquidVent", "GasVent",
            "StorageLocker", "RationBox", "Electrolyzer"
        ])
        
        self.build_x_spin = QSpinBox()
        self.build_x_spin.setRange(-1000, 1000)
        self.build_y_spin = QSpinBox()
        self.build_y_spin.setRange(-1000, 1000)
        self.build_btn = QPushButton("Build")
        
        build_layout.addWidget(QLabel("Building:"), 0, 0)
        build_layout.addWidget(self.building_combo, 0, 1, 1, 2)
        build_layout.addWidget(QLabel("X:"), 1, 0)
        build_layout.addWidget(self.build_x_spin, 1, 1)
        build_layout.addWidget(QLabel("Y:"), 1, 2)
        build_layout.addWidget(self.build_y_spin, 1, 3)
        build_layout.addWidget(self.build_btn, 2, 0, 1, 4)
        
        build_group.setLayout(build_layout)
        layout.addWidget(build_group)
        
        # Dig commands
        dig_group = QGroupBox("Dig Commands")
        dig_layout = QGridLayout()
        
        self.dig_x_spin = QSpinBox()
        self.dig_x_spin.setRange(-1000, 1000)
        self.dig_y_spin = QSpinBox()
        self.dig_y_spin.setRange(-1000, 1000)
        self.dig_btn = QPushButton("Dig")
        self.cancel_dig_btn = QPushButton("Cancel Dig")
        
        dig_layout.addWidget(QLabel("X:"), 0, 0)
        dig_layout.addWidget(self.dig_x_spin, 0, 1)
        dig_layout.addWidget(QLabel("Y:"), 0, 2)
        dig_layout.addWidget(self.dig_y_spin, 0, 3)
        dig_layout.addWidget(self.dig_btn, 1, 0, 1, 2)
        dig_layout.addWidget(self.cancel_dig_btn, 1, 2, 1, 2)
        
        dig_group.setLayout(dig_layout)
        layout.addWidget(dig_group)
        
        # Get state button
        self.get_state_btn = QPushButton("Get Current State")
        layout.addWidget(self.get_state_btn)
        
        # Command log
        log_group = QGroupBox("Command Log")
        log_layout = QVBoxLayout()
        
        self.command_log = QTextEdit()
        self.command_log.setReadOnly(True)
        self.command_log.setMaximumHeight(200)
        log_layout.addWidget(self.command_log)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Connect signals
        self._connect_signals()
        
    def _connect_signals(self):
        self.pause_btn.clicked.connect(lambda: self.command_sent.emit("Global.Pause", {}))
        self.resume_btn.clicked.connect(lambda: self.command_sent.emit("Global.Resume", {}))
        self.set_speed_btn.clicked.connect(
            lambda: self.command_sent.emit("Global.SetSpeed", {"speed": self.speed_spin.value()})
        )
        self.build_btn.clicked.connect(self._on_build)
        self.dig_btn.clicked.connect(self._on_dig)
        self.cancel_dig_btn.clicked.connect(self._on_cancel_dig)
        self.get_state_btn.clicked.connect(lambda: self.command_sent.emit("State.Get", {}))
        
    def _on_build(self):
        self.command_sent.emit("Global.Build", {
            "buildingId": self.building_combo.currentText(),
            "cellX": self.build_x_spin.value(),
            "cellY": self.build_y_spin.value()
        })
        
    def _on_dig(self):
        self.command_sent.emit("Global.Dig", {
            "cellX": self.dig_x_spin.value(),
            "cellY": self.dig_y_spin.value()
        })
        
    def _on_cancel_dig(self):
        self.command_sent.emit("Global.CancelDig", {
            "cellX": self.dig_x_spin.value(),
            "cellY": self.dig_y_spin.value()
        })
        
    def log_command(self, action: str, payload: dict):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.command_log.append(f"[{timestamp}] {action}: {json.dumps(payload, indent=2)}")
        
    def set_connection_status(self, connected: bool):
        if connected:
            self.status_label.setText("Status: Connected")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self.status_label.setText("Status: Disconnected")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")


class EventPanel(QWidget):
    """Right panel for events and training dashboard"""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Events tab
        events_widget = QWidget()
        events_layout = QVBoxLayout()
        
        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        events_layout.addWidget(self.event_log)
        
        self.clear_events_btn = QPushButton("Clear Events")
        self.clear_events_btn.clicked.connect(self.event_log.clear)
        events_layout.addWidget(self.clear_events_btn)
        
        events_widget.setLayout(events_layout)
        self.tabs.addTab(events_widget, "Events")
        
        # Training dashboard tab (placeholder)
        training_widget = self._create_training_dashboard()
        self.tabs.addTab(training_widget, "Training Dashboard")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
    def _create_training_dashboard(self) -> QWidget:
        """Create the training dashboard widget"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_training_btn = QPushButton("Start Training")
        self.pause_training_btn = QPushButton("Pause Training")
        self.stop_training_btn = QPushButton("Stop Training")
        self.save_model_btn = QPushButton("Save Model")
        self.load_model_btn = QPushButton("Load Model")
        
        control_layout.addWidget(self.start_training_btn)
        control_layout.addWidget(self.pause_training_btn)
        control_layout.addWidget(self.stop_training_btn)
        control_layout.addWidget(self.save_model_btn)
        control_layout.addWidget(self.load_model_btn)
        
        layout.addLayout(control_layout)
        
        # Create plots using pyqtgraph
        self.reward_plot = pg.PlotWidget(title="Episode Rewards")
        self.reward_plot.setLabel('left', 'Reward')
        self.reward_plot.setLabel('bottom', 'Episode')
        layout.addWidget(self.reward_plot)
        
        self.loss_plot = pg.PlotWidget(title="Training Loss")
        self.loss_plot.setLabel('left', 'Loss')
        self.loss_plot.setLabel('bottom', 'Step')
        layout.addWidget(self.loss_plot)
        
        # Statistics display
        stats_group = QGroupBox("Training Statistics")
        stats_layout = QGridLayout()
        
        self.episode_label = QLabel("Episode: 0")
        self.step_label = QLabel("Step: 0")
        self.reward_label = QLabel("Avg Reward: 0.0")
        self.loss_label = QLabel("Avg Loss: 0.0")
        
        stats_layout.addWidget(self.episode_label, 0, 0)
        stats_layout.addWidget(self.step_label, 0, 1)
        stats_layout.addWidget(self.reward_label, 1, 0)
        stats_layout.addWidget(self.loss_label, 1, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        widget.setLayout(layout)
        return widget
        
    def log_event(self, event: dict):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        event_type = event.get('type', 'Unknown')
        self.event_log.append(f"[{timestamp}] {event_type}: {json.dumps(event, indent=2)}")
        
        # Auto-scroll to bottom
        cursor = self.event_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.event_log.setTextCursor(cursor)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.api_worker = ApiWorkerThread()
        self._init_ui()
        self._connect_signals()
        
        # Start API worker thread
        self.api_worker.start()
        
    def _init_ui(self):
        self.setWindowTitle("ONI AI Debugger")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Create panels
        self.command_panel = CommandPanel()
        self.event_panel = EventPanel()
        
        # Add panels to splitter
        splitter.addWidget(self.command_panel)
        splitter.addWidget(self.event_panel)
        splitter.setSizes([500, 900])
        
        # Main layout
        layout = QHBoxLayout()
        layout.addWidget(splitter)
        central_widget.setLayout(layout)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
    def _create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        clear_logs_action = QAction("Clear All Logs", self)
        clear_logs_action.triggered.connect(self._clear_all_logs)
        tools_menu.addAction(clear_logs_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _connect_signals(self):
        # Connect command panel signals
        self.command_panel.command_sent.connect(self._on_command_sent)
        
        # Connect API worker signals
        self.api_worker.state_received.connect(self._on_state_received)
        self.api_worker.event_received.connect(self._on_event_received)
        self.api_worker.response_received.connect(self._on_response_received)
        self.api_worker.error_occurred.connect(self._on_error)
        self.api_worker.connection_status_changed.connect(
            self.command_panel.set_connection_status
        )
        
    @Slot(str, dict)
    def _on_command_sent(self, action: str, payload: dict):
        """Handle command sent from command panel"""
        self.command_panel.log_command(action, payload)
        command_id = self.api_worker.send_command(action, payload)
        self.statusBar().showMessage(f"Sent command: {action}")
        
    @Slot(dict)
    def _on_state_received(self, state_data: dict):
        """Handle state update from API"""
        self.event_panel.log_event({"type": "State.Update", "payload": state_data})
        
    @Slot(dict)
    def _on_event_received(self, event: dict):
        """Handle event from API"""
        self.event_panel.log_event(event)
        
    @Slot(str, dict)
    def _on_response_received(self, command_id: str, response: dict):
        """Handle command response from API"""
        self.command_panel.log_command("Response", response)
        self.statusBar().showMessage("Command completed")
        
    @Slot(str)
    def _on_error(self, error_msg: str):
        """Handle error from API"""
        QMessageBox.warning(self, "API Error", error_msg)
        self.statusBar().showMessage(f"Error: {error_msg}")
        
    def _clear_all_logs(self):
        """Clear all log windows"""
        self.command_panel.command_log.clear()
        self.event_panel.event_log.clear()
        
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About ONI AI Debugger",
            "ONI AI Debugger v0.1.0\n\n"
            "A debugging and control interface for Oxygen Not Included AI agents.\n\n"
            "Built with PySide6 and asyncio."
        )
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.api_worker.stop()
        self.api_worker.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()