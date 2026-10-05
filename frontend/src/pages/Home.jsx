import { useState } from "react";
import { searchFlights } from "../services/api";

function Home({ onFlightSearch }) {
  const [origin, setOrigin] = useState("DEL");
  const [destination, setDestination] = useState("BLR");
  const [departureDate, setDepartureDate] = useState("");
  const [passengers, setPassengers] = useState(1);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSearch() {
    setError("");

    if (!origin || !destination) {
      setError("Please select both origin and destination.");
      return;
    }

    if (origin === destination) {
      setError("Origin and destination cannot be the same.");
      return;
    }

    try {
      setLoading(true);

      const data = await searchFlights({
        origin,
        destination,
        departure_date: departureDate || null,
        passengers: Number(passengers),
      });

      console.log("Flight search result:", data);

      window.dispatchEvent(
        new CustomEvent("flight-search-results", {
          detail: data,
        })
      ); 
      onFlightSearch(data);

    } catch (err) {
      setError("Unable to search flights. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page home-page">
      <section className="hero">
        <h1>RaftMCP Travel</h1>

        <p>
          Your intelligent travel assistant for flights, hotels,
          and trip management.
        </p>
      </section>

      <section className="search-card">
        <h2>Search Flights</h2>

        <div className="search-grid">
          <div className="form-group">
            <label htmlFor="origin">From</label>

            <select
              id="origin"
              value={origin}
              onChange={(event) => setOrigin(event.target.value)}
            >
              <option value="DEL">Delhi</option>
              <option value="BLR">Bangalore</option>
              <option value="BOM">Mumbai</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="destination">To</label>

            <select
              id="destination"
              value={destination}
              onChange={(event) => setDestination(event.target.value)}
            >
              <option value="BLR">Bangalore</option>
              <option value="DEL">Delhi</option>
              <option value="BOM">Mumbai</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="departure">Departure</label>

            <input
              id="departure"
              type="date"
              value={departureDate}
              onChange={(event) => setDepartureDate(event.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="passengers">Passengers</label>

            <select
              id="passengers"
              value={passengers}
              onChange={(event) => setPassengers(event.target.value)}
            >
              <option value={1}>1 Passenger</option>
              <option value={2}>2 Passengers</option>
              <option value={3}>3 Passengers</option>
              <option value={4}>4 Passengers</option>
            </select>
          </div>
        </div>

        {error && <p className="error-message">{error}</p>}

        <button
          className="primary-button"
          onClick={handleSearch}
          disabled={loading}
        >
          {loading ? "Searching..." : "Search Flights"}
        </button>
      </section>

      <section className="destination-section">
        <h2>Popular Destinations</h2>

        <div className="destination-grid">
          <div className="destination-card">
            <h3>Bangalore</h3>
            <p>Technology & city escapes</p>
          </div>

          <div className="destination-card">
            <h3>Mumbai</h3>
            <p>Business & entertainment</p>
          </div>

          <div className="destination-card">
            <h3>Delhi</h3>
            <p>History & culture</p>
          </div>
        </div>
      </section>

      <section className="quick-actions">
        <button type="button">Search Hotels</button>
        <button type="button">AI Travel Assistant</button>
      </section>
    </div>
  );
}

export default Home;
