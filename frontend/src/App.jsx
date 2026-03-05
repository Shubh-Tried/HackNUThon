import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Monitoring from './pages/Monitoring'
import InverterDetail from './pages/InverterDetail'
import Alerts from './pages/Alerts'

export default function App() {
    return (
        <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-6 lg:p-8">
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/monitoring" element={<Monitoring />} />
                    <Route path="/inverter/:id" element={<InverterDetail />} />
                    <Route path="/alerts" element={<Alerts />} />
                </Routes>
            </main>
        </div>
    )
}
