
import { useState } from "react";

function Flights({ searchData }) {
  const [selectedFlight, setSelectedFlight] = useState(null);
  const [message, setMessage] = useState("");

  if (!searchData) {
    return (
      <div className="page">
        <h1>Flights</h1>
        <p>Search for flights to see available options.</p>
      </div>
    );
  }

  function handleSelectFlight(flight) {
    setSelectedFlight(flight);
    setMessage("");
  }

  return (
    <div className="page">
      <h1>
        {searchData.origin} → {searchData.destination}
      </h1>

      <p>
        {searchData.passengers} passenger
        {searchData.passengers > 1 ? "s" : ""}
      </p>

      <div className="flight-results">
        {!searchData.results || searchData.results.length === 0 ? (
          <p>No flights found for this route.</p>
        ) : (
          searchData.results.map((flight) => (
            <div className="flight-card" key={flight.flight}>
              <div>
                <h2>{flight.flight}</h2>
                <p>{flight.from} → {flight.to}</p>
              </div>

              <div>
                <p>₹{flight.price}</p>
                <p>{flight.status}</p>
              </div>

              <button
                type="button"
                onClick={() => handleSelectFlight(flight)}
              >
                {selectedFlight?.flight === flight.flight
                  ? "Selected"
                  : "Select Flight"}
              </button>
            </div>
          ))
        )}
      </div>

      {selectedFlight && (
        <div className="search-card">
          <h2>Flight Selected</h2>
          <p><strong>Flight:</strong> {selectedFlight.flight}</p>
          <p>
            <strong>Route:</strong> {selectedFlight.from} → {selectedFlight.to}
          </p>
          <p><strong>Price:</strong> ₹{selectedFlight.price}</p>
          <p><strong>Status:</strong> {selectedFlight.status}</p>
          <p><strong>Passengers:</strong> {searchData.passengers}</p>

          <p>
            This is a demo flight selection. Airline booking is not yet
            connected.
          </p>

          <button
            type="button"
            className="primary-button"
            onClick={() => {
              setMessage("Flight selection confirmed for this demo.");
            }}
          >
            Confirm Selection
          </button>

          {message && <p role="status">{message}</p>}
        </div>
      )}
    </div>
  );
}

export default Flights;
