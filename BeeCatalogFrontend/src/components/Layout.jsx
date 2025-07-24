import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

function Layout() {
    return (
        <div className="bg-gray-900 bg-radial-beams min-h-screen text-gray-300 font-sans">
            <Sidebar />
            <main className="ml-64 p-8 transition-all duration-300">
                <Outlet />
            </main>
        </div>
    );
}

export default Layout;