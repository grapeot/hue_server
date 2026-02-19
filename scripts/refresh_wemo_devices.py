#!/usr/bin/env python3
"""
刷新Wemo设备配置脚本
重新发现局域网内的Wemo设备，并更新 config/wemo_config.yaml 文件
"""

import sys
import os
import yaml
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pywemo

def discover_devices():
    """发现所有Wemo设备"""
    print("正在扫描局域网内的Wemo设备...")
    devices = pywemo.discover_devices()
    
    if not devices:
        print("未发现任何Wemo设备")
        return []
    
    print(f"发现 {len(devices)} 个设备:")
    device_list = []
    for device in devices:
        device_info = {
            'name': device.name,
            'host': device.host,
            'port': device.port,
            'type': type(device).__name__
        }
        device_list.append(device_info)
        print(f"  - {device.name} ({device.host}:{device.port}) - {device_info['type']}")
    
    return device_list

def load_existing_config(config_path):
    """加载现有的配置文件"""
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"已加载现有配置: {config_path}")
        return config
    except Exception as e:
        print(f"读取配置文件时出错: {str(e)}", file=sys.stderr)
        return None

def update_config_with_devices(config, devices):
    """使用发现的设备信息更新配置"""
    if config is None:
        # 创建新配置
        config = {
            'devices': [],
            'schedule': {
                'timezone': 'Pacific',
                'tasks': []
            }
        }
    
    # 更新设备信息
    # 保留现有设备的description等字段
    existing_devices = {d['name'].lower(): d for d in config.get('devices', [])}
    
    updated_devices = []
    for device in devices:
        device_name_lower = device['name'].lower()
        if device_name_lower in existing_devices:
            # 保留现有设备的额外字段（如description）
            existing = existing_devices[device_name_lower]
            updated_device = {
                'name': device['name'],
                'host': device['host'],
                'port': device['port'],
                'type': device['type']
            }
            # 保留description等可选字段
            if 'description' in existing:
                updated_device['description'] = existing['description']
            updated_devices.append(updated_device)
            print(f"更新设备: {device['name']}")
        else:
            # 新设备
            updated_devices.append(device)
            print(f"添加新设备: {device['name']}")
    
    config['devices'] = updated_devices
    
    # 确保schedule部分存在
    if 'schedule' not in config:
        config['schedule'] = {
            'timezone': 'Pacific',
            'tasks': []
        }
    
    return config

def save_config(config, config_path):
    """保存配置到文件"""
    try:
        # 创建备份
        if config_path.exists():
            backup_path = config_path.with_suffix('.yaml.bak')
            import shutil
            shutil.copy2(config_path, backup_path)
            print(f"已创建备份: {backup_path}")
        
        # 保存新配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"配置已保存: {config_path}")
        return True
    except Exception as e:
        print(f"保存配置文件时出错: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False

def main():
    """主函数"""
    # 确定配置文件路径
    project_root = Path(__file__).parent.parent
    config_path = project_root / 'config' / 'wemo_config.yaml'
    
    # 如果通过环境变量指定了配置文件路径
    config_file_env = os.getenv('WEMO_CONFIG_FILE')
    if config_file_env:
        config_path = Path(config_file_env)
        if not config_path.is_absolute():
            config_path = project_root / config_path
    
    print("=" * 60)
    print("Wemo设备配置刷新工具")
    print("=" * 60)
    print(f"配置文件: {config_path}")
    print()
    
    # 发现设备
    devices = discover_devices()
    
    if not devices:
        print("\n未发现任何设备，无法更新配置")
        sys.exit(1)
    
    print()
    
    # 加载现有配置
    config = load_existing_config(config_path)
    
    # 更新配置
    print("\n更新配置...")
    config = update_config_with_devices(config, devices)
    
    # 保存配置
    print("\n保存配置...")
    if save_config(config, config_path):
        print("\n配置更新完成!")
        print("\n提示: 修改配置后需要重启服务器才能生效")
        sys.exit(0)
    else:
        print("\n配置更新失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
