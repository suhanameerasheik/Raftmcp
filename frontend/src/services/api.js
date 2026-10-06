
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

export async function searchFlights({
  origin,
  destination,
  departure_date,
  passengers,
}) {
  return fetchFromAvailableNode("/tools/search_flights", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      origin,
      destination,
      departure_date,
      passengers,
    }),
  });
}
export async function sendAgentRequest(request) {
  return fetchFromAvailableNode("/agent/request", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      request,
    }),
  });
}
export async function searchHotels({
  city,
  check_in,
  check_out,
  guests,
}) {
  return fetchFromAvailableNode("/tools/search_hotels", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      city,
      check_in,
      check_out,
      guests,
    }),
  });
}
export async function bookHotel({
  hotel,
  city,
  check_in,
  check_out,
  guests,
}) {
  return fetchFromAvailableNode("/tools/book_hotel", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      hotel,
      city,
      check_in,
      check_out,
      guests,
    }),
  });
}
export async function getTrips() {
  return fetchFromAvailableNode("/trips");
}
