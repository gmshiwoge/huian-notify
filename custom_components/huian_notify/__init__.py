"""Huian Notify integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.http import HomeAssistantView

from .const import (
    DOMAIN,
    HUIAN_APP_KEY,
    HUIAN_MASTER_SECRET,
    CONF_REGISTRATION_ID,
    CONF_PRODUCTION,
    DEFAULT_PRODUCTION,
)
from .notify import HuianNotificationService

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Huian Notify component."""
    # 注册 HTTP API 视图
    hass.http.register_view(HuianNotifyRegisterView)
    _LOGGER.info("✅ Huian Notify API endpoint registered at /api/huian_notify/register")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Huian Notify from a config entry."""
    _LOGGER.info("Setting up Huian Notify integration")
    
    hass.data.setdefault(DOMAIN, {})
    
    # 注册 HTTP API 视图（只注册一次）
    if "_http_view_registered" not in hass.data[DOMAIN]:
        hass.http.register_view(HuianNotifyRegisterView)
        hass.data[DOMAIN]["_http_view_registered"] = True
        _LOGGER.info("✅ Huian Notify API endpoint registered at /api/huian_notify/register")
    
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    # 如果是 API 端点配置（不是设备配置），直接返回
    if entry.data.get("is_api_endpoint"):
        _LOGGER.info("API endpoint config entry loaded")
        return True

    # 直接创建并注册notify服务（而不是通过平台转发）
    service = HuianNotificationService(
        hass,
        entry.data["app_key"],
        entry.data["master_secret"],
        entry.data.get("registration_id"),
        entry.data.get("production", False),
    )
    
    # 注册notify服务
    # 服务名称格式: notify.<设备名称>（如：notify.iphone_65050）
    device_name = entry.data.get("device_name", "")
    registration_id = entry.data.get("registration_id", "")
    service_name = _generate_service_name(hass, entry, device_name, registration_id)
    
    # 创建服务处理函数，处理ServiceCall对象
    async def handle_notify(call):
        """Handle notify service call."""
        # 从ServiceCall中提取参数
        message = call.data.get("message", "")
        title = call.data.get("title", "Home Assistant")
        data = call.data.get("data", {})
        
        # 调用发送方法
        await service.async_send_message(message, title=title, data=data)
    
    hass.services.async_register(
        "notify",
        service_name,
        handle_notify,
    )
    
    # 存储服务名称以便卸载时使用
    hass.data[DOMAIN][f"{entry.entry_id}_service_name"] = service_name
    
    _LOGGER.info("Huian Notify service registered as: notify.%s", service_name)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


def _generate_service_name(hass: HomeAssistant, entry: ConfigEntry, device_name: str, registration_id: str) -> str:
    """Generate a unique service name based on device name (like mobile_app)."""
    import re
    
    # 如果有设备名称，使用设备名称（和 mobile_app 一样）
    if device_name:
        # 转换为小写，替换空格为下划线，移除特殊字符
        # 例如："iPhone 65050" -> "iphone_65050"
        service_name = device_name.lower()
        service_name = re.sub(r'\s+', '_', service_name)  # 空格转下划线
        service_name = re.sub(r'[^a-z0-9_]', '', service_name)  # 移除特殊字符
    else:
        # 如果没有设备名称，使用 Registration ID 后8位作为后备
        if registration_id and len(registration_id) >= 8:
            id_suffix = registration_id[-8:]
        else:
            id_suffix = registration_id or "unknown"
        service_name = f"huian_{id_suffix}"
    
    # 检查是否已存在
    existing_services = [
        hass.data[DOMAIN].get(f"{eid}_service_name")
        for eid in hass.data.get(DOMAIN, {})
        if eid != entry.entry_id and isinstance(eid, str) and not eid.endswith("_service_name")
    ]
    
    # 如果重复，添加数字后缀
    if service_name in existing_services:
        index = 2
        original_name = service_name
        while service_name in existing_services:
            service_name = f"{original_name}_{index}"
            index += 1
    
    return service_name


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Huian Notify integration")
    
    # 移除notify服务
    service_name = hass.data[DOMAIN].get(f"{entry.entry_id}_service_name")
    if service_name:
        hass.services.async_remove("notify", service_name)
        hass.data[DOMAIN].pop(f"{entry.entry_id}_service_name")
        _LOGGER.info("Removed notify service: notify.%s", service_name)
    
    # 清理数据
    hass.data[DOMAIN].pop(entry.entry_id, None)

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class HuianNotifyRegisterView(HomeAssistantView):
    """处理来自移动应用的注册请求."""

    url = "/api/huian_notify/register"
    name = "api:huian_notify:register"
    requires_auth = True

    async def post(self, request):
        """处理注册请求."""
        hass = request.app["hass"]
        
        try:
            data = await request.json()
        except ValueError:
            _LOGGER.error("❌ Invalid JSON in registration request")
            return self.json_message("Invalid JSON", status_code=400)
        
        registration_id = data.get("registration_id")
        device_name = data.get("device_name", "Unknown Device")
        production = data.get("production", DEFAULT_PRODUCTION)
        
        if not registration_id:
            _LOGGER.error("❌ Missing registration_id in request")
            return self.json_message(
                "Missing registration_id", 
                status_code=400
            )
        
        _LOGGER.info(
            "📱 Received registration request for device: %s (ID: %s)",
            device_name,
            registration_id[-8:] if len(registration_id) >= 8 else registration_id
        )
        
        # 检查是否已存在相同的 Registration ID
        existing_entries = hass.config_entries.async_entries(DOMAIN)
        for entry in existing_entries:
            if entry.data.get(CONF_REGISTRATION_ID) == registration_id:
                # 检查设备名称是否变化
                old_device_name = entry.data.get("device_name", "")
                
                if old_device_name != device_name:
                    # 设备名称变化了，更新 config entry
                    _LOGGER.info(
                        "🔄 Device name changed from '%s' to '%s', updating entry",
                        old_device_name,
                        device_name
                    )
                    
                    # 更新数据
                    new_data = dict(entry.data)
                    new_data["device_name"] = device_name
                    new_data[CONF_PRODUCTION] = production
                    
                    # 更新 config entry（包括标题）
                    hass.config_entries.async_update_entry(
                        entry,
                        title=device_name if device_name else f"Huian ({registration_id[-8:]})",
                        data=new_data,
                    )
                    
                    # 重新加载 entry 以重新创建 notify 服务
                    await hass.config_entries.async_reload(entry.entry_id)
                    
                    # 生成新的服务名称
                    import re
                    if device_name:
                        new_service_name = device_name.lower()
                        new_service_name = re.sub(r'\s+', '_', new_service_name)
                        new_service_name = re.sub(r'[^a-z0-9_]', '', new_service_name)
                    else:
                        new_service_name = f"huian_{registration_id[-8:] if len(registration_id) >= 8 else registration_id}"
                    
                    _LOGGER.info(
                        "✅ Device updated successfully: %s -> notify.%s",
                        device_name,
                        new_service_name
                    )
                    
                    return self.json({
                        "status": "updated",
                        "service": new_service_name,
                        "message": f"Device updated as notify.{new_service_name}"
                    })
                else:
                    # 设备名称未变化，返回已存在
                    service_name = hass.data[DOMAIN].get(f"{entry.entry_id}_service_name")
                    if not service_name:
                        # 如果没有存储的服务名，根据设备名称生成
                        service_name = _generate_service_name(hass, entry, device_name, registration_id)
                    
                    _LOGGER.info(
                        "ℹ️ Device already registered, service: notify.%s",
                        service_name
                    )
                    return self.json({
                        "status": "already_exists",
                        "service": service_name,
                        "message": f"Device already registered as notify.{service_name}"
                    })
        
        # 创建新的 config entry
        try:
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "api"},
                data={
                    "app_key": HUIAN_APP_KEY,
                    "master_secret": HUIAN_MASTER_SECRET,
                    CONF_REGISTRATION_ID: registration_id,
                    CONF_PRODUCTION: production,
                    "device_name": device_name,
                },
            )
            
            # 生成服务名称（基于设备名称）
            import re
            if device_name:
                service_name = device_name.lower()
                service_name = re.sub(r'\s+', '_', service_name)
                service_name = re.sub(r'[^a-z0-9_]', '', service_name)
            else:
                service_name = f"huian_{registration_id[-8:] if len(registration_id) >= 8 else registration_id}"
            
            _LOGGER.info(
                "✅ Device registered successfully: %s -> notify.%s",
                device_name,
                service_name
            )
            
            return self.json({
                "status": "success",
                "service": service_name,
                "message": f"Device registered as notify.{service_name}",
                "flow_id": result.get("flow_id"),
            })
            
        except Exception as err:
            _LOGGER.error("❌ Failed to register device: %s", err, exc_info=True)
            return self.json_message(
                f"Failed to register device: {str(err)}",
                status_code=500
            )
