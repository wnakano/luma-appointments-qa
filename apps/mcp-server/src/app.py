from server.mcp_server import ModularMCPServer
from services import DatabaseService


server = ModularMCPServer()

server.add_service("database", DatabaseService())
server_app = server.create_app()
app = server_app.http_app(path="/mcp/")
    
