// src/pages/LogsPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FileText, Search, ExternalLink, ArrowLeft, File, Download, FileUp } from 'lucide-react';
import { sessionService } from "@/api/services";
import { LogDirectory, LogInfo } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { Badge } from "@/components/ui/badge";

const LogsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [logs, setLogs] = useState<LogDirectory[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogDirectory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch logs on mount
  useEffect(() => {
    fetchLogs();
  }, []);

  // Filter logs when search term changes
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredLogs(logs);
    } else {
      const term = searchTerm.toLowerCase();
      const filtered = logs.filter(
        log =>
          (log.name && log.name.toLowerCase().includes(term)) ||
          log.hash.toLowerCase().includes(term)
      );
      setFilteredLogs(filtered);
    }
  }, [searchTerm, logs]);

  const fetchLogs = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await sessionService.getLogs();
      setLogs(response);
      setFilteredLogs(response);
    } catch (err) {
      console.error('Error fetching logs:', err);
      setError('Failed to load logs. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleViewLogs = (log: LogDirectory) => {
    navigate(`/app/logs/${log.hash}`);
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
        <h1 className="text-3xl font-bold tracking-tight">Logs</h1>
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
          placeholder="Search logs..."
          value={searchTerm}
          onChange={handleSearch}
          className="w-full md:w-[300px]"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Logs</CardTitle>
          <CardDescription>
            View logs for all document processing sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredLogs.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Hash</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Files</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLogs.map((log) => (
                    <TableRow key={log.hash}>
                      <TableCell className="font-medium">
                        {log.name || `Session ${log.hash.substring(0, 8)}`}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {log.hash.substring(0, 12)}...
                      </TableCell>
                      <TableCell>{formatDate(log.date)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{log.file_count}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewLogs(log)}
                        >
                          <FileText className="mr-2 h-4 w-4" />
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="font-medium text-lg mb-1">No logs found</h3>
              <p className="text-muted-foreground mb-4">
                {searchTerm ? 'No logs match your search' : 'No processing sessions have been completed yet'}
              </p>
              {searchTerm ? (
                <Button variant="outline" onClick={() => setSearchTerm('')}>
                  Clear Search
                </Button>
              ) : (
                <Button onClick={() => navigate('/app/workflow/upload')}>
                  Start New Session
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const LogDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [logInfo, setLogInfo] = useState<LogInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('html');

  // Fetch log details on mount
  useEffect(() => {
    if (id) {
      fetchLogDetails(id);
    }
  }, [id]);

  const fetchLogDetails = async (hash: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await sessionService.getLogInfo(hash);
      setLogInfo(response);
    } catch (err) {
      console.error('Error fetching log details:', err);
      setError('Failed to load log details. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToList = () => {
    navigate('/app/logs');
  };

  const viewFile = (fileType: string, fileName: string) => {
    // Construct URL to file
    const baseUrl = window.location.origin;
    let path;

    if (fileType === 'log') {
      path = `${baseUrl}/static/${id}/www/${fileName}`;
    } else {
      path = `${baseUrl}/static/${id}/${fileType}/${fileName}`;
    }

    window.open(path, '_blank');
  };

  const downloadFile = (fileType: string, fileName: string) => {
    // Construct URL and trigger download
    const baseUrl = window.location.origin;
    let path;

    if (fileType === 'log') {
      path = `${baseUrl}/static/${id}/www/${fileName}`;
    } else {
      path = `${baseUrl}/static/${id}/${fileType}/${fileName}`;
    }

    const a = document.createElement('a');
    a.href = path;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const continueSession = async () => {
    try {
      // First activate the session
      const result = await sessionService.activateSession(id!);
      if (result.success) {
        // Then navigate to the workflow page
        // The backend has already updated status.json with the correct last_operation
        navigate(`/app/workflow`);

        // Log the last operation for debugging
        console.log(`Session activated with last operation: ${result.result?.last_operation}`);
      } else {
        // Show error if activation failed
        setError(result.error || 'Failed to activate session');
      }
    } catch (err) {
      console.error('Error activating session:', err);
      setError('Failed to activate session. Please try again.');
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

  if (error || !logInfo) {
    return (
      <div className="space-y-6">
        <Button variant="outline" onClick={handleBackToList}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Logs
        </Button>

        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error || 'Log not found'}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="outline" onClick={handleBackToList}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Logs
        </Button>

        <Button onClick={continueSession}>
          <FileUp className="mr-2 h-4 w-4" />
          Continue Session
        </Button>
      </div>

      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {logInfo.name || `Session ${logInfo.hash.substring(0, 8)}`}
        </h1>
        <p className="text-muted-foreground">
          {formatDate(logInfo.date)} • Hash: <span className="font-mono">{logInfo.hash.substring(0, 16)}...</span>
        </p>
      </div>

      <Tabs defaultValue={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="html">
            HTML Files ({logInfo.html_files?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="pdf">
            PDF Files ({logInfo.pdf_files?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="logs">
            Log Files ({logInfo.log_files?.length || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="html" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>HTML Files</CardTitle>
              <CardDescription>
                Generated HTML documents from this session
              </CardDescription>
            </CardHeader>
            <CardContent>
              {(logInfo.html_files?.length || 0) > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(logInfo.html_files || []).map((fileName, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell className="font-mono text-xs">{fileName}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end space-x-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => viewFile('html', fileName)}
                              >
                                <ExternalLink className="h-4 w-4 mr-1" />
                                View
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => downloadFile('html', fileName)}
                              >
                                <Download className="h-4 w-4 mr-1" />
                                Download
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <File className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-medium mb-1">No HTML files</h3>
                  <p className="text-muted-foreground">
                    This session doesn't have any HTML files.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pdf" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>PDF Files</CardTitle>
              <CardDescription>
                Generated PDF documents from this session
              </CardDescription>
            </CardHeader>
            <CardContent>
              {(logInfo.pdf_files?.length || 0) > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(logInfo.pdf_files || []).map((fileName, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell className="font-mono text-xs">{fileName}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end space-x-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => viewFile('pdf', fileName)}
                              >
                                <ExternalLink className="h-4 w-4 mr-1" />
                                View
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => downloadFile('pdf', fileName)}
                              >
                                <Download className="h-4 w-4 mr-1" />
                                Download
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <File className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-medium mb-1">No PDF files</h3>
                  <p className="text-muted-foreground">
                    This session doesn't have any PDF files.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Log Files</CardTitle>
              <CardDescription>
                Processing logs and reports from this session
              </CardDescription>
            </CardHeader>
            <CardContent>
              {(logInfo.log_files?.length || 0) > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(logInfo.log_files || []).map((fileName, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell className="font-mono text-xs">{fileName}</TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => viewFile('log', fileName)}
                            >
                              <ExternalLink className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-medium mb-1">No log files</h3>
                  <p className="text-muted-foreground">
                    This session doesn't have any log files.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Export both components
export { LogsListPage, LogDetailPage };