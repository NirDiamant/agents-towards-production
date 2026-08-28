"""
A minimal MCP server that exposes cryptocurrency data as tools.

This is the server the MCP tutorial connects to. It publishes two tools over
stdio using FastMCP, both backed by the free CoinGecko public API (no API key
required):

    get_crypto_price(crypto_id, currency)       -> current price
    get_crypto_market_info(crypto_ids, currency) -> price, market cap, volume, changes

Run it directly:

    uv add "mcp[cli]>=2.0" httpx
    uv run mcp_server.py

The server speaks stdio, so it produces no output of its own when it starts.
That is expected - it is waiting for a client (the notebook, or Claude Desktop)
to connect and call `initialize`.
"""

import httpx
from mcp.server.mcpserver import MCPServer

# The server name is what clients display when they list connected servers.
# Note: in MCP SDK 2.x this class is MCPServer. It was called FastMCP in 1.x,
# so older tutorials you find elsewhere will import `mcp.server.fastmcp`.
mcp = MCPServer("crypto-price-tracker")

COINGECKO_API = "https://api.coingecko.com/api/v3"

# CoinGecko rate-limits anonymous callers fairly aggressively, so keep a single
# client with a sane timeout rather than opening a connection per call.
_TIMEOUT = httpx.Timeout(15.0)


@mcp.tool()
async def get_crypto_price(crypto_id: str, currency: str = "usd") -> str:
    """
    Get the current price of a cryptocurrency in a specified currency.

    Parameters:
    - crypto_id: The ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum')
    - currency: The currency to display the price in (default: 'usd')

    Returns:
    - Current price information as a formatted string
    """
    crypto_id = crypto_id.strip().lower()
    currency = currency.strip().lower()

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            response = await client.get(
                f"{COINGECKO_API}/simple/price",
                params={"ids": crypto_id, "vs_currencies": currency},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            # Return the error as text rather than raising: the client is an LLM,
            # and a readable message is more useful to it than a stack trace.
            return f"Could not reach CoinGecko to price {crypto_id}: {exc}"

    data = response.json()

    if crypto_id not in data:
        return (
            f"Unknown cryptocurrency '{crypto_id}'. "
            "Use a CoinGecko ID such as 'bitcoin', 'ethereum' or 'solana'."
        )
    if currency not in data[crypto_id]:
        return f"Unknown currency '{currency}' for {crypto_id}."

    price = data[crypto_id][currency]
    return f"The current price of {crypto_id} is {price} {currency.upper()}"


@mcp.tool()
async def get_crypto_market_info(crypto_ids: str, currency: str = "usd") -> str:
    """
    Get market information for one or more cryptocurrencies.

    Parameters:
    - crypto_ids: Comma-separated list of cryptocurrency IDs (e.g., 'bitcoin,ethereum')
    - currency: The currency to display values in (default: 'usd')

    Returns:
    - Market information including price, market cap, volume, and price changes
    """
    ids = [c.strip().lower() for c in crypto_ids.split(",") if c.strip()]
    if not ids:
        return "No cryptocurrency IDs provided."
    currency = currency.strip().lower()

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            response = await client.get(
                f"{COINGECKO_API}/coins/markets",
                params={"vs_currency": currency, "ids": ",".join(ids)},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return f"Could not reach CoinGecko for market data: {exc}"

    markets = response.json()
    if not markets:
        return (
            f"No market data found for: {', '.join(ids)}. "
            "Check that these are valid CoinGecko IDs."
        )

    unit = currency.upper()
    lines = []
    for coin in markets:
        change = coin.get("price_change_percentage_24h")
        change_text = f"{change:+.2f}%" if change is not None else "n/a"
        lines.append(
            f"{coin.get('name', coin['id'])} ({coin.get('symbol', '').upper()})\n"
            f"  Price:        {coin.get('current_price')} {unit}\n"
            f"  Market cap:   {coin.get('market_cap')} {unit}\n"
            f"  24h volume:   {coin.get('total_volume')} {unit}\n"
            f"  24h change:   {change_text}"
        )

    return "\n\n".join(lines)


if __name__ == "__main__":
    # stdio is the transport Claude Desktop and the notebook's StdioServerParameters
    # both expect. The server runs until the client disconnects.
    mcp.run(transport="stdio")
