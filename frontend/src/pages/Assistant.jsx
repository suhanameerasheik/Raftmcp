import { useState } from "react";
import { sendAgentRequest } from "../services/api";

function Assistant() {
  const [request, setRequest] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    if (!request.trim()) {
      return;
    }

    setLoading(true);
    setError("");
    setResponse(null);

    try {
      const data = await sendAgentRequest(request.trim());
      setResponse(data);
    } catch (error) {
      setError("Unable to process your travel request.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page assistant-page">
      <h1>AI Travel Assistant</h1>

      <p>
        Ask the RaftMCP Travel Assistant to help with your travel plans.
      </p>

      <form onSubmit={handleSubmit} className="assistant-form">
        <input
          type="text"
          value={request}
          onChange={(event) => setRequest(event.target.value)}
          placeholder="e.g. Search flights from Delhi to Bangalore"
          disabled={loading}
        />

        <button type="submit" disabled={loading || !request.trim()}>
          {loading ? "Processing..." : "Ask Assistant"}
        </button>
      </form>

      <div className="assistant-examples">
        <p>Try:</p>

        <button
          type="button"
          onClick={() =>
            setRequest("Search flights from Delhi to Bangalore")
          }
        >
          Search flights from Delhi to Bangalore
        </button>

        <button
          type="button"
          onClick={() =>
            setRequest("Check flight status for AI202")
          }
        >
          Check flight status for AI202
        </button>

        <button
          type="button"
          onClick={() =>
            setRequest("Search hotels in Dubai")
          }
        >
          Search hotels in Dubai
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {response && (
        <div className="assistant-response">
          <h2>Assistant Response</h2>

          <pre>
            {JSON.stringify(response, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default Assistant;
