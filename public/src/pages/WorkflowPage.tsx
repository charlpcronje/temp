// src/pages/WorkflowPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CommandResponse, SessionStatus, ValidationResult } from "@/types";
import { commandService, sessionService } from "@/api/services";
import WorkflowStepper from "@/components/workflow/WorkflowStepper";
import ValidateStep from "@/components/workflow/ValidateStep";
import HtmlGenerationStep from "@/components/workflow/HtmlGenerationStep";
import PdfGenerationStep from "@/components/workflow/PdfGenerationStep";
import LookupResolutionStep from "@/components/workflow/LookupResolutionStep";
import EntityCreationStep from "@/components/workflow/EntityCreationStep";
import SyncStep from "@/components/workflow/SyncStep";
import StorageStep from "@/components/workflow/StorageStep";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const WorkflowPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionHash = searchParams.get('session');

  // Step indices: 1=Validate, 2=HTML, ..., 8=Complete
  const [activeStep, setActiveStep] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus | null>(null);
  const [stepResults, setStepResults] = useState<Record<string, CommandResponse>>({});

  useEffect(() => {
    let isMounted = true; // Flag to track mount status

    if (!sessionHash) {
      console.error("WorkflowPage: No session hash provided in URL.");
      if (isMounted) {
        setError("No processing session specified. Please start by uploading a file or select a session.");
        setIsLoading(false);
      }
      return;
    }

    const fetchAndSetWorkflowState = async () => {
      if (!isMounted) return; // Exit if component unmounted
      setIsLoading(true);
      setError(null);

      try {
        console.log(`WorkflowPage: Activating session: ${sessionHash}`);
        const activationResponse = await sessionService.activateSession(sessionHash);

        if (!isMounted) return; // Exit if unmounted during async call

        if (!activationResponse.success || !activationResponse.result?.status) {
          throw new Error(activationResponse.error || `Failed to activate session ${sessionHash}. Status missing.`);
        }
        console.log('WorkflowPage: Session activated:', activationResponse.result);

        const status: SessionStatus = activationResponse.result.status;
        console.log("WorkflowPage: Fetched status:", status);
        setSessionStatus(status);
        console.log("active session",status.active_session);
        console.log("Session hash",status.session_hash);
        console.log("This session hash",sessionHash);
        if (!status.active_session || status.session_hash !== sessionHash) {
          throw new Error(`Session ${sessionHash} is not the active session after activation attempt.`);
        }

        // --- Determine active step based on session status ---
        const lastOp = status.last_operation;
        console.log(`WorkflowPage: Determining step from last_operation: "${lastOp}"`);

        // Define the map AFTER it can be fully constructed
        const operationToNextStepMap: { [key: string]: number } = {
          "IMPORT_DATA": 1,
          "VALIDATE_DATA": 2,
          "GENERATE_MAPPING": 2, // Assuming mapping is part of/before HTML
          "UPDATE_MAPPING": 2,
          "DELETE_MAPPING": 1, // Need to re-validate after deleting mapping
          "GENERATE_HTML": 3,
          "GENERATE_PDF": 4,
          "REPORT_GENERATED": 4, // Go to lookups after reports
          "RESOLVE_LOOKUPS": 5,
          "ENTITY_CREATION": 6,
          "SYNC_TENANT_DB": 7,
          "TRANSFER_TO_S3": 8,
          // ACTIVATE_SESSION is handled below, not in the map directly
        };

        let targetStep = 1; // Default to Validate (step 1)
        if (lastOp && lastOp !== "ACTIVATE_SESSION") {
          if (operationToNextStepMap[lastOp] !== undefined) {
            targetStep = operationToNextStepMap[lastOp];
            console.log(`WorkflowPage: Mapped "${lastOp}" to next step: ${targetStep}`);
          } else {
            console.warn(`WorkflowPage: Unknown last_operation: "${lastOp}". Defaulting to step 1 (Validate).`);
            targetStep = 1;
          }
        } else if (lastOp === "ACTIVATE_SESSION") {
            // If the *very last* operation was ACTIVATE, rely on the operation *before* that
            // which should have been returned by the backend during activation.
            // Let's assume the backend returns the PREVIOUS operation correctly in the activation result.
            const operationBeforeActivation = activationResponse.result.last_operation;
            console.log(`WorkflowPage: Activation detected. Prior operation was: "${operationBeforeActivation}"`);
            if (operationBeforeActivation && operationToNextStepMap[operationBeforeActivation] !== undefined) {
                targetStep = operationToNextStepMap[operationBeforeActivation];
                 console.log(`WorkflowPage: Based on prior op, mapped to next step: ${targetStep}`);
            } else {
                 console.warn(`WorkflowPage: No valid prior operation found after activation. Defaulting to step 1.`);
                 targetStep = 1;
            }
        } else {
          console.log("WorkflowPage: No last_operation found. Starting at step 1 (Validate).");
          targetStep = 1;
        }

        // Final check: if the process is already fully complete, stay on step 8
        if (lastOp === "TRANSFER_TO_S3") {
             targetStep = 8;
        }

        if (isMounted) { // Check mount status again before setting state
            setActiveStep(targetStep);
        }
        // --- End Step Determination ---

      } catch (err: any) {
        console.error('WorkflowPage: Error activating or fetching status:', err);
         if (isMounted) {
            setError(err.message || 'Failed to load workflow status. Please ensure the session exists and try again.');
         }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchAndSetWorkflowState();

    // Cleanup function
    return () => {
      isMounted = false;
      console.log("WorkflowPage: Unmounting...");
    };
  }, [sessionHash]); // Only re-run if sessionHash changes

  // Handle step completion
  const handleStepComplete = (completedStepIndex: number, result: CommandResponse) => {
    console.log(`WorkflowPage: Step ${completedStepIndex} completed:`, result);
    setStepResults(prev => ({ ...prev, [completedStepIndex]: result }));

    // Update local status immediately
    setSessionStatus(prev => ({
      ...prev!,
      last_operation: result.command.toUpperCase()
    }));

    const nextStepIndex = completedStepIndex + 1;

    // Add logic for skipping optional steps here if necessary
    // Example: Skip Entity Creation (step 5) if no entities are marked for creation
    // if (completedStepIndex === 4 && result.result?.for_creation === 0) {
    //   console.log("Skipping Entity Creation step.");
    //   setActiveStep(6); // Skip directly to Sync (step 6)
    //   return;
    // }

    setActiveStep(prev => Math.min(nextStepIndex, 8));
  };

  // Handle step click in the stepper
  const handleStepClick = (stepIndex: number) => {
    // Convert from 0-based to 1-based index
    const targetStep = stepIndex + 1;

    // Allow navigation to any step
    console.log(`WorkflowPage: Navigating to step ${targetStep}`);
    setActiveStep(targetStep);
  };

  // Helper to render the current step component
  const renderCurrentStep = () => {
    const validationResult = stepResults[1]?.result as ValidationResult | undefined;

    switch (activeStep) {
      case 1: return <ValidateStep onComplete={(result) => handleStepComplete(1, result)} />;
      case 2: return <HtmlGenerationStep
                sessionHash={sessionHash!}
                onComplete={(result) => handleStepComplete(2, result)}
              />;
      case 3: return <PdfGenerationStep onComplete={(result) => handleStepComplete(3, result)} />;
      case 4: return <LookupResolutionStep onComplete={(result) => handleStepComplete(4, result)} />;
      case 5: return <EntityCreationStep onComplete={(result) => handleStepComplete(5, result)} />;
      case 6: return <SyncStep onComplete={(result) => handleStepComplete(6, result)} />;
      case 7: return <StorageStep onComplete={(result) => handleStepComplete(7, result)} />;
      case 8:
        return (
          <div className="text-center py-12">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold">Processing Complete!</h2>
            <p className="text-muted-foreground mt-2">
              All workflow steps for this session have been successfully completed.
            </p>
            <Button onClick={() => navigate(`/app/sessions/${sessionHash}`)} className="mt-6">
                View Session Details & Logs
            </Button>
          </div>
        );
      default:
        console.error(`WorkflowPage: Invalid activeStep reached: ${activeStep}`);
        return (
            <Alert variant="warning">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Invalid Workflow State</AlertTitle>
                <AlertDescription>
                    Cannot determine the current workflow step ({activeStep}). An unexpected state was reached.
                     <Button variant="link" onClick={() => navigate('/app/dashboard')} className="p-0 h-auto">Go to Dashboard</Button>
                     {sessionHash && <Button variant="link" onClick={() => navigate(`/app/sessions/${sessionHash}`)} className="p-0 h-auto ml-2">View Session</Button>}
                </AlertDescription>
            </Alert>
        );
    }
  };

  // --- RENDER LOGIC ---

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-12rem)] items-center justify-center">
        <Spinner size="lg" />
        <span className="ml-3 text-muted-foreground">Loading session workflow...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className="max-w-3xl mx-auto mt-8">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error Loading Workflow</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
        <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm" onClick={() => navigate('/app/workflow/upload')}>
                Start New Session
            </Button>
             <Button variant="outline" size="sm" onClick={() => navigate('/app/dashboard')}>
                Go to Dashboard
            </Button>
            {/* Remove the retry button as it might cause infinite loops if the error persists */}
            {/* <Button variant="outline" size="sm" onClick={() => window.location.reload()}>Retry Loading</Button> */}
        </div>
      </Alert>
    );
  }

  return (
    <div className="space-y-8">
      <a href="app/">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Document Processing Workflow</h1>
          <p className="text-muted-foreground mt-2">
            Session: <span className="font-mono text-xs">{sessionHash?.substring(0, 16)}...</span>
            {sessionStatus?.document_type && <Badge variant="secondary" className="ml-2">{sessionStatus.document_type}</Badge>}
            {sessionStatus?.last_operation && <Badge variant="outline" className="ml-2">Last Op: {sessionStatus.last_operation}</Badge>}
          </p>
        </div>
      </a>
      {/* Stepper expects 0-based index, our state is 1-based */}
      <WorkflowStepper
        activeStep={activeStep - 1}
        onStepClick={handleStepClick}
      />

      <div className="mt-8">
        {renderCurrentStep()}
      </div>
    </div>
  );
};

export default WorkflowPage;