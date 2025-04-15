// src/components/layouts/DashboardLayout.tsx
import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { cn } from "@/lib/utils";
import Header from './Header';
import Sidebar from './Sidebar';

const DashboardLayout: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) {
        setIsSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Header toggleSidebar={toggleSidebar} />
      
      <div className="flex">
        <Sidebar
          isMobile={isMobile}
          isSidebarOpen={isSidebarOpen}
          toggleSidebar={toggleSidebar}
        />
        
        <main
          className={cn(
            "flex-1 p-4 sm:p-6 md:p-8",
            !isMobile && "md:ml-64"
          )}
        >
          <Outlet />
        </main>
      </div>
      
      {/* Backdrop for mobile sidebar */}
      {isMobile && isSidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm"
          onClick={toggleSidebar}
        />
      )}
    </div>
  );
};

export default DashboardLayout;