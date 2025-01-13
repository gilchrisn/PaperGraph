export const createWebSocket = (paperId, onMessage, maxDepth = 5, similarityThreshold = 0.88, traversalType = "bfs") => {

    const socket = new WebSocket(
        `ws://127.0.0.1:8000/papers/${paperId}/explore/?max_depth=${maxDepth}&similarity_threshold=${similarityThreshold}&traversal_type=${traversalType}`
    );

  socket.onopen = () => {
      console.log("WebSocket connected.");
      // Send an initial message to the server (optional, depends on your backend)
      socket.send(JSON.stringify({ paperId }));
  };

  socket.onmessage = (event) => {
      const data = JSON.parse(event.data); // Parse the incoming data
      console.log("WebSocket message received:", data);
      onMessage(data); // Pass the data to the provided callback
  };

  socket.onerror = (error) => {
      console.error("WebSocket error:", error);
  };

  socket.onclose = () => {
      console.log("WebSocket closed.");
  };

  return socket;
};
