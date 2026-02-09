const API_BASE = '/api'

export interface LoginResponse {
    student_id: number
    username: string
    baseline_level: string
    is_new: boolean
    pretest_completed: boolean
}

export interface Question {
    id: number
    type: 'mcq' | 'coding'
    concept: string
    prompt: string
    options?: Record<string, string>
    starter_code?: string
}

export interface NextContent {
    action: string
    concept: string
    reason: string
    content?: {
        bullets?: string[]
        worked_example?: string
        pitfall?: string
        quick_check?: string
    }
    question?: {
        type: string
        prompt: string
        options?: Record<string, string>
        difficulty?: string
    }
}

export interface ProgressData {
    current_concept: string
    mastery_scores: Record<string, number>
    overall_mastery: number
    misconceptions_history: string[]
    concepts_completed: string[]
}

export interface DashboardData {
    total_students: number
    struggling_students: number[]
    concept_heatmap: Record<string, Record<string, number>>
    misconception_clusters: Array<{
        misconception: string
        student_count: number
        severity: string
        recommended_intervention: string
    }>
    priority_students: Array<{
        student_id: number
        username: string
        priority_score: number
        needs_attention: boolean
    }>
    intervention_suggestions: string[]
}

// ─────────────────────────────────────────────────────────────
// Auth
// ─────────────────────────────────────────────────────────────

export async function login(
    username: string,
    password: string,
    baseline: string
): Promise<LoginResponse> {
    const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, baseline_level: baseline })
    })
    if (!res.ok) throw new Error('Login failed')
    return res.json()
}

export async function instructorLogin(
    username: string,
    password: string
): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/auth/instructor/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    if (!res.ok) throw new Error('Login failed')
    return res.json()
}

// ─────────────────────────────────────────────────────────────
// Pretest/Posttest
// ─────────────────────────────────────────────────────────────

export async function getPretest(): Promise<{ questions: Question[] }> {
    const res = await fetch(`${API_BASE}/pretest`)
    return res.json()
}

export async function submitPretest(
    studentId: number,
    responses: Array<{ question_id: number; response: string }>
): Promise<any> {
    const res = await fetch(`${API_BASE}/pretest/submit?student_id=${studentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(responses)
    })
    return res.json()
}

export async function getPosttest(): Promise<{ questions: Question[] }> {
    const res = await fetch(`${API_BASE}/posttest`)
    return res.json()
}

export async function submitPosttest(
    studentId: number,
    responses: Array<{ question_id: number; response: string }>
): Promise<any> {
    const res = await fetch(`${API_BASE}/posttest/submit?student_id=${studentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(responses)
    })
    return res.json()
}

// ─────────────────────────────────────────────────────────────
// Learning
// ─────────────────────────────────────────────────────────────

export async function getNextContent(studentId: number): Promise<NextContent> {
    const res = await fetch(`${API_BASE}/learn/${studentId}`)
    return res.json()
}

export async function submitAttempt(
    studentId: number,
    questionId: number,
    response: string
): Promise<{
    attempt_id: number
    is_correct: boolean
    misconceptions: string[]
    feedback: string
}> {
    const res = await fetch(`${API_BASE}/attempt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            student_id: studentId,
            question_id: questionId,
            response
        })
    })
    return res.json()
}

export async function getProgress(studentId: number): Promise<ProgressData> {
    const res = await fetch(`${API_BASE}/progress/${studentId}`)
    return res.json()
}

// ─────────────────────────────────────────────────────────────
// Instructor
// ─────────────────────────────────────────────────────────────

export async function getDashboard(): Promise<DashboardData> {
    const res = await fetch(`${API_BASE}/instructor/dashboard`)
    return res.json()
}

export async function getStudentDetail(studentId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/instructor/students/${studentId}`)
    return res.json()
}

export async function getStudentsList(page = 1): Promise<any> {
    const res = await fetch(`${API_BASE}/instructor/students?page=${page}`)
    return res.json()
}

export async function exportAttempts(): Promise<Blob> {
    const res = await fetch(`${API_BASE}/instructor/export/attempts`)
    return res.blob()
}

export async function exportMetrics(): Promise<any> {
    const res = await fetch(`${API_BASE}/instructor/export/metrics`)
    return res.json()
}
