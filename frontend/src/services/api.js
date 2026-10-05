const API_NODES = [
  "http://127.0.0.1:8001",
  "http://127.0.0.1:8002",
  "http://127.0.0.1:8003",
];

export async function fetchFromAvailableNode(path, options = {}) {
  for (const baseUrl of API_NODES) {
    try {
      const response = await fetch(`${baseUrl}${path}`, options);

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.log(`Node unavailable: ${baseUrl}`);
    }
  }

  throw new Error("No RaftMCP backend node is available");
}

export async function getHealth() {
  return fetchFromAvailableNode("/health");
}

export async function getNodeStatus() {
  return fetchFromAvailableNode("/raft/status");
}

export async function getTools() {
  return fetchFromAvailableNode("/registry/tools");
}

export async function getTravelTools() {
  return fetchFromAvailableNode("/tools");
}

export async function sendTravelRequest(request) {
  return fetchFromAvailableNode("/demo/travel-request", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      request,
    }),
  });
}