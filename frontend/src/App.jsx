import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './layouts/Layout';
import Dashboard from './pages/Dashboard';
import RiskCases from './pages/RiskCases';
import Investigation from './pages/Investigation';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="cases" element={<RiskCases />} />
          <Route path="cases/:caseId" element={<Investigation />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
