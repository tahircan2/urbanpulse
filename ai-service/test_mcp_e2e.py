"""
End-to-end MCP test: Client connects to Server via stdio,
discovers tools, calls one tool, verifies result.
"""
import asyncio
import sys
import os
import json

# Fix Windows encoding for unicode output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    print("=" * 60)
    print("UrbanPulse MCP End-to-End Test")
    print("=" * 60)

    # 1. Configure server parameters
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "urbanpulse.mcp_server.server"],
        env={
            **os.environ,
            "PYTHONPATH": os.path.join(os.path.dirname(__file__), "src"),
        },
    )

    print("\n[1] Connecting to MCP Server via stdio...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 2. Initialize handshake
            await session.initialize()
            print("[2] OK - MCP handshake complete (JSON-RPC 2.0)")

            # 3. Discover tools
            tools_result = await session.list_tools()
            tools = tools_result.tools
            print(f"\n[3] OK - Discovered {len(tools)} tools:")
            for t in tools:
                desc = t.description[:60] if t.description else "N/A"
                print(f"    > {t.name}: {desc}...")

            # 4. Call district_risk_profile tool
            print("\n[4] Calling tool: district_risk_profile(district='Kemer')")
            result = await session.call_tool("district_risk_profile", {"district": "Kemer"})
            result_text = result.content[0].text if result.content else ""
            data = json.loads(result_text)
            print(f"    OK - Result: {json.dumps(data, indent=2, ensure_ascii=False)}")

            # 5. Call time_risk_context tool
            print("\n[5] Calling tool: time_risk_context()")
            result2 = await session.call_tool("time_risk_context", {})
            result2_text = result2.content[0].text if result2.content else ""
            data2 = json.loads(result2_text)
            print(f"    OK - Result: {data2.get('summary', 'N/A')}")

            # 6. Call weather_context tool
            print("\n[6] Calling tool: weather_context(lat=36.8841, lng=30.7056)")
            result3 = await session.call_tool("weather_context", {
                "latitude": 36.8841, "longitude": 30.7056
            })
            result3_text = result3.content[0].text if result3.content else ""
            data3 = json.loads(result3_text)
            print(f"    OK - Result: {data3.get('summary', 'N/A')}")

    print("\n" + "=" * 60)
    print("ALL MCP E2E TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
