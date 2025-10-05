# Huian Notify for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for JPush (极光推送) push notifications.

## Features

- 🚀 Auto-registration from iOS app
- 📱 Unified service naming (e.g., `notify.iphone_65050`)
- 🔧 Web UI configuration
- 🌐 Multi-device support

## Installation via HACS

1. Open HACS > Integrations
2. Click menu > Custom repositories
3. Add: `https://github.com/yourusername/huian-notify`
4. Category: Integration
5. Search "Huian Notify" and install

## Usage

```yaml
service: notify.iphone_65050
data:
  title: "Hello"
  message: "Test message"
```

## License

MIT
