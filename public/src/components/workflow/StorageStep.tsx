// src/components/workflow/StorageStep.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { commandService } from '@/api/services';
import { CommandResponse } from '@/types';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { AlertCircle, CheckCircle, Cloud, Upload } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface StorageStepProps {
  onComplete: (result: CommandResponse) => void;
}

const StorageStep: React.FC<StorageStepProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  
  const [isTransferring, setIsTransferring] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transferResult, setTransferResult] = useState<any>(null);
  const [progress, setProgress] = useState(0);
  
  const simulateProgress = () => {
    setProgress(0);
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + Math.random() * 10;
        if (newProgress >= 100) {
          clearInterval(interval);
          return 100;
        }
        return newProgress;
      });
    }, 300);
    return interval;
  };
  
  const handleTransfer = async () => {
    setIsTransferring(true);
    setError(null);
    
    // Start progress simulation
    const progressInterval = simulateProgress();
    
    try {
      const result = await commandService.transferToS3();
      setTransferResult(result);
      
      // Ensure progress shows 100% when complete
      setProgress(100);
      
      if (result.success) {
        setIsComplete(true);
        toast({
          title: 'Transfer Complete',
          description: 'Successfully transferred to S3 storage',
          duration: 3000
        });
      } else {
        setError(result.error || 'Failed to transfer to S3 storage');
      }
    } catch (err: any) {
      console.error('Error transferring to S3 storage:', err);
      setError(err.message || 'Failed to transfer to S3 storage');
    } finally {
      setIsTransferring(false);
      clearInterval(progressInterval);
    }
  };
  
  const goBack = () => {
    navigate('/workflow/sync');
  };
  
  const goNext = () => {
    navigate('/workflow/complete');
    
    // Call onComplete with a success result
    onComplete({
      success: true,
      command: 'transfer_to_s3',
      result: transferResult || { status: 'success', message: 'Transfer to S3 storage completed' }
    });
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Storage</CardTitle>
        <CardDescription>Transfer documents and logs to S3 storage</CardDescription>
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
              <h3 className="text-lg font-medium mb-2">Transfer Complete</h3>
              <p className="text-muted-foreground mb-6">
                All documents and logs have been successfully transferred to S3 storage.
              </p>
            </>
          ) : (
            <>
              <Cloud className="h-16 w-16 text-blue-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Transfer to S3 Storage</h3>
              <p className="text-muted-foreground mb-6">
                This step will transfer all generated documents, logs, and session data to S3 storage
                for long-term archival and access.
              </p>
              
              {isTransferring && (
                <div className="w-full max-w-md mx-auto mb-4">
                  <div className="relative pt-1">
                    <div className="text-right mb-1 text-xs text-muted-foreground">
                      {Math.round(progress)}%
                    </div>
                    <div className="overflow-hidden h-2 text-xs flex rounded bg-muted">
                      <div 
                        style={{ width: `${progress}%` }}
                        className="shadow-none flex flex-col text-center whitespace-nowrap justify-center bg-blue-500"
                      />
                    </div>
                  </div>
                </div>
              )}
              
              <Button 
                onClick={handleTransfer}
                disabled={isTransferring}
                size="lg"
                className="mx-auto"
              >
                {isTransferring ? (
                  <>
                    <Spinner className="mr-2 h-4 w-4" />
                    Transferring...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Transfer to S3
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
          Next: Complete
        </Button>
      </CardFooter>
    </Card>
  );
};

export default StorageStep;
