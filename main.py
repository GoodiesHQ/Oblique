#!/usr/bin/env python3
import asyncio
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError as e:
    print("Running without uvloop")

import oblique

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000


@asyncio.coroutine
def main(loop):
    try:
        yield from oblique.create_server(port=8000, loop=loop)
        yield from oblique.create_client("127.0.0.1", 1234, SERVER_HOST, SERVER_PORT, loop=loop)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(loop))
        loop.run_forever()
    finally:
        loop.close()
