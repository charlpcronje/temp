// src/components/workflow/PdfGenerationStep.tsx
import React, { useState, useEffect } from 'react';
import { AlertCircle, Check, Loader2, ExternalLink, Download } from 'lucide-react';
import { commandService } from "@/api/services";
import { CommandResponse, PdfGenerationResult } from "@/types";
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
import { useNavigate } from 'react-router-dom';

interface PdfGenerationStepProps {
  onComplete: (result: CommandResponse) => void;
}

const PdfGenerationStep: React.FC<PdfGenerationStepProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<PdfGenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  // Start generation on mount
  useEffect(() => {
    generatePdf();
  }, []);

  const generatePdf = async () => {
    setIsGenerating(true);
    setError(null);
    setProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + Math.random() * 5;
        return newProgress >= 90 ? 90 : newProgress;
      });
    }, 500);

    try {
      // Use the correct method for PDF generation
      const result = await commandService.generatePdf();

      // Clear interval and set progress to 100%
      clearInterval(progressInterval);
      setProgress(100);

      setGenerationResult(result);

      setIsGenerating(false);
      return { success: true, command: 'pdf', result };
    } catch (err: any) {
      clearInterval(progressInterval);
      setError(err.response?.data?.error || 'An error occurred during PDF generation. Please try again.');
      setIsGenerating(false);
      throw err;
    }
  };

  const handleComplete = async () => {
    if (!generationResult) return;

    try {
      const result = await commandService.generatePdf();
      onComplete({
        success: true,
        command: 'pdf',
        result
      });

      // Get session hash and navigate to logs
      const status = await commandService.getStatus();
      if (status.session_hash) {
        navigate(`/logs/${status.session_hash}`);
      } else {
        navigate('/logs');
      }
    } catch (err) {
      console.error('Error completing PDF generation step:', err);
      setError('Failed to complete the process. Please try again.');
    }
  };

  const handleRetry = () => {
    generatePdf();
  };

  const viewPdfFile = (fileName: string) => {
    // Get the session hash from the status
    const sessionHash = generationResult?.log_file.split('/').pop()?.split('_')[0] || '';

    // Extract just the filename without any path
    // Handle Windows paths (C:/path/to/file.pdf)
    if (fileName.includes(':')) {
      // This is a full Windows path
      const parts = fileName.split('/');
      fileName = parts[parts.length - 1];
    }
    // Handle Unix paths (/path/to/file.pdf)
    else if (fileName.includes('/')) {
      fileName = fileName.split('/').pop() || fileName;
    }
    // Handle Windows backslash paths (C:\path\to\file.pdf)
    else if (fileName.includes('\\')) {
      fileName = fileName.split('\\').pop() || fileName;
    }

    // Construct URL to PDF file using the API endpoint
    const url = `/api/files/${sessionHash}/pdf/${fileName}`;
    console.log(`Opening PDF: ${url}`);
    window.open(url, '_blank');
  };

  const downloadPdfFile = (fileName: string) => {
    // Get the session hash from the status
    const sessionHash = generationResult?.log_file.split('/').pop()?.split('_')[0] || '';

    // Extract just the filename without any path
    // Handle Windows paths (C:/path/to/file.pdf)
    if (fileName.includes(':')) {
      // This is a full Windows path
      const parts = fileName.split('/');
      fileName = parts[parts.length - 1];
    }
    // Handle Unix paths (/path/to/file.pdf)
    else if (fileName.includes('/')) {
      fileName = fileName.split('/').pop() || fileName;
    }
    // Handle Windows backslash paths (C:\path\to\file.pdf)
    else if (fileName.includes('\\')) {
      fileName = fileName.split('\\').pop() || fileName;
    }

    console.log(`Extracted filename: ${fileName}`);

    // Construct URL and trigger download using the API endpoint
    const url = `/api/files/${sessionHash}/pdf/${fileName}`;
    console.log(`Downloading PDF: ${url}`);

    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>PDF Generation</CardTitle>
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
                <span>Generating PDF files...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} />
            </div>
            <div className="flex items-center justify-center py-8">
              <Loader2 className="mr-2 h-6 w-6 animate-spin text-primary" />
              <span>Converting HTML to PDF documents...</span>
            </div>
          </div>
        )}

        {!isGenerating && generationResult && (
          <div className="space-y-6">
            <Alert variant={generationResult.errors.length === 0 ? "success" : "warning"}>
              <Check className="h-4 w-4" />
              <AlertTitle>PDF Generation Complete</AlertTitle>
              <AlertDescription>
                Generated {generationResult.num_files} PDF files in {generationResult.total_time.toFixed(2)} seconds
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
                      <span className="text-sm text-muted-foreground">Total Time:</span>
                      <span className="font-medium">{generationResult.total_time.toFixed(2)} seconds</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Average Time:</span>
                      <span className="font-medium">
                        {(generationResult.total_time / generationResult.num_files).toFixed(2)} seconds per file
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
              <h3 className="font-medium mb-2">Generated PDF Files</h3>
              <div className="rounded-md border overflow-hidden">
                <div className="max-h-64 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {generationResult.pdf_files.slice(0, 10).map((fileName, index) => {
                        // Log the filename for debugging
                        console.log(`PDF file ${index}: ${fileName}`);
                        return (
                          <TableRow key={index}>
                            <TableCell>{index + 1}</TableCell>
                            <TableCell className="font-mono text-xs">{fileName}</TableCell>
                            <TableCell className="text-right">
                            <div className="flex justify-end space-x-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => viewPdfFile(fileName)}
                              >
                                <ExternalLink className="h-4 w-4 mr-1" />
                                View
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => downloadPdfFile(fileName)}
                              >
                                <Download className="h-4 w-4 mr-1" />
                                Download
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      )})}
                      {generationResult.pdf_files.length > 10 && (
                        <TableRow>
                          <TableCell colSpan={3} className="text-center text-muted-foreground">
                            +{generationResult.pdf_files.length - 10} more files
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
                        <TableHead>File</TableHead>
                        <TableHead>Error</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {generationResult.errors.map((error, index) => (
                        <TableRow key={index}>
                          <TableCell>{error.file}</TableCell>
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
          Regenerate PDFs
        </Button>
        <Button
          onClick={handleComplete}
          disabled={isGenerating || !generationResult}
        >
          Complete & View All
        </Button>
      </CardFooter>
    </Card>
  );
};

export default PdfGenerationStep;