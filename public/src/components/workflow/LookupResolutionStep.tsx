// src/components/workflow/LookupResolutionStep.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { commandService } from '@/api/services';
import { LookupResolutionResult, CommandResponse, LookupException } from '@/types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { AlertCircle, CheckCircle, AlertTriangle, FileText, Play, Plus, RotateCw, Wrench } from 'lucide-react';
import DocumentsTable from '@/components/lookup/DocumentsTable';
import ExceptionsTable from '@/components/lookup/ExceptionsTable';
import ForCreationTable from '@/components/lookup/ForCreationTable';
import LookupExceptionResolver from '@/components/lookup/LookupExceptionResolver';

interface StatusCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color?: string;
}

const StatusCard: React.FC<StatusCardProps> = ({ title, value, icon, color = 'default' }) => {
  const colorClasses = {
    'default': 'bg-card',
    'green': 'bg-green-50 border-green-200 text-green-800',
    'amber': 'bg-amber-50 border-amber-200 text-amber-800',
    'blue': 'bg-blue-50 border-blue-200 text-blue-800',
    'red': 'bg-red-50 border-red-200 text-red-800',
  };

  return (
    <div className={`flex items-center p-4 border rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
      <div className="mr-4">{icon}</div>
      <div>
        <div className="text-sm font-medium">{title}</div>
        <div className="text-2xl font-bold">{value}</div>
      </div>
    </div>
  );
};

interface LookupResolutionStepProps {
  onComplete: (result: CommandResponse) => void;
}

const LookupResolutionStep: React.FC<LookupResolutionStepProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  
  const [isResolving, setIsResolving] = useState(false);
  const [isExceptionResolverOpen, setIsExceptionResolverOpen] = useState(false);
  const [selectedExceptionId, setSelectedExceptionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LookupResolutionResult | null>(null);
  
  const [stats, setStats] = useState({
    total: 0,
    resolved: 0,
    exceptions: 0,
    forCreation: 0
  });
  
  // Properly type the state variables with the imported LookupException interface
  const [allDocuments, setAllDocuments] = useState<LookupException[]>([]);
  const [resolvedDocuments, setResolvedDocuments] = useState<LookupException[]>([]);
  const [exceptions, setExceptions] = useState<LookupException[]>([]);
  const [forCreationDocuments, setForCreationDocuments] = useState<LookupException[]>([]);
  
  useEffect(() => {
    // Fetch initial status
    fetchLookupStatus();
  }, []);
  
  const fetchLookupStatus = async () => {
    try {
      const exceptionsData = await commandService.getLookupExceptions();
      setExceptions(exceptionsData.exceptions);
      
      setStats({
        total: exceptionsData.total,
        resolved: exceptionsData.resolved,
        exceptions: exceptionsData.pending,
        forCreation: exceptionsData.for_creation
      });
      
      // For now, we'll use the exceptions data to populate our tables
      // In a real implementation, we'd have separate endpoints for each document category
      setAllDocuments(exceptionsData.exceptions);
      
      const resolvedDocs = exceptionsData.exceptions.filter(
        (exc: LookupException) => exc.status === 'accepted' || exc.status === 'rejected'
      );
      setResolvedDocuments(resolvedDocs);
      
      const forCreationDocs = exceptionsData.exceptions.filter(
        (exc: LookupException) => exc.status === 'for_creation'
      );
      setForCreationDocuments(forCreationDocs);
      
    } catch (err) {
      console.error('Error fetching lookup status:', err);
      setError('Failed to load lookup status. Please try again.');
    }
  };
  
  const handleResolve = async () => {
    setIsResolving(true);
    setError(null);
    
    try {
      const result = await commandService.resolveLookups();
      setResult(result);
      
      if (result.status === 'success') {
        // Update our stats based on the result
        setStats({
          total: result.records_processed,
          resolved: result.successful_lookups,
          exceptions: result.exceptions,
          forCreation: result.for_creation
        });
        
        // Refresh the data
        await fetchLookupStatus();
      } else {
        setError(result.message);
      }
    } catch (err: any) {
      console.error('Error resolving lookups:', err);
      setError(err.message || 'Failed to resolve lookups. Please try again.');
    } finally {
      setIsResolving(false);
    }
  };
  
  const openExceptionResolver = () => {
    setSelectedExceptionId(null);
    setIsExceptionResolverOpen(true);
  };
  
  const openExceptionResolverWithId = (id: number) => {
    setSelectedExceptionId(id);
    setIsExceptionResolverOpen(true);
  };
  
  const handleExceptionResolved = async () => {
    // Refresh data after an exception is resolved
    await fetchLookupStatus();
  };
  
  const goBack = () => {
    navigate('/workflow/pdf');
  };
  
  const goNext = () => {
    // Only go to entity creation if there are entities to create
    if (stats.forCreation > 0) {
      navigate('/workflow/entity-creation');
    } else {
      navigate('/workflow/sync');
    }
    
    // Call onComplete with a success result
    onComplete({
      success: true,
      command: 'resolve_lookups',
      result: { status: 'success', message: 'Lookup resolution completed' }
    });
  };
  
  const canProceed = stats.exceptions === 0; // Can only proceed if all exceptions are resolved
  
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Lookup Resolution</CardTitle>
          <CardDescription>Match documents to external data sources</CardDescription>
        </CardHeader>
        
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {/* Status Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatusCard title="Total Documents" value={stats.total} icon={<FileText className="h-5 w-5" />} />
            <StatusCard 
              title="Resolved" 
              value={stats.resolved} 
              icon={<CheckCircle className="h-5 w-5 text-green-600" />} 
              color="green" 
            />
            <StatusCard 
              title="Exceptions" 
              value={stats.exceptions} 
              icon={<AlertTriangle className="h-5 w-5 text-amber-600" />} 
              color="amber" 
            />
            <StatusCard 
              title="For Creation" 
              value={stats.forCreation} 
              icon={<Plus className="h-5 w-5 text-blue-600" />} 
              color="blue" 
            />
          </div>
          
          {/* Actions Panel */}
          <div className="flex flex-wrap gap-4 mb-6">
            <Button 
              onClick={handleResolve} 
              disabled={isResolving || stats.total === 0}
            >
              {isResolving ? (
                <>
                  <Spinner className="mr-2 h-4 w-4" />
                  Resolving...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Resolve Lookups
                </>
              )}
            </Button>
            
            <Button 
              variant="outline" 
              onClick={fetchLookupStatus}
              disabled={isResolving}
            >
              <RotateCw className="mr-2 h-4 w-4" />
              Refresh Status
            </Button>
            
            {stats.exceptions > 0 && (
              <Button variant="outline" onClick={openExceptionResolver}>
                <Wrench className="mr-2 h-4 w-4" />
                Resolve Exceptions
              </Button>
            )}
          </div>
          
          {/* Results Tabs */}
          <Tabs defaultValue="all">
            <TabsList>
              <TabsTrigger value="all">All Documents ({stats.total})</TabsTrigger>
              <TabsTrigger value="resolved">Resolved ({stats.resolved})</TabsTrigger>
              <TabsTrigger value="exceptions">Exceptions ({stats.exceptions})</TabsTrigger>
              <TabsTrigger value="creation">For Creation ({stats.forCreation})</TabsTrigger>
            </TabsList>
            
            <TabsContent value="all">
              <DocumentsTable documents={allDocuments} />
            </TabsContent>
            
            <TabsContent value="resolved">
              <DocumentsTable documents={resolvedDocuments} />
            </TabsContent>
            
            <TabsContent value="exceptions">
              <ExceptionsTable 
                exceptions={exceptions} 
                onResolve={openExceptionResolverWithId} 
              />
            </TabsContent>
            
            <TabsContent value="creation">
              <ForCreationTable documents={forCreationDocuments} />
            </TabsContent>
          </Tabs>
        </CardContent>
        
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={goBack}>Back</Button>
          <Button onClick={goNext} disabled={!canProceed}>
            {stats.forCreation > 0 ? 'Next: Entity Creation' : 'Next: Data Sync'}
          </Button>
        </CardFooter>
      </Card>
      
      {/* Exception Resolver Dialog */}
      <LookupExceptionResolver 
        isOpen={isExceptionResolverOpen}
        onClose={() => setIsExceptionResolverOpen(false)}
        exceptionId={selectedExceptionId}
        onResolved={handleExceptionResolved}
      />
    </>
  );
};

export default LookupResolutionStep;
