function Flights({ searchData }) {
  if (!searchData) {
    return (
      <div className="page">
        <h1>Flights</h1>
        <p>Search for flights to see available options.</p>
      </div>
    );
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
        {searchData.results.length === 0 ? (
          <p>No flights found for this route.</p>
        ) : (
          searchData.results.map((flight) => (
            <div className="flight-card" key={flight.flight}>
              <div>
                <h2>{flight.flight}</h2>
                <p>
                  {flight.from} → {flight.to}
                </p>
              </div>

              <div>
                <p>₹{flight.price}</p>
                <p>{flight.status}</p>
              </div>

              <button type="button">
                Select Flight
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Flights;
