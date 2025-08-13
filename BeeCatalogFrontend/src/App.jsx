import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import CriarListing from './pages/CriarListing';
import ExtrairImagens from './pages/ExtrairImagens';
import Organizador from './pages/Organizador';
import Configuracoes from './pages/Configuracoes';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<CriarListing />} />
        <Route path="listagem" element={<CriarListing />} />
        <Route path="organizador" element={<Organizador />} />
        <Route path="extrator" element={<ExtrairImagens />} />
        <Route path="configuracoes" element={<Configuracoes />} />
      </Route>
    </Routes>
  );
}

export default App;