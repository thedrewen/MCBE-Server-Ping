Simple python function to simply ping a bedrock server and retrieve data.

Example : 
```py
from MCBEPing import ping_bedrock

result = ping_bedrock('test.mc', 19132)
print(f"Server {result.name} : {result.ping}ms\nPlayers : {result.players.online}/{result.players.max}")
```
