import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../services/api'

interface Props {
    onLogin: (user: { id: number; username: string; role: 'student' | 'instructor' }) => void
}

export default function Login({ onLogin }: Props) {
    const navigate = useNavigate()
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [baseline, setBaseline] = useState('medium')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            const result = await login(username, password, baseline)
            onLogin({
                id: result.student_id,
                username: result.username,
                role: 'student'
            })

            if (result.pretest_completed) {
                navigate('/learn')
            } else {
                navigate('/pretest')
            }
        } catch {
            setError('Login failed. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="login-container">
            <div className="login-card fade-in">
                <h1 className="login-title">🤖 Agentic Copilot</h1>
                <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: 'var(--space-lg)' }}>
                    AI-Powered Adaptive Learning for Programming
                </p>

                {error && <div className="alert alert-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Username</label>
                        <input
                            type="text"
                            className="form-input"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter your username"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            className="form-input"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Your Experience Level</label>
                        <select
                            className="form-input form-select"
                            value={baseline}
                            onChange={(e) => setBaseline(e.target.value)}
                        >
                            <option value="low">Beginner - New to programming</option>
                            <option value="medium">Intermediate - Some experience</option>
                            <option value="high">Advanced - Comfortable with basics</option>
                        </select>
                    </div>

                    <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
                        {loading ? 'Signing in...' : 'Start Learning'}
                    </button>
                </form>

                <div style={{ marginTop: 'var(--space-lg)', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <a
                        href="/instructor/login"
                        style={{ color: 'var(--accent-primary)', textDecoration: 'none' }}
                    >
                        Instructor Login →
                    </a>
                </div>
            </div>
        </div>
    )
}
