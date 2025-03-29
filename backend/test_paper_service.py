import asyncio
from backend.services.paper_service import PaperService


# Define a dummy WebSocket that simulates send_json
class DummyWebSocket:
    def __init__(self):
        self.messages = []

    async def send_json(self, message):
        self.messages.append(message)
        print("DummyWebSocket sent:", message)

async def test_explore_paper():
    # Instantiate your dummy websocket
    ws = DummyWebSocket()
    
    # Instantiate your PaperService
    paper_service = PaperService()
    
    # Call the asynchronous explore_paper method
    result = await paper_service.explore_paper(
        websocket=ws,
        root_paper_id="manual1",
        start_paper_id="manual1",
        max_depth=1,
        similarity_threshold=0.7,
        traversal_type="bfs"
    )
    
    # Optionally, print out the result and any messages sent via the dummy websocket
    print("Result of explore_paper:", result)
    print("WebSocket messages:", ws.messages)

if __name__ == "__main__":
    asyncio.run(test_explore_paper())
