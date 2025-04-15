// src/components/workflow/HtmlGenerationStep.tsx
import React, { useState, useEffect } from 'react';
import { AlertCircle, Check, Loader2, ExternalLink } from 'lucide-react';
import { commandService } from "@/api/services";
import { CommandResponse, HtmlGenerationResult } from "@/types";
import { Button } from '../ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';

interface HtmlGenerationStepProps {
  sessionHash: string; // Add sessionHash prop
  onComplete: (result: CommandResponse) => void;
}

const HtmlGenerationStep: React.FC<HtmlGenerationStepProps> = ({ sessionHash, onComplete }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<HtmlGenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  // Start generation on mount
  useEffect(() => {
    generateHtml();
  }, []);

  const generateHtml = async () => {
    setIsGenerating(true);
    setError(null);
    setProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + Math.random() * 10;
        return newProgress >= 90 ? 90 : newProgress;
      });
    }, 300);

    try {
      // Use the correct method for HTML generation
      const result = await commandService.generateHtml();

      // Clear interval and set progress to 100%
      clearInterval(progressInterval);
      setProgress(100);

      setGenerationResult(result);

      setIsGenerating(false);
      return { success: true, command: 'html', result };
    } catch (err: any) {
      clearInterval(progressInterval);
      setError(err.response?.data?.error || 'An error occurred during HTML generation. Please try again.');
      setIsGenerating(false);
      throw err;
    }
  };

  const handleContinue = async () => {
    if (!generationResult) return;

    try {
      // Use the result we already have
      onComplete({
        success: true,
        command: 'html',
        result: generationResult
      });
    } catch (err) {
      console.error('Error completing HTML generation step:', err);
      setError('Failed to continue to the next step. Please try again.');
    }
  };

  const handleRetry = () => {
    generateHtml();
  };

  const viewHtmlFile = (fileName: string) => {
    // Construct URL to HTML file using the passed sessionHash prop
    // Use the new API endpoint for serving files
    const url = `/api/files/${sessionHash}/html/${fileName}`;
    window.open(url, '_blank');
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>HTML Generation</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {isGenerating && (
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span>Generating HTML files...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} />
            </div>
            <div className="flex items-center justify-center py-8">
              <Loader2 className="mr-2 h-6 w-6 animate-spin text-primary" />
              <span>Generating HTML files from template...</span>
            </div>
          </div>
        )}

        {!isGenerating && generationResult && (
          <div className="space-y-6">
            <Alert variant={generationResult.errors.length === 0 ? "success" : "warning"}>
              <Check className="h-4 w-4" />
              <AlertTitle>HTML Generation Complete</AlertTitle>
              <AlertDescription>
                Generated {generationResult.num_files} HTML files using template "{generationResult.template_name}"
                {generationResult.errors.length > 0 && (
                  <>. <span className="font-semibold text-warning">Warning: {generationResult.errors.length} files had errors</span></>
                )}
              </AlertDescription>
            </Alert>

            <div>
              <h3 className="font-medium mb-2">Generation Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-md p-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Files Generated:</span>
                      <span className="font-medium">{generationResult.num_files}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Template:</span>
                      <span className="font-medium">{generationResult.template_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Output Directory:</span>
                      <span className="font-medium truncate max-w-[200px]" title={generationResult.output_dir}>
                        {generationResult.output_dir}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Errors:</span>
                      <span className="font-medium">{generationResult.errors.length}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-medium mb-2">Generated HTML Files</h3>
              <div className="rounded-md border overflow-hidden">
                <div className="max-h-64 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {generationResult.html_files.slice(0, 10).map((fileName, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell className="font-mono text-xs">{fileName}</TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => viewHtmlFile(fileName)}
                            >
                              <ExternalLink className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                      {generationResult.html_files.length > 10 && (
                        <TableRow>
                          <TableCell colSpan={3} className="text-center text-muted-foreground">
                            +{generationResult.html_files.length - 10} more files
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </div>

            {generationResult.errors.length > 0 && (
              <div>
                <h3 className="font-medium mb-2">Generation Errors</h3>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Row</TableHead>
                        <TableHead>Error</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {generationResult.errors.map((error, index) => (
                        <TableRow key={index}>
                          <TableCell>Row {error.row}</TableCell>
                          <TableCell>{error.error}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleRetry}
          disabled={isGenerating}
        >
          Regenerate HTML
        </Button>
        <Button
          onClick={handleContinue}
          disabled={isGenerating || !generationResult}
        >
          Continue to PDF Generation
        </Button>
      </CardFooter>
    </Card>
  );
};

export default HtmlGenerationStep;