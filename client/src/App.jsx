import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [config, setConfig] = useState(null)
  const [toNumber, setToNumber] = useState('')
  const [sending, setSending] = useState(false)
  const [result, setResult] = useState('')
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${apiBase}/twilio/config`)
      .then((response) => response.json())
      .then((data) => setConfig(data))
      .catch(() => {
        setConfig({
          account_sid: false,
          auth_token: false,
          from_number: false,
          default_to_number: false,
        })
      })
  }, [apiBase])

  async function handleStartMessage() {
    setSending(true)
    setResult('')

    try {
      const response = await fetch(`${apiBase}/twilio/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(
          toNumber.trim() ? { to_number: toNumber.trim() } : {},
        ),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to send SMS')
      }

      setResult(`Start message sent to ${data.to}. Message SID: ${data.sid}`)
    } catch (error) {
      setResult(error.message)
    } finally {
      setSending(false)
    }
  }

  const morningQuestions = [
    'Full name',
    'Age',
    'Preferred course',
    'City',
  ]

  const eveningQuestions = [
    'Full name',
    'Occupation',
    'Preferred evening time',
  ]

  return (
    <main className="app-shell">
      <section className="hero-panel">
        <p className="eyebrow">Twilio SMS Flow</p>
        <h1>Batch Registration Bot</h1>
        <p className="hero-copy">
          This setup starts an SMS conversation, asks for a morning or evening
          batch, collects batch-specific answers, asks for confirmation, and
          then sends back the final response summary.
        </p>

        <div className="action-row">
          <input
            type="tel"
            placeholder="Optional recipient number"
            value={toNumber}
            onChange={(event) => setToNumber(event.target.value)}
          />
          <button onClick={handleStartMessage} disabled={sending}>
            {sending ? 'Sending...' : 'Send Start SMS'}
          </button>
        </div>

        {result ? <p className="result-banner">{result}</p> : null}
      </section>

      <section className="grid">
        <article className="card">
          <h2>Config Status</h2>
          <ul className="status-list">
            <li>Account SID: {config?.account_sid ? 'Ready' : 'Missing'}</li>
            <li>Auth Token: {config?.auth_token ? 'Ready' : 'Missing'}</li>
            <li>Twilio Number: {config?.from_number ? 'Ready' : 'Missing'}</li>
            <li>
              Default Recipient: {config?.default_to_number ? 'Ready' : 'Missing'}
            </li>
          </ul>
        </article>

        <article className="card">
          <h2>Morning Batch Questions</h2>
          <ol>
            {morningQuestions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ol>
        </article>

        <article className="card">
          <h2>Evening Batch Questions</h2>
          <ol>
            {eveningQuestions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ol>
        </article>

        <article className="card">
          <h2>Webhook Flow</h2>
          <ol>
            <li>User texts your Twilio number.</li>
            <li>Bot asks for Morning or Evening.</li>
            <li>Bot collects the matching questions.</li>
            <li>Bot sends a confirmation summary.</li>
            <li>On YES, bot replies with the final saved response.</li>
          </ol>
        </article>
      </section>
    </main>
  )
}

export default App
