import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Package, Image as ImageIcon, PanelLeft, FileText } from 'lucide-react';
import BeeLogo from '../assets/bee-logo.svg';

function Sidebar({ isRetracted, toggleSidebar }) {
  const activeLinkStyle = {
    color: '#FFBB00',
    fontWeight: 'bold',
  };

  return (
    <>
      <button
        onClick={toggleSidebar}
        className={`fixed top-5 z-20 p-2 rounded-full text-white bg-yellow-500/20 hover:bg-yellow-500/40 transition-all duration-300 ${isRetracted ? 'left-4' : 'left-[14.5rem]'}`}
        aria-label="Toggle Sidebar"
      >
        <PanelLeft size={20} />
      </button>
      <aside className={`fixed top-0 left-0 h-full w-64 bg-gray-900/50 backdrop-blur-lg border-r border-yellow-500/20 transition-all duration-300 ${isRetracted ? '-ml-64' : 'ml-0'}`}>
        <div className="flex items-center justify-center h-20 border-b border-yellow-500/20">
          <img src={BeeLogo} alt="BeeCatalog Logo" className="h-10 w-10 mr-2 filter drop-shadow-[0_0_8px_rgba(240,210,60,0.5)]"/>
          <h1 className="text-2xl font-bold text-yellow-400">BeeCatalog</h1>
        </div>
        <nav className="p-4">
          <h2 className="px-4 mb-2 text-xs font-semibold tracking-wider text-gray-500 uppercase">Menu Principal</h2>
          <ul>
            <li>
              <NavLink
                to="/organizador"
                className="flex items-center px-4 py-3 text-gray-300 rounded-lg hover:bg-yellow-500/10 hover:text-yellow-400 transition-colors"
                style={({ isActive }) => isActive ? activeLinkStyle : undefined}
              >
                <FileText size={18} className="mr-3" />
                <span>Organizador</span>
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/listagem"
                className="flex items-center px-4 py-3 text-gray-300 rounded-lg hover:bg-yellow-500/10 hover:text-yellow-400 transition-colors"
                style={({ isActive }) => isActive ? activeLinkStyle : undefined}
              >
                <Package size={18} className="mr-3" />
                <span>Criar Listing</span>
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/extrator"
                className="flex items-center px-4 py-3 text-gray-300 rounded-lg hover:bg-yellow-500/10 hover:text-yellow-400 transition-colors"
                style={({ isActive }) => isActive ? activeLinkStyle : undefined}
              >
                <ImageIcon size={18} className="mr-3" />
                <span>Extrair Imagens</span>
              </NavLink>
            </li>
          </ul>
        </nav>
      </aside>
    </>
  );
}

export default Sidebar;