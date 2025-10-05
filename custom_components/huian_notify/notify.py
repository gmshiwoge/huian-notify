"""Huian notification service."""
from __future__ import annotations

import logging
import base64
from typing import Any

import requests

from homeassistant.components.notify import (
    ATTR_TITLE,
    ATTR_DATA,
    BaseNotificationService,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    DOMAIN,
    CONF_REGISTRATION_ID,
    CONF_PRODUCTION,
    DEFAULT_PRODUCTION,
    HUIAN_API_URL,
    HUIAN_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> HuianNotificationService | None:
    """Get the Huian notification service."""
    if discovery_info is None:
        _LOGGER.error("No discovery info provided")
        return None

    # 从config entry获取配置
    entry_id = discovery_info.get("entry_id")
    if entry_id is None:
        _LOGGER.error("No entry_id in discovery_info")
        return None

    entry_data = hass.data[DOMAIN].get(entry_id)
    if entry_data is None:
        _LOGGER.error("No entry data found for entry_id: %s", entry_id)
        return None

    return HuianNotificationService(
        hass,
        entry_data["app_key"],
        entry_data["master_secret"],
        entry_data[CONF_REGISTRATION_ID],
        entry_data.get(CONF_PRODUCTION, DEFAULT_PRODUCTION),
    )


class HuianNotificationService(BaseNotificationService):
    """Implement the notification service for Huian."""

    def __init__(
        self,
        hass: HomeAssistant,
        app_key: str,
        master_secret: str,
        registration_id: str,
        production: bool = False,
    ) -> None:
        """Initialize the service."""
        self._hass = hass
        self._app_key = app_key
        self._master_secret = master_secret
        self._registration_id = registration_id
        self._production = production

        # 生成认证头（内部处理，不暴露）
        credentials = f"{app_key}:{master_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self._auth_header = f"Basic {encoded}"

        _LOGGER.info(
            "Huian Notify service initialized for device: %s",
            registration_id[-8:],
        )

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to Huian."""
        title = kwargs.get(ATTR_TITLE, "Home Assistant")
        data = kwargs.get(ATTR_DATA, {})

        # 从data中获取额外参数
        badge = data.get("badge", "+1")
        sound = data.get("sound", "default")

        # 构建推送payload
        payload = {
            "platform": ["ios"],
            "audience": {"registration_id": [self._registration_id]},
            "notification": {
                "ios": {
                    "alert": {"title": title, "body": message},
                    "badge": badge,
                    "sound": sound,
                }
            },
            "options": {"apns_production": self._production},
        }

        # 发送请求
        headers = {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
        }

        try:
            response = await self._hass.async_add_executor_job(
                lambda: requests.post(
                    HUIAN_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=HUIAN_TIMEOUT,
                )
            )

            if response.status_code == 200:
                result = response.json()
                _LOGGER.info(
                    "Huian notification sent successfully: msg_id=%s",
                    result.get("msg_id"),
                )
            else:
                _LOGGER.error(
                    "Huian notification failed: status=%s, response=%s",
                    response.status_code,
                    response.text,
                )
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Error sending Huian notification: %s", err)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error sending Huian notification: %s", err)
