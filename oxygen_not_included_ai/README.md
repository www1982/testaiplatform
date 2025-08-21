# 缺氧 AI Python 项目

## 概述

这个项目是一个使用 Python 开发的缺氧游戏 AI，旨在通过自动化规划和执行来优化游戏过程。

## 安装

1. 克隆仓库。
2. 安装依赖：`pip install -r requirements.txt`。

## 使用

运行`python main.py`启动 AI。

## 优化变化

- 更新 requirements.txt 添加 orjson 和 pydantic 以提高 JSON 处理和数据验证效率。
- 在 game_interface.py 添加 websocket 重连机制（每 5 秒重试）和异常处理（捕捉 ConnectionClosed 并日志记录）。
- 在 context_slicer.py 增强网格分析，映射 Mod CellInfo 字段（如提取 disease 和 temperature），替换占位符逻辑为完整 Mod 元素映射（e.g., "Unobtanium"分类为 minerals）。
- 在 planner.py 整合事件监听（添加 handle_event 方法处理 Mod GameEvent，如研究完成触发计划调整），并统一字段映射（e.g., 使用 duplicants["stress"]）。

## Mod 集成指南

- 确保 Mod API 兼容 websocket 事件广播。
- 在 context_slicer.py 中扩展 mod_element_map 以支持新 Mod 元素。
- 使用 planner.py 的 handle_event 处理自定义 Mod 事件，调整 AI 计划。
- 测试 Mod 字段映射兼容性，使用统一字段如"stress"而非旧 DuplicantState.Stress。
