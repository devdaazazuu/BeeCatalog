import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Menu, X, Package, FileText, Image, Settings, HelpCircle, Zap } from 'lucide-react';

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  const menuItems = [
    { to: '/organizador', icon: FileText, label: 'Organizador', description: 'Organize seus produtos' },
    { to: '/listagem', icon: Package, label: 'Criar Listing', description: 'Gere planilhas da Amazon' },
    { to: '/extrator', icon: Image, label: 'Extrair Imagens', description: 'Processe imagens de produtos' },
  ];

  if (!mounted) return null;

  return (
    <>
      {/* Mobile toggle button */}
      <button
        onClick={toggleSidebar}
        className="fixed top-6 left-6 z-[60] p-3 bg-gradient-to-r from-amber-400 to-amber-500 text-slate-900 rounded-xl md:hidden hover:from-amber-500 hover:to-amber-600 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105 backdrop-blur-sm border border-amber-300/20"
        aria-label="Toggle navigation menu"
      >
        <div className="relative">
          {isOpen ? <X size={20} /> : <Menu size={20} />}
        </div>
      </button>

      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[45] md:hidden transition-all duration-300"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar container */}
      <aside className={`
        !fixed top-0 left-0 h-full w-72 bg-gradient-to-b from-slate-900/95 via-slate-800/95 to-slate-900/95 
        backdrop-blur-xl border-r border-amber-500/20 z-[50] shadow-2xl
        transform transition-all duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        md:translate-x-0 md:static md:z-auto
        before:absolute before:inset-0 before:bg-gradient-to-b before:from-amber-500/5 before:to-transparent before:pointer-events-none
      `}>
        {/* Header */}
        <div className="p-6 border-b border-amber-500/20 relative">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-amber-500 rounded-xl flex items-center justify-center shadow-lg">
                <Zap className="w-7 h-7 text-slate-900" />
              </div>
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-r from-emerald-400 to-emerald-500 rounded-full animate-pulse" />
            </div>
            <div className="flex-1">
              <h1 className="text-xl font-bold text-white tracking-tight">BeeCatalog</h1>
              <p className="text-sm text-slate-400 font-medium">AI-Powered Platform</p>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        <div className="p-4 flex-1">
          <nav className="space-y-2">
            {menuItems.map((item, index) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `group flex items-center space-x-4 px-4 py-4 rounded-xl transition-all duration-300 relative overflow-hidden ${
                      isActive
                        ? 'bg-gradient-to-r from-amber-500/20 to-amber-400/20 text-amber-400 border border-amber-500/30 shadow-lg shadow-amber-500/10'
                        : 'text-slate-300 hover:bg-slate-800/50 hover:text-amber-400 hover:border-amber-500/20 border border-transparent hover:shadow-lg hover:shadow-amber-500/5'
                    }`
                  }
                  onClick={() => setIsOpen(false)}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex-shrink-0 relative z-10">
                    <Icon size={20} className="group-hover:scale-110 transition-all duration-300" />
                  </div>
                  <div className="flex-1 min-w-0 relative z-10">
                    <div className="font-semibold text-sm">{item.label}</div>
                    <div className="text-xs text-slate-500 group-hover:text-slate-400 transition-colors duration-300">
                      {item.description}
                    </div>
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-amber-500/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-amber-500/20 bg-gradient-to-t from-slate-900/50 to-transparent backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-xs font-medium text-slate-400">v1.0.0</span>
            </div>
            <div className="flex space-x-1">
              <button className="p-2 hover:text-amber-400 hover:bg-slate-800/50 rounded-lg transition-all duration-300 group">
                <Settings size={14} className="group-hover:rotate-90 transition-transform duration-300" />
              </button>
              <button className="p-2 hover:text-amber-400 hover:bg-slate-800/50 rounded-lg transition-all duration-300 group">
                <HelpCircle size={14} className="group-hover:scale-110 transition-transform duration-300" />
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;