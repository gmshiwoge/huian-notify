# Huian Notify - 服务参数说明

## 📱 notify 服务

每个注册的设备都有独立的 notify 服务，命名格式：`notify.<设备名称>`

例如：
- `notify.iphone_65050`
- `notify.ipadpro`
- `notify.xiaoming_iphone`

---

## 📋 所有可用参数

### 必填参数

#### `message` (string)
**推送通知的消息正文**

```yaml
service: notify.iphone_65050
data:
  message: "车库门已经打开10分钟了"
```

---

### 可选参数

#### `title` (string)
**推送通知的标题**

```yaml
service: notify.iphone_65050
data:
  title: "车库门提醒"
  message: "车库门已经打开10分钟了"
```

---

#### `data` (object)
**自定义推送选项**

支持的子参数：

##### `data.badge` (string)
应用角标数量
- `"+1"`: 角标数加 1
- `"5"`: 设置角标为 5
- `"0"`: 清除角标

##### `data.sound` (string)
通知铃声
- `"default"`: 默认铃声
- 自定义铃声文件名（需在应用中预先配置）

---

## 📖 使用示例

### 基本通知

```yaml
service: notify.iphone_65050
data:
  message: "这是一条测试消息"
```

---

### 带标题的通知

```yaml
service: notify.iphone_65050
data:
  title: "🏠 欢迎回家"
  message: "家中设备已就绪"
```

---

### 自定义角标和铃声

```yaml
service: notify.iphone_65050
data:
  title: "新消息"
  message: "您有一条新消息"
  data:
    badge: "+1"      # 角标加 1
    sound: "default" # 默认铃声
```

---

### 清除角标

```yaml
service: notify.iphone_65050
data:
  message: "角标已清除"
  data:
    badge: "0"  # 清除角标
```

---

### 设置固定角标数

```yaml
service: notify.iphone_65050
data:
  message: "您有5条未读消息"
  data:
    badge: "5"  # 角标设为 5
```

---

## 🔧 在自动化中使用

### 示例1：回家欢迎

```yaml
automation:
  - alias: "回家欢迎"
    trigger:
      - platform: state
        entity_id: device_tracker.iphone_65050
        to: "home"
    action:
      - service: notify.iphone_65050
        data:
          title: "🏠 欢迎回家"
          message: "家中温度：{{ states('sensor.living_room_temperature') }}°C"
          data:
            badge: "+1"
            sound: "default"
```

---

### 示例2：门窗警报

```yaml
automation:
  - alias: "门窗打开警报"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    condition:
      - condition: state
        entity_id: alarm_control_panel.home
        state: "armed_away"
    action:
      - service: notify.iphone_65050
        data:
          title: "⚠️ 安全警报"
          message: "前门已打开！"
          data:
            badge: "99"  # 紧急情况用大数字
            sound: "default"
```

---

### 示例3：定时提醒

```yaml
automation:
  - alias: "晚上关灯提醒"
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: state
        entity_id: light.bedroom
        state: "on"
    action:
      - service: notify.iphone_65050
        data:
          title: "💡 睡前提醒"
          message: "卧室灯还开着哦"
          data:
            sound: "default"
```

---

## 🎯 参数对照表

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `message` | string | ✅ | - | 消息正文 |
| `title` | string | ❌ | - | 消息标题 |
| `data` | object | ❌ | `{}` | 额外选项 |
| `data.badge` | string | ❌ | - | 角标数量 |
| `data.sound` | string | ❌ | `"default"` | 铃声文件 |

---

## ⚠️ 注意事项

1. **角标格式**
   - 必须是**字符串**，不是数字
   - ✅ 正确：`badge: "+1"` 或 `badge: "5"`
   - ❌ 错误：`badge: 1` 或 `badge: 5`

2. **消息长度**
   - 标题建议不超过 20 字符
   - 消息建议不超过 200 字符
   - 超长内容会被截断

3. **铃声文件**
   - 必须是应用内置或用户自定义的铃声
   - 文件格式：`.caf`, `.aiff`, `.wav`
   - 如果铃声不存在，使用默认铃声

4. **推送频率**
   - 建议不要过于频繁（每分钟不超过10条）
   - 避免短时间内大量推送，可能被系统限流

---

## 🔍 调试技巧

### 查看 Home Assistant 日志

```
配置 > 系统 > 日志
搜索：huian_notify
```

### 测试推送

在 **开发者工具 > 服务** 中测试：

```yaml
service: notify.iphone_65050
data:
  title: "测试"
  message: "这是一条测试消息"
  data:
    badge: "+1"
    sound: "default"
```

点击 **调用服务** 按钮发送。

---

## 📞 支持

- **GitHub**: https://github.com/gmshiwoge/huian-notify
- **Issues**: https://github.com/gmshiwoge/huian-notify/issues

---

## 📝 更新日志

- **v2.2.0**: 添加 services.yaml 和参数文档
- **v2.1.0**: 支持设备名称更新
- **v2.0.0**: 多设备支持和统一命名

