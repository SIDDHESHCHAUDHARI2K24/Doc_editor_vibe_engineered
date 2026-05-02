import { useState, useEffect } from 'react'

type HealthData = Record<string, unknown> | null

function App() {
  const [proxied, setProxied] = useState<HealthData>(null)
  const [direct, setDirect] = useState<HealthData>(null)
  const [proxiedError, setProxiedError] = useState<string | null>(null)
  const [directError, setDirectError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function checkHealth() {
      setLoading(true)

      try {
        const proxiedRes = await fetch('/api/health')
        if (!proxiedRes.ok) {
          throw new Error(`HTTP ${proxiedRes.status}: ${proxiedRes.statusText}`)
        }
        setProxied(await proxiedRes.json())
      } catch (err) {
        setProxiedError(err instanceof Error ? err.message : 'Unknown error')
      }

      try {
        const directRes = await fetch('http://localhost:8000/health', {
          credentials: 'include',
        })
        if (!directRes.ok) {
          throw new Error(`HTTP ${directRes.status}: ${directRes.statusText}`)
        }
        setDirect(await directRes.json())
      } catch (err) {
        setDirectError(err instanceof Error ? err.message : 'Unknown error')
      }

      setLoading(false)
    }

    checkHealth()
  }, [])

  return (
    <div className="bg-slate-100 text-slate-900 min-h-screen p-8">
      <h1 className="text-2xl font-bold mb-6">Document Editor — Health Check</h1>

      {loading && <p className="text-slate-500">Checking backend health...</p>}

      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h2 className="font-semibold mb-2">Proxied</h2>
            <pre className="bg-white p-4 rounded border text-sm overflow-auto">
              {proxiedError
                ? `Error: ${proxiedError}`
                : JSON.stringify(proxied, null, 2)}
            </pre>
          </div>
          <div>
            <h2 className="font-semibold mb-2">Direct (CORS)</h2>
            <pre className="bg-white p-4 rounded border text-sm overflow-auto">
              {directError
                ? `Error: ${directError}`
                : JSON.stringify(direct, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
