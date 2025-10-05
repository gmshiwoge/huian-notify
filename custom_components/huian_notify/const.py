"""Constants for Huian Notify integration."""

DOMAIN = "huian_notify"

# ⭐ 硬编码的应用级配置（所有用户共用）
HUIAN_APP_KEY = "6dd5afc6f3041614e6fa741c"
HUIAN_MASTER_SECRET = "6f6fb742770bdbcfe72fbeb3"

# 用户配置项（每个设备不同）
CONF_REGISTRATION_ID = "registration_id"
CONF_PRODUCTION = "production"

# 默认值
DEFAULT_NAME = "Huian"
DEFAULT_PRODUCTION = False

# API配置
HUIAN_API_URL = "https://api.jpush.cn/v3/push"
HUIAN_TIMEOUT = 10

