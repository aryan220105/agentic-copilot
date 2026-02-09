import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import Login from './pages/Login'
import Pretest from './pages/Pretest'
import Learn from './pages/Learn'
import Progress from './pages/Progress'
import Posttest from './pages/Posttest'
import InstructorLogin from './pages/InstructorLogin'
import Dashboard from './pages/Dashboard'
import StudentDetail from './pages/StudentDetail'

interface User {
    id: number
    username: string
    role: 'student' | 'instructor'
}

function App() {
    const [user, setUser] = useState<User | null>(null)

    const handleLogin = (userData: User) => {
        setUser(userData)
    }

    const handleLogout = () => {
        setUser(null)
    }

    return (
        <BrowserRouter>
            <Routes>
                {/* Student Routes */}
                <Route path="/login" element={<Login onLogin={handleLogin} />} />
                <Route
                    path="/pretest"
                    element={user ? <Pretest studentId={user.id} /> : <Navigate to="/login" />}
                />
                <Route
                    path="/learn"
                    element={user ? <Learn studentId={user.id} /> : <Navigate to="/login" />}
                />
                <Route
                    path="/progress"
                    element={user ? <Progress studentId={user.id} /> : <Navigate to="/login" />}
                />
                <Route
                    path="/posttest"
                    element={user ? <Posttest studentId={user.id} /> : <Navigate to="/login" />}
                />

                {/* Instructor Routes */}
                <Route path="/instructor/login" element={<InstructorLogin onLogin={handleLogin} />} />
                <Route
                    path="/instructor/dashboard"
                    element={user?.role === 'instructor' ? <Dashboard onLogout={handleLogout} /> : <Navigate to="/instructor/login" />}
                />
                <Route
                    path="/instructor/student/:id"
                    element={user?.role === 'instructor' ? <StudentDetail /> : <Navigate to="/instructor/login" />}
                />

                {/* Default */}
                <Route path="/" element={<Navigate to="/login" />} />
            </Routes>
        </BrowserRouter>
    )
}

export default App
