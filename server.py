"""
Sudoku Race — room server.

A thin relay: it owns room codes, pairs two players, decides which board both
will play, and forwards game events between them. It deliberately knows nothing
about sudoku — the puzzle strings live in index.html, and the server only picks
an *index* into the pool whose size the client reports. That keeps board data in
one place.

Run locally:      py -3 server.py
Environment:      PORT (default 8787), HOST (default 0.0.0.0)

Protocol (JSON text frames)
---------------------------
client -> server
  {"t":"create",   "name":str, "difficulty":str, "poolSize":int}
  {"t":"join",     "name":str, "code":str, "poolSize":int}
  {"t":"progress", "filled":int}
  {"t":"lockout",  "ms":int}
  {"t":"finished", "ms":int, "mistakes":int, "lockouts":int, "lockedMs":int}
  {"t":"rematch",  "same":bool}
  {"t":"leave"}

server -> client
  {"t":"created",  "code":str}
  {"t":"begin",    "difficulty":str, "board":int, "opponent":str}
  {"t":"progress", "filled":int}          # mirrored from the other player
  {"t":"lockout",  "ms":int}
  {"t":"finished", "ms":int, "mistakes":int, "lockouts":int, "lockedMs":int}
  {"t":"rematchWait"}
  {"t":"oppLeft"}
  {"t":"error",    "code":str}
"""

import asyncio
import json
import os
import random
import string

from websockets.asyncio.server import serve
from websockets.http11 import Response
from websockets.datastructures import Headers

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # no O/0/I/1
RELAYED = {"progress", "lockout", "finished"}

# code -> {"players": [player, ...], "difficulty": str, "poolSize": int,
#          "board": int|None, "rematch": {id: bool}}
rooms = {}


def new_code():
    for _ in range(500):
        code = "".join(random.choice(CODE_ALPHABET) for _ in range(4))
        if code not in rooms:
            return code
    raise RuntimeError("code space exhausted")


async def send(player, payload):
    try:
        await player["ws"].send(json.dumps(payload))
    except Exception:
        pass


async def other(player):
    room = rooms.get(player["code"])
    if not room:
        return None
    for p in room["players"]:
        if p is not player:
            return p
    return None


async def do_create(player, msg):
    if player["code"]:
        return await send(player, {"t": "error", "code": "already_in_room"})
    code = new_code()
    player["name"] = str(msg.get("name") or "Player")[:14]
    player["code"] = code
    rooms[code] = {
        "players": [player],
        "difficulty": str(msg.get("difficulty") or "easy"),
        "poolSize": max(1, int(msg.get("poolSize") or 1)),
        "board": None,
        "rematch": {},
    }
    await send(player, {"t": "created", "code": code})
    print(f"[room {code}] created by {player['name']}")


async def do_join(player, msg):
    if player["code"]:
        return await send(player, {"t": "error", "code": "already_in_room"})
    code = str(msg.get("code") or "").upper()
    room = rooms.get(code)
    if not room:
        return await send(player, {"t": "error", "code": "no_such_room"})
    if len(room["players"]) >= 2:
        return await send(player, {"t": "error", "code": "room_full"})

    player["name"] = str(msg.get("name") or "Player")[:14]
    player["code"] = code
    room["players"].append(player)
    # be defensive: if the two clients disagree on pool size, use the smaller
    room["poolSize"] = min(room["poolSize"], max(1, int(msg.get("poolSize") or 1)))
    print(f"[room {code}] {player['name']} joined")
    await begin(code)


async def begin(code, board=None):
    """Tell both players which board to build, then let them run their own
    3-2-1. Each starts on receipt, so no clock synchronisation is needed."""
    room = rooms.get(code)
    if not room or len(room["players"]) != 2:
        return
    if board is None:
        board = random.randrange(room["poolSize"])
    room["board"] = board
    room["rematch"] = {}
    a, b = room["players"]
    await send(a, {"t": "begin", "difficulty": room["difficulty"],
                   "board": board, "opponent": b["name"]})
    await send(b, {"t": "begin", "difficulty": room["difficulty"],
                   "board": board, "opponent": a["name"]})
    print(f"[room {code}] begin board={board} diff={room['difficulty']}")


async def do_rematch(player, msg):
    room = rooms.get(player["code"])
    if not room or len(room["players"]) != 2:
        return await send(player, {"t": "error", "code": "no_opponent"})
    room["rematch"][id(player)] = bool(msg.get("same"))
    if len(room["rematch"]) < 2:
        await send(player, {"t": "rematchWait"})
        opp = await other(player)
        if opp:
            await send(opp, {"t": "rematchAsk"})
        return
    # both agreed: same board only if BOTH asked for the same one
    same = all(room["rematch"].values())
    board = room["board"] if same else random.randrange(room["poolSize"])
    await begin(player["code"], board)


async def relay(player, msg):
    opp = await other(player)
    if opp:
        await send(opp, msg)


async def do_leave(player):
    code = player["code"]
    if not code:
        return
    player["code"] = None
    room = rooms.get(code)
    if not room:
        return
    if player in room["players"]:
        room["players"].remove(player)
    room["rematch"].pop(id(player), None)
    for p in room["players"]:
        await send(p, {"t": "oppLeft"})
    if not room["players"]:
        rooms.pop(code, None)
        print(f"[room {code}] closed")
    else:
        print(f"[room {code}] {player['name']} left")


async def handler(ws):
    player = {"ws": ws, "name": "?", "code": None}
    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            if not isinstance(msg, dict):
                continue
            t = msg.get("t")
            if t == "create":
                await do_create(player, msg)
            elif t == "join":
                await do_join(player, msg)
            elif t == "rematch":
                await do_rematch(player, msg)
            elif t == "leave":
                await do_leave(player)
            elif t in RELAYED:
                await relay(player, msg)
    except Exception:
        pass
    finally:
        await do_leave(player)


async def health(connection, request):
    """Plain GET (health checks, browsers) gets a 200 instead of a handshake
    error; websocket upgrades fall through to the handler."""
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return None
    return Response(200, "OK", Headers({"Content-Type": "text/plain"}), b"sudoku-race server\n")


async def main():
    port = int(os.environ.get("PORT", "8787"))
    host = os.environ.get("HOST", "0.0.0.0")
    async with serve(handler, host, port, process_request=health):
        print(f"sudoku-race server listening on {host}:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
