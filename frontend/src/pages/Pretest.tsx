import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPretest, submitPretest, Question } from '../services/api'

interface Props {
    studentId: number
}

export default function Pretest({ studentId }: Props) {
    const navigate = useNavigate()
    const [questions, setQuestions] = useState<Question[]>([])
    const [answers, setAnswers] = useState<Record<number, string>>({})
    const [currentIndex, setCurrentIndex] = useState(0)
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)

    useEffect(() => {
        getPretest().then(data => {
            setQuestions(data.questions || [])
            setLoading(false)
        })
    }, [])

    const currentQ = questions[currentIndex]

    const handleSelect = (option: string) => {
        setAnswers({ ...answers, [currentQ.id]: option })
    }

    const handleNext = () => {
        if (currentIndex < questions.length - 1) {
            setCurrentIndex(currentIndex + 1)
        }
    }

    const handlePrev = () => {
        if (currentIndex > 0) {
            setCurrentIndex(currentIndex - 1)
        }
    }

    const handleSubmit = async () => {
        setSubmitting(true)
        const responses = questions.map(q => ({
            question_id: q.id,
            response: answers[q.id] || ''
        }))

        try {
            await submitPretest(studentId, responses)
            navigate('/learn')
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
                    <span className="app-logo">📝 Pretest Assessment</span>
                </div>
                <div className="loading"><div className="spinner"></div></div>
            </div>
        )
    }

    if (questions.length === 0) {
        return (
            <div className="app-container">
                <div className="app-header">
                    <span className="app-logo">📝 Pretest Assessment</span>
                </div>
                <div className="app-main">
                    <div className="card">
                        <p>No pretest questions available. Proceeding to learning...</p>
                        <button className="btn btn-primary" onClick={() => navigate('/learn')}>
                            Continue to Learning
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    const answered = Object.keys(answers).length
    const progress = (answered / questions.length) * 100

    return (
        <div className="app-container">
            <div className="app-header">
                <span className="app-logo">📝 Pretest Assessment</span>
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
                        <span className="badge badge-warning">{currentQ.type.toUpperCase()}</span>
                    </div>

                    <h3 style={{ marginBottom: 'var(--space-lg)' }}>{currentQ.prompt}</h3>

                    {currentQ.type === 'mcq' && currentQ.options && (
                        <div className="options-list">
                            {Object.entries(currentQ.options).map(([key, value]) => (
                                <div
                                    key={key}
                                    className={`option-item ${answers[currentQ.id] === key ? 'selected' : ''}`}
                                    onClick={() => handleSelect(key)}
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
                            onClick={handlePrev}
                            disabled={currentIndex === 0}
                        >
                            ← Previous
                        </button>

                        {currentIndex < questions.length - 1 ? (
                            <button className="btn btn-primary" onClick={handleNext}>
                                Next →
                            </button>
                        ) : (
                            <button
                                className="btn btn-success"
                                onClick={handleSubmit}
                                disabled={submitting || answered < questions.length}
                            >
                                {submitting ? 'Submitting...' : 'Submit Pretest'}
                            </button>
                        )}
                    </div>
                </div>

                <div style={{ marginTop: 'var(--space-md)', textAlign: 'center', color: 'var(--text-muted)' }}>
                    {answered} of {questions.length} answered
                </div>
            </div>
        </div>
    )
}
