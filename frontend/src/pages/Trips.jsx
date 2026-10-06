import { useEffect, useState } from "react";
import { getTrips } from "../services/api";

function Trips() {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadTrips() {
    setLoading(true);
    setError("");

    try {
      const data = await getTrips();
      setTrips(data.trips || []);
    } catch (error) {
      console.error(error);
      setError("Unable to load your trips right now.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTrips();
  }, []);

  return (
    <div className="page">
      <h1>My Trips</h1>

      {loading && <p>Loading your trips...</p>}

      {error && <p className="error-message">{error}</p>}

      {!loading && !error && trips.length === 0 && (
        <p>You don't have any bookings yet.</p>
      )}

      {!loading && trips.length > 0 && (
        <div>
          <h2>Your Bookings</h2>

          {trips.map((trip) => (
            <div key={trip.booking_id}>
              <h3>{trip.hotel}</h3>

              <p>
                <strong>Booking ID:</strong> {trip.booking_id}
              </p>

              <p>
                <strong>City:</strong> {trip.city}
              </p>

              <p>
                <strong>Dates:</strong> {trip.check_in} → {trip.check_out}
              </p>

              <p>
                <strong>Guests:</strong> {trip.guests}
              </p>

              <p>
                <strong>Price per night:</strong> ₹{trip.price_per_night}
              </p>

              <p>
                <strong>Status:</strong> {trip.status}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Trips;
