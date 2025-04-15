// src/components/workflow/WorkflowStepper.tsx
import React from 'react';
import { Check, X } from 'lucide-react';
import { cn } from "@/lib/utils";

interface WorkflowStepperProps {
  activeStep: number;
  onStepClick?: (stepIndex: number) => void;
}

interface Step {
  id: number;
  name: string;
  description: string;
  optional?: boolean;
}

const WorkflowStepper: React.FC<WorkflowStepperProps> = ({ activeStep, onStepClick }) => {
  const steps: Step[] = [
    {
      id: 0,
      name: 'Import',
      description: 'Upload CSV or Excel file',
    },
    {
      id: 1,
      name: 'Validate & Map',
      description: 'Validate data and map fields',
    },
    {
      id: 2,
      name: 'HTML',
      description: 'Generate HTML documents',
    },
    {
      id: 3,
      name: 'PDF',
      description: 'Generate PDF documents',
      optional: true,
    },
    {
      id: 4,
      name: 'Lookups',
      description: 'Resolve lookups against external data',
    },
    {
      id: 5,
      name: 'Entity Creation',
      description: 'Create missing entities',
      optional: true,
    },
    {
      id: 6,
      name: 'Data Sync',
      description: 'Sync to tenant database',
      optional: true,
    },
    {
      id: 7,
      name: 'Storage',
      description: 'Move to S3 storage',
      optional: true,
    },
    {
      id: 8,
      name: 'Complete',
      description: 'Processing complete',
    },
  ];

  return (
    <div className="w-full">
      <div className="hidden md:flex">
        <div className="w-full flex items-center">
          {steps.map((step, index) => (
            <React.Fragment key={step.id}>
              {/* Step indicator */}
              <div className="relative flex flex-col items-center">
                <button
                  type="button"
                  onClick={() => onStepClick && onStepClick(step.id)}
                  disabled={!onStepClick}
                  className={cn(
                    "w-10 h-10 flex items-center justify-center rounded-full border-2 transition-colors relative z-10",
                    "cursor-pointer hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary",
                    activeStep > step.id
                      ? "bg-primary border-primary text-primary-foreground"
                      : activeStep === step.id
                      ? "border-primary text-primary"
                      : "border-muted-foreground text-muted-foreground"
                  )}
                  aria-label={`Go to ${step.name} step`}
                >
                  {activeStep > step.id ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <span>{step.id + 1}</span>
                  )}
                </button>
                <div className="mt-2 text-center">
                  <div
                    className={cn(
                      "text-sm font-medium",
                      activeStep >= step.id
                        ? "text-foreground"
                        : "text-muted-foreground"
                    )}
                  >
                    {step.name}
                  </div>
                  <div className="text-xs text-muted-foreground hidden lg:block">
                    {step.description}
                  </div>
                </div>
              </div>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    "flex-1 border-t-2 transition-colors",
                    activeStep > step.id
                      ? "border-primary"
                      : "border-muted-foreground/30"
                  )}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Mobile view - just show current step */}
      <div className="md:hidden">
        {steps[activeStep] && (
          <div className="flex items-center justify-center">
            <button
              type="button"
              onClick={() => onStepClick && onStepClick(activeStep)}
              disabled={!onStepClick}
              className={cn(
                "w-10 h-10 flex items-center justify-center rounded-full border-2 border-primary text-primary",
                "cursor-pointer hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
              )}
              aria-label={`Go to ${steps[activeStep].name} step`}
            >
              <span>{activeStep + 1}</span>
            </button>
            <div className="ml-4">
              <div className="text-base font-medium">
                {steps[activeStep].name}
              </div>
              <div className="text-sm text-muted-foreground">
                {steps[activeStep].description}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowStepper;