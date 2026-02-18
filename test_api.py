import asyncio
import os
from dotenv import load_dotenv
from aiorinnai import API

load_dotenv()

async def main():
    username = os.getenv("RINNAI_USERNAME")
    password = os.getenv("RINNAI_PASSWORD")
    
    if not username or not password:
        print("Error: RINNAI_USERNAME and RINNAI_PASSWORD must be set in .env")
        return
    
    print(f"Logging in as {username}...")
    
    async with API() as api:
        await api.async_login(username, password)
        print(f"Connected: {api.is_connected}")
        
        user_info = await api.user.get_info()
        print(f"\n=== User Info ===")
        print(f"  Email: {user_info.get('email')}")
        print(f"  First name: {user_info.get('first_name')}")
        print(f"  Last name: {user_info.get('last_name')}")
        
        devices = user_info.get("devices", {}).get("items", [])
        print(f"\n=== Found {len(devices)} device(s) ===")
        
        for device in devices:
            device_id = device.get("id")
            device_name = device.get("name", "Unknown")
            print(f"\n--- Device: {device_name} ---")
            print(f"  ID: {device_id}")
            print(f"  Serial: {device.get('serial_number')}")
            print(f"  Model: {device.get('model_number')}")
            print(f"  Address: {device.get('address')}")
            
            info = await api.device.get_info(device_id)
            print(f"\n  Raw device info:")
            import json
            print(json.dumps(info, indent=4, default=str))
        
        await api.close()

if __name__ == "__main__":
    asyncio.run(main())
