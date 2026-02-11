import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getNextContent, submitAttempt, NextContent } from '../services/api'

interface Props {
    studentId: number
}

export default function Learn({ studentId }: Props) {
    const navigate = useNavigate()
    const [content, setContent] = useState<NextContent | null>(null)
    const [answer, setAnswer] = useState('')
    const [feedback, setFeedback] = useState<{
        shown: boolean
        correct: boolean
        message: string
        misconceptions: string[]
    } | null>(null)
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)
    const [questionId, setQuestionId] = useState(0)

    const fetchContent = async () => {
        setLoading(true)
        setFeedback(null)
        setAnswer('')
        try {
            const data = await getNextContent(studentId)
            setContent(data)
            setQuestionId(prev => prev + 1)
        } catch (err) {
            console.error(err)
        }
        setLoading(false)
    }

    useEffect(() => {
        fetchContent()
    }, [studentId])

    const handleSubmit = async () => {
        if (!answer.trim()) return
        setSubmitting(true)

        try {
            const result = await submitAttempt(studentId, questionId, answer)
            setFeedback({
                shown: true,
                correct: result.is_correct,
                message: result.feedback,
                misconceptions: result.misconceptions
            })
        } catch (err) {
            console.error(err)
        }
        setSubmitting(false)
    }

    const handleContinue = () => {
        fetchContent()
    }

    if (loading) {
        return (
            <div className="app-container">
                <div className="app-header">
                    <span className="app-logo">📚 Learning</span>
                    <div>
                        <button className="btn btn-secondary" onClick={() => navigate('/progress')}>
                            View Progress
                        </button>
                    </div>
                </div>
                <div className="loading"><div className="spinner"></div></div>
            </div>
        )
    }

    return (
        <div className="app-container">
            <div className="app-header">
                <span className="app-logo">📚 Learning</span>
                <div style={{ display: 'flex', gap: 'var(--space-md)' }}>
                    <button className="btn btn-secondary" onClick={() => navigate('/progress')}>
                        View Progress
                    </button>
                    <button className="btn btn-primary" onClick={() => navigate('/posttest')}>
                        Take Posttest
                    </button>
                </div>
            </div>

            <div className="app-main">
                {content && (
                    <div className="fade-in">
                        {/* Action Badge */}
                        <div style={{ marginBottom: 'var(--space-md)', display: 'flex', gap: 'var(--space-sm)' }}>
                            <span className={`badge ${content.action === 'TEACH' ? 'badge-info' :
                                    content.action === 'TEST' ? 'badge-warning' :
                                        content.action === 'RETEACH' ? 'badge-error' :
                                            content.action === 'ADVANCE' ? 'badge-success' : 'badge-info'
                                }`}>
                                {content.action}
                            </span>
                            <span className="badge badge-info">{content.concept}</span>
                        </div>

                        {/* Lesson Content */}
                        {content.content && (
                            <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                                <h2 style={{ marginBottom: 'var(--space-md)' }}>📖 Lesson: {content.concept}</h2>

                                {content.content.bullets && (
                                    <div className="lesson-content">
                                        <ul className="lesson-bullets">
                                            {content.content.bullets.map((b, i) => (
                                                <li key={i}>{b}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {content.content.worked_example && (
                                    <div className="lesson-section">
                                        <h4>💡 Example</h4>
                                        <div className="code-block">
                                            <pre>{content.content.worked_example}</pre>
                                        </div>
                                    </div>
                                )}

                                {content.content.pitfall && (
                                    <div className="lesson-section">
                                        <h4>⚠️ Common Mistake</h4>
                                        <div className="alert alert-warning">{content.content.pitfall}</div>
                                    </div>
                                )}

                                {content.content.quick_check && (
                                    <div className="lesson-section">
                                        <h4>🤔 Think About It</h4>
                                        <p style={{ color: 'var(--text-secondary)' }}>{content.content.quick_check}</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Question */}
                        {content.question && (
                            <div className="card">
                                <h3 style={{ marginBottom: 'var(--space-md)' }}>
                                    📝 {content.action === 'TEST' ? 'Practice Question' : 'Quick Check'}
                                </h3>

                                <p style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-lg)' }}>
                                    {content.question.prompt}
                                </p>

                                {content.question.type === 'mcq' && content.question.options && (
                                    <div className="options-list">
                                        {Object.entries(content.question.options).map(([key, value]) => (
                                            <div
                                                key={key}
                                                className={`option-item ${answer === key ? 'selected' : ''} ${feedback?.shown ? (
                                                        answer === key ? (feedback.correct ? 'correct' : 'incorrect') : ''
                                                    ) : ''
                                                    }`}
                                                onClick={() => !feedback?.shown && setAnswer(key)}
                                            >
                                                <span className="option-key">{key}</span>
                                                <span>{value}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {content.question.type === 'coding' && (
                                    <div className="code-editor">
                                        <textarea
                                            value={answer}
                                            onChange={(e) => setAnswer(e.target.value)}
                                            placeholder="Write your code here..."
                                            disabled={feedback?.shown}
                                        />
                                    </div>
                                )}

                                {/* Feedback */}
                                {feedback?.shown && (
                                    <div className={`alert ${feedback.correct ? 'alert-success' : 'alert-error'}`}
                                        style={{ marginTop: 'var(--space-lg)' }}>
                                        <strong>{feedback.correct ? '✓ Correct!' : '✗ Not quite right'}</strong>
                                        <p>{feedback.message}</p>
                                        {feedback.misconceptions.length > 0 && (
                                            <p style={{ marginTop: 'var(--space-sm)', fontSize: 'var(--font-size-sm)' }}>
                                                Focus areas: {feedback.misconceptions.join(', ')}
                                            </p>
                                        )}
                                    </div>
                                )}

                                {/* Actions */}
                                <div style={{ marginTop: 'var(--space-lg)', display: 'flex', gap: 'var(--space-md)' }}>
                                    {!feedback?.shown ? (
                                        <button
                                            className="btn btn-primary"
                                            onClick={handleSubmit}
                                            disabled={!answer.trim() || submitting}
                                        >
                                            {submitting ? 'Checking...' : 'Submit Answer'}
                                        </button>
                                    ) : (
                                        <button className="btn btn-primary" onClick={handleContinue}>
                                            Continue Learning →
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* No question - just lesson */}
                        {!content.question && content.content && (
                            <button className="btn btn-primary" onClick={handleContinue}>
                                I understand, continue →
                            </button>
                        )}

                        {/* Advance / Review - no lesson or question, just a transition */}
                        {!content.question && !content.content && (
                            <div className="card" style={{ textAlign: 'center', padding: 'var(--space-xl)' }}>
                                <h2 style={{ marginBottom: 'var(--space-md)' }}>
                                    {content.action === 'advance' ? '🎉 Great job!' : '🔄 Let\'s review'}
                                </h2>
                                <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-lg)' }}>
                                    {content.reason}
                                </p>
                                <button className="btn btn-primary" onClick={handleContinue}>
                                    Continue to {content.concept} →
                                </button>
                            </div>
                        )}

                        {/* Reason */}
                        <p style={{ marginTop: 'var(--space-lg)', color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
                            🤖 {content.reason}
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}
