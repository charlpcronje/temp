// src/components/workflow/MappingStep.tsx
import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, Check, Loader2, Edit, Save } from 'lucide-react';
import { commandService } from "@/api/services";
import { CommandResponse, ValidationResult, MappingResult } from "@/types";
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
import { Badge } from '../ui/badge';
import { Label } from '../ui/label';
import { Progress } from '../ui/progress';
import { ScrollArea } from '../ui/scroll-area';

interface MappingStepProps {
  onComplete: (result: CommandResponse) => void;
  validationResult?: ValidationResult;
}

const MappingStep: React.FC<MappingStepProps> = ({ onComplete, validationResult }) => {
  const [isMapping, setIsMapping] = useState(false);
  const [mappingResult, setMappingResult] = useState<MappingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [tableColumns, setTableColumns] = useState<string[]>([]);

  // For editing mappings
  const [editMode, setEditMode] = useState(false);
  const [editedMappings, setEditedMappings] = useState<Record<string, any>>({});
  const [currentColumn, setCurrentColumn] = useState<{ name: string, type: string | null }>({ name: '', type: null });

  const editButtonRef = useRef<HTMLButtonElement>(null);

  // Start mapping on mount
  useEffect(() => {
    generateMapping();

    // Get table columns from validation results or API
    if (validationResult) {
      extractTableColumns();
    }
  }, [validationResult]);

  const extractTableColumns = async () => {
    try {
      // First try to extract columns from validation result if available
      if (validationResult?.field_matches) {
        const columns = new Set<string>();

        // Add all matched columns
        Object.values(validationResult.field_matches).forEach(match => {
          if (match.column) columns.add(match.column);
        });

        if (columns.size > 0) {
          setTableColumns(Array.from(columns));
          return;
        }
      }

      // Fallback: try to get table data from existing API
      try {
        // This uses the existing table_data API endpoint
        const response = await commandService.runCommand('table_data');

        if (response.success && response.result?.columns) {
          setTableColumns(response.result.columns);
        } else {
          console.error('Failed to fetch table data:', response.error);
        }
      } catch (err) {
        console.error('Error fetching table data:', err);
      }
    } catch (err) {
      console.error('Error extracting table columns:', err);
    }
  };

  const generateMapping = async () => {
    setIsMapping(true);
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
      const response = await commandService.runCommand('map');

      // Clear interval and set progress to 100%
      clearInterval(progressInterval);
      setProgress(100);

      if (response.success) {
        setMappingResult(response.result);

        // Set the edited mappings from the result
        if (response.result.mapped_fields) {
          setEditedMappings(response.result.mapped_fields);
        }
      } else {
        setError(response.error || 'Mapping generation failed. Please try again.');
      }

      setIsMapping(false);
      return response;
    } catch (err: any) {
      clearInterval(progressInterval);
      setError(err.response?.data?.error || 'An error occurred during mapping. Please try again.');
      setIsMapping(false);
      throw err;
    }
  };

  const handleContinue = async () => {
    if (!mappingResult) return;

    try {
      // If mappings were edited, update them first
      let response;

      if (editMode) {
        response = await commandService.updateMapping(editedMappings);
      } else {
        response = await commandService.runCommand('map');
      }

      onComplete(response as CommandResponse);
    } catch (err) {
      console.error('Error completing mapping step:', err);
      setError('Failed to continue to the next step. Please try again.');
    }
  };

  const handleRetry = () => {
    generateMapping();
  };

  const handleValidateWithMappings = async () => {
    setIsMapping(true);
    setError(null);

    try {
      // First save the mappings
      await handleSaveMapping();

      // Then run validation using the updated mappings
      const response = await commandService.runCommand('validate');

      if (response.success) {
        // Update with the new validation results
        setMappingResult(response.result);
      } else {
        setError(response.error || 'Validation failed. Please check your mappings.');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred during validation. Please try again.');
    } finally {
      setIsMapping(false);
    }
  };

  const handleEditMapping = () => {
    setEditMode(true);
  };

  const handleSaveMapping = async () => {
    setIsMapping(true);
    setError(null);

    try {
      const response = await commandService.updateMapping(editedMappings);

      if (response) {
        setMappingResult(response);
        setEditMode(false);
      } else {
        setError('Failed to update mappings. Please try again.');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred while updating mappings. Please try again.');
    } finally {
      setIsMapping(false);
    }
  };

  const handleSelectType = (column: string, typeName: string) => {
    if (!typeName) {
      // If unselecting, remove the mapping
      const newMappings = { ...editedMappings };
      delete newMappings[column];
      setEditedMappings(newMappings);
      return;
    }

    // Get the full type info from schema
    const typeInfo = mappingResult?.schema_fields[typeName];
    if (!typeInfo) {
      console.error(`Type ${typeName} not found in schema`);
      return;
    }

    // Create a complete mapping object by copying ALL properties from the type definition
    // This ensures we match the format in docs/validation/mapping,example.json
    const completeMapping: Record<string, any> = {
      type: typeName,
      validation_type: typeInfo.validate_type,
      required: typeInfo.required || false,
      description: typeInfo.description,
      slug: typeInfo.slug || [typeName]
    };

    // Copy all other properties from the type definition
    Object.entries(typeInfo).forEach(([key, value]) => {
      // Skip properties we've already set above
      if (!['validate_type', 'required', 'description', 'slug'].includes(key)) {
        completeMapping[key] = value;
      }
    });

    // Update the mappings
    setEditedMappings({
      ...editedMappings,
      [column]: completeMapping
    });
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Field Mapping</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {isMapping && (
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span>Generating field mapping...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} />
            </div>
            <div className="flex items-center justify-center py-8">
              <Loader2 className="mr-2 h-6 w-6 animate-spin text-primary" />
              <span>Generating field-to-column mapping...</span>
            </div>
          </div>
        )}

        {!isMapping && mappingResult && (
          <div className="space-y-6">
            <Alert variant={(mappingResult.missing_required?.length ?? 0) === 0 ? "success" : "warning"}>
              <Check className="h-4 w-4" />
              <AlertTitle>Mapping Generated</AlertTitle>
              <AlertDescription>
                {Object.keys(mappingResult.mapped_fields).length} fields mapped successfully
                {mappingResult.missing_required && mappingResult.missing_required.length > 0 && (
                  <>. <span className="font-semibold text-warning">Warning: {mappingResult.missing_required.length} required fields not mapped</span></>
                )}
              </AlertDescription>
            </Alert>

            <div className="flex items-center justify-between">
              <h3 className="font-medium">Column to Type Mapping</h3>
              {!editMode ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleEditMapping}
                  ref={editButtonRef}
                >
                  <Edit className="mr-2 h-4 w-4" />
                  Edit Mapping
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSaveMapping}
                  disabled={isMapping}
                >
                  <Save className="mr-2 h-4 w-4" />
                  Save Changes
                </Button>
              )}
            </div>

            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Column Name</TableHead>
                    <TableHead>Matched Type</TableHead>
                    <TableHead>Validation Type</TableHead>
                    {editMode && <TableHead className="text-right">Action</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tableColumns.map((column) => {
                    const mapping = editedMappings[column] || null;
                    const mappedType = mapping?.type || null;
                    const typeInfo = mappedType ? mappingResult.schema_fields[mappedType] : null;
                    const isRequired = typeInfo?.required === true;

                    return (
                      <TableRow key={column} className={isRequired && !mappedType ? "bg-warning/10" : undefined}>
                        <TableCell className="font-medium">{column}</TableCell>
                        <TableCell>
                          {mappedType ? (
                            <span>{mappedType}</span>
                          ) : (
                            <span className="text-muted-foreground italic">Unknown</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {mapping?.validation_type ? (
                            <Badge
                              variant={isRequired ? "default" : "outline"}
                            >
                              {mapping.validation_type}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">string</span>
                          )}
                        </TableCell>
                        {editMode && (
                          <TableCell className="text-right">
                            <div className="border rounded p-1 w-full h-64 overflow-auto bg-white">
                              <div
                                className="p-2 hover:bg-gray-100 cursor-pointer border-b"
                                onClick={() => handleSelectType(column, "")}
                              >
                                <span className="text-gray-500">None (unmapped)</span>
                              </div>
                              {mappingResult && Object.keys(mappingResult.schema_fields).map((typeName) => {
                                const typeInfo = mappingResult.schema_fields[typeName];
                                return (
                                  <div
                                    key={typeName}
                                    className={`p-2 cursor-pointer border-b hover:bg-gray-100 ${mappedType === typeName ? 'bg-blue-50' : ''}`}
                                    onClick={() => handleSelectType(column, typeName)}
                                  >
                                    <div className="font-bold">{typeName}</div>
                                    <div>
                                      <span className="font-semibold mr-1">Type:</span>{typeInfo.validate_type}
                                      {typeInfo.required && <span className="ml-2 text-red-500 font-bold">Required</span>}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </TableCell>
                        )}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleRetry}
            disabled={isMapping}
          >
            Regenerate Mapping
          </Button>
          {editMode && (
            <Button
              variant="secondary"
              onClick={handleValidateWithMappings}
              disabled={isMapping}
            >
              Validate with Mappings
            </Button>
          )}
        </div>
        <Button
          onClick={handleContinue}
          disabled={isMapping || !mappingResult}
        >
          Continue to HTML Generation
        </Button>
      </CardFooter>
    </Card>
  );
};

export default MappingStep;