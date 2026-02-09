import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDashboard, getStudentsList, exportAttempts, exportMetrics, DashboardData } from '../services/api'

interface Props {
    onLogout: () => void
}

export default function Dashboard({ onLogout }: Props) {
    const navigate = useNavigate()
    const [data, setData] = useState<DashboardData | null>(null)
    const [students, setStudents] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState<'overview' | 'students' | 'export'>('overview')

    useEffect(() => {
        Promise.all([
            getDashboard(),
            getStudentsList()
        ]).then(([dashboard, studentData]) => {
            setData(dashboard)
            setStudents(studentData.students || [])
            setLoading(false)
        }).catch(() => setLoading(false))
    }, [])

    const handleExportAttempts = async () => {
        try {
            const blob = await exportAttempts()
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `attempts_${new Date().toISOString().split('T')[0]}.csv`
            a.click()
        } catch (err) {
            console.error(err)
        }
    }

    const handleExportMetrics = async () => {
        try {
            const metrics = await exportMetrics()
            const blob = new Blob([JSON.stringify(metrics, null, 2)], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `metrics_${new Date().toISOString().split('T')[0]}.json`
            a.click()
        } catch (err) {
            console.error(err)
        }
    }

    if (loading) {
        return (
            <div className="app-container">
                <div className="app-header">
                    <span className="app-logo">📊 Instructor Dashboard</span>
                </div>
                <div className="loading"><div className="spinner"></div></div>
            </div>
        )
    }

    return (
        <div className="app-container">
            <div className="app-header">
                <span className="app-logo">📊 Instructor Dashboard</span>
                <button className="btn btn-secondary" onClick={onLogout}>
                    Logout
                </button>
            </div>

            <div className="app-main">
                {/* Tab Navigation */}
                <div style={{ display: 'flex', gap: 'var(--space-sm)', marginBottom: 'var(--space-xl)' }}>
                    {(['overview', 'students', 'export'] as const).map(tab => (
                        <button
                            key={tab}
                            className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
                            onClick={() => setActiveTab(tab)}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </div>

                {/* Overview Tab */}
                {activeTab === 'overview' && data && (
                    <div className="fade-in">
                        {/* Summary Cards */}
                        <div className="card-grid" style={{ marginBottom: 'var(--space-xl)' }}>
                            <div className="card">
                                <h3 style={{ color: 'var(--text-secondary)' }}>Total Students</h3>
                                <div className="mastery-score" style={{ fontSize: '3rem' }}>{data.total_students}</div>
                            </div>
                            <div className="card">
                                <h3 style={{ color: 'var(--text-secondary)' }}>Struggling Students</h3>
                                <div className="mastery-score" style={{ fontSize: '3rem', color: 'var(--error)' }}>
                                    {data.struggling_students.length}
                                </div>
                            </div>
                            <div className="card">
                                <h3 style={{ color: 'var(--text-secondary)' }}>Misconception Clusters</h3>
                                <div className="mastery-score" style={{ fontSize: '3rem' }}>
                                    {data.misconception_clusters.length}
                                </div>
                            </div>
                        </div>

                        {/* Misconception Clusters */}
                        <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                            <h3 style={{ marginBottom: 'var(--space-lg)' }}>🔍 Misconception Clusters</h3>
                            {data.misconception_clusters.length > 0 ? (
                                <table className="stats-table">
                                    <thead>
                                        <tr>
                                            <th>Misconception</th>
                                            <th>Students</th>
                                            <th>Severity</th>
                                            <th>Intervention</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.misconception_clusters.map((c, i) => (
                                            <tr key={i}>
                                                <td>{c.misconception}</td>
                                                <td>{c.student_count}</td>
                                                <td>
                                                    <span className={`badge badge-${c.severity === 'high' ? 'error' : c.severity === 'medium' ? 'warning' : 'info'}`}>
                                                        {c.severity}
                                                    </span>
                                                </td>
                                                <td style={{ fontSize: 'var(--font-size-sm)' }}>{c.recommended_intervention}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <p style={{ color: 'var(--text-muted)' }}>No significant clusters detected yet.</p>
                            )}
                        </div>

                        {/* Priority Students */}
                        <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
                            <h3 style={{ marginBottom: 'var(--space-lg)' }}>⚠️ Priority Students</h3>
                            {data.priority_students.length > 0 ? (
                                <table className="stats-table">
                                    <thead>
                                        <tr>
                                            <th>Student</th>
                                            <th>Priority Score</th>
                                            <th>Status</th>
                                            <th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.priority_students.map((s, i) => (
                                            <tr key={i}>
                                                <td>{s.username}</td>
                                                <td>{s.priority_score.toFixed(2)}</td>
                                                <td>
                                                    {s.needs_attention && <span className="badge badge-error">Needs Attention</span>}
                                                </td>
                                                <td>
                                                    <button
                                                        className="btn btn-secondary"
                                                        style={{ padding: '4px 12px', fontSize: 'var(--font-size-sm)' }}
                                                        onClick={() => navigate(`/instructor/student/${s.student_id}`)}
                                                    >
                                                        View
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <p style={{ color: 'var(--text-muted)' }}>No priority students at this time.</p>
                            )}
                        </div>

                        {/* Intervention Suggestions */}
                        {data.intervention_suggestions.length > 0 && (
                            <div className="card">
                                <h3 style={{ marginBottom: 'var(--space-lg)' }}>💡 AI Suggestions</h3>
                                <ul className="lesson-bullets">
                                    {data.intervention_suggestions.map((s, i) => (
                                        <li key={i}>{s}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}

                {/* Students Tab */}
                {activeTab === 'students' && (
                    <div className="fade-in">
                        <div className="card">
                            <h3 style={{ marginBottom: 'var(--space-lg)' }}>All Students</h3>
                            <table className="stats-table">
                                <thead>
                                    <tr>
                                        <th>Username</th>
                                        <th>Level</th>
                                        <th>Pretest</th>
                                        <th>Posttest</th>
                                        <th>Avg Mastery</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {students.map((s, i) => (
                                        <tr key={i}>
                                            <td>{s.username}</td>
                                            <td>
                                                <span className={`badge badge-${s.baseline_level === 'high' ? 'success' : s.baseline_level === 'low' ? 'error' : 'warning'}`}>
                                                    {s.baseline_level}
                                                </span>
                                            </td>
                                            <td>{s.pretest_completed ? '✓' : '—'}</td>
                                            <td>{s.posttest_completed ? '✓' : '—'}</td>
                                            <td>{(s.avg_mastery * 100).toFixed(0)}%</td>
                                            <td>
                                                <button
                                                    className="btn btn-secondary"
                                                    style={{ padding: '4px 12px', fontSize: 'var(--font-size-sm)' }}
                                                    onClick={() => navigate(`/instructor/student/${s.id}`)}
                                                >
                                                    Details
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {students.length === 0 && (
                                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 'var(--space-lg)' }}>
                                    No students registered yet.
                                </p>
                            )}
                        </div>
                    </div>
                )}

                {/* Export Tab */}
                {activeTab === 'export' && (
                    <div className="fade-in">
                        <div className="card-grid">
                            <div className="card">
                                <h3>📥 Export Attempts</h3>
                                <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-lg)' }}>
                                    Download all student attempts as CSV for external analysis.
                                </p>
                                <button className="btn btn-primary" onClick={handleExportAttempts}>
                                    Download CSV
                                </button>
                            </div>

                            <div className="card">
                                <h3>📊 Export Metrics</h3>
                                <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-lg)' }}>
                                    Download computed research metrics as JSON.
                                </p>
                                <button className="btn btn-primary" onClick={handleExportMetrics}>
                                    Download JSON
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
