#!/usr/bin/env python3
"""Browser entry point for pygbag."""

import asyncio

from ui.app import PygameApp


async def main():
    app = PygameApp()
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
