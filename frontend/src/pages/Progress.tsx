import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getProgress, ProgressData } from '../services/api'

interface Props {
    studentId: number
}

export default function Progress({ studentId }: Props) {
    const navigate = useNavigate()
    const [progress, setProgress] = useState<ProgressData | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        getProgress(studentId).then(data => {
            setProgress(data)
            setLoading(false)
        }).catch(() => setLoading(false))
    }, [studentId])

    if (loading) {
        return (
            <div className="app-container">
                <div className="app-header">
                    <span className="app-logo">📊 Your Progress</span>
                </div>
                <div className="loading"><div className="spinner"></div></div>
            </div>
        )
    }

    if (!progress) {
        return (
            <div className="app-container">
                <div className="app-header">
                    <span className="app-logo">📊 Your Progress</span>
                </div>
                <div className="app-main">
                    <div className="card">
                        <p>Unable to load progress data.</p>
                    </div>
                </div>
            </div>
        )
    }

    const concepts = [
        { id: 'variables', name: 'Variables', icon: '📦' },
        { id: 'types', name: 'Data Types', icon: '🏷️' },
        { id: 'operators', name: 'Operators', icon: '➕' },
        { id: 'conditionals', name: 'Conditionals', icon: '🔀' },
        { id: 'loops', name: 'Loops', icon: '🔄' },
        { id: 'arrays', name: 'Arrays', icon: '📚' },
        { id: 'functions', name: 'Functions', icon: '⚡' },
        { id: 'strings', name: 'Strings', icon: '📝' },
        { id: 'io', name: 'Input/Output', icon: '💬' },
    ]

    return (
        <div className="app-container">
            <div className="app-header">
                <span className="app-logo">📊 Your Progress</span>
                <div style={{ display: 'flex', gap: 'var(--space-md)' }}>
                    <button className="btn btn-secondary" onClick={() => navigate('/learn')}>
                        ← Back to Learning
                    </button>
                    <button className="btn btn-primary" onClick={() => navigate('/posttest')}>
                        Take Posttest
                    </button>
                </div>
            </div>

            <div className="app-main">
                {/* Overall Score */}
                <div className="card" style={{ textAlign: 'center', marginBottom: 'var(--space-xl)' }}>
                    <h2 style={{ marginBottom: 'var(--space-md)' }}>Overall Mastery</h2>
                    <div className="mastery-score" style={{ fontSize: '4rem' }}>
                        {Math.round(progress.overall_mastery * 100)}%
                    </div>
                    <div className="progress-bar" style={{ height: '12px', marginTop: 'var(--space-lg)' }}>
                        <div
                            className="progress-fill"
                            style={{ width: `${progress.overall_mastery * 100}%` }}
                        ></div>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', marginTop: 'var(--space-md)' }}>
                        Current focus: <strong>{progress.current_concept}</strong>
                    </p>
                </div>

                {/* Concept Mastery Grid */}
                <h3 style={{ marginBottom: 'var(--space-md)' }}>Concept Mastery</h3>
                <div className="mastery-grid" style={{ marginBottom: 'var(--space-xl)' }}>
                    {concepts.map(c => {
                        const score = progress.mastery_scores[c.id] || 0
                        const level = score >= 0.8 ? 'high' : score >= 0.5 ? 'medium' : 'low'
                        const completed = progress.concepts_completed?.includes(c.id)

                        return (
                            <div
                                key={c.id}
                                className={`mastery-item heatmap-cell ${level}`}
                                style={{
                                    opacity: progress.current_concept === c.id ? 1 : 0.8,
                                    border: progress.current_concept === c.id ? '2px solid var(--accent-primary)' : 'none'
                                }}
                            >
                                <div style={{ fontSize: '2rem', marginBottom: 'var(--space-xs)' }}>{c.icon}</div>
                                <div className="mastery-score" style={{ fontSize: 'var(--font-size-xl)' }}>
                                    {Math.round(score * 100)}%
                                </div>
                                <div className="mastery-label">{c.name}</div>
                                {completed && <span className="badge badge-success" style={{ marginTop: 'var(--space-xs)' }}>✓</span>}
                            </div>
                        )
                    })}
                </div>

                {/* Recent Misconceptions */}
                {progress.misconceptions_history.length > 0 && (
                    <div className="card">
                        <h3 style={{ marginBottom: 'var(--space-md)' }}>🔍 Areas for Improvement</h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
                            {[...new Set(progress.misconceptions_history)].slice(0, 5).map((m, i) => (
                                <span key={i} className="badge badge-warning">{m}</span>
                            ))}
                        </div>
                        <p style={{ color: 'var(--text-muted)', marginTop: 'var(--space-md)', fontSize: 'var(--font-size-sm)' }}>
                            The AI tutor will focus on these concepts to help you improve.
                        </p>
                    </div>
                )}

                {/* Completed Concepts */}
                {progress.concepts_completed.length > 0 && (
                    <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
                        <h3 style={{ marginBottom: 'var(--space-md)' }}>🏆 Mastered Concepts</h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
                            {progress.concepts_completed.map((c, i) => (
                                <span key={i} className="badge badge-success">{c}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
