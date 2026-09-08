import { useEffect, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

type HealthStatus = 'checking' | 'ok' | 'error';

function App() {
  const [apiStatus, setApiStatus] = useState<HealthStatus>('checking');
  const [dbStatus, setDbStatus] = useState<HealthStatus>('checking');

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then((res) => (res.ok ? setApiStatus('ok') : setApiStatus('error')))
      .catch(() => setApiStatus('error'));

    fetch(`${API_BASE_URL}/health/db`)
      .then((res) => (res.ok ? setDbStatus('ok') : setDbStatus('error')))
      .catch(() => setDbStatus('error'));
  }, []);

  return (
    <main style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
      <h1>USNPS Tracker</h1>
      <p>Phase 0 — verifying the stack is wired together.</p>
      <ul>
        <li>Backend API: {apiStatus}</li>
        <li>Database (via backend): {dbStatus}</li>
      </ul>
    </main>
  );
}

export default App;
