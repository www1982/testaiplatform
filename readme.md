我将为您创建一个完整的 PyDev-Toolkit 应用程序。让我按照您的要求，逐个模块生成代码。

## 项目结构

```
PyDev-Toolkit/
├── desktop_app/
│   ├── __init__.py
│   └── main.py
├── websocket_tool/
│   ├── __init__.py
│   ├── connection_window.py
│   ├── websocket_thread.py
│   ├── signal_bridge.py
│   └── views/
│       ├── __init__.py
│       ├── base_view.py
│       ├── json_tree_view.py
│       └── raw_log_view.py
├── conda_manager/
│   ├── __init__.py
│   ├── conda_service.py
│   └── conda_widget.py
├── vscode_integration/
│   ├── __init__.py
│   └── manager.py
├── utils/
│   ├── __init__.py
│   └── logger.py
├── environment.yml
├── requirements.txt
├── main.py
└── .github/
    └── workflows/
        └── build.yml
```

## 第一部分：应用程序核心与主窗口

### desktop_app/**init**.py

```python
"""PyDev-Toolkit Desktop Application"""
__version__ = "1.0.0"
```

### desktop_app/main.py

```python
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMdiArea, QMenuBar,
    QStatusBar, QMenu, QDialog, QVBoxLayout, QFileDialog,
    QLabel, QPushButton, QHBoxLayout, QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QIcon

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from websocket_tool.connection_window import ConnectionWindow
from conda_manager.conda_widget import CondaManagerWidget
from conda_manager.conda_service import CondaService
from vscode_integration.manager import VSCodeManager
from utils.logger import setup_logger


class VSCodeConfigDialog(QDialog):
    """Dialog for configuring VS Code workspace with Conda environment"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure VS Code Workspace")
        self.setModal(True)
        self.setMinimumWidth(500)

        self.conda_service = CondaService()
        self.vscode_manager = VSCodeManager()
        self.setup_ui()
        self.load_environments()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Project path selection
        project_layout = QHBoxLayout()
        project_layout.addWidget(QLabel("Project Path:"))
        self.project_path_edit = QLineEdit()
        project_layout.addWidget(self.project_path_edit)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_project)
        project_layout.addWidget(self.browse_btn)
        layout.addLayout(project_layout)

        # Environment selection
        env_layout = QHBoxLayout()
        env_layout.addWidget(QLabel("Conda Environment:"))
        self.env_combo = QComboBox()
        env_layout.addWidget(self.env_combo)
        layout.addLayout(env_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.open_btn = QPushButton("Open in VS Code")
        self.open_btn.clicked.connect(self.open_vscode)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.open_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def browse_project(self):
        path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if path:
            self.project_path_edit.setText(path)

    def load_environments(self):
        environments = self.conda_service.list_environments_sync()
        self.env_combo.addItems([env['name'] for env in environments])

    def open_vscode(self):
        project_path = self.project_path_edit.text()
        env_name = self.env_combo.currentText()

        if not project_path:
            return

        self.vscode_manager.open_project_with_env(project_path, env_name)
        self.accept()


class MainWindow(QMainWindow):
    """Main application window with MDI support"""

    def __init__(self):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.setWindowTitle("PyDev-Toolkit - Python Developer Toolkit")
        self.setGeometry(100, 100, 1400, 900)

        # Initialize MDI area
        self.mdi_area = QMdiArea()
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setCentralWidget(self.mdi_area)

        # Setup UI components
        self.setup_menu_bar()
        self.setup_status_bar()

        # Window counter for unique naming
        self.ws_window_counter = 0

        self.logger.info("MainWindow initialized successfully")

    def setup_menu_bar(self):
        """Create and configure the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_ws_action = QAction("&New WebSocket Connection", self)
        new_ws_action.setShortcut("Ctrl+N")
        new_ws_action.setStatusTip("Create a new WebSocket connection")
        new_ws_action.triggered.connect(self.new_websocket_connection)
        file_menu.addAction(new_ws_action)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        conda_manager_action = QAction("&Conda Environment Manager", self)
        conda_manager_action.setShortcut("Ctrl+E")
        conda_manager_action.setStatusTip("Manage Conda environments")
        conda_manager_action.triggered.connect(self.open_conda_manager)
        tools_menu.addAction(conda_manager_action)

        tools_menu.addSeparator()

        vscode_config_action = QAction("Configure &VS Code Workspace", self)
        vscode_config_action.setShortcut("Ctrl+Shift+V")
        vscode_config_action.setStatusTip("Configure VS Code with Conda environment")
        vscode_config_action.triggered.connect(self.configure_vscode)
        tools_menu.addAction(vscode_config_action)

        # Window menu
        window_menu = menubar.addMenu("&Window")

        cascade_action = QAction("&Cascade", self)
        cascade_action.setStatusTip("Cascade windows")
        cascade_action.triggered.connect(self.mdi_area.cascadeSubWindows)
        window_menu.addAction(cascade_action)

        tile_action = QAction("&Tile", self)
        tile_action.setStatusTip("Tile windows")
        tile_action.triggered.connect(self.mdi_area.tileSubWindows)
        window_menu.addAction(tile_action)

        window_menu.addSeparator()

        close_all_action = QAction("Close &All", self)
        close_all_action.setStatusTip("Close all windows")
        close_all_action.triggered.connect(self.mdi_area.closeAllSubWindows)
        window_menu.addAction(close_all_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.setStatusTip("About PyDev-Toolkit")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        """Create and configure the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Add permanent widget to show connection count
        self.connection_label = QLabel("Connections: 0")
        self.status_bar.addPermanentWidget(self.connection_label)

        # Update connection count periodically
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_connection_count)
        self.update_timer.start(1000)  # Update every second

    def new_websocket_connection(self):
        """Create a new WebSocket connection window"""
        self.ws_window_counter += 1
        window = ConnectionWindow(f"WebSocket Connection #{self.ws_window_counter}")
        self.mdi_area.addSubWindow(window)
        window.show()
        self.logger.info(f"Created new WebSocket connection window #{self.ws_window_counter}")

    def open_conda_manager(self):
        """Open the Conda environment manager dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Conda Environment Manager")
        dialog.setModal(True)
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout()
        conda_widget = CondaManagerWidget(dialog)
        layout.addWidget(conda_widget)
        dialog.setLayout(layout)

        dialog.exec()
        self.logger.info("Opened Conda environment manager")

    def configure_vscode(self):
        """Open VS Code configuration dialog"""
        dialog = VSCodeConfigDialog(self)
        dialog.exec()
        self.logger.info("Opened VS Code configuration dialog")

    def show_about(self):
        """Show about dialog"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About PyDev-Toolkit",
            "PyDev-Toolkit v1.0.0\n\n"
            "A comprehensive Python development toolkit featuring:\n"
            "• WebSocket debugging with pluggable views\n"
            "• Conda environment management\n"
            "• VS Code workspace configuration\n\n"
            "Built with Python and PySide6"
        )

    def update_connection_count(self):
        """Update the connection count in status bar"""
        count = len([w for w in self.mdi_area.subWindowList()
                    if isinstance(w.widget(), ConnectionWindow)])
        self.connection_label.setText(f"Connections: {count}")

    def closeEvent(self, event):
        """Handle application close event"""
        # Close all sub-windows properly
        self.mdi_area.closeAllSubWindows()
        event.accept()
        self.logger.info("Application closed")


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    app.setApplicationName("PyDev-Toolkit")
    app.setOrganizationName("PyDev")

    # Set application style
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

## 第二部分：通用 WebSocket 调试器

### websocket_tool/**init**.py

```python
"""WebSocket debugging tool module"""
```

### websocket_tool/signal_bridge.py

```python
from PySide6.QtCore import QObject, Signal


class SignalBridge(QObject):
    """Signal bridge for cross-thread communication"""

    # Connection signals
    connected = Signal()
    disconnected = Signal()
    connection_error = Signal(str)

    # Message signals
    message_received = Signal(str, str)  # timestamp, message
    message_sent = Signal(str, str)  # timestamp, message

    # Status signals
    status_update = Signal(str)

    def __init__(self):
        super().__init__()
```

### websocket_tool/websocket_thread.py

```python
import json
import asyncio
import websockets
from datetime import datetime
from PySide6.QtCore import QThread, QObject
from websocket_tool.signal_bridge import SignalBridge


class WebSocketThread(QThread):
    """Background thread for WebSocket communication"""

    def __init__(self, signal_bridge: SignalBridge):
        super().__init__()
        self.signal_bridge = signal_bridge
        self.websocket = None
        self.uri = None
        self.running = False
        self.loop = None

    def set_uri(self, uri: str):
        """Set the WebSocket URI"""
        self.uri = uri

    async def connect_websocket(self):
        """Establish WebSocket connection"""
        try:
            self.signal_bridge.status_update.emit(f"Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.signal_bridge.connected.emit()
            self.signal_bridge.status_update.emit(f"Connected to {self.uri}")

            # Start receiving messages
            await self.receive_messages()

        except Exception as e:
            self.signal_bridge.connection_error.emit(str(e))
            self.signal_bridge.status_update.emit(f"Connection failed: {e}")

    async def receive_messages(self):
        """Receive messages from WebSocket"""
        try:
            async for message in self.websocket:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.signal_bridge.message_received.emit(timestamp, message)
        except websockets.exceptions.ConnectionClosed:
            self.signal_bridge.disconnected.emit()
            self.signal_bridge.status_update.emit("Connection closed")
        except Exception as e:
            self.signal_bridge.connection_error.emit(str(e))

    async def send_message_async(self, message: str):
        """Send a message through WebSocket"""
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.send(message)
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.signal_bridge.message_sent.emit(timestamp, message)
            except Exception as e:
                self.signal_bridge.connection_error.emit(str(e))

    def send_message(self, message: str):
        """Queue a message to be sent"""
        if self.loop and self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.send_message_async(message),
                self.loop
            )

    async def disconnect_websocket(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.signal_bridge.disconnected.emit()
            self.signal_bridge.status_update.emit("Disconnected")

    def disconnect(self):
        """Request disconnection"""
        if self.loop and self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.disconnect_websocket(),
                self.loop
            )
        self.running = False

    def run(self):
        """Run the WebSocket event loop"""
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        if self.uri:
            self.loop.run_until_complete(self.connect_websocket())

        self.loop.close()
```

### websocket_tool/views/base_view.py

```python
from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget


class BaseView(QWidget, ABC):
    """Base class for pluggable view widgets"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    @abstractmethod
    def setup_ui(self):
        """Setup the view's UI"""
        pass

    @abstractmethod
    def on_message_received(self, timestamp: str, message: str):
        """Handle received message"""
        pass

    @abstractmethod
    def on_message_sent(self, timestamp: str, message: str):
        """Handle sent message"""
        pass

    @abstractmethod
    def get_view_name(self) -> str:
        """Return the display name of this view"""
        pass

    def clear(self):
        """Clear the view contents"""
        pass
```

### websocket_tool/views/json_tree_view.py

```python
import json
from PySide6.QtWidgets import (
    QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from websocket_tool.views.base_view import BaseView


class JsonTreeView(BaseView):
    """Tree view for JSON message display"""

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        self.title_label = QLabel("JSON Tree View")
        self.title_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.title_label)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Key", "Value", "Type"])
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        layout.addWidget(self.tree)
        self.setLayout(layout)

    def on_message_received(self, timestamp: str, message: str):
        """Display received message in tree format"""
        self._add_message_to_tree(f"[{timestamp}] Received", message, QColor(0, 128, 0))

    def on_message_sent(self, timestamp: str, message: str):
        """Display sent message in tree format"""
        self._add_message_to_tree(f"[{timestamp}] Sent", message, QColor(0, 0, 255))

    def _add_message_to_tree(self, title: str, message: str, color: QColor):
        """Add a message to the tree widget"""
        root = QTreeWidgetItem(self.tree)
        root.setText(0, title)
        root.setForeground(0, color)

        # Make title bold
        font = QFont()
        font.setBold(True)
        root.setFont(0, font)

        try:
            data = json.loads(message)
            self._add_json_to_tree(data, root)
            root.setExpanded(True)
        except json.JSONDecodeError:
            # If not JSON, show as plain text
            item = QTreeWidgetItem(root)
            item.setText(0, "Raw Message")
            item.setText(1, message)
            item.setText(2, "string")

    def _add_json_to_tree(self, data, parent):
        """Recursively add JSON data to tree"""
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent)
                item.setText(0, str(key))

                if isinstance(value, (dict, list)):
                    item.setText(2, type(value).__name__)
                    self._add_json_to_tree(value, item)
                else:
                    item.setText(1, str(value))
                    item.setText(2, type(value).__name__)

        elif isinstance(data, list):
            for i, value in enumerate(data):
                item = QTreeWidgetItem(parent)
                item.setText(0, f"[{i}]")

                if isinstance(value, (dict, list)):
                    item.setText(2, type(value).__name__)
                    self._add_json_to_tree(value, item)
                else:
                    item.setText(1, str(value))
                    item.setText(2, type(value).__name__)

    def get_view_name(self) -> str:
        return "JSON Tree View"

    def clear(self):
        """Clear all items from the tree"""
        self.tree.clear()
```

### websocket_tool/views/raw_log_view.py

```python
from PySide6.QtWidgets import QVBoxLayout, QTextEdit, QLabel
from PySide6.QtGui import QTextCharFormat, QColor, QFont
from websocket_tool.views.base_view import BaseView


class RawLogView(BaseView):
    """Raw text log view for messages"""

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        self.title_label = QLabel("Raw Log View")
        self.title_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.title_label)

        # Text area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def on_message_received(self, timestamp: str, message: str):
        """Display received message"""
        cursor = self.log_area.textCursor()
        cursor.movePosition(cursor.End)

        # Format for received messages (green)
        format_received = QTextCharFormat()
        format_received.setForeground(QColor(0, 128, 0))
        format_received.setFontWeight(QFont.Bold)

        cursor.insertText(f"[{timestamp}] ← RECEIVED\n", format_received)

        # Message content
        format_content = QTextCharFormat()
        cursor.insertText(f"{message}\n\n", format_content)

        # Scroll to bottom
        self.log_area.ensureCursorVisible()

    def on_message_sent(self, timestamp: str, message: str):
        """Display sent message"""
        cursor = self.log_area.textCursor()
        cursor.movePosition(cursor.End)

        # Format for sent messages (blue)
        format_sent = QTextCharFormat()
        format_sent.setForeground(QColor(0, 0, 255))
        format_sent.setFontWeight(QFont.Bold)

        cursor.insertText(f"[{timestamp}] → SENT\n", format_sent)

        # Message content
        format_content = QTextCharFormat()
        cursor.insertText(f"{message}\n\n", format_content)

        # Scroll to bottom
        self.log_area.ensureCursorVisible()

    def get_view_name(self) -> str:
        return "Raw Log View"

    def clear(self):
        """Clear the log"""
        self.log_area.clear()
```

### websocket_tool/connection_window.py

```python
from PySide6.QtWidgets import (
    QMdiSubWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLineEdit, QPushButton, QTextEdit,
    QToolBar, QComboBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QTextCharFormat, QColor, QFont
from websocket_tool.websocket_thread import WebSocketThread
from websocket_tool.signal_bridge import SignalBridge
from websocket_tool.views.json_tree_view import JsonTreeView
from websocket_tool.views.raw_log_view import RawLogView


class ConnectionWindow(QMdiSubWindow):
    """WebSocket connection window with pluggable views"""

    def __init__(self, title="WebSocket Connection"):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumSize(1000, 600)

        # Create main widget
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)

        # Initialize components
        self.signal_bridge = SignalBridge()
        self.ws_thread = WebSocketThread(self.signal_bridge)
        self.current_view = None
        self.views = {}

        # Setup UI
        self.setup_ui()
        self.register_default_views()
        self.connect_signals()

    def setup_ui(self):
        """Setup the main UI layout"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create toolbar
        self.toolbar = QToolBar()
        self.setup_toolbar()
        main_layout.addWidget(self.toolbar)

        # Create splitter for left and right panels
        self.splitter = QSplitter(Qt.Horizontal)

        # Left panel - Connection and messaging
        left_panel = self.create_left_panel()
        self.splitter.addWidget(left_panel)

        # Right panel - View container
        self.view_container = QWidget()
        self.view_layout = QVBoxLayout()
        self.view_layout.setContentsMargins(0, 0, 0, 0)
        self.view_container.setLayout(self.view_layout)
        self.splitter.addWidget(self.view_container)

        # Set initial splitter sizes (40% left, 60% right)
        self.splitter.setSizes([400, 600])

        main_layout.addWidget(self.splitter)
        self.main_widget.setLayout(main_layout)

    def setup_toolbar(self):
        """Setup the toolbar with view selection"""
        # View selection
        view_label = QLabel("View: ")
        self.toolbar.addWidget(view_label)

        self.view_combo = QComboBox()
        self.view_combo.currentTextChanged.connect(self.switch_view)
        self.toolbar.addWidget(self.view_combo)

        self.toolbar.addSeparator()

        # Clear action
        clear_action = QAction("Clear View", self)
        clear_action.triggered.connect(self.clear_current_view)
        self.toolbar.addAction(clear_action)

    def create_left_panel(self):
        """Create the left panel with connection and messaging controls"""
        panel = QWidget()
        layout = QVBoxLayout()

        # Connection group
        connection_group = QGroupBox("Connection")
        connection_layout = QVBoxLayout()

        # URI input
        uri_layout = QHBoxLayout()
        self.uri_input = QLineEdit()
        self.uri_input.setPlaceholderText("ws://localhost:8000 or wss://...")
        self.uri_input.setText("ws://localhost:8000")
        uri_layout.addWidget(self.uri_input)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        uri_layout.addWidget(self.connect_btn)

        connection_layout.addLayout(uri_layout)

        # Status label
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        connection_layout.addWidget(self.status_label)

        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)

        # Message group
        message_group = QGroupBox("Message")
        message_layout = QVBoxLayout()

        # Message input
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter message to send (JSON supported)")
        self.message_input.setMaximumHeight(150)
        message_layout.addWidget(self.message_input)

        # Send button
        self.send_btn = QPushButton("Send Message")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self.send_message)
        message_layout.addWidget(self.send_btn)

        message_group.setLayout(message_layout)
        layout.addWidget(message_group)

        # Timeline group
        timeline_group = QGroupBox("Message Timeline")
        timeline_layout = QVBoxLayout()

        self.timeline = QTextEdit()
        self.timeline.setReadOnly(True)
        self.timeline.setFont(QFont("Consolas", 9))
        timeline_layout.addWidget(self.timeline)

        timeline_group.setLayout(timeline_layout)
        layout.addWidget(timeline_group)

        panel.setLayout(layout)
        return panel

    def register_default_views(self):
        """Register default view plugins"""
        self.register_view(JsonTreeView())
        self.register_view(RawLogView())

        # Set JSON Tree as default
        self.switch_view("JSON Tree View")

    def register_view(self, view):
        """Register a new view plugin"""
        name = view.get_view_name()
        self.views[name] = view
        self.view_combo.addItem(name)

        # Connect view to signals
        self.signal_bridge.message_received.connect(view.on_message_received)
        self.signal_bridge.message_sent.connect(view.on_message_sent)

    def switch_view(self, view_name):
        """Switch to a different view"""
        if view_name not in self.views:
            return

        # Remove current view
        if self.current_view:
            self.view_layout.removeWidget(self.current_view)
            self.current_view.setParent(None)

        # Add new view
        self.current_view = self.views[view_name]
        self.view_layout.addWidget(self.current_view)

    def clear_current_view(self):
        """Clear the current view"""
        if self.current_view:
            self.current_view.clear()

    def connect_signals(self):
        """Connect all signals"""
        self.signal_bridge.connected.connect(self.on_connected)
        self.signal_bridge.disconnected.connect(self.on_disconnected)
        self.signal_bridge.connection_error.connect(self.on_connection_error)
        self.signal_bridge.message_received.connect(self.on_message_received)
        self.signal_bridge.message_sent.connect(self.on_message_sent)
        self.signal_bridge.status_update.connect(self.on_status_update)

    def toggle_connection(self):
        """Toggle WebSocket connection"""
        if self.connect_btn.text() == "Connect":
            uri = self.uri_input.text().strip()
            if not uri:
                return

            self.ws_thread.set_uri(uri)
            self.ws_thread.start()
            self.connect_btn.setText("Connecting...")
            self.connect_btn.setEnabled(False)
        else:
            self.ws_thread.disconnect()
            self.connect_btn.setText("Disconnecting...")
            self.connect_btn.setEnabled(False)

    def send_message(self):
        """Send a message through WebSocket"""
        message = self.message_input.toPlainText().strip()
        if message:
            self.ws_thread.send_message(message)
            self.message_input.clear()

    def on_connected(self):
        """Handle connection established"""
        self.connect_btn.setText("Disconnect")
        self.connect_btn.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.status_label.setText("Connected")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.uri_input.setEnabled(False)

    def on_disconnected(self):
        """Handle disconnection"""
        self.connect_btn.setText("Connect")
        self.connect_btn.setEnabled(True)
        self.send_btn.setEnabled(False)
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.uri_input.setEnabled(True)

    def on_connection_error(self, error):
        """Handle connection error"""
        self.on_disconnected()
        self.add_timeline_message(f"ERROR: {error}", QColor(255, 0, 0))

    def on_message_received(self, timestamp, message):
        """Handle received message"""
        self.add_timeline_message(f"[{timestamp}] ← RECEIVED: {message}", QColor(0, 128, 0))

    def on_message_sent(self, timestamp, message):
        """Handle sent message"""
        self.add_timeline_message(f"[{timestamp}] → SENT: {message}", QColor(0, 0, 255))

    def on_status_update(self, status):
        """Handle status update"""
        self.add_timeline_message(f"STATUS: {status}", QColor(128, 128, 128))

    def add_timeline_message(self, message, color):
        """Add a message to the timeline"""
        cursor = self.timeline.textCursor()
        cursor.movePosition(cursor.End)

        format = QTextCharFormat()
        format.setForeground(color)

        cursor.insertText(f"{message}\n", format)
        self.timeline.ensureCursorVisible()

    def closeEvent(self, event):
        """Handle window close"""
        if self.ws_thread.isRunning():
            self.ws_thread.disconnect()
            self.ws_thread.wait()
        event.accept()
```

## 第三部分：Conda 环境管理器

### conda_manager/**init**.py

```python
"""Conda environment manager module"""
```

### conda_manager/conda_service.py

```python
import os
import sys
import json
import subprocess
import platform
import requests
from pathlib import Path
from PySide6.QtCore import QThread, Signal, QObject


class CondaService(QThread):
    """Background service for Conda operations"""

    # Signals
    conda_found = Signal(str)  # conda path
    conda_not_found = Signal()
    operation_started = Signal(str)  # operation name
    operation_progress = Signal(str)  # progress message
    operation_completed = Signal(str)  # result message
    operation_failed = Signal(str)  # error message
    environment_list_updated = Signal(list)  # list of environments
    download_progress = Signal(int, int)  # current, total bytes

    def __init__(self):
        super().__init__()
        self.conda_path = None
        self.operation = None
        self.operation_args = None

    def run(self):
        """Run the requested operation"""
        if self.operation == "detect":
            self.detect_conda()
        elif self.operation == "install":
            self.install_miniconda(self.operation_args)
        elif self.operation == "list":
            self.list_environments()
        elif self.operation == "create":
            self.create_environment(**self.operation_args)
        elif self.operation == "delete":
            self.delete_environment(self.operation_args)
        elif self.operation == "update":
            self.update_environment(self.operation_args)

    def start_operation(self, operation, args=None):
        """Start an operation in the background thread"""
        self.operation = operation
        self.operation_args = args
        self.start()

    def detect_conda(self):
        """Detect Conda installation on the system"""
        self.operation_started.emit("Detecting Conda installation...")

        # Common conda executable names
        conda_names = ["conda", "conda.exe", "conda.bat"]

        # Common installation paths
        common_paths = []

        if platform.system() == "Windows":
            common_paths.extend([
                Path.home() / "Miniconda3",
                Path.home() / "Anaconda3",
                Path("C:/ProgramData/Miniconda3"),
                Path("C:/ProgramData/Anaconda3"),
                Path("C:/Miniconda3"),
                Path("C:/Anaconda3"),
            ])
        else:
            common_paths.extend([
                Path.home() / "miniconda3",
                Path.home() / "anaconda3",
                Path("/opt/miniconda3"),
                Path("/opt/anaconda3"),
                Path("/usr/local/miniconda3"),
                Path("/usr/local/anaconda3"),
            ])

        # Check PATH first
        for name in conda_names:
            try:
                result = subprocess.run(
                    [name, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.conda_path = name
                    self.conda_found.emit(name)
                    self.operation_completed.emit(f"Conda found in PATH: {name}")
                    return
            except:
                pass

        # Check common installation paths
        for path in common_paths:
            for subdir in ["", "Scripts", "bin", "condabin"]:
                conda_dir = path / subdir if subdir else path
                for name in conda_names:
                    conda_exe = conda_dir / name
                    if conda_exe.exists():
                        try:
                            result = subprocess.run(
                                [str(conda_exe), "--version"],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if result.returncode == 0:
                                self.conda_path = str(conda_exe)
                                self.conda_found.emit(str(conda_exe))
                                self.operation_completed.emit(f"Conda found at: {conda_exe}")
                                return
                        except:
                            pass

        self.conda_not_found.emit()
        self.operation_completed.emit("Conda not found on system")

    def install_miniconda(self, install_path):
        """Download and install Miniconda silently"""
        self.operation_started.emit("Installing Miniconda...")

        try:
            # Determine installer URL based on platform
            system = platform.system()
            machine = platform.machine()

            if system == "Windows":
                if machine.endswith("64"):
                    installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
                    installer_name = "Miniconda3-installer.exe"
                else:
                    installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86.exe"
                    installer_name = "Miniconda3-installer.exe"
            elif system == "Darwin":  # macOS
                installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
                installer_name = "Miniconda3-installer.sh"
            else:  # Linux
                installer_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
                installer_name = "Miniconda3-installer.sh"

            # Download installer
            self.operation_progress.emit(f"Downloading from {installer_url}")
            installer_path = Path.home() / installer_name

            response = requests.get(installer_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.download_progress.emit(downloaded, total_size)

            self.operation_progress.emit("Download complete. Installing...")

            # Run installer
            if system == "Windows":
                # Silent install on Windows
                cmd = [
                    str(installer_path),
                    "/S",
                    f"/D={install_path}"
                ]
            else:
                # Silent install on Unix-like systems
                cmd = [
                    "bash",
                    str(installer_path),
                    "-b",
                    "-p",
                    install_path
                ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:
                self.operation_progress.emit(line.strip())

            process.wait()

            if process.returncode == 0:
                self.operation_completed.emit(f"Miniconda installed successfully at {install_path}")
                # Update conda path
                if system == "Windows":
                    self.conda_path = str(Path(install_path) / "Scripts" / "conda.exe")
                else:
                    self.conda_path = str(Path(install_path) / "bin" / "conda")
                self.conda_found.emit(self.conda_path)
            else:
                self.operation_failed.emit("Installation failed")

            # Clean up installer
            installer_path.unlink()

        except Exception as e:
            self.operation_failed.emit(str(e))

    def list_environments(self):
        """List all Conda environments"""
        if not self.conda_path:
            self.detect_conda()
            if not self.conda_path:
                self.operation_failed.emit("Conda not found")
                return

        self.operation_started.emit("Listing environments...")

        try:
            result = subprocess.run(
                [self.conda_path, "env", "list", "--json"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                environments = []
                for env_path in data.get("envs", []):
                    env_name = Path(env_path).name
                    if env_name == "miniconda3" or env_name == "anaconda3":
                        env_name = "base"
                    environments.append({
                        "name": env_name,
                        "path": env_path
                    })
                self.environment_list_updated.emit(environments)
                self.operation_completed.emit(f"Found {len(environments)} environments")
            else:
                self.operation_failed.emit(result.stderr)

        except Exception as e:
            self.operation_failed.emit(str(e))

    def list_environments_sync(self):
        """Synchronously list environments (for use in main thread)"""
        if not self.conda_path:
            self.detect_conda()
            if not self.conda_path:
                return []

        try:
            result = subprocess.run(
                [self.conda_path, "env", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                environments = []
                for env_path in data.get("envs", []):
                    env_name = Path(env_path).name
                    if env_name == "miniconda3" or env_name == "anaconda3":
                        env_name = "base"
                    environments.append({
                        "name": env_name,
                        "path": env_path
                    })
                return environments
        except:
            pass

        return []

    def create_environment(self, name=None, yaml_file=None):
        """Create a new Conda environment"""
        if not self.conda_path:
            self.operation_failed.emit("Conda not found")
            return

        self.operation_started.emit(f"Creating environment...")

        try:
            if yaml_file:
                # Create from YAML file
                cmd = [self.conda_path, "env", "create", "-f", yaml_file]
            else:
                # Create empty environment with Python
                cmd = [self.conda_path, "create", "-n", name, "python", "-y"]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:
                self.operation_progress.emit(line.strip())

            process.wait()

            if process.returncode == 0:
                self.operation_completed.emit("Environment created successfully")
                self.list_environments()  # Refresh list
            else:
                self.operation_failed.emit("Failed to create environment")

        except Exception as e:
            self.operation_failed.emit(str(e))

    def delete_environment(self, env_name):
        """Delete a Conda environment"""
        if not self.conda_path:
            self.operation_failed.emit("Conda not found")
            return

        self.operation_started.emit(f"Deleting environment: {env_name}")

        try:
            cmd = [self.conda_path, "env", "remove", "-n", env_name, "-y"]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:
                self.operation_progress.emit(line.strip())

            process.wait()

            if process.returncode == 0:
                self.operation_completed.emit(f"Environment '{env_name}' deleted")
                self.list_environments()  # Refresh list
            else:
                self.operation_failed.emit("Failed to delete environment")

        except Exception as e:
            self.operation_failed.emit(str(e))

    def update_environment(self, env_name):
        """Update all packages in a Conda environment"""
        if not self.conda_path:
            self.operation_failed.emit("Conda not found")
            return

        self.operation_started.emit(f"Updating environment: {env_name}")

        try:
            cmd = [self.conda_path, "update", "-n", env_name, "--all", "-y"]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:
                self.operation_progress.emit(line.strip())

            process.wait()

            if process.returncode == 0:
                self.operation_completed.emit(f"Environment '{env_name}' updated")
            else:
                self.operation_failed.emit("Failed to update environment")

        except Exception as e:
            self.operation_failed.emit(str(e))

    def get_python_path(self, env_name):
        """Get Python interpreter path for an environment"""
        if not self.conda_path:
            return None

        try:
            # Get environment info
            result = subprocess.run(
                [self.conda_path, "info", "--envs", "--json"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                for env_path in data.get("envs", []):
                    if Path(env_path).name == env_name or (env_name == "base" and "miniconda3" in env_path):
                        if platform.system() == "Windows":
                            python_path = Path(env_path) / "python.exe"
                        else:
                            python_path = Path(env_path) / "bin" / "python"
                        if python_path.exists():
                            return str(python_path)
        except:
            pass

        return None
```

### conda_manager/conda_widget.py

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QTextEdit, QLabel, QFileDialog,
    QMessageBox, QGroupBox, QProgressBar, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from conda_manager.conda_service import CondaService


class CondaManagerWidget(QWidget):
    """UI widget for Conda environment management"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.conda_service = CondaService()
        self.setup_ui()
        self.connect_signals()

        # Start by detecting Conda
        self.conda_service.start_operation("detect")

    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout()

        # Status section
        status_group = QGroupBox("Conda Status")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Detecting Conda installation...")
        self.status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.status_label)

        self.conda_path_label = QLabel("Path: Not detected")
        status_layout.addWidget(self.conda_path_label)

        self.install_btn = QPushButton("Install Miniconda")
        self.install_btn.setEnabled(False)
        self.install_btn.clicked.connect(self.install_miniconda)
        status_layout.addWidget(self.install_btn)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Environments section
        env_group = QGroupBox("Environments")
        env_layout = QVBoxLayout()

        # Environment list
        self.env_list = QListWidget()
        env_layout.addWidget(self.env_list)

        # Environment actions
        actions_layout = QHBoxLayout()

        self.create_btn = QPushButton("Create New")
        self.create_btn.clicked.connect(self.create_environment)
        actions_layout.addWidget(self.create_btn)

        self.create_from_file_btn = QPushButton("Create from file...")
        self.create_from_file_btn.clicked.connect(self.create_from_file)
        actions_layout.addWidget(self.create_from_file_btn)

        self.update_btn = QPushButton("Update Selected")
        self.update_btn.clicked.connect(self.update_environment)
        actions_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_environment)
        actions_layout.addWidget(self.delete_btn)

        env_layout.addLayout(actions_layout)
        env_group.setLayout(env_layout)
        layout.addWidget(env_group)

        # Progress section
        progress_group = QGroupBox("Operation Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)
        progress_layout.addWidget(self.log_output)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        self.setLayout(layout)

        # Initially disable environment actions
        self.set_environment_actions_enabled(False)

    def connect_signals(self):
        """Connect service signals to UI handlers"""
        self.conda_service.conda_found.connect(self.on_conda_found)
        self.conda_service.conda_not_found.connect(self.on_conda_not_found)
        self.conda_service.operation_started.connect(self.on_operation_started)
        self.conda_service.operation_progress.connect(self.on_operation_progress)
        self.conda_service.operation_completed.connect(self.on_operation_completed)
        self.conda_service.operation_failed.connect(self.on_operation_failed)
        self.conda_service.environment_list_updated.connect(self.on_environments_updated)
        self.conda_service.download_progress.connect(self.on_download_progress)

    def on_conda_found(self, conda_path):
        """Handle Conda found signal"""
        self.status_label.setText("Conda detected ✓")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.conda_path_label.setText(f"Path: {conda_path}")
        self.install_btn.setEnabled(False)
        self.set_environment_actions_enabled(True)

        # Load environments
        self.conda_service.start_operation("list")

    def on_conda_not_found(self):
        """Handle Conda not found signal"""
        self.status_label.setText("Conda not found ✗")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.conda_path_label.setText("Path: Not detected")
        self.install_btn.setEnabled(True)
        self.set_environment_actions_enabled(False)

    def on_operation_started(self, operation):
        """Handle operation started signal"""
        self.log_output.append(f"\n>>> {operation}")
        self.set_environment_actions_enabled(False)

    def on_operation_progress(self, message):
        """Handle operation progress signal"""
        self.log_output.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_operation_completed(self, message):
        """Handle operation completed signal"""
        self.log_output.append(f"✓ {message}")
        self.set_environment_actions_enabled(True)
        self.progress_bar.setVisible(False)

    def on_operation_failed(self, error):
        """Handle operation failed signal"""
        self.log_output.append(f"✗ Error: {error}")
        self.set_environment_actions_enabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Operation Failed", error)

    def on_environments_updated(self, environments):
        """Handle environments list update"""
        self.env_list.clear()
        for env in environments:
            self.env_list.addItem(f"{env['name']} ({env['path']})")

    def on_download_progress(self, current, total):
        """Handle download progress signal"""
        if total > 0:
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            percent = (current / total) * 100
            self.progress_bar.setFormat(f"Downloading: {percent:.1f}%")

    def set_environment_actions_enabled(self, enabled):
        """Enable/disable environment action buttons"""
        self.create_btn.setEnabled(enabled)
        self.create_from_file_btn.setEnabled(enabled)
        self.update_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        self.env_list.setEnabled(enabled)

    def install_miniconda(self):
        """Install Miniconda"""
        install_path = QFileDialog.getExistingDirectory(
            self,
            "Select Installation Directory",
            str(Path.home())
        )

        if install_path:
            self.conda_service.start_operation("install", install_path)

    def create_environment(self):
        """Create a new environment"""
        name, ok = QInputDialog.getText(
            self,
            "Create Environment",
            "Environment name:"
        )

        if ok and name:
            self.conda_service.start_operation("create", {"name": name})

    def create_from_file(self):
        """Create environment from YAML file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select environment.yml file",
            "",
            "YAML files (*.yml *.yaml)"
        )

        if file_path:
            self.conda_service.start_operation("create", {"yaml_file": file_path})

    def update_environment(self):
        """Update selected environment"""
        current_item = self.env_list.currentItem()
        if current_item:
            env_name = current_item.text().split(" (")[0]

            reply = QMessageBox.question(
                self,
                "Update Environment",
                f"Update all packages in '{env_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.conda_service.start_operation("update", env_name)

    def delete_environment(self):
        """Delete selected environment"""
        current_item = self.env_list.currentItem()
        if current_item:
            env_name = current_item.text().split(" (")[0]

            if env_name == "base":
                QMessageBox.warning(
                    self,
                    "Cannot Delete",
                    "Cannot delete the base environment"
                )
                return

            reply = QMessageBox.question(
                self,
                "Delete Environment",
                f"Delete environment '{env_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.conda_service.start_operation("delete", env_name)
```

## 第四部分：VS Code 集成

### vscode_integration/**init**.py

```python
"""VS Code integration module"""
```

### vscode_integration/manager.py

```python
import json
import subprocess
import platform
from pathlib import Path
from conda_manager.conda_service import CondaService


class VSCodeManager:
    """Manager for VS Code workspace configuration and integration"""

    def __init__(self):
        self.conda_service = CondaService()

    def open_project_with_env(self, project_path: str, env_name: str):
        """Open a project in VS Code with specified Conda environment"""

        # Get Python interpreter path for the environment
        python_path = self.conda_service.get_python_path(env_name)

        if not python_path:
            raise ValueError(f"Could not find Python interpreter for environment: {env_name}")

        # Create workspace configuration
        workspace_config = {
            "folders": [
                {
                    "path": "."
                }
            ],
            "settings": {
                "python.defaultInterpreterPath": python_path,
                "python.terminal.activateEnvironment": True,
                "python.terminal.activateEnvInCurrentTerminal": True,
                "python.condaPath": self.conda_service.conda_path or "conda",
            }
        }

        # Write workspace file
        project_path = Path(project_path)
        workspace_file = project_path / f"{project_path.name}.code-workspace"

        with open(workspace_file, 'w') as f:
            json.dump(workspace_config, f, indent=4)

        # Open VS Code with the workspace
        self.open_vscode(str(workspace_file))

        return workspace_file

    def open_vscode(self, workspace_path: str):
        """Open VS Code with the specified workspace file"""

        # Determine VS Code command based on platform
        if platform.system() == "Windows":
            vscode_commands = ["code.cmd", "code.exe", "code"]
        else:
            vscode_commands = ["code"]

        # Try to launch VS Code
        for cmd in vscode_commands:
            try:
                subprocess.Popen([cmd, workspace_path])
                return True
            except FileNotFoundError:
                continue

        raise RuntimeError("VS Code not found. Please ensure it's installed and in PATH.")

    def create_launch_json(self, project_path: str, env_name: str):
        """Create a launch.json file for debugging configuration"""

        python_path = self.conda_service.get_python_path(env_name)

        if not python_path:
            raise ValueError(f"Could not find Python interpreter for environment: {env_name}")

        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Python: Current File",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}",
                    "console": "integratedTerminal",
                    "python": python_path
                },
                {
                    "name": "Python: Module",
                    "type": "python",
                    "request": "launch",
                    "module": "enter-your-module-name",
                    "python": python_path
                }
            ]
        }

        # Create .vscode directory if it doesn't exist
        vscode_dir = Path(project_path) / ".vscode"
        vscode_dir.mkdir(exist_ok=True)

        # Write launch.json
        launch_file = vscode_dir / "launch.json"
        with open(launch_file, 'w') as f:
            json.dump(launch_config, f, indent=4)

        return launch_file
```

## 第五部分：工具模块

### utils/**init**.py

```python
"""Utility modules"""
```

### utils/logger.py

```python
import logging
import sys
from pathlib import Path


def setup_logger(name, level=logging.INFO):
    """Setup a logger with console and file handlers"""

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # File handler
    log_dir = Path.home() / ".pydev-toolkit" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
```

## 主入口文件

### main.py

```python
#!/usr/bin/env python
"""
PyDev-Toolkit Main Entry Point
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from desktop_app.main import main

if __name__ == "__main__":
    main()
```

## 配置文件

### environment.yml

```yaml
name: pydev-toolkit
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.9
  - pip
  - pip:
      - PySide6>=6.5.0
      - websockets>=11.0
      - requests>=2.28.0
      - pyinstaller>=5.10.0
```

### requirements.txt

```
PySide6>=6.5.0
websockets>=11.0
requests>=2.28.0
pyinstaller>=5.10.0
```

## GitHub Actions 工作流

### .github/workflows/build.yml

```yaml
name: Build PyDev-Toolkit

on:
  push:
    branches: [main, develop]
    tags:
      - "v*"
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Miniconda
        uses: conda-incubator/setup-miniconda@v2
        with:
          auto-update-conda: true
          python-version: 3.9
          activate-environment: pydev-toolkit
          environment-file: environment.yml
          auto-activate-base: false

      - name: Install dependencies
        shell: bash -l {0}
        run: |
          conda info
          conda list
          pip install -r requirements.txt

      - name: Build with PyInstaller
        shell: bash -l {0}
        run: |
          pyinstaller --name="PyDev-Toolkit" \
                      --noconsole \
                      --onefile \
                      --windowed \
                      --icon=NONE \
                      --add-data="websocket_tool;websocket_tool" \
                      --add-data="conda_manager;conda_manager" \
                      --add-data="vscode_integration;vscode_integration" \
                      --add-data="utils;utils" \
                      --hidden-import="websockets" \
                      --hidden-import="requests" \
                      --hidden-import="PySide6.QtCore" \
                      --hidden-import="PySide6.QtWidgets" \
                      --hidden-import="PySide6.QtGui" \
                      main.py

      - name: Test executable
        shell: bash -l {0}
        run: |
          # Basic smoke test - check if exe was created
          test -f dist/PyDev-Toolkit.exe && echo "Executable created successfully"

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: PyDev-Toolkit-Windows
          path: dist/PyDev-Toolkit.exe

  build-linux:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Miniconda
        uses: conda-incubator/setup-miniconda@v2
        with:
          auto-update-conda: true
          python-version: 3.9
          activate-environment: pydev-toolkit
          environment-file: environment.yml
          auto-activate-base: false

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xfixes0

      - name: Install Python dependencies
        shell: bash -l {0}
        run: |
          conda info
          conda list
          pip install -r requirements.txt

      - name: Build with PyInstaller
        shell: bash -l {0}
        run: |
          pyinstaller --name="PyDev-Toolkit" \
                      --noconsole \
                      --onefile \
                      --windowed \
                      --add-data="websocket_tool:websocket_tool" \
                      --add-data="conda_manager:conda_manager" \
                      --add-data="vscode_integration:vscode_integration" \
                      --add-data="utils:utils" \
                      --hidden-import="websockets" \
                      --hidden-import="requests" \
                      --hidden-import="PySide6.QtCore" \
                      --hidden-import="PySide6.QtWidgets" \
                      --hidden-import="PySide6.QtGui" \
                      main.py

      - name: Test executable
        shell: bash -l {0}
        run: |
          # Basic smoke test
          test -f dist/PyDev-Toolkit && echo "Executable created successfully"

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: PyDev-Toolkit-Linux
          path: dist/PyDev-Toolkit

  build-macos:
    runs-on: macos-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Miniconda
        uses: conda-incubator/setup-miniconda@v2
        with:
          auto-update-conda: true
          python-version: 3.9
          activate-environment: pydev-toolkit
          environment-file: environment.yml
          auto-activate-base: false

      - name: Install dependencies
        shell: bash -l {0}
        run: |
          conda info
          conda list
          pip install -r requirements.txt

      - name: Build with PyInstaller
        shell: bash -l {0}
        run: |
          pyinstaller --name="PyDev-Toolkit" \
                      --noconsole \
                      --onefile \
                      --windowed \
                      --osx-bundle-identifier="com.pydev.toolkit" \
                      --add-data="websocket_tool:websocket_tool" \
                      --add-data="conda_manager:conda_manager" \
                      --add-data="vscode_integration:vscode_integration" \
                      --add-data="utils:utils" \
                      --hidden-import="websockets" \
                      --hidden-import="requests" \
                      --hidden-import="PySide6.QtCore" \
                      --hidden-import="PySide6.QtWidgets" \
                      --hidden-import="PySide6.QtGui" \
                      main.py

      - name: Create DMG (optional)
        shell: bash -l {0}
        run: |
          # Create a simple DMG for distribution
          hdiutil create -volname "PyDev-Toolkit" -srcfolder dist/ -ov -format UDZO PyDev-Toolkit.dmg

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: PyDev-Toolkit-macOS
          path: |
            dist/PyDev-Toolkit.app
            PyDev-Toolkit.dmg

  create-release:
    needs: [build-windows, build-linux, build-macos]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')

    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v3

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            PyDev-Toolkit-Windows/PyDev-Toolkit.exe
            PyDev-Toolkit-Linux/PyDev-Toolkit
            PyDev-Toolkit-macOS/PyDev-Toolkit.dmg
          draft: false
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 使用说明

### 开发环境设置

1. **克隆仓库**

```bash
git clone https://github.com/yourusername/PyDev-Toolkit.git
cd PyDev-Toolkit
```

2. **创建 Conda 环境**

```bash
conda env create -f environment.yml
conda activate pydev-toolkit
```

3. **运行应用程序**

```bash
python main.py
```

### 功能使用

1. **WebSocket 调试**

   - File → New WebSocket Connection 创建新连接
   - 输入 WebSocket URL (ws:// 或 wss://)
   - 发送和接收消息，支持 JSON 格式化显示
   - 切换不同的视图插件（JSON Tree View, Raw Log View）

2. **Conda 环境管理**

   - Tools → Conda Environment Manager
   - 自动检测系统中的 Conda 安装
   - 创建、更新、删除环境
   - 从 environment.yml 文件创建环境

3. **VS Code 集成**
   - Tools → Configure VS Code Workspace
   - 选择项目目录和 Conda 环境
   - 自动生成 .code-workspace 文件并打开 VS Code

### 扩展视图插件

创建自定义视图插件：

```python
from websocket_tool.views.base_view import BaseView

class CustomView(BaseView):
    def setup_ui(self):
        # 实现 UI 设置
        pass

    def on_message_received(self, timestamp, message):
        # 处理接收的消息
        pass

    def on_message_sent(self, timestamp, message):
        # 处理发送的消息
        pass

    def get_view_name(self):
        return "Custom View"
```

然后在 ConnectionWindow 中注册：

```python
window.register_view(CustomView())
```

这个完整的 PyDev-Toolkit 应用程序提供了您要求的所有功能，具有模块化、可扩展的架构，以及专业级的用户体验。
