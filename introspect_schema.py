import asyncio
import os
import json
from dotenv import load_dotenv
from aiorinnai import API
from aiorinnai.const import GRAPHQL_ENDPOINT, GET_PAYLOAD_HEADERS

load_dotenv()

INTROSPECTION_QUERY = """
{
  __schema {
    mutationType {
      fields {
        name
        args {
          name
          type {
            name
            kind
            ofType {
              name
              kind
            }
          }
        }
      }
    }
  }
}
"""

async def main():
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    
    async with API() as api:
        await api.async_login(username, password)
        print(f"Connected: {api.is_connected}")
        
        headers = {
            **GET_PAYLOAD_HEADERS,
            "Authorization": api.id_token,
        }
        
        payload = json.dumps({"query": INTROSPECTION_QUERY})
        
        async with api._get_session().post(
            GRAPHQL_ENDPOINT,
            data=payload,
            headers=headers,
        ) as resp:
            result = await resp.json()
            
            mutations = result.get("data", {}).get("__schema", {}).get("mutationType", {}).get("fields", [])
            print(f"Available mutations ({len(mutations)}):")
            for m in mutations:
                name = m.get("name")
                if "schedule" in name.lower() or "device" in name.lower():
                    args = m.get("args", [])
                    arg_strs = []
                    for a in args:
                        arg_name = a.get("name")
                        arg_type = a.get("type", {})
                        type_name = arg_type.get("name") or ""
                        if arg_type.get("ofType"):
                            type_name = arg_type["ofType"].get("name", "")
                        arg_strs.append(f"{arg_name}: {type_name}")
                    print(f"  {name}({', '.join(arg_strs)})")

if __name__ == "__main__":
    asyncio.run(main())
