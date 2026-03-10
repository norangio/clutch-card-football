#!/usr/bin/env python3
"""Browser entry point for pygbag."""

import asyncio
import traceback

from ui.app import PygameApp


async def main():
    try:
        app = PygameApp()
        await app.run_async()
    except Exception:
        # Keep stack trace visible in browser dev tools if startup fails.
        traceback.print_exc()
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
