import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Homepage from '@pages/Homepage';
import ChatbotCategory from '@pages/ChatbotCategory';
import AnimatedBackground from '@components/AnimatedBackground';
import '@styles/App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <AnimatedBackground />
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/chatbots" element={<ChatbotCategory />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App; 