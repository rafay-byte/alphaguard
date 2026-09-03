"""
AlphaGuard AI - Alpaca MCP Client
==================================
Lightweight Model Context Protocol (MCP) client that connects to Alpaca's
official MCP server (`alpaca-mcp-server`) over stdio using JSON-RPC 2.0.

This satisfies the hackathon requirement: "projects must use Alpaca's
MCP server or CLI." The Market Analyst agent calls mcp_get_account() and
mcp_get_positions() to pull live account context into its analysis.

The official server is at: https://github.com/alpacahq/alpaca-mcp-server
Install: pip install alpaca-mcp-server  (or run via `uvx alpaca-mcp-server`)
"""
import json
import subprocess
import logging
import os

logger = logging.getLogger(__name__)

# Incrementing JSON-RPC request ID
_request_id = 0


def _next_id():
    global _request_id
    _request_id += 1
    return _request_id


def _run_mcp_session(tool_name, arguments=None):
    """Spawn the Alpaca MCP server over stdio, initialize the MCP session,
    call one tool, then shut down.

    This is a synchronous, short-lived session — we spawn the server,
    send initialize + tools/call, read the response, and exit. This is
    simpler and more robust than maintaining a long-lived connection.

    Args:
        tool_name: Name of the MCP tool to call (e.g. 'get_account_info')
        arguments: Dict of arguments to pass to the tool

    Returns:
        The tool result as a dict, or None if anything fails.
    """
    api_key = os.environ.get("ALPACA_API_KEY", "")
    secret_key = os.environ.get("ALPACA_SECRET_KEY", "")

    if not api_key or not secret_key:
        logger.debug("[MCP] No Alpaca API keys configured, skipping MCP call")
        return None

    env = os.environ.copy()
    env["ALPACA_API_KEY"] = api_key
    env["ALPACA_SECRET_KEY"] = secret_key

    try:
        proc = subprocess.Popen(
            ["uvx", "alpaca-mcp-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        )
    except FileNotFoundError:
        logger.warning(
            "[MCP] 'uvx' not found. Install uv: https://docs.astral.sh/uv/getting-started/installation/"
        )
        return None

    try:
        # Step 1: Send MCP initialize request
        init_msg = json.dumps({
            "jsonrpc": "2.0",
            "id": _next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "alphaguard-ai",
                    "version": "1.0.0"
                }
            }
        }) + "\n"
        proc.stdin.write(init_msg)
        proc.stdin.flush()

        # Read initialize response
        init_response = proc.stdout.readline()
        if init_response:
            logger.info("[MCP] Initialize response received")

        # Step 2: Send initialized notification
        initialized_msg = json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }) + "\n"
        proc.stdin.write(initialized_msg)
        proc.stdin.flush()

        # Step 3: Call the requested tool
        tool_msg = json.dumps({
            "jsonrpc": "2.0",
            "id": _next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }) + "\n"
        proc.stdin.write(tool_msg)
        proc.stdin.flush()

        # Read tool response
        tool_response = proc.stdout.readline()
        if not tool_response:
            logger.warning("[MCP] No response from MCP server for tool call")
            return None

        response_data = json.loads(tool_response)
        logger.info(f"[MCP] Tool '{tool_name}' response received")

        # Extract content from MCP response
        result = response_data.get("result", {})
        content = result.get("content", [])

        # MCP tool results come as content blocks
        for block in content:
            if block.get("type") == "text":
                try:
                    return json.loads(block["text"])
                except json.JSONDecodeError:
                    return {"raw_text": block["text"]}

        return result

    except Exception as e:
        logger.warning(f"[MCP] Error during MCP session: {e}")
        return None
    finally:
        try:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def mcp_get_account():
    """Pull live account info (equity, cash, buying_power, etc.) from
    Alpaca's official MCP server.

    Returns:
        dict with account fields, or None if MCP is unavailable.
    """
    logger.info("[MCP] Requesting account info from Alpaca MCP server")
    return _run_mcp_session("get_account_info")


def mcp_get_positions():
    """Pull current open positions from Alpaca's official MCP server.

    Returns:
        dict/list with position data, or None if MCP is unavailable.
    """
    logger.info("[MCP] Requesting positions from Alpaca MCP server")
    return _run_mcp_session("get_all_positions")
