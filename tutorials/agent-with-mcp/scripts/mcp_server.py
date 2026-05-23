"""Minimal MCP server used by the agent-with-mcp tutorial.

The server exposes a CoinGecko-backed tool that Claude Desktop or another MCP
client can call to look up the current price of a cryptocurrency.
"""

import httpx
from mcp.server.fastmcp import FastMCP

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

mcp = FastMCP("crypto_price_tracker")


@mcp.tool()
async def get_crypto_price(crypto_id: str, currency: str = "usd") -> str:
    """Return the current price for a cryptocurrency.

    Args:
        crypto_id: CoinGecko cryptocurrency ID, such as "bitcoin" or "ethereum".
        currency: Fiat or crypto quote currency, such as "usd".
    """
    params = {"ids": crypto_id, "vs_currencies": currency}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_BASE_URL}/simple/price",
                params=params,
                timeout=10,
            )
            response.raise_for_status()

        data = response.json()
        if crypto_id not in data or currency not in data[crypto_id]:
            return (
                f"No price found for '{crypto_id}' in '{currency}'. "
                "Please check the CoinGecko ID and currency."
            )

        price = data[crypto_id][currency]
        return f"The current price of {crypto_id} is {price} {currency.upper()}."
    except httpx.HTTPStatusError as exc:
        return f"CoinGecko API error: {exc.response.status_code} - {exc.response.text}"
    except httpx.HTTPError as exc:
        return f"Error fetching price data: {exc}"


if __name__ == "__main__":
    mcp.run()
