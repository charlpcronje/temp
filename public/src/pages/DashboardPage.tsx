// src/pages/DashboardPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Plus, FileInput, Workflow, FileText, File, ArrowRight } from 'lucide-react';
import { sessionService, commandService } from "@/api/services";
// Use the correct Session type alias if LogDirectory doesn't fit perfectly
import { LogDirectory as Session, SessionStatus } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/contexts/AuthContext";
import { Spinner } from "@/components/ui/spinner";
import ErrorWithHelper from "@/components/ui/ErrorWithHelper"; // Assuming this component exists
import { Badge } from '@/components/ui/badge'; // Import Badge

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<SessionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch sessions and active session on mount
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Get active session status first
        const statusResponse = await commandService.getStatus();
        setActiveSession(statusResponse); // <-- Set active session state here

        // Get all sessions (logs)
        const logResponse = await sessionService.getLogs();
        // Map LogDirectory to Session if types differ slightly, otherwise use directly
        setSessions(logResponse as Session[]); // Adjust type casting if necessary
      } catch (err: any) { // Added type annotation for err
        console.error('Error fetching dashboard data:', err);
        setError(err.message || 'Failed to load dashboard data. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []); // Dependency array is empty, runs once on mount

  // --- *** CRITICAL FIX AREA *** ---
  // Determine the correct workflow link *dynamically* based on the fetched activeSession state
  // Ensure this uses the 'activeSession' state variable updated by useEffect
  const getWorkflowLink = () => {
    if (activeSession && activeSession.active_session && activeSession.session_hash) {
      return `/app/workflow?session=${activeSession.session_hash}`;
    }
    return '/app/workflow/upload'; // Default to upload if no active session
  };
  // --- *** END CRITICAL FIX AREA *** ---

  // Cards to display in the dashboard
  const dashboardCards = [
    {
      title: 'Upload Document',
      description: 'Import a CSV or Excel file to start processing',
      icon: FileInput,
      route: '/app/workflow/upload', // Always links to upload
      footer: 'Start by uploading a file',
    },
    {
      title: 'Processing Workflow',
      description: activeSession?.active_session ? 'Continue your active session' : 'Validate, map, and generate documents',
      icon: Workflow,
      // Use the function to get the dynamic link *at render time*
      getRoute: getWorkflowLink,
      footer: activeSession?.active_session ? 'Continue processing' : 'Start a new workflow',
    },
    {
      title: 'View Sessions',
      description: 'Browse all processing sessions',
      icon: File,
      route: '/app/sessions',
      footer: 'Manage existing sessions',
    },
    {
      title: 'Logs & Reports',
      description: 'View logs and generated reports',
      icon: FileText,
      route: '/app/logs',
      footer: 'Access logs and reports',
    },
  ];

  // Recent sessions to display (limit to 5)
  // Make sure 'date' property exists on the Session type
  const recentSessions = sessions
    .sort((a, b) => new Date(b.date || 0).getTime() - new Date(a.date || 0).getTime()) // Handle potential missing date
    .slice(0, 5);


  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <Link to="/app/workflow/upload">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Session
          </Button>
        </Link>
      </div>

      {error && (
        <ErrorWithHelper message={error} helperKey="failedDashboardData" />
      )}

      {/* Active Session card */}
      {activeSession && activeSession.active_session && (
        <Card className="border-primary"> {/* Added border for emphasis */}
          <CardHeader>
            <CardTitle>Active Session</CardTitle>
            <CardDescription>
              You have an active processing session.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              Session Hash: <span className="font-mono">{activeSession.session_hash}</span>
            </p>
             {activeSession.last_operation && (
                 <p className="text-sm mt-1">
                    Last Operation: <Badge variant="outline">{activeSession.last_operation}</Badge>
                 </p>
             )}
             {activeSession.document_type && (
                 <p className="text-sm mt-1">
                    Document Type: <Badge variant="secondary">{activeSession.document_type}</Badge>
                 </p>
             )}
          </CardContent>
          <CardFooter>
            {/* This link correctly includes the session hash */}
            <Link to={`/app/workflow?session=${activeSession.session_hash}`}>
              <Button className="w-full sm:w-auto">
                Continue Session
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardFooter>
        </Card>
      )}

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="recent">Recent Sessions</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Render cards using the dynamic route function */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {dashboardCards.map((card) => {
              // Determine route: use getRoute if available, otherwise use static route
              const route = typeof card.getRoute === 'function' ? card.getRoute() : card.route;
              return (
                <Card key={card.title} className="overflow-hidden transition-shadow hover:shadow-md">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-lg font-medium">
                      {card.title}
                    </CardTitle>
                    <card.icon className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground h-10"> {/* Fixed height for description */}
                      {card.description}
                    </p>
                  </CardContent>
                  <CardFooter className="pt-0">
                    <Link to={route || '#'} className="w-full"> {/* Ensure Link wraps Button and provide fallback */}
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        // Optional: Disable the workflow button if no active session AND it's not linking to upload
                        disabled={card.title === 'Processing Workflow' && route === '/app/workflow/upload' && !activeSession?.active_session && !!activeSession} // Example condition
                      >
                        {card.footer}
                      </Button>
                    </Link>
                  </CardFooter>
                </Card>
              );
            })}
          </div>

          {/* Admin Controls remain the same */}
          {user?.role === 'admin' && (
             <Card>
              <CardHeader>
                <CardTitle>Admin Controls</CardTitle>
                <CardDescription>
                  Administrative functions and settings
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2">
                <Link to="/app/users" className="w-full">
                  <Button
                    variant="outline" className="w-full"
                  >
                    User Management
                  </Button>
                </Link>
                <Link to="/app/settings" className="w-full">
                  <Button
                    variant="outline" className="w-full"
                  >
                    System Settings
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Recent Sessions Tab remains the same */}
        <TabsContent value="recent">
          <Card>
            <CardHeader>
              <CardTitle>Recent Sessions</CardTitle>
              <CardDescription>
                Your recent document processing sessions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {recentSessions.length > 0 ? (
                <div className="space-y-4">
                  {recentSessions.map((session) => (
                    <div
                      key={session.hash}
                      className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50 transition-colors"
                    >
                      <div>
                        <p className="font-medium">
                          {session.name || `Session ${session.hash.substring(0, 8)}`}
                        </p>
                        <p className="text-sm text-muted-foreground">
                           {session.date ? new Date(session.date).toLocaleString() : 'Date unknown'}
                        </p>
                        {session.last_operation && (
                            <Badge variant="secondary" className="mt-1">{session.last_operation}</Badge>
                        )}
                      </div>
                      {/* Link to session details (logs page for now) */}
                      <Link to={`/app/sessions/${session.hash}`}>
                        <Button
                          variant="ghost"
                        >
                          View Details
                        </Button>
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No recent sessions found. Start by uploading a new file.
                </p>
              )}
            </CardContent>
            <CardFooter>
              <Link to="/app/sessions" className="w-full">
                <Button
                  variant="outline"
                  className="w-full"
                >
                  View All Sessions
                </Button>
              </Link>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DashboardPage;