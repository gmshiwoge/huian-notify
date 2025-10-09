"""Config flow for Huian Notify integration."""
from __future__ import annotations

import logging
import base64
from typing import Any

import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    HUIAN_APP_KEY,
    HUIAN_MASTER_SECRET,
    CONF_REGISTRATION_ID,
    CONF_PRODUCTION,
    DEFAULT_PRODUCTION,
    HUIAN_API_URL,
    HUIAN_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class HuianConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Huian Notify."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - 直接激活 API 端点."""
        
        # 检查是否已经激活过 API
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)
        for entry in existing_entries:
            if entry.data.get("is_api_endpoint"):
                return self.async_abort(reason="already_configured")
        
        # 直接创建 API 端点配置条目，不需要用户确认
        _LOGGER.info("Creating API endpoint config entry via Web UI")
        
        return self.async_create_entry(
            title="Huian Notify API",
            data={
                "is_api_endpoint": True,  # 标记这是 API 端点配置
                "app_key": HUIAN_APP_KEY,
                "master_secret": HUIAN_MASTER_SECRET,
            },
        )

    async def async_step_api_activation(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Activate API endpoint without user input."""
        
        # 检查是否已经激活过 API
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)
        for entry in existing_entries:
            if entry.data.get("is_api_endpoint"):
                return self.async_abort(reason="already_configured")
        
        # 创建 API 端点配置条目
        _LOGGER.info("Creating API endpoint config entry")
        
        return self.async_create_entry(
            title="Huian Notify API",
            data={
                "is_api_endpoint": True,  # 标记这是 API 端点配置
                "app_key": HUIAN_APP_KEY,
                "master_secret": HUIAN_MASTER_SECRET,
            },
        )

    async def async_step_add_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual device addition - 用户需输入Registration ID."""
        errors = {}

        if user_input is not None:
            registration_id = user_input[CONF_REGISTRATION_ID].strip()
            
            # 检查是否已经添加过这个设备
            await self.async_set_unique_id(registration_id)
            self._abort_if_unique_id_configured()

            # 验证Registration ID
            try:
                await self.hass.async_add_executor_job(
                    self._test_connection,
                    registration_id,
                )
                
                # 验证成功，创建配置条目
                return self.async_create_entry(
                    title=f"Huian ({registration_id[-8:]})",
                    data={
                        "app_key": HUIAN_APP_KEY,
                        "master_secret": HUIAN_MASTER_SECRET,
                        CONF_REGISTRATION_ID: registration_id,
                        CONF_PRODUCTION: user_input.get(
                            CONF_PRODUCTION, DEFAULT_PRODUCTION
                        ),
                    },
                )
            except ConnectionError as err:
                _LOGGER.error("Failed to validate Registration ID: %s", err)
                errors["base"] = "cannot_connect"
            except ValueError as err:
                _LOGGER.error("Invalid Registration ID format: %s", err)
                errors[CONF_REGISTRATION_ID] = "invalid_format"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

        # 显示配置表单
        data_schema = vol.Schema(
            {
                vol.Required(CONF_REGISTRATION_ID): str,
                vol.Optional(CONF_PRODUCTION, default=DEFAULT_PRODUCTION): bool,
            }
        )

        return self.async_show_form(
            step_id="add_device",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "app_hint": "在App的设置页面 > 通知 一栏可以找到并复制Registration ID"
            },
        )

    async def async_step_api(
        self, data: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle API registration from mobile app."""
        if data is None:
            _LOGGER.error("API registration called with no data")
            return self.async_abort(reason="missing_data")
        
        registration_id = data.get(CONF_REGISTRATION_ID, "").strip()
        device_name = data.get("device_name", "Unknown")
        
        if not registration_id:
            _LOGGER.error("API registration missing registration_id")
            return self.async_abort(reason="missing_registration_id")
        
        _LOGGER.info(
            "Creating config entry from API for device: %s (ID: %s)",
            device_name,
            registration_id[-8:] if len(registration_id) >= 8 else registration_id
        )
        
        # 检查是否已存在
        await self.async_set_unique_id(registration_id)
        self._abort_if_unique_id_configured()
        
        # 跳过测试连接（因为是从应用发起的，假设ID有效）
        # 创建配置条目（使用设备名称作为标题）
        return self.async_create_entry(
            title=device_name if device_name else f"Huian ({registration_id[-8:]})",
            data={
                "app_key": data.get("app_key", HUIAN_APP_KEY),
                "master_secret": data.get("master_secret", HUIAN_MASTER_SECRET),
                CONF_REGISTRATION_ID: registration_id,
                CONF_PRODUCTION: data.get(CONF_PRODUCTION, DEFAULT_PRODUCTION),
                "device_name": device_name,
            },
        )

    @staticmethod
    def _test_connection(registration_id: str) -> bool:
        """Test if Registration ID is valid by sending a test notification."""
        if len(registration_id) < 10:
            raise ValueError("Registration ID too short")

        # 创建认证头
        credentials = f"{HUIAN_APP_KEY}:{HUIAN_MASTER_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }
        
        # 发送测试推送（使用生产环境）
        payload = {
            "platform": ["ios"],
            "audience": {"registration_id": [registration_id]},
            "notification": {
                "ios": {
                    "alert": "✅ Huian配置成功！Home Assistant集成已就绪。",
                    "badge": "+1",
                    "sound": "default",
                }
            },
            "options": {"apns_production": True},  # 生产环境
        }
        
        try:
            response = requests.post(
                HUIAN_API_URL,
                json=payload,
                headers=headers,
                timeout=HUIAN_TIMEOUT,
            )
            
            if response.status_code == 200:
                _LOGGER.info("Test notification sent successfully")
                return True
            
            _LOGGER.error(
                "Huian API returned error: %s - %s",
                response.status_code,
                response.text,
            )
            raise ConnectionError(
                f"Huian API returned {response.status_code}: {response.text}"
            )
        except requests.exceptions.Timeout as err:
            _LOGGER.error("Connection timeout: %s", err)
            raise ConnectionError("Connection timeout") from err
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Connection error: %s", err)
            raise ConnectionError(f"Connection error: {err}") from err

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return HuianOptionsFlowHandler()


class HuianOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow - 允许用户切换生产/开发环境."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        # 检查是否是 API 端点配置
        if self.config_entry.data.get("is_api_endpoint"):
            # API 端点配置没有可配置的选项
            return self.async_abort(reason="no_options_available")
        
        if user_input is not None:
            # 更新配置（保留原有的app_key和master_secret）
            new_data = dict(self.config_entry.data)
            new_data[CONF_PRODUCTION] = user_input[CONF_PRODUCTION]
            
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )
            return self.async_create_entry(title="", data={})

        # 显示当前配置
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PRODUCTION,
                        default=self.config_entry.data.get(
                            CONF_PRODUCTION, DEFAULT_PRODUCTION
                        ),
                    ): bool,
                }
            ),
        )
