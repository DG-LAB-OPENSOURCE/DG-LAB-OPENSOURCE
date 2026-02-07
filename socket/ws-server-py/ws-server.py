import asyncio
import json
import websockets
from uuid import uuid4

# Storage for connected users and their identifiers
clients = {}

# Storage for message relations
relations = {}

punishment_duration = 5
punishment_time = 1

# Storage for client and send timer relations
client_timers = {}

# Define heartbeat message
heartbeat_msg = {
    "type": "heartbeat",
    "clientId": "",
    "targetId": "",
    "message": "200"
}

# Define timer for heartbeat
heartbeat_interval = None


async def server(websocket, path):
    # Generate a unique identifier
    client_id = str(uuid4())
    print(f'New WebSocket connection established, identifier: {client_id}')

    # Store
    clients[client_id] = websocket

    # Send identifier to the client (format fixed, both parties must obtain it to continue communication, such as browser and app)
    await websocket.send(json.dumps({"type": "bind", "clientId": client_id, "message": "targetId", "targetId": ""}))

    # Listen for messages
    async for message in websocket:
        print(f"Received message: {message}")
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            # Non-JSON data handling
            await websocket.send(json.dumps({"type": "msg", "clientId": "", "targetId": "", "message": "403"}))
            continue

        if data.get("type") and data.get("clientId") and data.get("message") and data.get("targetId"):
            # Prioritize handling binding relationships
            if data["type"] == "bind":
                # Server issues binding relationship
                if data["clientId"] in clients and data["targetId"] in clients:
                    if not any(id in [data["clientId"], data["targetId"]] for id in relations.keys()):
                        relations[data["clientId"]] = data["targetId"]
                        client = clients[data["clientId"]]
                        send_data = {"clientId": data["clientId"], "targetId": data["targetId"], "message": "200",
                                     "type": "bind"}
                        await websocket.send(json.dumps(send_data))
                        await client.send(json.dumps(send_data))
                    else:
                        await websocket.send(json.dumps(
                            {"type": "bind", "clientId": data["clientId"], "targetId": data["targetId"],
                             "message": "400"}))
                else:
                    await websocket.send(json.dumps(
                        {"type": "bind", "clientId": data["clientId"], "targetId": data["targetId"], "message": "401"}))

            # Handle other types of messages
            elif data["type"] == "clientMsg":
                # Server sends message to client
                if relations.get(data["clientId"]) != data["targetId"]:
                    await websocket.send(json.dumps(
                        {"type": "bind", "clientId": data["clientId"], "targetId": data["targetId"], "message": "402"}))
                else:
                    target = clients.get(data["targetId"])
                    if target:
                        await target.send(json.dumps(data))
                    else:
                        print(f"Client {data['clientId']} not found")
                        await websocket.send(json.dumps(
                            {"clientId": data["clientId"], "targetId": data["targetId"], "message": "404",
                             "type": "msg"}))


async def main():
    global heartbeat_interval
    async with websockets.serve(server, "0.0.0.0", 9999):
        print("Server started on ws://0.0.0.0:9999")
        await asyncio.Future()  # Run forever


asyncio.run(main())
