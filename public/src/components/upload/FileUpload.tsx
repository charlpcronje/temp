// src/components/upload/FileUpload.tsx
import React, { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { FileUp, AlertCircle, Check, Loader2 } from 'lucide-react';
import { commandService } from "@/api/services";
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import config from "@/config";
import { formatFileSize } from '@/lib/utils';

// Convert accepted file types string to dropzone format
const parseAcceptedTypes = (types: string): Record<string, string[]> => {
  const result: Record<string, string[]> = {};
  
  types.split(',').forEach(type => {
    const trimmedType = type.trim();
    if (trimmedType.startsWith('.')) {
      // Handle extensions like .csv
      const ext = trimmedType.substring(1);
      switch (ext) {
        case 'csv':
          result['text/csv'] = [`.${ext}`];
          break;
        case 'xls':
          result['application/vnd.ms-excel'] = [`.${ext}`];
          break;
        case 'xlsx':
          result['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] = [`.${ext}`];
          break;
        default:
          // Generic handling
          result[`application/${ext}`] = [`.${ext}`];
      }
    } else {
      // Handle MIME types directly
      result[trimmedType] = [];
    }
  });
  
  return result;
};

const FileUpload: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Get config values
  const MAX_FILE_SIZE = config.upload.maxFileSize;
  const ACCEPTED_FILE_TYPES = config.upload.acceptedFileTypes;
  
  // Handle file drop with react-dropzone
  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError(null);
    
    // Validate file size
    const selectedFile = acceptedFiles[0];
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`File size too large. Maximum allowed size is ${formatFileSize(MAX_FILE_SIZE)}.`);
      return;
    }
    
    // Handle file selection
    setFile(selectedFile);
  }, [MAX_FILE_SIZE]);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: parseAcceptedTypes(ACCEPTED_FILE_TYPES),
    multiple: false,
    maxSize: MAX_FILE_SIZE,
  });
  
  // Handle file upload
  const handleUpload = async () => {
    if (!file) return;
    
    setError(null);
    setUploading(true);
    setUploadProgress(0);
    
    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          const newProgress = prev + Math.random() * 10;
          return newProgress >= 90 ? 90 : newProgress;
        });
      }, 300);
      
      // Upload the file
      const response = await commandService.uploadFile(file);
      
      // Clear interval and set progress to 100%
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (response.success) {
        setSuccess(true);
        
        // Redirect to workflow page after a short delay
        setTimeout(() => {
          navigate(`/workflow?session=${response.result.hash}`);
        }, 1000);
      } else {
        setError(response.error || 'File upload failed. Please try again.');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred during upload. Please try again.');
    } finally {
      setUploading(false);
    }
  };
  
  // Reset the component
  const handleReset = () => {
    setFile(null);
    setError(null);
    setSuccess(false);
    setUploadProgress(0);
  };

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle>Import Data File</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {success && (
          <Alert variant="success">
            <Check className="h-4 w-4" />
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>
              File uploaded successfully! Redirecting to workflow...
            </AlertDescription>
          </Alert>
        )}
        
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center
            transition-colors cursor-pointer
            ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
            ${file ? 'bg-muted/50' : ''}
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center space-y-2">
            <FileUp className="h-8 w-8 text-muted-foreground" />
            {file ? (
              <>
                <p className="text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(file.size)}
                </p>
              </>
            ) : (
              <>
                <p className="text-sm font-medium">
                  {isDragActive ? 'Drop the file here' : 'Drag and drop your file here'}
                </p>
                <p className="text-xs text-muted-foreground">
                  Supported formats: {ACCEPTED_FILE_TYPES} (max {formatFileSize(MAX_FILE_SIZE)})
                </p>
              </>
            )}
          </div>
        </div>
        
        {uploading && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span>Uploading...</span>
              <span>{Math.round(uploadProgress)}%</span>
            </div>
            <Progress value={uploadProgress} />
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleReset}
          disabled={uploading || !file}
        >
          Reset
        </Button>
        <Button
          onClick={handleUpload}
          disabled={uploading || !file || success}
        >
          {uploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            'Upload & Process'
          )}
        </Button>
      </CardFooter>
    </Card>
  );
};

export default FileUpload;