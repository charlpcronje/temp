// src/components/workflow/SyncStep.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { commandService } from '@/api/services';
import { CommandResponse } from '@/types';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { AlertCircle, CheckCircle, Database, HardDrive } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface SyncStepProps {
  onComplete: (result: CommandResponse) => void;
}

const SyncStep: React.FC<SyncStepProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  
  const [isSyncing, setIsSyncing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<any>(null);
  
  const handleSync = async () => {
    setIsSyncing(true);
    setError(null);
    
    try {
      const result = await commandService.syncToTenantDb();
      setSyncResult(result);
      
      if (result.success) {
        setIsComplete(true);
        toast({
          title: 'Sync Complete',
          description: 'Successfully synced to tenant database',
          duration: 3000
        });
      } else {
        setError(result.error || 'Failed to sync to tenant database');
      }
    } catch (err: any) {
      console.error('Error syncing to tenant database:', err);
      setError(err.message || 'Failed to sync to tenant database');
    } finally {
      setIsSyncing(false);
    }
  };
  
  const goBack = () => {
    navigate('/workflow/entity-creation');
  };
  
  const goNext = () => {
    navigate('/workflow/storage');
    
    // Call onComplete with a success result
    onComplete({
      success: true,
      command: 'sync_tenant_db',
      result: syncResult || { status: 'success', message: 'Sync to tenant database completed' }
    });
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Sync</CardTitle>
        <CardDescription>Sync processed documents to tenant database</CardDescription>
      </CardHeader>
      
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        <div className="text-center py-12">
          {isComplete ? (
            <>
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Sync Complete</h3>
              <p className="text-muted-foreground mb-6">
                All documents have been successfully synced to the tenant database.
              </p>
            </>
          ) : (
            <>
              <Database className="h-16 w-16 text-blue-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Sync to Tenant Database</h3>
              <p className="text-muted-foreground mb-6">
                This step will synchronize all processed documents to the tenant database.
                This includes all generated documents, lookups, and entity relationships.
              </p>
              
              <Button 
                onClick={handleSync}
                disabled={isSyncing}
                size="lg"
                className="mx-auto"
              >
                {isSyncing ? (
                  <>
                    <Spinner className="mr-2 h-4 w-4" />
                    Syncing...
                  </>
                ) : (
                  <>
                    <Database className="mr-2 h-4 w-4" />
                    Sync to Database
                  </>
                )}
              </Button>
            </>
          )}
        </div>
      </CardContent>
      
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={goBack}>Back</Button>
        <Button onClick={goNext} disabled={!isComplete}>
          Next: Storage
        </Button>
      </CardFooter>
    </Card>
  );
};

export default SyncStep;
