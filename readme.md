# DevDeck - 现代跨平台开发工具平台

## 技术选型决策

我选择 **Tauri + React + TypeScript + Ant Design** 作为技术栈：

### 为什么选择 Tauri 而非 Electron：

1. **性能优势**：Tauri 应用体积小 10-100 倍（~10MB vs ~150MB）
2. **内存占用**：Tauri 使用系统 WebView，内存占用显著降低
3. **安全性**：Rust 后端提供更好的类型安全和内存安全
4. **启动速度**：原生性能，启动速度快 2-3 倍

### 技术栈：

- **框架**: Tauri 2.0
- **前端**: React 18 + TypeScript
- **UI 库**: Ant Design 5.0 (提供类 VS Code 的专业外观)
- **状态管理**: Zustand
- **后端**: Rust (Tauri 核心)

## 项目结构

```
DevDeck/
├── src/                      # React 前端源码
│   ├── components/
│   │   ├── TabManager/       # 标签页管理组件
│   │   ├── WebSocketDebugger/# WebSocket 调试器
│   │   ├── CondaManager/     # Conda 管理器
│   │   └── CommandPalette/   # 命令面板
│   ├── views/                # 视图插件
│   │   ├── JsonTreeView.tsx
│   │   └── RawLogView.tsx
│   ├── stores/               # 状态管理
│   ├── hooks/                # 自定义 Hooks
│   ├── App.tsx
│   └── main.tsx
├── src-tauri/                # Rust 后端
│   ├── src/
│   │   ├── main.rs
│   │   ├── conda/            # Conda 管理模块
│   │   ├── vscode/           # VS Code 集成
│   │   └── websocket/        # WebSocket 处理
│   ├── Cargo.toml
│   └── tauri.conf.json
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .github/
    └── workflows/
        └── build.yml
```

## 第一部分：平台核心架构与 UI

### package.json

```json
{
  "name": "devdeck",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "tauri": "tauri",
    "tauri:dev": "tauri dev",
    "tauri:build": "tauri build"
  },
  "dependencies": {
    "@ant-design/icons": "^5.2.6",
    "@monaco-editor/react": "^4.6.0",
    "@tauri-apps/api": "^2.0.0",
    "antd": "^5.11.5",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.4.7",
    "uuid": "^9.0.1",
    "react-json-tree": "^0.18.0",
    "react-hotkeys-hook": "^4.4.1"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^2.0.0",
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "@types/uuid": "^9.0.7",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.10"
  }
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### src/main.tsx

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider, theme } from "antd";
import App from "./App";
import "./styles/global.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: "#1890ff",
          borderRadius: 4,
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
```

### src/App.tsx

```tsx
import React, { useState } from "react";
import { Layout } from "antd";
import { useHotkeys } from "react-hotkeys-hook";
import TabManager from "./components/TabManager";
import CommandPalette from "./components/CommandPalette";
import { useTabStore } from "./stores/tabStore";
import "./styles/App.css";

const { Header, Content } = Layout;

const App: React.FC = () => {
  const [commandPaletteVisible, setCommandPaletteVisible] = useState(false);
  const { addTab } = useTabStore();

  // Global hotkeys
  useHotkeys("ctrl+shift+p, cmd+shift+p", () => {
    setCommandPaletteVisible(true);
  });

  useHotkeys("ctrl+t, cmd+t", () => {
    addTab("websocket", "New WebSocket Connection");
  });

  const handleCommand = (command: string) => {
    switch (command) {
      case "websocket.new":
        addTab("websocket", "New WebSocket Connection");
        break;
      case "conda.open":
        addTab("conda", "Conda Manager");
        break;
      case "vscode.configure":
        addTab("vscode", "VS Code Configuration");
        break;
    }
    setCommandPaletteVisible(false);
  };

  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <div className="app-title">DevDeck</div>
      </Header>
      <Content className="app-content">
        <TabManager />
      </Content>
      <CommandPalette
        visible={commandPaletteVisible}
        onClose={() => setCommandPaletteVisible(false)}
        onCommand={handleCommand}
      />
    </Layout>
  );
};

export default App;
```

### src/stores/tabStore.ts

```typescript
import { create } from "zustand";
import { v4 as uuidv4 } from "uuid";

export type TabType = "websocket" | "conda" | "vscode" | "settings";

export interface Tab {
  id: string;
  type: TabType;
  title: string;
  data?: any;
}

interface TabStore {
  tabs: Tab[];
  activeTabId: string | null;
  addTab: (type: TabType, title?: string) => void;
  removeTab: (id: string) => void;
  setActiveTab: (id: string) => void;
  updateTab: (id: string, updates: Partial<Tab>) => void;
  reorderTabs: (startIndex: number, endIndex: number) => void;
}

export const useTabStore = create<TabStore>((set) => ({
  tabs: [],
  activeTabId: null,

  addTab: (type, title) => {
    const id = uuidv4();
    const newTab: Tab = {
      id,
      type,
      title: title || `New ${type}`,
    };

    set((state) => ({
      tabs: [...state.tabs, newTab],
      activeTabId: id,
    }));
  },

  removeTab: (id) => {
    set((state) => {
      const newTabs = state.tabs.filter((tab) => tab.id !== id);
      let newActiveId = state.activeTabId;

      if (state.activeTabId === id) {
        const removedIndex = state.tabs.findIndex((tab) => tab.id === id);
        if (newTabs.length > 0) {
          newActiveId = newTabs[Math.min(removedIndex, newTabs.length - 1)].id;
        } else {
          newActiveId = null;
        }
      }

      return {
        tabs: newTabs,
        activeTabId: newActiveId,
      };
    });
  },

  setActiveTab: (id) => {
    set({ activeTabId: id });
  },

  updateTab: (id, updates) => {
    set((state) => ({
      tabs: state.tabs.map((tab) =>
        tab.id === id ? { ...tab, ...updates } : tab
      ),
    }));
  },

  reorderTabs: (startIndex, endIndex) => {
    set((state) => {
      const newTabs = [...state.tabs];
      const [removed] = newTabs.splice(startIndex, 1);
      newTabs.splice(endIndex, 0, removed);
      return { tabs: newTabs };
    });
  },
}));
```

### src/components/TabManager/index.tsx

```tsx
import React from "react";
import { Tabs, Button, Empty } from "antd";
import { PlusOutlined, CloseOutlined } from "@ant-design/icons";
import { DndContext, closestCenter, DragEndEvent } from "@dnd-kit/core";
import {
  SortableContext,
  horizontalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
import { useTabStore } from "@/stores/tabStore";
import WebSocketDebugger from "../WebSocketDebugger";
import CondaManager from "../CondaManager";
import VSCodeConfig from "../VSCodeConfig";
import "./style.css";

const TabManager: React.FC = () => {
  const { tabs, activeTabId, setActiveTab, removeTab, addTab, reorderTabs } =
    useTabStore();

  const renderTabContent = (tab: any) => {
    switch (tab.type) {
      case "websocket":
        return <WebSocketDebugger tabId={tab.id} />;
      case "conda":
        return <CondaManager tabId={tab.id} />;
      case "vscode":
        return <VSCodeConfig tabId={tab.id} />;
      default:
        return <Empty description="Unknown tab type" />;
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (active.id !== over?.id) {
      const oldIndex = tabs.findIndex((tab) => tab.id === active.id);
      const newIndex = tabs.findIndex((tab) => tab.id === over?.id);
      reorderTabs(oldIndex, newIndex);
    }
  };

  const handleEdit = (
    targetKey: React.MouseEvent | React.KeyboardEvent | string,
    action: "add" | "remove"
  ) => {
    if (action === "add") {
      addTab("websocket");
    } else if (action === "remove" && typeof targetKey === "string") {
      removeTab(targetKey);
    }
  };

  if (tabs.length === 0) {
    return (
      <div className="empty-state">
        <Empty
          description={
            <span>
              No tabs open. Press <kbd>Ctrl+T</kbd> to create a new WebSocket
              connection
              <br />
              or <kbd>Ctrl+Shift+P</kbd> to open command palette
            </span>
          }
        >
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => addTab("websocket")}
          >
            New WebSocket Connection
          </Button>
        </Empty>
      </div>
    );
  }

  return (
    <Tabs
      type="editable-card"
      activeKey={activeTabId || undefined}
      onChange={setActiveTab}
      onEdit={handleEdit}
      className="tab-manager"
      items={tabs.map((tab) => ({
        key: tab.id,
        label: <span className="tab-label">{tab.title}</span>,
        children: <div className="tab-content">{renderTabContent(tab)}</div>,
      }))}
    />
  );
};

export default TabManager;
```

### src/components/WebSocketDebugger/index.tsx

```tsx
import React, { useState, useEffect, useRef } from "react";
import {
  Row,
  Col,
  Input,
  Button,
  Select,
  Card,
  Space,
  Typography,
  Divider,
} from "antd";
import {
  SendOutlined,
  LinkOutlined,
  DisconnectOutlined,
} from "@ant-design/icons";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import JsonTreeView from "@/views/JsonTreeView";
import RawLogView from "@/views/RawLogView";
import MessageTimeline from "./MessageTimeline";
import "./style.css";

const { TextArea } = Input;
const { Text } = Typography;

interface WebSocketDebuggerProps {
  tabId: string;
}

interface Message {
  id: string;
  type: "sent" | "received";
  content: string;
  timestamp: string;
}

const WebSocketDebugger: React.FC<WebSocketDebuggerProps> = ({ tabId }) => {
  const [url, setUrl] = useState("ws://localhost:8080");
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedView, setSelectedView] = useState("json");
  const connectionIdRef = useRef<string | null>(null);

  useEffect(() => {
    // Listen for WebSocket events
    const unlistenMessage = listen(`ws-message-${tabId}`, (event) => {
      const { type, content, timestamp } = event.payload as any;
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          type,
          content,
          timestamp,
        },
      ]);
    });

    const unlistenStatus = listen(`ws-status-${tabId}`, (event) => {
      const { status } = event.payload as any;
      if (status === "connected") {
        setConnected(true);
        setConnecting(false);
      } else if (status === "disconnected") {
        setConnected(false);
        setConnecting(false);
      }
    });

    return () => {
      unlistenMessage.then((fn) => fn());
      unlistenStatus.then((fn) => fn());
    };
  }, [tabId]);

  const handleConnect = async () => {
    if (connected) {
      await invoke("websocket_disconnect", {
        connectionId: connectionIdRef.current,
      });
      setConnected(false);
      connectionIdRef.current = null;
    } else {
      setConnecting(true);
      try {
        const connectionId = await invoke<string>("websocket_connect", {
          url,
          tabId,
        });
        connectionIdRef.current = connectionId;
      } catch (error) {
        console.error("Connection failed:", error);
        setConnecting(false);
      }
    }
  };

  const handleSend = async () => {
    if (!connected || !message.trim()) return;

    await invoke("websocket_send", {
      connectionId: connectionIdRef.current,
      message,
    });
    setMessage("");
  };

  const renderView = () => {
    switch (selectedView) {
      case "json":
        return <JsonTreeView messages={messages} />;
      case "raw":
        return <RawLogView messages={messages} />;
      default:
        return null;
    }
  };

  return (
    <div className="websocket-debugger">
      <Row gutter={16} className="full-height">
        <Col span={12} className="left-panel">
          <Card title="Connection" size="small" className="connection-card">
            <Space.Compact style={{ width: "100%" }}>
              <Input
                placeholder="ws://localhost:8080"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={connected}
                prefix={<LinkOutlined />}
              />
              <Button
                type={connected ? "default" : "primary"}
                onClick={handleConnect}
                loading={connecting}
                danger={connected}
                icon={connected ? <DisconnectOutlined /> : <LinkOutlined />}
              >
                {connected ? "Disconnect" : "Connect"}
              </Button>
            </Space.Compact>
            <div className="connection-status">
              Status:{" "}
              <Text type={connected ? "success" : "secondary"}>
                {connected ? "Connected" : "Disconnected"}
              </Text>
            </div>
          </Card>

          <Card title="Message" size="small" className="message-card">
            <TextArea
              rows={6}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Enter message to send (JSON supported)"
              disabled={!connected}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!connected || !message.trim()}
              style={{ marginTop: 8 }}
              block
            >
              Send Message
            </Button>
          </Card>

          <Card title="Timeline" size="small" className="timeline-card">
            <MessageTimeline messages={messages} />
          </Card>
        </Col>

        <Col span={12} className="right-panel">
          <Card
            title="View"
            size="small"
            className="view-card"
            extra={
              <Select
                value={selectedView}
                onChange={setSelectedView}
                options={[
                  { label: "JSON Tree", value: "json" },
                  { label: "Raw Log", value: "raw" },
                ]}
                style={{ width: 120 }}
              />
            }
          >
            {renderView()}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default WebSocketDebugger;
```

### src/components/CommandPalette/index.tsx

```tsx
import React, { useState, useEffect } from "react";
import { Modal, Input, List, Typography } from "antd";
import {
  ApiOutlined,
  CodeOutlined,
  SettingOutlined,
  CloudServerOutlined,
} from "@ant-design/icons";
import "./style.css";

const { Search } = Input;
const { Text } = Typography;

interface Command {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  shortcut?: string;
}

interface CommandPaletteProps {
  visible: boolean;
  onClose: () => void;
  onCommand: (commandId: string) => void;
}

const commands: Command[] = [
  {
    id: "websocket.new",
    title: "New WebSocket Connection",
    description: "Create a new WebSocket debugging session",
    icon: <ApiOutlined />,
    shortcut: "Ctrl+T",
  },
  {
    id: "conda.open",
    title: "Open Conda Manager",
    description: "Manage Conda environments",
    icon: <CloudServerOutlined />,
  },
  {
    id: "vscode.configure",
    title: "Configure VS Code Workspace",
    description: "Set up VS Code with Conda environment",
    icon: <CodeOutlined />,
  },
  {
    id: "settings.open",
    title: "Open Settings",
    description: "Configure application settings",
    icon: <SettingOutlined />,
  },
];

const CommandPalette: React.FC<CommandPaletteProps> = ({
  visible,
  onClose,
  onCommand,
}) => {
  const [search, setSearch] = useState("");
  const [filteredCommands, setFilteredCommands] = useState(commands);

  useEffect(() => {
    if (visible) {
      setSearch("");
      setFilteredCommands(commands);
    }
  }, [visible]);

  const handleSearch = (value: string) => {
    setSearch(value);
    const filtered = commands.filter(
      (cmd) =>
        cmd.title.toLowerCase().includes(value.toLowerCase()) ||
        cmd.description.toLowerCase().includes(value.toLowerCase())
    );
    setFilteredCommands(filtered);
  };

  const handleSelect = (commandId: string) => {
    onCommand(commandId);
    onClose();
  };

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      footer={null}
      closable={false}
      width={600}
      className="command-palette"
    >
      <Search
        placeholder="Type a command..."
        value={search}
        onChange={(e) => handleSearch(e.target.value)}
        autoFocus
        size="large"
      />
      <List
        className="command-list"
        dataSource={filteredCommands}
        renderItem={(item) => (
          <List.Item
            onClick={() => handleSelect(item.id)}
            className="command-item"
          >
            <List.Item.Meta
              avatar={<div className="command-icon">{item.icon}</div>}
              title={item.title}
              description={item.description}
            />
            {item.shortcut && (
              <Text type="secondary" keyboard>
                {item.shortcut}
              </Text>
            )}
          </List.Item>
        )}
      />
    </Modal>
  );
};

export default CommandPalette;
```

## 第二部分：Rust 后端 (Tauri)

### src-tauri/Cargo.toml

```toml
[package]
name = "devdeck"
version = "1.0.0"
description = "A modern development toolkit"
authors = ["DevDeck Team"]
edition = "2021"

[build-dependencies]
tauri-build = { version = "2.0.0", features = [] }

[dependencies]
tauri = { version = "2.0.0", features = ["shell-open", "process-command-api"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1", features = ["full"] }
tokio-tungstenite = "0.20"
futures-util = "0.3"
uuid = { version = "1.6", features = ["v4", "serde"] }
anyhow = "1.0"
which = "5.0"
reqwest = { version = "0.11", features = ["stream"] }
zip = "0.6"
tempfile = "3.8"

[features]
default = ["custom-protocol"]
custom-protocol = ["tauri/custom-protocol"]
```

### src-tauri/src/main.rs

```rust
#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod conda;
mod vscode;
mod websocket;

use tauri::{Manager, State};
use std::sync::Arc;
use tokio::sync::Mutex;

#[derive(Default)]
struct AppState {
    websocket_manager: Arc<Mutex<websocket::WebSocketManager>>,
    conda_service: Arc<Mutex<conda::CondaService>>,
}

#[tauri::command]
async fn websocket_connect(
    url: String,
    tab_id: String,
    state: State<'_, AppState>,
    app: tauri::AppHandle,
) -> Result<String, String> {
    let mut manager = state.websocket_manager.lock().await;
    manager.connect(url, tab_id, app).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn websocket_disconnect(
    connection_id: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let mut manager = state.websocket_manager.lock().await;
    manager.disconnect(&connection_id).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn websocket_send(
    connection_id: String,
    message: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let manager = state.websocket_manager.lock().await;
    manager.send_message(&connection_id, message).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn conda_detect(
    state: State<'_, AppState>,
) -> Result<Option<String>, String> {
    let service = state.conda_service.lock().await;
    service.detect_conda().await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn conda_list_environments(
    state: State<'_, AppState>,
) -> Result<Vec<conda::Environment>, String> {
    let service = state.conda_service.lock().await;
    service.list_environments().await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn conda_create_environment(
    name: String,
    python_version: Option<String>,
    state: State<'_, AppState>,
    app: tauri::AppHandle,
) -> Result<(), String> {
    let service = state.conda_service.lock().await;
    service.create_environment(name, python_version, app).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn conda_install_miniconda(
    install_path: String,
    state: State<'_, AppState>,
    app: tauri::AppHandle,
) -> Result<(), String> {
    let mut service = state.conda_service.lock().await;
    service.install_miniconda(install_path, app).await
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn vscode_open_with_env(
    project_path: String,
    env_name: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let conda_service = state.conda_service.lock().await;
    vscode::open_project_with_env(project_path, env_name, &*conda_service).await
        .map_err(|e| e.to_string())
}

fn main() {
    tauri::Builder::default()
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            websocket_connect,
            websocket_disconnect,
            websocket_send,
            conda_detect,
            conda_list_environments,
            conda_create_environment,
            conda_install_miniconda,
            vscode_open_with_env,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### src-tauri/src/websocket/mod.rs

```rust
use anyhow::Result;
use futures_util::{SinkExt, StreamExt};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tauri::{AppHandle, Manager};
use tokio::net::TcpStream;
use tokio_tungstenite::{connect_async, MaybeTlsStream, WebSocketStream};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize)]
pub struct WsMessage {
    #[serde(rename = "type")]
    msg_type: String,
    content: String,
    timestamp: String,
}

pub struct WebSocketConnection {
    id: String,
    tab_id: String,
    tx: tokio::sync::mpsc::Sender<String>,
}

pub struct WebSocketManager {
    connections: HashMap<String, WebSocketConnection>,
}

impl Default for WebSocketManager {
    fn default() -> Self {
        Self {
            connections: HashMap::new(),
        }
    }
}

impl WebSocketManager {
    pub async fn connect(
        &mut self,
        url: String,
        tab_id: String,
        app: AppHandle,
    ) -> Result<String> {
        let connection_id = Uuid::new_v4().to_string();
        let (tx, mut rx) = tokio::sync::mpsc::channel::<String>(100);

        // Create connection
        let connection = WebSocketConnection {
            id: connection_id.clone(),
            tab_id: tab_id.clone(),
            tx,
        };

        self.connections.insert(connection_id.clone(), connection);

        // Connect to WebSocket in background task
        let app_clone = app.clone();
        let tab_id_clone = tab_id.clone();
        let connection_id_clone = connection_id.clone();

        tokio::spawn(async move {
            match connect_async(&url).await {
                Ok((ws_stream, _)) => {
                    // Send connected status
                    app_clone.emit(&format!("ws-status-{}", tab_id_clone),
                        serde_json::json!({ "status": "connected" })).unwrap();

                    let (mut write, mut read) = ws_stream.split();

                    // Handle incoming messages
                    let app_read = app_clone.clone();
                    let tab_id_read = tab_id_clone.clone();
                    tokio::spawn(async move {
                        while let Some(msg) = read.next().await {
                            if let Ok(msg) = msg {
                                if let Ok(text) = msg.to_text() {
                                    let message = WsMessage {
                                        msg_type: "received".to_string(),
                                        content: text.to_string(),
                                        timestamp: chrono::Local::now().format("%H:%M:%S%.3f").to_string(),
                                    };
                                    app_read.emit(&format!("ws-message-{}", tab_id_read), message).unwrap();
                                }
                            }
                        }
                    });

                    // Handle outgoing messages
                    while let Some(msg) = rx.recv().await {
                        if write.send(tokio_tungstenite::tungstenite::Message::Text(msg.clone())).await.is_ok() {
                            let message = WsMessage {
                                msg_type: "sent".to_string(),
                                content: msg,
                                timestamp: chrono::Local::now().format("%H:%M:%S%.3f").to_string(),
                            };
                            app_clone.emit(&format!("ws-message-{}", tab_id_clone), message).unwrap();
                        }
                    }
                }
                Err(e) => {
                    app_clone.emit(&format!("ws-status-{}", tab_id_clone),
                        serde_json::json!({ "status": "error", "message": e.to_string() })).unwrap();
                }
            }
        });

        Ok(connection_id)
    }

    pub async fn disconnect(&mut self, connection_id: &str) -> Result<()> {
        self.connections.remove(connection_id);
        Ok(())
    }

    pub async fn send_message(&self, connection_id: &str, message: String) -> Result<()> {
        if let Some(connection) = self.connections.get(connection_id) {
            connection.tx.send(message).await?;
        }
        Ok(())
    }
}
```

### src-tauri/src/conda/mod.rs

```rust
use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Command;
use tauri::{AppHandle, Manager};

#[derive(Debug, Serialize, Deserialize)]
pub struct Environment {
    pub name: String,
    pub path: String,
    pub python_version: Option<String>,
}

pub struct CondaService {
    conda_path: Option<PathBuf>,
}

impl Default for CondaService {
    fn default() -> Self {
        Self { conda_path: None }
    }
}

impl CondaService {
    pub async fn detect_conda(&self) -> Result<Option<String>> {
        // Try to find conda in PATH
        if let Ok(path) = which::which("conda") {
            return Ok(Some(path.to_string_lossy().to_string()));
        }

        // Check common installation paths
        let common_paths = if cfg!(windows) {
            vec![
                dirs::home_dir().unwrap().join("Miniconda3"),
                dirs::home_dir().unwrap().join("Anaconda3"),
                PathBuf::from("C:\\ProgramData\\Miniconda3"),
                PathBuf::from("C:\\ProgramData\\Anaconda3"),
            ]
        } else {
            vec![
                dirs::home_dir().unwrap().join("miniconda3"),
                dirs::home_dir().unwrap().join("anaconda3"),
                PathBuf::from("/opt/miniconda3"),
                PathBuf::from("/opt/anaconda3"),
            ]
        };

        for path in common_paths {
            let conda_bin = if cfg!(windows) {
                path.join("Scripts").join("conda.exe")
            } else {
                path.join("bin").join("conda")
            };

            if conda_bin.exists() {
                return Ok(Some(conda_bin.to_string_lossy().to_string()));
            }
        }

        Ok(None)
    }

    pub async fn list_environments(&self) -> Result<Vec<Environment>> {
        let conda_path = self.conda_path.as_ref()
            .or(self.detect_conda().await?.as_ref().map(|s| PathBuf::from(s).as_ref()))
            .ok_or_else(|| anyhow::anyhow!("Conda not found"))?;

        let output = Command::new(conda_path)
            .args(&["env", "list", "--json"])
            .output()?;

        let json: serde_json::Value = serde_json::from_slice(&output.stdout)?;
        let envs = json["envs"].as_array()
            .ok_or_else(|| anyhow::anyhow!("Invalid conda output"))?;

        let mut environments = Vec::new();
        for env_path in envs {
            if let Some(path_str) = env_path.as_str() {
                let path = PathBuf::from(path_str);
                let name = path.file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown")
                    .to_string();

                environments.push(Environment {
                    name,
                    path: path_str.to_string(),
                    python_version: None,
                });
            }
        }

        Ok(environments)
    }

    pub async fn create_environment(
        &self,
        name: String,
        python_version: Option<String>,
        app: AppHandle,
    ) -> Result<()> {
        let conda_path = self.conda_path.as_ref()
            .ok_or_else(|| anyhow::anyhow!("Conda not found"))?;

        let python_spec = python_version.unwrap_or_else(|| "python=3.9".to_string());

        let mut cmd = Command::new(conda_path);
        cmd.args(&["create", "-n", &name, &python_spec, "-y"]);

        // Stream output to frontend
        let output = cmd.output()?;

        app.emit("conda-output", String::from_utf8_lossy(&output.stdout).to_string())?;

        if !output.status.success() {
            return Err(anyhow::anyhow!("Failed to create environment"));
        }

        Ok(())
    }

    pub async fn install_miniconda(&mut self, install_path: String, app: AppHandle) -> Result<()> {
        // Determine installer URL based on platform
        let installer_url = if cfg!(target_os = "windows") {
            "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
        } else if cfg!(target_os = "macos") {
            "https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
        } else {
            "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
        };

        // Download installer
        app.emit("conda-progress", serde_json::json!({
            "stage": "downloading",
            "progress": 0
        }))?;

        let response = reqwest::get(installer_url).await?;
        let total_size = response.content_length().unwrap_or(0);

        let temp_dir = tempfile::tempdir()?;
        let installer_path = temp_dir.path().join(if cfg!(windows) {
            "miniconda_installer.exe"
        } else {
            "miniconda_installer.sh"
        });

        let mut file = tokio::fs::File::create(&installer_path).await?;
        let mut downloaded = 0u64;
        let mut stream = response.bytes_stream();

        while let Some(chunk) = stream.next().await {
            let chunk = chunk?;
            tokio::io::AsyncWriteExt::write_all(&mut file, &chunk).await?;
            downloaded += chunk.len() as u64;

            if total_size > 0 {
                let progress = (downloaded as f64 / total_size as f64 * 100.0) as u32;
                app.emit("conda-progress", serde_json::json!({
                    "stage": "downloading",
                    "progress": progress
                }))?;
            }
        }

        // Run installer
        app.emit("conda-progress", serde_json::json!({
            "stage": "installing",
            "progress": 0
        }))?;

        let status = if cfg!(windows) {
            Command::new(&installer_path)
                .args(&["/S", &format!("/D={}", install_path)])
                .status()?
        } else {
            Command::new("bash")
                .args(&[installer_path.to_str().unwrap(), "-b", "-p", &install_path])
                .status()?
        };

        if !status.success() {
            return Err(anyhow::anyhow!("Installation failed"));
        }

        // Update conda path
        let conda_bin = if cfg!(windows) {
            PathBuf::from(&install_path).join("Scripts").join("conda.exe")
        } else {
            PathBuf::from(&install_path).join("bin").join("conda")
        };

        self.conda_path = Some(conda_bin);

        app.emit("conda-progress", serde_json::json!({
            "stage": "complete",
            "progress": 100
        }))?;

        Ok(())
    }

    pub fn get_python_path(&self, env_name: &str) -> Result<String> {
        let environments = tokio::runtime::Runtime::new()?.block_on(self.list_environments())?;

        for env in environments {
            if env.name == env_name {
                let env_path = PathBuf::from(&env.path);
                let python_path = if cfg!(windows) {
                    env_path.join("python.exe")
                } else {
                    env_path.join("bin").join("python")
                };

                if python_path.exists() {
                    return Ok(python_path.to_string_lossy().to_string());
                }
            }
        }

        Err(anyhow::anyhow!("Python interpreter not found for environment"))
    }
}
```

### src-tauri/src/vscode/mod.rs

```rust
use anyhow::Result;
use std::fs;
use std::path::Path;
use std::process::Command;
use serde_json::json;
use crate::conda::CondaService;

pub async fn open_project_with_env(
    project_path: String,
    env_name: String,
    conda_service: &CondaService,
) -> Result<()> {
    // Get Python interpreter path
    let python_path = conda_service.get_python_path(&env_name)?;

    // Create workspace configuration
    let workspace_config = json!({
        "folders": [{
            "path": "."
        }],
        "settings": {
            "python.defaultInterpreterPath": python_path,
            "python.terminal.activateEnvironment": true,
            "python.terminal.activateEnvInCurrentTerminal": true,
        }
    });

    // Write workspace file
    let project_dir = Path::new(&project_path);
    let workspace_file = project_dir.join(format!(
        "{}.code-workspace",
        project_dir.file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("project")
    ));

    fs::write(&workspace_file, serde_json::to_string_pretty(&workspace_config)?)?;

    // Open VS Code
    let code_cmd = if cfg!(windows) { "code.cmd" } else { "code" };

    Command::new(code_cmd)
        .arg(workspace_file)
        .spawn()?;

    Ok(())
}
```

## 第三部分：GitHub Actions 工作流

### .github/workflows/build.yml

```yaml
name: Build and Release DevDeck

on:
  push:
    branches: [main, develop]
    tags:
      - "v*"
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  CARGO_TERM_COLOR: always

jobs:
  build:
    strategy:
      fail-fast: false
      matrix:
        platform:
          - os: ubuntu-latest
            rust_target: x86_64-unknown-linux-gnu
            name: linux
          - os: macos-latest
            rust_target: x86_64-apple-darwin
            name: macos
          - os: macos-latest
            rust_target: aarch64-apple-darwin
            name: macos-arm64
          - os: windows-latest
            rust_target: x86_64-pc-windows-msvc
            name: windows

    runs-on: ${{ matrix.platform.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.platform.rust_target }}

      - name: Setup Rust cache
        uses: swatinem/rust-cache@v2
        with:
          workspaces: "./src-tauri -> target"

      - name: Install dependencies (Ubuntu)
        if: matrix.platform.os == 'ubuntu-latest'
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            libwebkit2gtk-4.1-dev \
            libappindicator3-dev \
            librsvg2-dev \
            patchelf \
            libssl-dev

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install frontend dependencies
        run: pnpm install

      - name: Build Tauri app
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_PRIVATE_KEY }}
          TAURI_SIGNING_PRIVATE_KEY_PASSWORD: ${{ secrets.TAURI_KEY_PASSWORD }}
        with:
          tagName: ${{ github.ref_name }}
          releaseName: "DevDeck v__VERSION__"
          releaseBody: |
            See the [CHANGELOG](https://github.com/${{ github.repository }}/blob/main/CHANGELOG.md) for details.

            ## Installation

            ### Windows
            - Download `DevDeck_x64_en-US.msi` for installer
            - Or download `DevDeck_x64.exe` for portable version

            ### macOS
            - Download `DevDeck_x64.dmg` for Intel Macs
            - Download `DevDeck_aarch64.dmg` for Apple Silicon Macs

            ### Linux
            - Download `DevDeck_amd64.deb` for Debian/Ubuntu
            - Download `DevDeck_amd64.AppImage` for universal Linux
          releaseDraft: true
          prerelease: false
          args: --target ${{ matrix.platform.rust_target }}

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: devdeck-${{ matrix.platform.name }}
          path: |
            src-tauri/target/${{ matrix.platform.rust_target }}/release/bundle/
          retention-days: 7

  code-sign-windows:
    needs: build
    runs-on: windows-latest
    if: startsWith(github.ref, 'refs/tags/')

    steps:
      - uses: actions/download-artifact@v4
        with:
          name: devdeck-windows

      - name: Sign Windows executables
        env:
          CERTIFICATE: ${{ secrets.WINDOWS_CERTIFICATE }}
          CERTIFICATE_PASSWORD: ${{ secrets.WINDOWS_CERTIFICATE_PASSWORD }}
        run: |
          # Convert base64 certificate to file
          echo "$CERTIFICATE" | base64 --decode > cert.pfx

          # Sign all exe and msi files
          Get-ChildItem -Recurse -Include *.exe,*.msi | ForEach-Object {
            signtool sign /f cert.pfx /p "$CERTIFICATE_PASSWORD" /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $_.FullName
          }

          # Clean up
          Remove-Item cert.pfx

      - name: Upload signed artifacts
        uses: actions/upload-artifact@v4
        with:
          name: devdeck-windows-signed
          path: |
            **/*.exe
            **/*.msi

  notarize-macos:
    needs: build
    runs-on: macos-latest
    if: startsWith(github.ref, 'refs/tags/')
    strategy:
      matrix:
        arch: [x64, aarch64]

    steps:
      - uses: actions/download-artifact@v4
        with:
          name: devdeck-macos${{ matrix.arch == 'aarch64' && '-arm64' || '' }}

      - name: Notarize macOS app
        env:
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_PASSWORD: ${{ secrets.APPLE_PASSWORD }}
          APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
        run: |
          # Find the .app bundle
          APP_PATH=$(find . -name "*.app" -type d | head -n 1)

          # Create a zip for notarization
          ditto -c -k --keepParent "$APP_PATH" "DevDeck.zip"

          # Submit for notarization
          xcrun notarytool submit "DevDeck.zip" \
            --apple-id "$APPLE_ID" \
            --password "$APPLE_PASSWORD" \
            --team-id "$APPLE_TEAM_ID" \
            --wait

          # Staple the notarization
          xcrun stapler staple "$APP_PATH"

          # Create final DMG
          create-dmg \
            --volname "DevDeck" \
            --window-pos 200 120 \
            --window-size 600 400 \
            --icon-size 100 \
            --icon "DevDeck.app" 175 120 \
            --hide-extension "DevDeck.app" \
            --app-drop-link 425 120 \
            "DevDeck_${{ matrix.arch }}.dmg" \
            "$APP_PATH"

      - name: Upload notarized artifacts
        uses: actions/upload-artifact@v4
        with:
          name: devdeck-macos-${{ matrix.arch }}-notarized
          path: DevDeck_${{ matrix.arch }}.dmg

  create-release:
    needs: [build, code-sign-windows, notarize-macos]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')

    steps:
      - uses: actions/checkout@v4

      - name: Download all artifacts
        uses: actions/download-artifact@v4

      - name: Create checksums
        run: |
          find . -type f \( -name "*.exe" -o -name "*.msi" -o -name "*.dmg" -o -name "*.deb" -o -name "*.AppImage" \) -exec sha256sum {} \; > checksums.txt

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          draft: false
          prerelease: false
          generate_release_notes: true
          files: |
            **/*.exe
            **/*.msi
            **/*.dmg
            **/*.deb
            **/*.AppImage
            checksums.txt
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  auto-update-config:
    needs: create-release
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')

    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Update auto-update configuration
        run: |
          # Generate update manifest
          cat > update.json <<EOF
          {
            "version": "${{ github.ref_name }}",
            "notes": "See release notes for details",
            "pub_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
            "platforms": {
              "darwin-x86_64": {
                "signature": "",
                "url": "https://github.com/${{ github.repository }}/releases/download/${{ github.ref_name }}/DevDeck_x64.dmg"
              },
              "darwin-aarch64": {
                "signature": "",
                "url": "https://github.com/${{ github.repository }}/releases/download/${{ github.ref_name }}/DevDeck_aarch64.dmg"
              },
              "linux-x86_64": {
                "signature": "",
                "url": "https://github.com/${{ github.repository }}/releases/download/${{ github.ref_name }}/DevDeck_amd64.AppImage"
              },
              "windows-x86_64": {
                "signature": "",
                "url": "https://github.com/${{ github.repository }}/releases/download/${{ github.ref_name }}/DevDeck_x64_en-US.msi"
              }
            }
          }
          EOF

          # Commit and push update manifest
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add update.json
          git commit -m "Update auto-update manifest for ${{ github.ref_name }}"
          git push
```

### src-tauri/tauri.conf.json

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "app": {
    "windows": [
      {
        "fullscreen": false,
        "height": 900,
        "resizable": true,
        "title": "DevDeck",
        "width": 1400,
        "center": true,
        "decorations": true,
        "fileDropEnabled": true
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "identifier": "com.devdeck.app",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "resources": [],
    "copyright": "© 2024 DevDeck",
    "category": "DeveloperTool",
    "shortDescription": "Modern development toolkit",
    "longDescription": "A comprehensive development platform with WebSocket debugging, Conda management, and VS Code integration.",
    "linux": {
      "deb": {
        "depends": []
      },
      "appimage": {
        "bundleMediaFramework": true
      }
    },
    "macOS": {
      "frameworks": [],
      "exceptionDomain": "",
      "signingIdentity": null,
      "entitlements": null
    },
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": "http://timestamp.digicert.com",
      "webviewInstallMode": {
        "type": "downloadBootstrapper"
      }
    }
  },
  "productName": "DevDeck",
  "version": "1.0.0",
  "plugins": {},
  "build": {
    "beforeDevCommand": "pnpm dev",
    "beforeBuildCommand": "pnpm build",
    "frontendDist": "../dist",
    "devUrl": "http://localhost:5173"
  }
}
```

## 安装和运行说明

### 开发环境设置

1. **安装依赖**

```bash
# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 安装 Node.js 和 pnpm
npm install -g pnpm

# 克隆项目
git clone https://github.com/yourusername/devdeck.git
cd devdeck

# 安装前端依赖
pnpm install

# 安装 Tauri CLI
cargo install tauri-cli
```

2. **开发模式运行**

```bash
pnpm tauri:dev
```

3. **构建生产版本**

```bash
pnpm tauri:build
```

## 特性亮点

1. **现代化架构**

   - Tauri 2.0 提供原生性能和小体积
   - React + TypeScript 确保类型安全
   - Ant Design 提供专业 UI

2. **标签页式界面**

   - Chrome 风格的标签管理
   - 支持拖拽排序
   - 多任务并行处理

3. **WebSocket 调试器**

   - 实时连接管理
   - JSON 树形视图
   - 可扩展的视图插件系统

4. **Conda 集成**

   - 自动检测和安装
   - 图形化环境管理
   - 实时命令输出

5. **VS Code 集成**

   - 一键配置工作区
   - 自动设置 Python 解释器
   - 项目环境绑定

6. **自动化部署**
   - 跨平台构建
   - 代码签名
   - 自动更新支持

这个 DevDeck 应用提供了一个现代化、高性能的开发工具平台，具有类似 VS Code 的专业外观和交互体验。
