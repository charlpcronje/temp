// src/components/layouts/Sidebar.tsx
import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileInput,
  Workflow,
  File,
  FileText,
  Users,
  Settings,
  Menu,
  X,
  Loader2 // Import Loader icon
} from 'lucide-react';
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { commandService } from '@/api/services'; // Import commandService
import { SessionStatus } from '@/types'; // Import SessionStatus

interface SidebarProps {
  isMobile: boolean;
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  isMobile,
  isSidebarOpen,
  toggleSidebar
}) => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [activeSessionStatus, setActiveSessionStatus] = useState<SessionStatus | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true); // State for loading status

  // Fetch active session status when the component mounts or auth state changes
  useEffect(() => {
    // Flag to prevent state updates if component unmounts during async operation
    let isMounted = true;

    const fetchStatus = async () => {
      // Reset loading state at the beginning
      setIsLoadingStatus(true);
      try {
        console.log("Sidebar: Fetching session status...");
        const status = await commandService.getStatus();
        if (isMounted) {
          console.log("Sidebar: Fetched status:", status);
          setActiveSessionStatus(status);
        }
      } catch (error) {
        console.error("Sidebar: Failed to fetch session status", error);
        if (isMounted) {
          setActiveSessionStatus(null); // Reset status on error
        }
      } finally {
        if (isMounted) {
          setIsLoadingStatus(false);
        }
      }
    };

    fetchStatus();

    // Cleanup function to set isMounted to false when component unmounts
    return () => {
      isMounted = false;
    };
  }, [user]); // Re-fetch if user changes (e.g., after login)

  // Determine the dynamic workflow link
  const getWorkflowLink = () => {
    if (isLoadingStatus) {
      // console.log("Sidebar: Workflow link loading...");
      return '#'; // Return a dummy link while loading
    }
    if (activeSessionStatus?.active_session && activeSessionStatus?.session_hash) {
      const link = `/app/workflow?session=${activeSessionStatus.session_hash}`;
      // console.log("Sidebar: Generating active workflow link:", link);
      return link;
    }
    // console.log("Sidebar: Generating upload workflow link.");
    return '/app/workflow/upload'; // Default to upload if no active session
  };

  const navItems = [
    { name: 'Dashboard', path: '/app/dashboard', icon: LayoutDashboard },
    { name: 'Sessions', path: '/app/sessions', icon: FileInput },
    // Use the dynamic link function for Workflow
    { name: 'Workflow', getPath: getWorkflowLink, icon: Workflow },
    { name: 'Logs', path: '/app/logs', icon: FileText },
    ...(isAdmin ? [{ name: 'Users', path: '/app/users', icon: Users }] : []),
    { name: 'Settings', path: '/app/settings', icon: Settings },
  ];

  // Determine the correct class for the sidebar container based on mobile/open state
  const sidebarContainerClasses = cn(
    "fixed inset-y-0 left-0 z-50 w-64 bg-background border-r transition-transform duration-300 ease-in-out print:hidden", // Added print:hidden
    isMobile ? // Mobile specific logic
      (isSidebarOpen ? "translate-x-0" : "-translate-x-full") :
      "translate-x-0" // Always visible and in place on desktop
  );


  return (
    <aside // Changed div to aside for semantics
      className={sidebarContainerClasses}
      aria-label="Main Navigation Sidebar"
    >
      <div className="flex h-14 items-center border-b px-4">
        {/* Added Link to Dashboard on title */}
        <NavLink to="/app/dashboard" className="flex items-center gap-2 font-semibold">
           {/* Optional: Add an icon here */}
           <span className="text-lg">DocTypeGen</span>
        </NavLink>
        {isMobile && (
          <Button
            variant="ghost"
            size="icon"
            className="ml-auto h-8 w-8" // Slightly smaller close button
            onClick={toggleSidebar}
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
      <ScrollArea className="h-[calc(100vh-3.5rem)]">
        <nav className="grid items-start px-4 text-sm font-medium">
            {navItems.map((item) => {
              // Determine path dynamically or statically
              const path = typeof item.getPath === 'function' ? item.getPath() : item.path;
              // Disable workflow link while loading status or if path is '#'
              const isDisabled = (item.name === 'Workflow' && isLoadingStatus); // Simplified: only disable while loading

              return (
                <NavLink
                  key={item.name} // Use name as key since path can change
                  to={isDisabled ? '#' : path || '#'} // If disabled, link to '#', otherwise use calculated path or fallback
                  end={item.path === '/app/dashboard'} // Use static path for 'end' prop if it exists
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 transition-all hover:text-primary",
                       // Style active link differently only if not disabled
                      isActive && !isDisabled ? "bg-muted text-primary" : "text-muted-foreground",
                      // Apply disabled styles
                      isDisabled ? "opacity-50 cursor-not-allowed" : ""
                    )
                  }
                  onClick={(e) => {
                      if (isDisabled) {
                          e.preventDefault(); // Prevent navigation if disabled
                          return;
                      }
                      // Close sidebar on mobile click ONLY if it's currently open
                      if (isMobile && isSidebarOpen) toggleSidebar();
                  }}
                  // Add aria-disabled for accessibility
                  aria-disabled={isDisabled}
                  // Prevent click events entirely if disabled
                  style={{ pointerEvents: isDisabled ? 'none' : 'auto' }}
                  // Add title for disabled state
                  title={isDisabled && item.name === 'Workflow' ? "Loading session status..." : undefined}
                >
                  {/* Show spinner for workflow item while loading */}
                  {item.name === 'Workflow' && isLoadingStatus ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <item.icon className="h-4 w-4" />
                  )}
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
        </nav>
      </ScrollArea>
    </aside>
  );
};

export default Sidebar;