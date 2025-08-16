# 配置文件说明和示例

配置文件 `configs/configs.json` 采用JSON格式，可以直接编辑。

## 配置项说明

### 静置触发 (idle_trigger)
当系统空闲指定时间后自动执行同步。

```json
"idle_trigger": {
  "enabled": true,           // 是否启用静置触发
  "idle_minutes": 10,        // 静置分钟数
  "cooldown_minutes": 20     // 全局冷却时间（所有触发类型共享）
}
```

**注意**：`cooldown_minutes` 是全局冷却时间，适用于手动、定时、空闲所有触发方式，防止过于频繁的同步操作。

### 定时触发 (scheduled_trigger)
在指定时间自动执行同步。

```json
"scheduled_trigger": {
  "enabled": true,           // 是否启用定时触发
  "time": "05:00",          // 执行时间 (24小时格式)
  "days": ["daily"]         // 执行日期
}
```

**days 选项：**
- `["daily"]` - 每天执行
- `["monday", "friday"]` - 每周一和周五
- `["saturday", "sunday"]` - 每周末

### 同步设置 (sync_settings)
```json
"sync_settings": {
  "wait_after_sync_minutes": 5,  // OneDrive同步等待时间
  "max_retry_attempts": 3,       // 失败重试次数
  "debug_mode": false            // 调试模式开关
}
```

**debug_mode 说明**：
- `false`（默认）：执行完整的4步同步流程
- `true`：短路同步流程，3秒后直接返回成功（便于开发调试）

### 日志设置 (logging)
```json
"logging": {
  "enabled": true,          // 是否启用日志
  "level": "info",         // 日志级别
  "max_log_files": 5       // 最大日志文件数
}
```

**level 选项：** `debug`, `info`, `warning`, `error`

## 常用配置示例

### 示例1：仅启用静置触发（系统空闲15分钟后执行）
```json
{
  "idle_trigger": {
    "enabled": true,
    "idle_minutes": 15,
    "cooldown_minutes": 20
  },
  "scheduled_trigger": {
    "enabled": false
  }
}
```

### 示例2：仅启用定时触发（每天凌晨3点执行）
```json
{
  "idle_trigger": {
    "enabled": false
  },
  "scheduled_trigger": {
    "enabled": true,
    "time": "03:00",
    "days": ["daily"]
  }
}
```

### 示例3：工作日定时触发（周一到周五早上8点）
```json
{
  "scheduled_trigger": {
    "enabled": true,
    "time": "08:00",
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
  }
}
```

### 示例4：双重触发（静置+定时）
```json
{
  "idle_trigger": {
    "enabled": true,
    "idle_minutes": 10,
    "cooldown_minutes": 20
  },
  "scheduled_trigger": {
    "enabled": true,
    "time": "05:00",
    "days": ["daily"]
  }
}
```

## 配置文件管理

```bash
# 创建默认配置
python core/config_manager.py create

# 验证配置是否正确
python core/config_manager.py validate

# 查看当前配置
python core/config_manager.py show
```

## 注意事项

1. **时间格式**：使用24小时格式，如 "05:00", "23:30"
2. **静置时间**：建议设置为5分钟以上，避免频繁触发
3. **日志级别**：生产环境建议使用 "info"，调试时使用 "debug"
4. **配置修改**：修改配置后需要重启监控服务才能生效