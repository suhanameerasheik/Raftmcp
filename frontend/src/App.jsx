import { useEffect, useState } from "react";

import Navbar from "./components/Navbar";

import Home from "./pages/Home";
import Flights from "./pages/Flights";
import Hotels from "./pages/Hotels";
import Trips from "./pages/Trips";
import Assistant from "./pages/Assistant";

import { getHealth } from "./services/api";

import "./App.css";

function App() {
  const [currentPage, setCurrentPage] = useState("Home");
  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [flightSearchData, setFlightSearchData] = useState(null);

  useEffect(() => {
    async function checkBackend() {
      try {
        await getHealth();
        setBackendStatus("Connected");
      } catch (error) {
        setBackendStatus("Backend unavailable");
      }
    }

    checkBackend();
  }, []);

  function handleFlightSearch(data) {
    setFlightSearchData(data);
    setCurrentPage("Flights");
  }

  function renderPage() {
    switch (currentPage) {
      case "Flights":
        return <Flights searchData={flightSearchData} />;

      case "Hotels":
        return <Hotels />;

      case "My Trips":
        return <Trips />;

      case "AI Assistant":
        return <Assistant />;

      case "Home":
      default:
        return <Home
  onFlightSearch={handleFlightSearch}
  onNavigate={setCurrentPage}
/>;
    }
  }

  return (
    <div className="app">
      <Navbar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
      />

      <div className="status-bar">
        Backend:{" "}
        <span
          className={
            backendStatus === "Connected"
              ? "status-connected"
              : "status-error"
          }
        >
          {backendStatus}
        </span>
      </div>

      <main>{renderPage()}</main>
    </div>
  );
}

export default App;
