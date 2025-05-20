import socket
import struct
import time
import random

MAGIC = bytes.fromhex("00ffff00fefefefefdfdfdfd12345678")
UNCONNECTED_PONG = 0x1C


def create_unconnected_ping_frame(timestamp):
    buffer = struct.pack("<BQ", 0x01, timestamp) + MAGIC + struct.pack("<Q", random.getrandbits(64))
    return buffer


def extract_modt(unconnected_pong_packet):
    if not isinstance(unconnected_pong_packet, bytes) or len(unconnected_pong_packet) < 35:
        raise ValueError("Invalid pong packet")

    offset = 33
    length = struct.unpack_from("!H", unconnected_pong_packet, offset)[0]
    
    if offset + 2 + length > len(unconnected_pong_packet):
        raise ValueError("Malformed pong packet")
    
    modt = unconnected_pong_packet[offset + 2 : offset + 2 + length].decode("utf-8")
    components = modt.split(";")
    
    if len(components) < 9:
        raise ValueError("Invalid MODT format")
    
    return {
        "edition": components[0],
        "name": components[1],
        "version": {
            "protocolVersion": int(components[2]),
            "minecraftVersion": components[3],
        },
        "players": {
            "online": int(components[4]),
            "max": int(components[5]),
        },
        "serverId": components[6],
        "mapName": components[7],
        "gameMode": components[8],
    }


def ping(host, port=19132, timeout=5):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        timestamp = int(time.time() * 1000)
        ping_packet = create_unconnected_ping_frame(timestamp)
        
        try:
            start_time = time.time()
            sock.sendto(ping_packet, (host, port))
            pong_packet, _ = sock.recvfrom(4096)
            end_time = time.time()
            
            if not pong_packet or pong_packet[0] != UNCONNECTED_PONG:
                raise ValueError("Unexpected packet received")
            
            server_ping = int((end_time - start_time) * 1000)  # Convert to milliseconds
            response = extract_modt(pong_packet)
            response["ping"] = server_ping
            return response
        except socket.timeout:
            raise TimeoutError("Socket timeout")
        except Exception as e:
            raise e

class ServerVersion:
    def __init__(self, protocolVersion : int, minecraftVersion : str):
        self.protocolVersion = protocolVersion
        self.minecraftVersion = minecraftVersion

class ServerPlayers:
    def __init__(self, online : int, max: int):
        self.online = online
        self.max = max

class PingResult:
    def __init__(self, edition : str, name : str, version : ServerVersion, players : ServerPlayers, serverId : int, mapName : str, gameMode : str, ping : int):
        self.edition = edition
        self.name = name
        self.version = version
        self.players = players
        self.serverId = serverId
        self.mapName = mapName
        self.gameMode = gameMode
        self.ping = ping

def ping_bedrock(host, port=19132, timeout=5):
    if not host:
        raise ValueError("Host argument is not provided")
    
    result = ping(host, port, timeout)
    return PingResult(
        result['edition'],
        result['name'],
        ServerVersion(result['version']['protocolVersion'], result['version']['minecraftVersion']),
        ServerPlayers(result['players']['online'], result['players']['max']),
        result['serverId'],
        result['mapName'],
        result['gameMode'],
        result['ping']
    )
