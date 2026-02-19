#!/usr/bin/env python3
"""Rinnai 创建 Schedule 脚本 - 直接调用 GraphQL mutation"""
import asyncio
import os
import json
import uuid
from pathlib import Path

from dotenv import load_dotenv
from aiorinnai import API
from aiorinnai.const import GRAPHQL_ENDPOINT, GET_PAYLOAD_HEADERS

load_dotenv(Path(__file__).parent.parent / ".env")

CREATE_SCHEDULE_MUTATION = """
mutation CreateDeviceSchedule($input: CreateDeviceScheduleInput!, $condition: ModelDeviceScheduleConditionInput) {
  createDeviceSchedule(input: $input, condition: $condition) {
    id
    serial_id
    name
    days
    times
    schedule_date
    active
    createdAt
    updatedAt
  }
}
"""

async def main():
    username = os.getenv("RINNAI_USERNAME")
    password = os.getenv("RINNAI_PASSWORD")

    async with API() as api:
        await api.async_login(username, password)
        print(f"Connected: {api.is_connected}")

        user_info = await api.user.get_info()
        devices = user_info.get("devices", {}).get("items", [])

        if not devices:
            print("No devices found")
            return

        device = devices[0]
        device_id = device.get("id")
        print(f"Device ID: {device_id}")

        schedule_id = str(uuid.uuid4()).upper()

        variables = {
            "input": {
                "id": schedule_id,
                "serial_id": device_id,
                "name": "AfternoonPeak",
                "days": ["{0=Su,1=M,2=T,3=W,4=Th,5=F,6=S}"],
                "times": ["{start=16:30,end=18:00}"],
                "schedule_date": "02/17/2026 20:50",
                "active": True,
            }
        }

        payload = json.dumps({"query": CREATE_SCHEDULE_MUTATION, "variables": variables})

        headers = {
            **GET_PAYLOAD_HEADERS,
            "Authorization": api.id_token,
        }

        print(f"\nCreating schedule...")
        print(f"Payload: {json.dumps(variables, indent=2)}")

        async with api._get_session().post(
            GRAPHQL_ENDPOINT,
            data=payload,
            headers=headers,
        ) as resp:
            result = await resp.json()
            print(f"\nResponse status: {resp.status}")
            print(f"Response: {json.dumps(result, indent=2, default=str)}")

if __name__ == "__main__":
    asyncio.run(main())
