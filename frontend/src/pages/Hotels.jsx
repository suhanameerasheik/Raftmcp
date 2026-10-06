import { useState } from "react";
import { bookHotel, searchHotels } from "../services/api";

function Hotels() {
  const [city, setCity] = useState("Hyderabad");
  const [checkIn, setCheckIn] = useState("2026-10-10");
  const [checkOut, setCheckOut] = useState("2026-10-12");
  const [guests, setGuests] = useState(2);

  const [hotels, setHotels] = useState([]);
  const [selectedHotel, setSelectedHotel] = useState(null);
  const [booking, setBooking] = useState(null);

  const [loading, setLoading] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSearch(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setHotels([]);
    setSelectedHotel(null);
    setBooking(null);

    try {
      const data = await searchHotels({
        city,
        check_in: checkIn,
        check_out: checkOut,
        guests: Number(guests),
      });

      setHotels(data.results || []);
    } catch (error) {
      console.error(error);
      setError("Unable to search hotels right now.");
    } finally {
      setLoading(false);
    }
  }

  function handleSelectHotel(hotel) {
    setSelectedHotel(hotel);
    setBooking(null);
    setError("");
  }

  async function handleBooking() {
    if (!selectedHotel) {
      return;
    }

    setBookingLoading(true);
    setError("");

    try {
      const data = await bookHotel({
        hotel: selectedHotel.hotel,
        city: selectedHotel.city,
        check_in: checkIn,
        check_out: checkOut,
        guests: Number(guests),
      });

      setBooking(data);
    } catch (error) {
      console.error(error);
      setError("Unable to complete the hotel booking.");
    } finally {
      setBookingLoading(false);
    }
  }

  return (
    <div className="page">
      <h1>Hotels</h1>

      <p>Search hotels for your trip.</p>

      <form onSubmit={handleSearch}>
        <div>
          <label>City</label>
          <input
            type="text"
            value={city}
            onChange={(event) => setCity(event.target.value)}
            placeholder="Enter city"
          />
        </div>

        <div>
          <label>Check-in</label>
          <input
            type="date"
            value={checkIn}
            onChange={(event) => setCheckIn(event.target.value)}
          />
        </div>

        <div>
          <label>Check-out</label>
          <input
            type="date"
            value={checkOut}
            onChange={(event) => setCheckOut(event.target.value)}
          />
        </div>

        <div>
          <label>Guests</label>
          <input
            type="number"
            min="1"
            value={guests}
            onChange={(event) => setGuests(event.target.value)}
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search Hotels"}
        </button>
      </form>

      {error && <p className="error-message">{error}</p>}

      {hotels.length > 0 && (
        <div>
          <h2>Available Hotels</h2>

          {hotels.map((hotel) => (
            <div key={hotel.hotel}>
              <h3>{hotel.hotel}</h3>

              <p>City: {hotel.city}</p>
              <p>Rating: {hotel.rating}</p>
              <p>₹{hotel.price_per_night} per night</p>

              <button
                type="button"
                onClick={() => handleSelectHotel(hotel)}
              >
                Select Hotel
              </button>
            </div>
          ))}
        </div>
      )}

      {selectedHotel && !booking && (
        <div>
          <h2>Confirm Hotel Booking</h2>

          <p>
            <strong>{selectedHotel.hotel}</strong>
          </p>

          <p>
            {selectedHotel.city}
          </p>

          <p>
            {checkIn} → {checkOut}
          </p>

          <p>
            Guests: {guests}
          </p>

          <p>
            ₹{selectedHotel.price_per_night} per night
          </p>

          <button
            type="button"
            onClick={handleBooking}
            disabled={bookingLoading}
          >
            {bookingLoading ? "Confirming..." : "Confirm Booking"}
          </button>
        </div>
      )}

      {booking && (
        <div>
          <h2>Booking Confirmed</h2>

          <p>
            Your hotel booking has been confirmed.
          </p>

          <p>
            <strong>Booking ID:</strong> {booking.booking_id}
          </p>

          <p>
            <strong>Hotel:</strong> {booking.hotel}
          </p>

          <p>
            <strong>City:</strong> {booking.city}
          </p>

          <p>
            <strong>Dates:</strong> {booking.check_in} →{" "}
            {booking.check_out}
          </p>

          <p>
            <strong>Guests:</strong> {booking.guests}
          </p>

          <p>
            <strong>Status:</strong> {booking.status}
          </p>
        </div>
      )}

      {!loading && hotels.length === 0 && !error && (
        <p>Search to see available hotels.</p>
      )}
    </div>
  );
}

export default Hotels;
