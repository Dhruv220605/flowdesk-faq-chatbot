import { useState, useRef, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000'

const SUGGESTIONS = [
  'How much is the Pro plan?',
  'Does FlowDesk integrate with Slack?',
  'How do I invite team members?',
]

function ConfidenceBadge({ score, low }) {
  const pct = Math.round(score * 100)
  const tone = low ? 'low' : pct > 70 ? 'high' : 'mid'
  return (
    <span className={`confidence-badge confidence-${tone}`}>
      <span className="confidence-dot" />
      {pct}% match
    </span>
  )
}

function SourcesDisclosure({ sources }) {
  const [open, setOpen] = useState(false)
  if (!sources || sources.length === 0) return null
  return (
    <div className="sources-block">
      <button className="sources-toggle" onClick={() => setOpen(!open)}>
        {open ? 'Hide sources' : `View ${sources.length} source${sources.length > 1 ? 's' : ''}`}
        <span className={`chevron ${open ? 'chevron-open' : ''}`}>›</span>
      </button>
      {open && (
        <ul className="sources-list">
          {sources.map((s, i) => (
            <li key={i} className="source-pill">{s}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

function FeedbackButtons({ logId, onFeedback, given }) {
  if (given !== null) {
    return (
      <div className="feedback-given">
        {given ? 'Thanks for the feedback' : 'Noted — we\'ll improve this'}
      </div>
    )
  }
  return (
    <div className="feedback-buttons">
      <span className="feedback-label">Helpful?</span>
      <button className="feedback-btn" onClick={() => onFeedback(logId, true)} aria-label="Helpful">👍</button>
      <button className="feedback-btn" onClick={() => onFeedback(logId, false)} aria-label="Not helpful">👎</button>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(text) {
    const query = text.trim()
    if (!query || loading) return

    setError(null)
    setMessages((prev) => [...prev, { role: 'user', text: query }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query }),
      })
      if (!res.ok) throw new Error('Server error')
      const data = await res.json()

      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          text: data.answer,
          confidence: data.confidence,
          lowConfidence: data.low_confidence,
          sources: data.sources,
          logId: data.log_id,
          feedbackGiven: null,
        },
      ])
    } catch (err) {
      setError('Could not reach FlowDesk Assistant. Is the backend running on port 5000?')
    } finally {
      setLoading(false)
    }
  }

  async function handleFeedback(logId, helpful) {
    setMessages((prev) =>
      prev.map((m) => (m.logId === logId ? { ...m, feedbackGiven: helpful } : m))
    )
    try {
      await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ log_id: logId, helpful }),
      })
    } catch {
      // silent fail, feedback is non-critical
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <div className="app-shell">
      <div className="chat-panel">
        <header className="chat-header">
          <div className="brand">
            <div className="brand-mark">FD</div>
            <div className="brand-text">
              <div className="brand-name">FlowDesk Assistant</div>
              <div className="brand-status">
                <span className="status-dot" />
                Online — grounded answers only
              </div>
            </div>
          </div>
        </header>

        <div className="message-list" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="empty-state">
              <p className="empty-title">Ask about FlowDesk</p>
              <p className="empty-sub">Pricing, features, integrations, account help.</p>
              <div className="suggestion-chips">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="chip" onClick={() => sendMessage(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) =>
            m.role === 'user' ? (
              <div key={i} className="bubble-row bubble-row-user">
                <div className="bubble bubble-user">{m.text}</div>
              </div>
            ) : (
              <div key={i} className="bubble-row bubble-row-bot">
                <div className="bubble bubble-bot">
                  <p className="bubble-text">{m.text}</p>
                  <div className="bubble-meta">
                    <ConfidenceBadge score={m.confidence} low={m.lowConfidence} />
                  </div>
                  <SourcesDisclosure sources={m.sources} />
                  <FeedbackButtons
                    logId={m.logId}
                    given={m.feedbackGiven}
                    onFeedback={handleFeedback}
                  />
                </div>
              </div>
            )
          )}

          {loading && (
            <div className="bubble-row bubble-row-bot">
              <div className="bubble bubble-bot typing-bubble">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}

          {error && <div className="error-banner">{error}</div>}
        </div>

        <div className="input-bar">
          <textarea
            className="input-field"
            placeholder="Type your question..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button
            className="send-btn"
            onClick={() => sendMessage(input)}
            disabled={loading || !input.trim()}
            aria-label="Send"
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  )
}