import React, { lazy, Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Layout from './components/Layout'
import './theme/variables.css'
import './theme/base.css'
import './theme/components.css'

const Landing = lazy(() => import('./pages/Landing'))
const Agents = lazy(() => import('./pages/Agents'))
const AgentDetail = lazy(() => import('./pages/AgentDetail'))
const Services = lazy(() => import('./pages/Services'))
const ServiceDetail = lazy(() => import('./pages/ServiceDetail'))
const Docs = lazy(() => import('./pages/Docs'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const DashOverview = lazy(() => import('./pages/dashboard/Overview'))
const DashJobs = lazy(() => import('./pages/dashboard/Jobs'))
const DashMyServices = lazy(() => import('./pages/dashboard/MyServices'))
const DashNegotiations = lazy(() => import('./pages/dashboard/Negotiations'))
const DashTransactions = lazy(() => import('./pages/dashboard/Transactions'))

function Loading() {
  return <div className="d7-loading">Loading...</div>
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Landing />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/agents/:id" element={<AgentDetail />} />
              <Route path="/services" element={<Services />} />
              <Route path="/services/:id" element={<ServiceDetail />} />
              <Route path="/docs" element={<Docs />} />
              <Route path="/dashboard" element={<Dashboard />}>
                <Route index element={<DashOverview />} />
                <Route path="jobs" element={<DashJobs />} />
                <Route path="services" element={<DashMyServices />} />
                <Route path="negotiations" element={<DashNegotiations />} />
                <Route path="transactions" element={<DashTransactions />} />
              </Route>
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>
)
