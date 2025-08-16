# 测试文件说明

本目录包含各种功能测试、实验性功能和开发工具的测试脚本。

## 🧪 GUI性能测试工具

| 文件 | 用途 | 说明 |
|------|------|------|
| `gui_profiler.py` | GUI性能分析器 | 分析GUI界面的性能表现和响应时间 |
| `gui_profiler_integration.py` | GUI性能分析集成版 | 集成版本的性能分析工具 |
| `simple_gui_profiler.py` | 简化版性能分析器 | 轻量级GUI性能监控工具 |
| `gui_structure_analyzer.py` | GUI结构分析器 | 分析界面结构和布局问题 |
| `performance_debug_config.json` | 性能调试配置 | 性能测试的配置参数 |

## 🔐 微信自动登录测试

> 这些测试文件用于验证微信自动登录功能，该功能目前为实验性功能。

| 文件 | 用途 | 说明 |
|------|------|------|
| `auto_test_login.py` | 自动化登录测试 | 非交互式测试，自动执行关闭-启动-登录流程 |
| `simple_test_login.py` | 简单登录测试 | 基础的登录功能验证 |
| `test_auto_login.py` | 登录功能综合测试 | 包含窗口检测、按钮识别等完整测试 |
| `test_login_only.py` | 专项登录测试 | 仅测试登录相关功能 |
| `test_graceful_close.py` | 优雅关闭测试 | 测试通过Windows消息优雅关闭微信 |
| `test_wechat_params.py` | 启动参数测试 | 测试微信的各种命令行启动参数 |

## 使用方法

```bash
# 进入测试目录
cd tests

# 运行特定测试
python auto_test_login.py
python test_graceful_close.py
python test_wechat_params.py
```

## 注意事项

⚠️ **重要提醒**：
- 这些测试可能会影响当前运行的微信进程
- 测试前请保存重要的微信对话
- 某些测试需要管理员权限
- 自动登录功能为实验性功能，可能不稳定

## 技术背景

这些测试文件是为了解决"微信重启后需要手动登录"问题而开发的。虽然基础技术方案已经实现，但由于技术复杂性（Windows API、字符编码、界面兼容性等），目前作为未来功能保留。

详细的技术方案和分析请参考同级目录的 `WECHAT_LOGIN_SOLUTION.md` 文件。