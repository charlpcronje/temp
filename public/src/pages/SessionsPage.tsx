// src/pages/SessionsPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, MoreHorizontal, Edit, FileText, FileUp } from 'lucide-react';
import { sessionService, commandService } from "@/api/services";
import { Session, SessionStatus } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";

const SessionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [filteredSessions, setFilteredSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeSession, setActiveSession] = useState<SessionStatus | null>(null);

  // For rename dialog
  const [isRenameDialogOpen, setIsRenameDialogOpen] = useState(false);
  const [sessionToRename, setSessionToRename] = useState<Session | null>(null);
  const [newName, setNewName] = useState('');

  // Fetch sessions and active session on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  // Filter sessions when search term changes
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredSessions(sessions);
    } else {
      const term = searchTerm.toLowerCase();
      const filtered = sessions.filter(
        session =>
          (session.name && session.name.toLowerCase().includes(term)) ||
          session.hash.toLowerCase().includes(term) ||
          (session.document_type && session.document_type.toLowerCase().includes(term))
      );
      setFilteredSessions(filtered);
    }
  }, [searchTerm, sessions]);

  const fetchSessions = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Get active session
      const statusResponse = await commandService.getStatus();
      setActiveSession(statusResponse);

      // Get all sessions
      const logResponse = await sessionService.getLogs();
      setSessions(logResponse);
      setFilteredSessions(logResponse);
    } catch (err) {
      console.error('Error fetching sessions:', err);
      setError('Failed to load sessions. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleNewSession = () => {
    navigate('/app/workflow/upload');
  };

  const handleOpenSession = (session: Session) => {
    navigate(`/app/workflow?session=${session.hash}`);
  };

  const handleViewLogs = (session: Session) => {
    navigate(`/app/logs/${session.hash}`);
  };

  const openRenameDialog = (session: Session) => {
    setSessionToRename(session);
    setNewName(session.name || '');
    setIsRenameDialogOpen(true);
  };

  const handleRename = async () => {
    if (!sessionToRename) return;

    try {
      await sessionService.renameLog(sessionToRename.hash, newName);

      // Update session in state
      setSessions(prevSessions =>
        prevSessions.map(session =>
          session.hash === sessionToRename.hash
            ? { ...session, name: newName }
            : session
        )
      );

      setIsRenameDialogOpen(false);
    } catch (err) {
      console.error('Error renaming session:', err);
      setError('Failed to rename session. Please try again.');
    }
  };

  // Function to format date
  const formatDate = (dateString: string) => {
    try {
      // Check if the date string is valid
      if (!dateString || isNaN(Date.parse(dateString))) {
        return 'Invalid date';
      }

      const date = new Date(dateString);
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'Invalid date';
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Sessions</h1>
        <Button onClick={handleNewSession}>
          <Plus className="mr-2 h-4 w-4" />
          New Session
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex items-center space-x-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search sessions..."
          value={searchTerm}
          onChange={handleSearch}
          className="w-full md:w-[300px]"
        />
      </div>

      {activeSession && activeSession.active_session && (
        <Card>
          <CardHeader>
            <CardTitle>Active Session</CardTitle>
            <CardDescription>
              You have an active processing session
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              Session Hash: <span className="font-mono">{activeSession.session_hash}</span>
            </p>
          </CardContent>
          <CardFooter>
            <Button
              onClick={() => navigate(`/app/workflow?session=${activeSession.session_hash}`)}
              className="w-full sm:w-auto"
            >
              Continue Processing
            </Button>
          </CardFooter>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>All Sessions</CardTitle>
          <CardDescription>
            Manage your document processing sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredSessions.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSessions.map((session) => (
                    <TableRow key={session.hash}>
                      <TableCell className="font-medium">
                        {session.name || `Session ${session.hash.substring(0, 8)}`}
                      </TableCell>
                      <TableCell>
                        {session.document_type ? (
                          <Badge variant="outline">{session.document_type}</Badge>
                        ) : (
                          <span className="text-muted-foreground">Unknown</span>
                        )}
                      </TableCell>
                      <TableCell>{formatDate(session.date)}</TableCell>
                      <TableCell>
                        {session.hash === activeSession?.session_hash ? (
                          <Badge>Active</Badge>
                        ) : (
                          <Badge variant="outline">{session.last_operation || 'Completed'}</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                              <span className="sr-only">Open menu</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => handleOpenSession(session)}>
                              <FileUp className="mr-2 h-4 w-4" />
                              Open in Workflow
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleViewLogs(session)}>
                              <FileText className="mr-2 h-4 w-4" />
                              View Logs
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => openRenameDialog(session)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Rename
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="font-medium text-lg mb-1">No sessions found</h3>
              <p className="text-muted-foreground mb-4">
                {searchTerm ? 'No sessions match your search' : 'You have not created any sessions yet'}
              </p>
              {searchTerm ? (
                <Button variant="outline" onClick={() => setSearchTerm('')}>
                  Clear Search
                </Button>
              ) : (
                <Button onClick={handleNewSession}>
                  Create New Session
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Rename dialog */}
      <Dialog open={isRenameDialogOpen} onOpenChange={setIsRenameDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Session</DialogTitle>
            <DialogDescription>
              Give this session a meaningful name for easier identification.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Label htmlFor="session-name" className="mb-2 block">
              Session Name
            </Label>
            <Input
              id="session-name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Enter session name"
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRenameDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleRename}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SessionsPage;