# JPush Notify - Home Assistant 自定义集成

适用于 Home Assistant 2025+ 的极光推送（JPush）通知服务集成。

## 🌟 特性

- ✅ **Web UI配置** - 通过Home Assistant Web界面轻松添加设备
- ✅ **安全存储** - AppKey和Master Secret自动加密存储在Config Entry
- ✅ **简单易用** - 用户只需输入Registration ID
- ✅ **多设备支持** - 可以添加多个iOS设备
- ✅ **标准Notify服务** - 完全兼容Home Assistant的notify平台
- ✅ **生产/开发环境** - 支持切换APNs环境
- ✅ **中英文界面** - 支持中文和英文UI

## 📦 安装

### 方式1：手动安装

1. 将 `custom_components/jpush_notify` 文件夹复制到您的Home Assistant配置目录下的 `custom_components` 文件夹中

   ```
   /config/
   └── custom_components/
       └── jpush_notify/
           ├── __init__.py
           ├── config_flow.py
           ├── const.py
           ├── manifest.json
           ├── notify.py
           ├── strings.json
           └── translations/
               └── zh-Hans.json
   ```

2. 重启Home Assistant

### 方式2：HACS（推荐，需要先发布到GitHub）

1. 在HACS中添加自定义仓库
2. 搜索"JPush Notify"
3. 点击安装
4. 重启Home Assistant

## 🚀 配置

### 添加集成

1. 打开Home Assistant
2. 进入 **配置** > **设备与服务** > **添加集成**
3. 搜索 **JPush Notify**
4. 输入您的 **Registration ID**
   - 📱 在App的设置页面 > 通知 一栏可以找到并复制
5. （可选）勾选"生产环境"（发布版本使用）
6. 点击提交

系统会自动发送一条测试通知到您的设备，验证配置是否正确。

### 添加多个设备

重复上述步骤，输入不同设备的Registration ID即可。每个设备会创建一个独立的notify实体：

- `notify.jpush` - 第一个设备
- `notify.jpush_2` - 第二个设备
- `notify.jpush_3` - 第三个设备

## 📱 使用方法

### 基本用法

在自动化或脚本中：

```yaml
service: notify.jpush
data:
  title: "🏠 Home Assistant"
  message: "这是一条测试通知"
```

### 自定义角标和铃声

```yaml
service: notify.jpush
data:
  title: "温度提醒"
  message: "室内温度过高"
  data:
    badge: "+1"    # 角标增加1
    sound: "default"  # 使用默认铃声
```

### 在自动化中使用

```yaml
automation:
  - alias: "温度过高提醒"
    trigger:
      - platform: numeric_state
        entity_id: sensor.temperature
        above: 30
    action:
      - service: notify.jpush
        data:
          title: "🌡 温度提醒"
          message: "室内温度{{ states('sensor.temperature') }}°C，建议开启空调"

  - alias: "回家欢迎"
    trigger:
      - platform: state
        entity_id: person.your_name
        to: "home"
    action:
      - service: notify.jpush
        data:
          title: "🏠 欢迎回家"
          message: "场景「回家模式」已自动触发"
          data:
            badge: "+1"

  - alias: "早安提醒"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.jpush
        data:
          title: "☀️ 早安"
          message: "新的一天开始啦！今日天气晴朗"
```

### 发送到所有设备

创建通知组：

```yaml
# configuration.yaml
notify:
  - name: all_jpush_devices
    platform: group
    services:
      - service: jpush
      - service: jpush_2
      - service: jpush_3
```

使用：

```yaml
service: notify.all_jpush_devices
data:
  title: "重要通知"
  message: "所有设备都会收到"
```

## ⚙️ 配置选项

### Registration ID
- **必填**
- 从App设置页面复制
- 格式：20-30位字符串

### 生产环境
- **可选**，默认：关闭（开发环境）
- 开启时使用生产APNs服务器
- 关闭时使用开发APNs服务器
- 发布版本请勾选此选项

## 🔒 安全性

### 数据存储

- **AppKey** 和 **Master Secret** 硬编码在插件中
- 添加集成时自动存储到Home Assistant的Config Entry
- Config Entry数据自动加密存储在 `.storage/core.config_entries`
- 只有Home Assistant进程可以访问

### 权限要求

- 需要访问网络（极光推送API）
- 不需要额外的Home Assistant权限

## 🐛 故障排查

### 收不到通知

1. **检查Registration ID是否正确**
   - 在App设置中重新复制
   - 确认没有多余的空格

2. **检查生产/开发环境设置**
   - App使用开发证书 → 关闭"生产环境"
   - App使用发布证书 → 开启"生产环境"

3. **检查iOS通知权限**
   - 设置 > 通知 > [您的App] > 允许通知

4. **检查App是否在后台运行**
   - iOS在前台运行时可能不显示通知

### 配置失败

1. **检查Home Assistant日志**
   - 配置 > 系统 > 日志
   - 搜索"jpush_notify"

2. **网络连接问题**
   - 确保Home Assistant可以访问 `https://api.jpush.cn`
   - 检查防火墙设置

3. **重新添加集成**
   - 删除现有集成
   - 重启Home Assistant
   - 重新添加

## 📊 版本要求

- Home Assistant >= 2024.1.0
- Python >= 3.11
- iOS App已集成极光推送SDK

## 🔧 开发

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/jpush_notify

# 链接到Home Assistant
ln -s /path/to/jpush_notify /config/custom_components/

# 重启Home Assistant
ha core restart
```

### 调试模式

在 `configuration.yaml` 中启用调试日志：

```yaml
logger:
  default: info
  logs:
    custom_components.jpush_notify: debug
```

## 📝 更新日志

### v1.0.0 (2025-10-05)
- 初始版本发布
- 支持Web UI配置
- 支持多设备
- 中英文界面
- 生产/开发环境切换

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [Home Assistant](https://www.home-assistant.io/)
- [极光推送](https://www.jiguang.cn/)

---

**如有问题，请提交Issue或查看[极光推送文档](https://docs.jiguang.cn/jpush/)**

