import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { instructorLogin } from '../services/api'

interface Props {
    onLogin: (user: { id: number; username: string; role: 'student' | 'instructor' }) => void
}

export default function InstructorLogin({ onLogin }: Props) {
    const navigate = useNavigate()
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            await instructorLogin(username, password)
            onLogin({ id: 0, username, role: 'instructor' })
            navigate('/instructor/dashboard')
        } catch {
            setError('Invalid credentials. Use: instructor / teach123')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="login-container">
            <div className="login-card fade-in">
                <h1 className="login-title">👨‍🏫 Instructor Portal</h1>
                <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: 'var(--space-lg)' }}>
                    Access student analytics and insights
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
                            placeholder="instructor"
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
                            placeholder="teach123"
                            required
                        />
                    </div>

                    <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
                        {loading ? 'Signing in...' : 'Access Dashboard'}
                    </button>
                </form>

                <div style={{ marginTop: 'var(--space-lg)', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <a href="/login" style={{ color: 'var(--accent-primary)', textDecoration: 'none' }}>
                        ← Student Login
                    </a>
                </div>
            </div>
        </div>
    )
}
