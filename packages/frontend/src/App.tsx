import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'sonner'
import HomePage from '@/pages/HomePage'
import ChatbotsPage from '@/pages/ChatbotsPage'
import MetricsPage from '@/pages/MetricsPage'
import Layout from '@/layouts/Layout'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/chatbots" element={<ChatbotsPage />} />
          <Route path="/metrics" element={<MetricsPage />} />
        </Routes>
      </Layout>
      <Toaster 
        position="top-right" 
        theme="dark"
        richColors
      />
    </Router>
  )
}

export default App