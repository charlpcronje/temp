import React from 'react';
import { Alert, AlertDescription } from "./alert";
import { HelpCircle } from "lucide-react";
import { Button } from "./button";
import { useToast } from "./use-toast";
import { apiClient } from "@/api/client";

interface ErrorWithHelperProps {
  message: string;
  helperKey?: string;
  className?: string;
}

/**
 * A component that displays an error message with a help icon that shows a solution
 * when clicked.
 */
const ErrorWithHelper: React.FC<ErrorWithHelperProps> = ({ 
  message, 
  helperKey, 
  className 
}) => {
  const { toast } = useToast();

  const getHelp = async () => {
    if (!helperKey) return;
    
    try {
      const response = await apiClient.get(`/helper/${helperKey}`);
      const data = response.data;
      
      if (response.status === 200) {
        toast({
          title: data.title,
          description: (
            <div className="mt-2">
              <p className="mb-2">{data.description}</p>
              <p className="font-semibold mb-2">Solution:</p>
              <p className="mb-2">{data.solution}</p>
              {data.command && (
                <div className="bg-slate-100 dark:bg-slate-800 p-2 rounded-md mb-2">
                  <code>{data.command}</code>
                  {data.command_location && (
                    <p className="text-xs mt-1">Run in: {data.command_location}</p>
                  )}
                </div>
              )}
            </div>
          ),
          duration: 10000,
        });
      } else {
        toast({
          title: "Error",
          description: "Failed to get help information",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Could not connect to the helper service",
        variant: "destructive",
      });
    }
  };

  return (
    <Alert variant="destructive" className={className}>
      <div className="flex justify-between items-center">
        <AlertDescription>{message}</AlertDescription>
        {helperKey && (
          <Button
            variant="ghost"
            size="sm"
            onClick={getHelp}
            className="p-0 h-8 w-8"
            title="Get help"
          >
            <HelpCircle className="h-4 w-4" />
          </Button>
        )}
      </div>
    </Alert>
  );
};

export default ErrorWithHelper;
