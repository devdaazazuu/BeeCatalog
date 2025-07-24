import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import CriarListing from './pages/CriarListing';
import ExtrairImagens from './pages/ExtrairImagens';
import Organizador from './pages/Organizador';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<CriarListing />} />
        <Route path="listagem" element={<CriarListing />} />
        <Route path="organizador" element={<Organizador />} />
        <Route path="extrator" element={<ExtrairImagens />} />
      </Route>
    </Routes>
  );
}

export default App;