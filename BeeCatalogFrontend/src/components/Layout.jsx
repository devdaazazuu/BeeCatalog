import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import NotificationContainer from './NotificationContainer';
import useNotification from '../hooks/useNotification';

const Layout = () => {
  const { notifications, removeNotification } = useNotification();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white relative overflow-hidden">
      {/* Background pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(251,191,36,0.05),transparent_70%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(251,191,36,0.02)_50%,transparent_75%)] pointer-events-none" />
      
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content area */}
      <main className="md:ml-72 transition-all duration-300 ease-in-out min-h-screen relative z-10">
        <div className="p-6 md:p-8 lg:p-10">
          <div className="max-w-7xl mx-auto">
            <div className="animate-fade-in">
              <Outlet context={{ notifications: { notifications, removeNotification } }} />
            </div>
          </div>
        </div>
      </main>
      
      {/* Notification system */}
      <NotificationContainer 
        notifications={notifications} 
        onRemove={removeNotification} 
      />
    </div>
  );
};

export default Layout;