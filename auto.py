import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Replace with your list of transaction hashes
TX_HASHES = [
    "0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060",
    "0x88df016429689c079f3b2f6ad39fa052532c567d32d90e3912067858c9167c37",
    "0x2b06297072a28cf1b373801f92c20692994e77dd623a31c51db3f059bc430e33"
]

async def add_tx_hashes_to_metasleuth(tx_list: list[str], headless: bool = False):
    """
    Automates submitting transaction hashes to MetaSleuth's canvas.
    
    :param tx_list: List of Ethereum/EVM transaction hash strings.
    :param headless: Set to False to watch the browser execution live.
    """
    async with async_playwright() as p:
        # Launch browser (use persistent context if you want to keep login sessions)
        browser = await p.chromium.launch(
            headless=headless,
            args=["--start-maximized"]
        )
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print("Navigating to MetaSleuth...")
        await page.goto("https://metasleuth.io/", wait_until="networkidle")

        for index, tx_hash in enumerate(tx_list, start=1):
            print(f"[{index}/{len(tx_list)}] Processing tx: {tx_hash}")

            try:
                # Locate the search/input box on the canvas interface
                search_selector = "input[placeholder*='address'], input[placeholder*='tx'], input[type='text']"
                search_input = page.locator(search_selector).first

                # Ensure search box is ready
                await search_input.wait_for(state="visible", timeout=10000)
                await search_input.click()

                # Clear existing text and fill with current tx hash
                await search_input.fill("")
                await search_input.type(tx_hash, delay=50)  # Type with human-like delay
                await page.keyboard.press("Enter")

                print(f"    Submitted: {tx_hash:.18s}...")

                # Pause to allow graph node generation & API background fetches
                await asyncio.sleep(4)

            except PlaywrightTimeoutError:
                print(f"    [Error] Timed out waiting for input bar on tx: {tx_hash}")
            except Exception as e:
                print(f"    [Error] Failed to process {tx_hash}: {e}")

        print("\nAll transaction hashes submitted successfully!")
        print("Keeping browser open for 30 seconds for review...")
        await asyncio.sleep(30)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(add_tx_hashes_to_metasleuth(TX_HASHES, headless=False))
