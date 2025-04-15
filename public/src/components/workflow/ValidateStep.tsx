// src/components/workflow/ValidateStep.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { commandService } from '@/api/services';
import {
  ValidationResult,
  CommandResponse,
  MappingResult, // Assuming MappingResult includes schema_fields and mapped_fields
  SchemaField // Import SchemaField type if not already imported or defined
} from '@/types';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Spinner } from '@/components/ui/spinner';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  ArrowRight,
  CheckCircle,
  XCircle,
  Loader2,
  AlertTriangle,
  Edit,
  RefreshCw,
  Trash2,
  Info,
  Save,
  FileText
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast'; // Ensure useToast is set up

interface ValidateStepProps {
  onComplete: (result: CommandResponse) => void;
}

// Type for column-to-type mapping - This now directly holds the schema field definition
// We might not need a separate ColumnMapping interface if it's just the SchemaField
// type ColumnMapping = SchemaField & { type: string }; // Or just use SchemaField directly

const ValidateStep: React.FC<ValidateStepProps> = ({ onComplete }) => {
  // STATE
  const [isValidating, setIsValidating] = useState(false);
  const [validationResults, setValidationResults] = useState<ValidationResult | null>(null);
  const [tableColumns, setTableColumns] = useState<string[]>([]);
  const [schemaFields, setSchemaFields] = useState<Record<string, SchemaField>>({});
  // State now holds the full schema field definition for the mapped column
  const [columnMappings, setColumnMappings] = useState<Record<string, SchemaField>>({});
  const [editMode, setEditMode] = useState(false);
  const [activeTab, setActiveTab] = useState('fields');
  const [rowErrors, setRowErrors] = useState<any[]>([]);
  const [isAdjustingMapping, setIsAdjustingMapping] = useState(false);
  const [currentEditColumn, setCurrentEditColumn] = useState<string | null>(null);
  const [isResetConfirmOpen, setIsResetConfirmOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [passThreshold, setPassThreshold] = useState(80);

  // API Mutations
  const validateMutation = useMutation({
    mutationFn: () => commandService.validateData(),
    onSuccess: (data: any) => {
      console.log('Validation response:', data);
      if (data) {
        // Check if validation_results exists in the data
        if (data.validation_results) {
          console.log('Found validation_results:', data.validation_results);
          // Set all validation results directly from validation_results
          setValidationResults({
            document_type: data.validation_results.document_type || 'Unknown',
            match_score: data.validation_results.match_score || 0,
            total_rows: data.validation_results.total_rows || 0,
            valid_rows: data.validation_results.valid_rows || 0,
            invalid_rows: data.validation_results.invalid_rows || 0,
            success_rate: data.validation_results.success_rate || 0,
            // Add required fields from ValidationResult type
            valid: true,
            errors: [],
            field_matches: {},
            required_missing: [],
            schema_id: data.validation_results.schema_name || ''
          });
        } else {
          console.log('No validation_results found in data');
          setValidationResults(data);
        }

        if (data.pass_threshold) {
          setPassThreshold(data.pass_threshold);
        }

        // Use all_columns from the validation response if available
        if (data.all_columns && Array.isArray(data.all_columns) && data.all_columns.length > 0) {
            console.log('Using all_columns from validation response:', data.all_columns);
            setTableColumns([...data.all_columns].sort()); // Sort for consistent order
        }
        // Fallback to extracting columns from row_validations
        else if (data.row_validations && data.row_validations[0]?.fields) {
            const columns = new Set<string>();

            // Extract all unique column names from the first row's fields
            data.row_validations[0].fields.forEach((field: any) => {
                if (field.column) columns.add(field.column);
            });

            // If we found columns, set them in state
            if (columns.size > 0) {
                console.log('Found columns from row_validations:', Array.from(columns));
                setTableColumns(Array.from(columns).sort()); // Sort for consistent order
            } else {
                console.warn("Could not extract columns from validation results.");
                // Fallback to field_matches if no columns found in row_validations
                if (data.field_matches) {
                    const fallbackColumns = new Set<string>();
                    Object.values(data.field_matches).forEach((match: any) => {
                        if (match.column) fallbackColumns.add(match.column);
                    });
                    if (fallbackColumns.size > 0) {
                        console.log('Using fallback columns from field_matches:', Array.from(fallbackColumns));
                        setTableColumns(Array.from(fallbackColumns).sort());
                    }
                }
            }
        }


        if (data.row_validations) {
          setRowErrors(data.row_validations.filter((row: any) => !row.valid));
        }

        if (data.schema && data.schema.schema) {
          setSchemaFields(data.schema.schema);
        }

        toast({
          title: 'Validation completed',
          description: 'Data has been validated against the schema',
          duration: 3000
        });
      } else {
        toast({
          title: 'Error',
          description: 'Validation returned unexpected result',
          variant: 'destructive',
          duration: 3000
        });
      }
      setIsValidating(false);
    },
    onError: (error: any) => {
      console.error('Validation error:', error);
      const errorMsg = error.response?.data?.error || error.message || 'Failed to validate data';
      setError(errorMsg); // Set error state
      toast({
        title: 'Validation Error',
        description: errorMsg,
        variant: 'destructive',
        duration: 5000
      });
      setIsValidating(false);
    },
  });

  const generateMappingMutation = useMutation({
    mutationFn: () => commandService.generateMapping(),
    onSuccess: (data: any) => {
      if (data && data.mapped_fields) {
        // The backend returns mapped_fields which might be the simplified version.
        // We need to reconstruct the full mapping using the schemaFields we loaded.
        const initialFullMappings: Record<string, SchemaField> = {};
        Object.entries(data.mapped_fields).forEach(([columnName, mappingInfo]: [string, any]) => {
            const typeName = typeof mappingInfo === 'string' ? mappingInfo : mappingInfo?.type;
            if (typeName && schemaFields[typeName]) {
                initialFullMappings[columnName] = {
                    ...schemaFields[typeName], // Copy all properties from schema
                    type: typeName // Ensure 'type' field exists, matching user's desired format
                };
            } else {
                // Handle cases where type isn't found or mapping is malformed
                 initialFullMappings[columnName] = { // Basic fallback
                    type: typeName || 'UNKNOWN',
                    validation_type: 'NONE',
                    description: 'Type not found in schema or invalid mapping',
                    slug: [typeName || 'UNKNOWN'],
                    required: false
                } as SchemaField; // Type assertion
                console.warn(`Type "${typeName}" for column "${columnName}" not found in schemaFields during initial mapping load.`);
            }
        });
        setColumnMappings(initialFullMappings);

        toast({
          title: 'Mapping loaded',
          description: 'Field mapping has been loaded or generated',
          duration: 3000
        });
      } else if (data && data.error) {
         setError(data.error); // Show mapping error
         toast({ title: 'Mapping Error', description: data.error, variant: 'destructive' });
      } else {
        toast({
          title: 'Warning',
          description: 'Mapping generation returned no data or unexpected result.',
          variant: 'default' // Use default or warning
        });
      }
    },
    onError: (error: any) => {
      console.error('Mapping generation error:', error);
      const errorMsg = error.response?.data?.error || error.message || 'Failed to generate/load mapping';
      setError(errorMsg);
      toast({
        title: 'Mapping Error',
        description: errorMsg,
        variant: 'destructive',
        duration: 5000
      });
    },
  });

  // *** IMPORTANT: Ensure the payload sent matches backend expectations ***
  // The backend `update_mapping` might expect the simplified `{ "column": "TYPE_NAME" }` format
  // OR it might expect the full schema object format `{ "column": { "type": "TYPE_NAME", ... } }`.
  // Adjust the payload in `updateMappingMutation.mutate(payload)` accordingly.
  // Assuming backend expects the full object format based on the desired JSON output:
  const updateMappingMutation = useMutation({
      mutationFn: (updatedMapping: Record<string, SchemaField>) =>
          // Send the entire `columnMappings` object
          commandService.updateMapping(updatedMapping),
      onSuccess: (data: any) => {
          if (data && data.mapped_fields) {
              // Re-process the returned mapped_fields to ensure full format
              const updatedFullMappings: Record<string, SchemaField> = {};
              Object.entries(data.mapped_fields).forEach(([columnName, mappingInfo]: [string, any]) => {
                 const typeName = typeof mappingInfo === 'string' ? mappingInfo : mappingInfo?.type;
                 if (typeName && schemaFields[typeName]) {
                    updatedFullMappings[columnName] = {
                        ...schemaFields[typeName],
                        type: typeName
                    };
                 } else {
                     updatedFullMappings[columnName] = {
                        type: typeName || 'UNKNOWN',
                        validation_type: 'NONE',
                        description: 'Type not found in schema or invalid mapping',
                        slug: [typeName || 'UNKNOWN'],
                        required: false
                    } as SchemaField;
                     console.warn(`Type "${typeName}" for column "${columnName}" not found in schemaFields after update.`);
                 }
              });
              setColumnMappings(updatedFullMappings);

              toast({
                  title: 'Mapping updated',
                  description: 'Field mapping has been saved',
                  duration: 3000
              });
          } else if (data && data.error) {
              setError(data.error);
              toast({ title: 'Mapping Update Error', description: data.error, variant: 'destructive' });
          } else {
              toast({
                  title: 'Warning',
                  description: 'Mapping update returned unexpected result',
                  variant: 'default'
              });
          }
          setEditMode(false);
          setIsAdjustingMapping(false);
      },
      onError: (error: any) => {
          console.error('Mapping update error:', error);
          const errorMsg = error.response?.data?.error || error.message || 'Failed to update mapping';
          setError(errorMsg);
          toast({
              title: 'Mapping Update Error',
              description: errorMsg,
              variant: 'destructive',
              duration: 5000
          });
          setIsAdjustingMapping(false);
      },
  });


  const deleteMappingMutation = useMutation({
    mutationFn: () => commandService.deleteMapping(),
    onSuccess: () => {
      toast({
        title: 'Mapping deleted',
        description: 'Field mapping has been reset',
        duration: 3000
      });
      // After deleting, immediately try to generate/load a new one
      generateMappingMutation.mutate();
    },
    onError: (error: any) => {
      console.error('Mapping delete error:', error);
       const errorMsg = error.response?.data?.error || error.message || 'Failed to reset mapping';
       setError(errorMsg);
      toast({
        title: 'Error',
        description: 'Failed to reset mapping',
        variant: 'destructive',
        duration: 5000
      });
    },
  });

  // EFFECTS
  // Initialize data by checking status and loading mapping
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setIsValidating(true);
        setError(null); // Clear previous errors

        // First try to load existing mapping without validating
        try {
            console.log('Calling mapping API to load existing mapping...');
            await generateMappingMutation.mutateAsync();
            console.log('Mapping API call successful');

            // If we have mapping data, we can assume validation was done previously
            // No need to run validation again unless the user clicks the Re-validate button
        } catch (mappingError: any) {
            console.error('Initial mapping generation/load failed:', mappingError);
            // If mapping fails, we might need to run validation
            console.log('No existing mapping found, running validation...');
            try {
              await validateMutation.mutateAsync();
              // Try to generate mapping again after validation
              await generateMappingMutation.mutateAsync();
            } catch (validationError: any) {
              console.error('Initial validation failed:', validationError);
              // Error is already set by the mutation's onError
              setError(prev => prev ? `${prev}\nFailed to validate data.` : 'Failed to validate data.');
            }
        }

      } catch (error: any) {
        console.error('Error during initial data loading:', error);
        // Error is already set by the mutation's onError
      } finally {
        setIsValidating(false);
      }
    };

    loadInitialData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount

  // HANDLERS
  const handleValidate = () => {
    setIsValidating(true);
    validateMutation.mutate();
  };

  const handleSaveMapping = () => {
    setIsAdjustingMapping(true);
    // Pass the current state of columnMappings, which should be the full objects
    updateMappingMutation.mutate(columnMappings);
  };

  const handleResetMapping = () => {
    setIsResetConfirmOpen(true);
  };

  const confirmResetMapping = () => {
    setIsResetConfirmOpen(false);
    deleteMappingMutation.mutate(); // This will trigger generateMappingMutation on success
  };

  const handleContinue = async () => {
    if (editMode) {
        toast({ title: "Save Changes", description: "Please save or cancel your mapping edits first.", variant: "default" });
        return;
    }

    // Optional: Re-validate one last time before proceeding
    // try {
    //   await validateMutation.mutateAsync();
    //   if (validationResults && validationResults.success_rate < passThreshold) {
    //      toast({ title: "Validation Failed", description: `Success rate (${validationResults.success_rate.toFixed(1)}%) is below threshold (${passThreshold}%). Cannot continue.`, variant: "destructive" });
    //      return;
    //   }
    // } catch (e) {
    //    toast({ title: "Validation Failed", description: "Could not re-validate data before proceeding.", variant: "destructive" });
    //    return;
    // }


    // Pass the results needed by the next step (HTML Generation)
    // We're skipping the mapping step and going directly to HTML generation
    onComplete({
      success: true, // Indicate this step passed validation threshold
      command: 'validate', // Name of the step completed
      result: { // Pass relevant data forward
        validation_results: validationResults,
        // Pass the *final* saved mappings
        mapped_fields: columnMappings
      }
    });
  };

  const handleEditMapping = () => {
    setEditMode(true);
  };

  // *** CORRECTED: Set the FULL schema object as the mapping value ***
  const handleSetColumnType = (column: string, typeName: string) => {
    const newMappings = { ...columnMappings };

    if (!typeName) {
      // If typeName is empty, remove the mapping for this column
      delete newMappings[column];
    } else if (schemaFields[typeName]) {
      // Get the full schema definition for the selected type
      const fieldSchema = schemaFields[typeName];
      // Store the entire schema object, ensuring 'type' is present
      newMappings[column] = {
        ...fieldSchema,
         // Explicitly add 'type' if backend expects it at the top level,
         // otherwise remove this line if the schema already includes it.
        type: typeName
      };
    } else {
      console.warn(`Selected type "${typeName}" not found in schemaFields.`);
      // Optionally handle this case, e.g., clear the mapping or show an error
      delete newMappings[column]; // Safest option might be to unmap
    }

    setColumnMappings(newMappings);
    // Close the dialog
    setCurrentEditColumn(null);
  };


  // RENDERING HELPERS
  const renderValidationStatus = () => {
    if (!validationResults) return null;

    // Ensure properties exist before destructuring
    const { document_type = 'Unknown', match_score = 0, valid_rows = 0, invalid_rows = 0, total_rows = 0, success_rate = 0 } = validationResults;

    // Determine severity based on success rate
    let severity: 'success' | 'warning' | 'error' = 'success';
    if (success_rate < passThreshold) {
      severity = 'error';
    } else if (success_rate < 95) {
      severity = 'warning';
    }

    return (
      <div className="space-y-6">
        {/* Document type detection alert */}
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertTitle>Document Type Detection</AlertTitle>
          <AlertDescription>
            Document type detected: <Badge className="ml-1">{document_type}</Badge> with {match_score.toFixed(1)}% match confidence
          </AlertDescription>
        </Alert>

        {/* Stats overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-card border rounded-lg p-4 text-center">
            <h4 className="text-sm font-medium">Total Rows</h4>
            <p className="text-2xl font-bold">{total_rows}</p>
          </div>
          <div className="bg-card border rounded-lg p-4 text-center">
            <h4 className="text-sm font-medium">Valid Rows</h4>
            <p className="text-2xl font-bold text-green-600">{valid_rows}</p>
          </div>
          <div className="bg-card border rounded-lg p-4 text-center">
            <h4 className="text-sm font-medium">Invalid Rows</h4>
            <p className="text-2xl font-bold text-red-600">{invalid_rows}</p>
          </div>
        </div>

        {/* Success rate progress */}
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium">Success Rate</span>
            <span className="text-sm font-medium">{success_rate.toFixed(1)}%</span>
          </div>
          <Progress
            value={success_rate}
            className="h-3"
            indicatorClassName={
              success_rate >= 95 ? "bg-green-600" :
                success_rate >= passThreshold ? "bg-amber-500" :
                  "bg-red-600"
            }
          />
          <div className="flex justify-end mt-1">
            <span className="text-xs text-muted-foreground">Minimum threshold: {passThreshold}%</span>
          </div>
        </div>
      </div>
    );
  };

  const renderFieldMappingTab = () => {
    const hasMappingData = Object.keys(columnMappings).length > 0;
    const hasColumns = tableColumns.length > 0;

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium">Field Mapping</h3>
          <div className="space-x-2">
            {editMode ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => { /* TODO: Reset edits, maybe reload original mappings */ setEditMode(false); }}
                  disabled={isAdjustingMapping}
                >
                  <XCircle className="h-4 w-4 mr-1" /> Cancel
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleSaveMapping}
                  disabled={isAdjustingMapping || updateMappingMutation.isPending}
                >
                  {updateMappingMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-1" />
                  )}
                  Save Mapping
                </Button>
              </>
            ) : (
              hasMappingData && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleEditMapping}
                >
                  <Edit className="h-4 w-4 mr-1" /> Edit Mapping
                </Button>
              )
            )}
          </div>
        </div>

        {!hasColumns && !isValidating && !generateMappingMutation.isPending ? (
           <div className="flex flex-col items-center justify-center py-8 text-center">
             <FileText className="h-16 w-16 text-muted-foreground mb-4" />
             <h3 className="text-lg font-medium mb-2">No Columns Found</h3>
             <p className="text-muted-foreground mb-6 max-w-md">
               Could not determine columns from the validation data. Please re-validate or check the source file.
             </p>
             <Button onClick={handleValidate} disabled={isValidating}>
                 Re-validate Data
             </Button>
           </div>
        ) : !hasMappingData && (generateMappingMutation.isPending || isValidating) ? (
             <div className="flex items-center justify-center py-8">
                <Spinner size="lg" />
                <span className="ml-2">Loading mapping...</span>
             </div>
        ) : !hasMappingData && !generateMappingMutation.isPending ? (
           <div className="flex flex-col items-center justify-center py-8 text-center">
             <FileText className="h-16 w-16 text-muted-foreground mb-4" />
             <h3 className="text-lg font-medium mb-2">Mapping Not Generated</h3>
             <p className="text-muted-foreground mb-6 max-w-md">
               Could not automatically generate mapping. Check validation results or try generating manually if supported.
             </p>
             {/* Optionally add a manual generate button if the backend supports it without validation results */}
             {/* <Button onClick={() => generateMappingMutation.mutate()}>Generate Mapping</Button> */}
           </div>
        ) : ( // Only render table if we have columns
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-left">Column Name</TableHead>
                  <TableHead className="text-left">Mapped Type</TableHead>
                  <TableHead className="text-left">Validation Type</TableHead>
                  {editMode && <TableHead className="text-center">Action</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {tableColumns.map(columnName => {
                  const mapping = columnMappings[columnName]; // This is now the full SchemaField object or undefined
                  const typeName = mapping?.type || null;
                  const validationType = mapping?.validate_type || null;
                  const isRequired = mapping?.required === true;

                  return (
                    <TableRow key={columnName} className="hover:bg-muted/50">
                      <TableCell className="font-medium">{columnName}</TableCell>
                      <TableCell>
                        {typeName ? (
                          <div className="flex items-center">
                            <span>{typeName}</span>
                            {isRequired && <Badge variant="destructive" className="ml-2">Required</Badge>}
                          </div>
                        ) : (
                          <span className="text-muted-foreground italic">Unmapped</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {validationType ? (
                          <Badge variant="outline">{validationType}</Badge>
                        ) : (
                          <span className="text-muted-foreground italic">-</span>
                        )}
                      </TableCell>
                      {editMode && (
                        <TableCell className="text-center">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentEditColumn(columnName)}
                          >
                            <Edit className="h-4 w-4 mr-1" />
                            Map
                          </Button>
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    );
  };

   const renderRowErrorsTab = () => {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Validation Errors</h3>
        {rowErrors.length > 0 ? (
          <div className="border rounded-lg overflow-auto max-h-[400px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Row #</TableHead>
                  <TableHead>Field</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Error</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rowErrors.map((row, rowIndex) => (
                  // Ensure row.fields exists and is an array before filtering/mapping
                  (row.fields || []).filter((field: any) => !field.valid).map((field: any, fieldIndex: number) => (
                    <TableRow key={`${rowIndex}-${fieldIndex}`}>
                      <TableCell>{row.row_id}</TableCell>
                      <TableCell>{field.field}</TableCell>
                      <TableCell className="max-w-[200px] truncate" title={String(field.value || '')}>
                        {String(field.value || 'N/A')}
                      </TableCell>
                      <TableCell>
                        {(field.errors || []).map((error: string, errorIndex: number) => (
                          <div key={errorIndex} className="text-red-500 text-xs">{error}</div>
                        ))}
                      </TableCell>
                    </TableRow>
                  ))
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <Alert variant="success">
            <CheckCircle className="h-4 w-4" />
            <AlertTitle>All rows valid</AlertTitle>
            <AlertDescription>
              All rows in your data have passed validation based on the current mapping.
            </AlertDescription>
          </Alert>
        )}
      </div>
    );
  };


  // MAIN RENDER
  if (isValidating && !validationResults) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <h3 className="text-lg font-medium">Validating data...</h3>
        <p className="text-center text-muted-foreground max-w-md">
          The system is analyzing your data, detecting document type, and validating fields.
        </p>
        {/* Progress simulation - can be removed or made more accurate */}
        {/* <Progress value={30} className="w-64 h-2" /> */}
      </div>
    );
  }

  // Main content
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Data Validation & Field Mapping</CardTitle>
        <CardDescription>
          Validate data against schema requirements and map columns to field types. After completing this step, you'll proceed directly to HTML generation.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Validation status section */}
        {renderValidationStatus()}

        {/* Tabs for fields and errors */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-2 mb-4">
            <TabsTrigger value="fields">Field Mapping</TabsTrigger>
            <TabsTrigger value="errors">Validation Errors ({rowErrors.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="fields">
            {renderFieldMappingTab()}
          </TabsContent>

          <TabsContent value="errors">
            {renderRowErrorsTab()}
          </TabsContent>
        </Tabs>
      </CardContent>
      <CardFooter className="flex justify-between">
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleValidate}
            disabled={isValidating || validateMutation.isPending}
          >
            {validateMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Re-validate
          </Button>

          <Button
            variant="outline"
            onClick={handleResetMapping}
            disabled={isValidating || deleteMappingMutation.isPending}
            className="text-destructive hover:text-destructive"
          >
             {deleteMappingMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
               <Trash2 className="mr-2 h-4 w-4" />
            )}
            Reset Mapping
          </Button>
        </div>

        <Button
          onClick={handleContinue}
          disabled={
            isValidating ||
            validateMutation.isPending ||
            !validationResults ||
            editMode || // Don't allow continue while editing
            Object.keys(columnMappings).length === 0 || // Need some mappings
            validationResults.success_rate < passThreshold // Must meet threshold
          }
        >
          Continue to HTML Generation <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </CardFooter>

      {/* Type selection dialog */}
      <Dialog open={currentEditColumn !== null} onOpenChange={(open) => !open && setCurrentEditColumn(null)}>
        <DialogContent className="max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Select Type for Column</DialogTitle>
            <DialogDescription>
              Choose a field type to map to column "{currentEditColumn}"
            </DialogDescription>
          </DialogHeader>

          {currentEditColumn && (
            <div className="space-y-4 py-2">
              <div className="grid gap-2">
                <div className="border rounded-md overflow-auto max-h-[400px]">
                  {/* None option */}
                  <div
                    className="p-3 cursor-pointer hover:bg-muted border-b"
                    onClick={() => handleSetColumnType(currentEditColumn, "")} // Pass empty string for 'None'
                  >
                    <span className="text-muted-foreground">None (unmapped)</span>
                  </div>

                  {/* List of all field types from schema */}
                  {Object.entries(schemaFields)
                    .sort(([keyA], [keyB]) => keyA.localeCompare(keyB)) // Sort alphabetically by field name
                    .map(([fieldName, fieldInfo]) => (
                    <div
                      key={fieldName}
                      className={`p-3 cursor-pointer border-b hover:bg-muted ${
                        columnMappings[currentEditColumn!]?.type === fieldName ? 'bg-muted font-semibold' : '' // Use non-null assertion, safe here
                      }`}
                      onClick={() => handleSetColumnType(currentEditColumn!, fieldName)} // Use non-null assertion
                    >
                      <div className="font-bold">{fieldName}</div>
                      <div className="text-sm text-muted-foreground">
                        <span className="font-medium">Type:</span> {fieldInfo.validate_type}
                        {fieldInfo.required && <Badge className="ml-2" variant="destructive">Required</Badge>}
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        {fieldInfo.description}
                      </div>
                      {/* Optionally show more details like regex */}
                      {fieldInfo.regex && (
                        <div className="text-xs font-mono bg-muted p-1 mt-1 rounded">
                          Pattern: {fieldInfo.regex}
                        </div>
                      )}
                       {fieldInfo.list && (
                        <div className="text-xs font-mono bg-muted p-1 mt-1 rounded">
                          List: {fieldInfo.list} (Dist: {fieldInfo.distance || 'N/A'}%)
                        </div>
                      )}
                       {fieldInfo.enum && (
                        <div className="text-xs font-mono bg-muted p-1 mt-1 rounded">
                          Enum: {fieldInfo.enum}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Reset confirmation dialog */}
      <Dialog open={isResetConfirmOpen} onOpenChange={setIsResetConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset Field Mappings</DialogTitle>
            <DialogDescription>
              This will delete your current field mappings and generate new ones based on the initial validation.
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 mt-4">
            <Button variant="outline" onClick={() => setIsResetConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmResetMapping} disabled={deleteMappingMutation.isPending}>
              {deleteMappingMutation.isPending ?
                <Loader2 className="h-4 w-4 mr-2 animate-spin" /> :
                <Trash2 className="h-4 w-4 mr-2" />
              }
              Reset Mappings
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default ValidateStep;
