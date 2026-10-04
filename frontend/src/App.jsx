
import { useEffect, useState } from 'react'
import './App.css'

const NODES = [
  { id: 'node-1', port: 8001 },
  { id: 'node-2', port: 8002 },
  { id: 'node-3', port: 8003 },
]

const API = 'http://127.0.0.1:8001'

function App() {
  const [cluster, setCluster] = useState(null)
  const [raftLog, setRaftLog] = useState(null)
  const [error, setError] = useState('')
  const [logError, setLogError] = useState('')
  const [actionMessage, setActionMessage] = useState('')
  const [actionError, setActionError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)
  const [loadingAction, setLoadingAction] = useState('')

  async function fetchCluster() {
    try {
      const response = await fetch(`${API}/demo/state`)

      if (!response.ok) {
        throw new Error('Unable to fetch cluster state')
      }

      const data = await response.json()
      setCluster(data)
      setLastUpdated(new Date().toLocaleTimeString())
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }

  async function fetchRaftLog() {
    try {
      const response = await fetch(`${API}/raft/log`)

      if (!response.ok) {
        throw new Error('Unable to fetch Raft log')
      }

      const data = await response.json()
      setRaftLog(data)
      setLogError('')
    } catch (err) {
      setLogError(err.message)
    }
  }

  async function refreshDashboard() {
    await Promise.all([fetchCluster(), fetchRaftLog()])
  }

  async function handleNodeAction(node, action) {
    const actionKey = `${node.id}-${action}`

    setLoadingAction(actionKey)
    setActionMessage('')
    setActionError('')

    try {
      const response = await fetch(
        `http://127.0.0.1:${node.port}/admin/${action}`,
        { method: 'POST' }
      )

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(
          data.detail || `Failed to ${action} ${node.id}`
        )
      }

      setActionMessage(
        `${node.id} ${action === 'kill' ? 'stopped' : 'restarted'} successfully.`
      )

      await refreshDashboard()
    } catch (err) {
      setActionError(err.message)
    } finally {
      setLoadingAction('')
    }
  }

  useEffect(() => {
    refreshDashboard()

    const interval = setInterval(() => {
      refreshDashboard()
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  const nodes = cluster?.nodes
    ? Object.entries(cluster.nodes)
    : []

  const leader = cluster?.current_leader
  const leaderNode = leader ? cluster.nodes?.[leader] : null
  const activeTools = cluster?.active_tools ?? []

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <h1>RaftMCP</h1>
          <p>Distributed Travel Tool Registry</p>
        </div>

        <div className="live-indicator">
          <span className="pulse"></span>
          Live Monitoring
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      {actionMessage && (
        <div className="success">{actionMessage}</div>
      )}

      {actionError && (
        <div className="error">{actionError}</div>
      )}

      <section className="summary">
        <div className="summary-card">
          <span>Current Leader</span>
          <strong>{leader || 'Not elected'}</strong>
        </div>

        <div className="summary-card">
          <span>Current Term</span>
          <strong>{leaderNode?.term ?? '—'}</strong>
        </div>

        <div className="summary-card">
          <span>Commit Index</span>
          <strong>{leaderNode?.commit_index ?? '—'}</strong>
        </div>

        <div className="summary-card">
          <span>Registered Tools</span>
          <strong>{activeTools.length}</strong>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <h2>Cluster Nodes</h2>
          <span>Refreshes every 2 seconds</span>
        </div>

        <div className="node-grid">
          {nodes.map(([id, node]) => (
            <article className="node-card" key={id}>
              <div className="node-heading">
                <h3>{id}</h3>

                <span
                  className={`status ${
                    node.is_active ? 'online' : 'offline'
                  }`}
                >
                  {node.is_active ? 'ONLINE' : 'OFFLINE'}
                </span>
              </div>

              <div className="node-role">
                {node.role || 'UNKNOWN'}
              </div>

              <div className="node-details">
                <div>
                  <span>Term</span>
                  <strong>{node.term ?? '—'}</strong>
                </div>

                <div>
                  <span>Commit Index</span>
                  <strong>{node.commit_index ?? '—'}</strong>
                </div>

                <div>
                  <span>Health</span>
                  <strong>{node.health || 'Unknown'}</strong>
                </div>
              </div>

              <div className="node-actions">
                <button
                  className="kill-button"
                  disabled={
                    !node.is_active ||
                    loadingAction !== ''
                  }
                  onClick={() =>
                    handleNodeAction(
                      NODES.find((item) => item.id === id),
                      'kill'
                    )
                  }
                >
                  {loadingAction === `${id}-kill`
                    ? 'Stopping...'
                    : 'Kill Node'}
                </button>

                <button
                  className="restart-button"
                  disabled={
                    node.is_active ||
                    loadingAction !== ''
                  }
                  onClick={() =>
                    handleNodeAction(
                      NODES.find((item) => item.id === id),
                      'restart'
                    )
                  }
                >
                  {loadingAction === `${id}-restart`
                    ? 'Restarting...'
                    : 'Restart Node'}
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <h2>Raft Log</h2>
          <span>{raftLog?.entries?.length ?? 0} entries</span>
        </div>

        {logError && <div className="error">{logError}</div>}

        <div className="tool-list">
          {raftLog?.entries?.length ? (
            raftLog.entries.map((entry, index) => (
              <div className="tool-item" key={index}>
                <strong>Entry {index + 1}</strong>
                <pre>{JSON.stringify(entry, null, 2)}</pre>
              </div>
            ))
          ) : (
            <p className="empty">
              {raftLog
                ? 'No log entries yet.'
                : 'Loading Raft log...'}
            </p>
          )}
        </div>

        <div className="node-details">
          <div>
            <span>Log Term</span>
            <strong>{raftLog?.term ?? '—'}</strong>
          </div>

          <div>
            <span>Commit Index</span>
            <strong>{raftLog?.commit_index ?? '—'}</strong>
          </div>

          <div>
            <span>Last Applied</span>
            <strong>{raftLog?.last_applied ?? '—'}</strong>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <h2>Tool Registry</h2>
          <span>{activeTools.length} active tools</span>
        </div>

        <div className="tool-list">
          {activeTools.length ? (
            activeTools.map((tool, index) => (
              <div
                className="tool-item"
                key={tool.name || index}
              >
                {typeof tool === 'string'
                  ? tool
                  : tool.name || JSON.stringify(tool)}
              </div>
            ))
          ) : (
            <p className="empty">
              No registered tools yet.
            </p>
          )}
        </div>
      </section>

      <footer>
        <span>
          {lastUpdated
            ? `Last updated: ${lastUpdated}`
            : 'Connecting to cluster...'}
        </span>

        <button onClick={refreshDashboard}>
          Refresh now
        </button>
      </footer>
    </main>
  )
}

export default App
