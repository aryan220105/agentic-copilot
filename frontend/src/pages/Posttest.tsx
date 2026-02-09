import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPosttest, submitPosttest, Question } from '../services/api'

interface Props {
    studentId: number
}

export default function Posttest({ studentId }: Props) {
    const navigate = useNavigate()
    const [questions, setQuestions] = useState<Question[]>([])
    const [answers, setAnswers] = useState<Record<number, string>>({})
    const [currentIndex, setCurrentIndex] = useState(0)
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)
    const [result, setResult] = useState<{
        score: number
        total: number
        percentage: number
    } | null>(null)

    useEffect(() => {
        getPosttest().then(data => {
            setQuestions(data.questions || [])
            setLoading(false)
        })
    }, [])

    const currentQ = questions[currentIndex]

    const handleSubmit = async () => {
        setSubmitting(true)
        const responses = questions.map(q => ({
            question_id: q.id,
            response: answers[q.id] || ''
        }))

        try {
            const res = await submitPosttest(studentId, responses)
            setResult({
                score: res.score,
                total: res.total,
                percentage: res.percentage
            })
        } catch (err) {
            console.error(err)
        } finally {
            setSubmitting(false)
        }
    }

    if (loading) {
        return (
            <div className="app-container">
                <div className="app-header">
                    <span className="app-logo">🎓 Final Assessment</span>
                </div>
                <div className="loading"><div className="spinner"></div></div>
            </div>
        )
    }

    if (result) {
        return (
            <div className="app-container">
                <div className="app-header">
                    <span className="app-logo">🎓 Results</span>
                </div>
                <div className="app-main">
                    <div className="card fade-in" style={{ textAlign: 'center', maxWidth: '500px', margin: '0 auto' }}>
                        <h1 style={{ fontSize: '3rem', marginBottom: 'var(--space-md)' }}>
                            {result.percentage >= 80 ? '🏆' : result.percentage >= 60 ? '👍' : '💪'}
                        </h1>
                        <h2>Posttest Complete!</h2>
                        <div className="mastery-score" style={{ fontSize: '4rem', margin: 'var(--space-lg) 0' }}>
                            {result.percentage.toFixed(0)}%
                        </div>
                        <p style={{ color: 'var(--text-secondary)' }}>
                            You got {result.score} out of {result.total} questions correct.
                        </p>

                        <div className={`alert ${result.percentage >= 80 ? 'alert-success' :
                                result.percentage >= 60 ? 'alert-warning' : 'alert-info'
                            }`} style={{ marginTop: 'var(--space-lg)' }}>
                            {result.percentage >= 80
                                ? 'Excellent work! You have demonstrated strong understanding.'
                                : result.percentage >= 60
                                    ? 'Good progress! Keep practicing to strengthen your skills.'
                                    : 'Keep learning! Review the concepts and try again.'}
                        </div>

                        <div style={{ display: 'flex', gap: 'var(--space-md)', justifyContent: 'center', marginTop: 'var(--space-xl)' }}>
                            <button className="btn btn-secondary" onClick={() => navigate('/progress')}>
                                View Progress
                            </button>
                            <button className="btn btn-primary" onClick={() => navigate('/learn')}>
                                Continue Learning
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    if (questions.length === 0) {
        return (
            <div className="app-container">
                <div className="app-header">
                    <span className="app-logo">🎓 Final Assessment</span>
                </div>
                <div className="app-main">
                    <div className="card">
                        <p>No posttest questions available.</p>
                        <button className="btn btn-primary" onClick={() => navigate('/progress')}>
                            View Progress
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    const progress = (Object.keys(answers).length / questions.length) * 100

    return (
        <div className="app-container">
            <div className="app-header">
                <span className="app-logo">🎓 Final Assessment</span>
                <span style={{ color: 'var(--text-secondary)' }}>
                    Question {currentIndex + 1} of {questions.length}
                </span>
            </div>

            <div className="app-main">
                <div className="progress-bar" style={{ marginBottom: 'var(--space-lg)' }}>
                    <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                </div>

                <div className="card fade-in" key={currentQ.id}>
                    <div className="card-header">
                        <span className="badge badge-info">{currentQ.concept}</span>
                    </div>

                    <h3 style={{ marginBottom: 'var(--space-lg)' }}>{currentQ.prompt}</h3>

                    {currentQ.type === 'mcq' && currentQ.options && (
                        <div className="options-list">
                            {Object.entries(currentQ.options).map(([key, value]) => (
                                <div
                                    key={key}
                                    className={`option-item ${answers[currentQ.id] === key ? 'selected' : ''}`}
                                    onClick={() => setAnswers({ ...answers, [currentQ.id]: key })}
                                >
                                    <span className="option-key">{key}</span>
                                    <span>{value}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {currentQ.type === 'coding' && (
                        <div className="code-editor">
                            <textarea
                                value={answers[currentQ.id] || currentQ.starter_code || ''}
                                onChange={(e) => setAnswers({ ...answers, [currentQ.id]: e.target.value })}
                                placeholder="Write your code here..."
                            />
                        </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-lg)' }}>
                        <button
                            className="btn btn-secondary"
                            onClick={() => setCurrentIndex(i => i - 1)}
                            disabled={currentIndex === 0}
                        >
                            ← Previous
                        </button>

                        {currentIndex < questions.length - 1 ? (
                            <button className="btn btn-primary" onClick={() => setCurrentIndex(i => i + 1)}>
                                Next →
                            </button>
                        ) : (
                            <button
                                className="btn btn-success"
                                onClick={handleSubmit}
                                disabled={submitting}
                            >
                                {submitting ? 'Submitting...' : 'Submit Assessment'}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
