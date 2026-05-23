"""Minimal MCP server used by the agent-with-mcp tutorial.

The server exposes a CoinGecko-backed tool that Claude Desktop or another MCP
client can call to look up the current price of a cryptocurrency.
"""

import json

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
    normalized_crypto_id = crypto_id.strip().lower()
    normalized_currency = currency.strip().lower()
    params = {"ids": normalized_crypto_id, "vs_currencies": normalized_currency}

    response: httpx.Response | None = None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{COINGECKO_BASE_URL}/simple/price",
                params=params,
                timeout=10,
            )
            response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict):
            return "CoinGecko returned an unexpected response format."

        coin_data = data.get(normalized_crypto_id)
        if not isinstance(coin_data, dict) or normalized_currency not in coin_data:
            return (
                f"No price found for '{crypto_id}' in '{currency}'. "
                "Please check the CoinGecko ID and currency."
            )

        price = coin_data[normalized_currency]
        return f"The current price of {normalized_crypto_id} is {price} {normalized_currency.upper()}."
    except json.JSONDecodeError:
        if response is None:
            return "CoinGecko returned non-JSON data before a response was available."
        snippet = response.text[:200]
        return (
            f"CoinGecko returned non-JSON data with status {response.status_code}: "
            f"{snippet}"
        )
    except httpx.HTTPStatusError as exc:
        return f"CoinGecko API error: {exc.response.status_code} - {exc.response.text}"
    except httpx.HTTPError as exc:
        return f"Error fetching price data: {exc}"


if __name__ == "__main__":
    mcp.run()
