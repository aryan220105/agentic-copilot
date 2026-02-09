import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getStudentDetail } from '../services/api'

export default function StudentDetail() {
    const { id } = useParams()
    const navigate = useNavigate()
    const [detail, setDetail] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (id) {
            getStudentDetail(parseInt(id)).then(data => {
                setDetail(data)
                setLoading(false)
            }).catch(() => setLoading(false))
        }
    }, [id])

    if (loading) {
        return (
            <div className="app-container">
                <div className="app-header">
                    <span className="app-logo">👤 Student Details</span>
                </div>
                <div className="loading"><div className="spinner"></div></div>
            </div>
        )
    }

    if (!detail) {
        return (
            <div className="app-container">
                <div className="app-header">
                    <span className="app-logo">👤 Student Details</span>
                </div>
                <div className="app-main">
                    <div className="card">
                        <p>Student not found.</p>
                        <button className="btn btn-secondary" onClick={() => navigate('/instructor/dashboard')}>
                            ← Back to Dashboard
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="app-container">
            <div className="app-header">
                <span className="app-logo">👤 {detail.username || `Student ${id}`}</span>
                <button className="btn btn-secondary" onClick={() => navigate('/instructor/dashboard')}>
                    ← Back to Dashboard
                </button>
            </div>

            <div className="app-main">
                {/* Student Info */}
                <div className="card-grid" style={{ marginBottom: 'var(--space-xl)' }}>
                    <div className="card">
                        <h3 style={{ color: 'var(--text-secondary)' }}>Baseline Level</h3>
                        <span className={`badge badge-${detail.baseline_level === 'high' ? 'success' :
                                detail.baseline_level === 'low' ? 'error' : 'warning'
                            }`}>
                            {detail.baseline_level || 'Unknown'}
                        </span>
                    </div>
                    <div className="card">
                        <h3 style={{ color: 'var(--text-secondary)' }}>Current Concept</h3>
                        <span className="badge badge-info">{detail.current_concept || 'N/A'}</span>
                    </div>
                    <div className="card">
                        <h3 style={{ color: 'var(--text-secondary)' }}>Average Mastery</h3>
                        <div className="mastery-score">
                            {detail.mastery_scores
                                ? `${(Object.values(detail.mastery_scores as Record<string, number>).reduce((a, b) => a + b, 0) /
                                    Math.max(Object.keys(detail.mastery_scores).length, 1) * 100).toFixed(0)}%`
                                : 'N/A'}
                        </div>
                    </div>
                </div>

                {/* Mastery Breakdown */}
                {detail.mastery_scores && Object.keys(detail.mastery_scores).length > 0 && (
                    <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                        <h3 style={{ marginBottom: 'var(--space-lg)' }}>📊 Concept Mastery</h3>
                        <div className="mastery-grid">
                            {Object.entries(detail.mastery_scores as Record<string, number>).map(([concept, score]) => {
                                const level = score >= 0.8 ? 'high' : score >= 0.5 ? 'medium' : 'low'
                                return (
                                    <div key={concept} className={`mastery-item heatmap-cell ${level}`}>
                                        <div className="mastery-score" style={{ fontSize: 'var(--font-size-xl)' }}>
                                            {Math.round(score * 100)}%
                                        </div>
                                        <div className="mastery-label">{concept}</div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                )}

                {/* Misconceptions */}
                {detail.misconceptions && detail.misconceptions.length > 0 && (
                    <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                        <h3 style={{ marginBottom: 'var(--space-lg)' }}>🔍 Identified Misconceptions</h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
                            {detail.misconceptions.map((m: string, i: number) => (
                                <span key={i} className="badge badge-warning">{m}</span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Recent Attempts */}
                {detail.recent_attempts && detail.recent_attempts.length > 0 && (
                    <div className="card">
                        <h3 style={{ marginBottom: 'var(--space-lg)' }}>📝 Recent Attempts</h3>
                        <table className="stats-table">
                            <thead>
                                <tr>
                                    <th>Question</th>
                                    <th>Concept</th>
                                    <th>Result</th>
                                    <th>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {detail.recent_attempts.slice(0, 10).map((a: any, i: number) => (
                                    <tr key={i}>
                                        <td>#{a.question_id}</td>
                                        <td>{a.concept || 'N/A'}</td>
                                        <td>
                                            <span className={`badge badge-${a.is_correct ? 'success' : 'error'}`}>
                                                {a.is_correct ? 'Correct' : 'Incorrect'}
                                            </span>
                                        </td>
                                        <td style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
                                            {a.submitted_at ? new Date(a.submitted_at).toLocaleDateString() : 'N/A'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Intervention */}
                {detail.intervention_suggestion && (
                    <div className="alert alert-info" style={{ marginTop: 'var(--space-xl)' }}>
                        <strong>💡 Recommended Intervention:</strong>
                        <p style={{ marginTop: 'var(--space-sm)' }}>{detail.intervention_suggestion}</p>
                    </div>
                )}
            </div>
        </div>
    )
}
