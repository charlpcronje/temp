// src/components/workflow/EntityCreationStep.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { commandService } from '@/api/services';
import { CommandResponse, EntitiesForCreationResult, Entity, EntityCreationResult } from '@/types';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle, CheckCircle, FileText, Database } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface EntityCreationStepProps {
  onComplete: (result: CommandResponse) => void;
}

const EntityCreationStep: React.FC<EntityCreationStepProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entities, setEntities] = useState<EntitiesForCreationResult>({ entities: [], total: 0 });
  const [selectedEntityIndex, setSelectedEntityIndex] = useState<number | null>(null);
  const [entityForm, setEntityForm] = useState<Entity>({
    entity_type: '',
    name: '',
    properties: {}
  });
  
  useEffect(() => {
    loadEntitiesForCreation();
  }, []);
  
  const loadEntitiesForCreation = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await commandService.getEntitiesForCreation();
      setEntities(result);
      
      if (result.entities.length > 0) {
        // Pre-select the first entity
        selectEntity(0);
      }
    } catch (err: any) {
      console.error('Error loading entities for creation:', err);
      setError(err.message || 'Failed to load entities for creation');
    } finally {
      setIsLoading(false);
    }
  };
  
  const selectEntity = (index: number) => {
    if (index >= 0 && index < entities.entities.length) {
      setSelectedEntityIndex(index);
      const entityData = entities.entities[index];
      
      // Initialize the form with entity data
      setEntityForm({
        entity_type: entityData.entity_type,
        name: entityData.lookup_value,
        properties: { ...entityData.sample_data }
      });
    }
  };
  
  const handleInputChange = (field: string, value: string) => {
    if (field === 'name') {
      setEntityForm({ ...entityForm, name: value });
    } else {
      setEntityForm({
        ...entityForm,
        properties: {
          ...entityForm.properties,
          [field]: value
        }
      });
    }
  };
  
  const handleCreateEntity = async () => {
    if (selectedEntityIndex === null) return;
    
    setIsCreating(true);
    setError(null);
    
    try {
      const result = await commandService.createEntity(entityForm);
      
      if (result.status === 'success') {
        toast({
          title: 'Entity Created',
          description: `Successfully created ${entityForm.entity_type} entity: ${entityForm.name}`,
          duration: 3000
        });
        
        // Remove the created entity from the list
        const updatedEntities = [...entities.entities];
        updatedEntities.splice(selectedEntityIndex, 1);
        
        setEntities({
          entities: updatedEntities,
          total: updatedEntities.length
        });
        
        // Select the next entity or reset if none left
        if (updatedEntities.length > 0) {
          selectEntity(selectedEntityIndex < updatedEntities.length ? selectedEntityIndex : 0);
        } else {
          setSelectedEntityIndex(null);
        }
      } else {
        setError(result.message);
      }
    } catch (err: any) {
      console.error('Error creating entity:', err);
      setError(err.message || 'Failed to create entity');
    } finally {
      setIsCreating(false);
    }
  };
  
  const handleCreateAll = async () => {
    // This would handle batch creation of all entities
    // For now, we'll just show a toast message
    toast({
      title: 'Batch Creation',
      description: 'Batch entity creation feature is coming soon',
      duration: 3000
    });
  };
  
  const goBack = () => {
    navigate('/workflow/lookups');
  };
  
  const goNext = () => {
    navigate('/workflow/sync');
    
    // Call onComplete with a success result
    onComplete({
      success: true,
      command: 'entity_creation',
      result: { status: 'success', message: 'Entity creation completed' }
    });
  };
  
  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <Spinner size="lg" />
            <span className="ml-2">Loading entities for creation...</span>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Entity Creation</CardTitle>
        <CardDescription>Create missing entities from lookup exceptions</CardDescription>
      </CardHeader>
      
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {entities.entities.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No Entities to Create</h3>
            <p className="text-muted-foreground">
              There are no entities marked for creation. You can proceed to the next step.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Entity List */}
            <div className="md:col-span-1 border rounded-md overflow-hidden">
              <div className="bg-muted p-3 border-b">
                <h3 className="font-medium">Entities for Creation ({entities.total})</h3>
              </div>
              <div className="overflow-auto max-h-[400px]">
                <Table>
                  <TableBody>
                    {entities.entities.map((entity, index) => (
                      <TableRow 
                        key={index}
                        className={selectedEntityIndex === index ? 'bg-muted' : ''}
                        onClick={() => selectEntity(index)}
                      >
                        <TableCell>
                          <div className="font-medium">{entity.lookup_value}</div>
                          <div className="text-xs text-muted-foreground">{entity.entity_type}</div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge>{entity.exception_count}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              
              <div className="p-3 border-t">
                <Button 
                  variant="outline" 
                  className="w-full" 
                  onClick={handleCreateAll}
                >
                  <Database className="mr-2 h-4 w-4" />
                  Create All
                </Button>
              </div>
            </div>
            
            {/* Entity Form */}
            <div className="md:col-span-2 border rounded-md overflow-hidden">
              {selectedEntityIndex !== null ? (
                <>
                  <div className="bg-muted p-3 border-b">
                    <h3 className="font-medium">
                      Create {entityForm.entity_type}: {entityForm.name}
                    </h3>
                  </div>
                  
                  <div className="p-4 space-y-4 overflow-auto max-h-[400px]">
                    <div>
                      <Label htmlFor="entity-name">Entity Name</Label>
                      <Input 
                        id="entity-name"
                        value={entityForm.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        className="mt-1"
                      />
                    </div>
                    
                    <div className="border-t pt-3">
                      <h4 className="text-sm font-medium mb-2">Properties</h4>
                      <div className="space-y-3">
                        {Object.entries(entityForm.properties).map(([key, value]) => (
                          <div key={key}>
                            <Label htmlFor={`property-${key}`}>{key}</Label>
                            <Input 
                              id={`property-${key}`}
                              value={value as string}
                              onChange={(e) => handleInputChange(key, e.target.value)}
                              className="mt-1"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-3 border-t flex justify-end">
                    <Button 
                      onClick={handleCreateEntity}
                      disabled={isCreating || !entityForm.name.trim()}
                    >
                      {isCreating ? (
                        <>
                          <Spinner className="mr-2 h-4 w-4" />
                          Creating...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Create Entity
                        </>
                      )}
                    </Button>
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center py-12 px-4 text-center">
                  <div>
                    <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">No Entity Selected</h3>
                    <p className="text-muted-foreground">
                      Select an entity from the list to create it.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={goBack}>Back</Button>
        <Button onClick={goNext}>
          Next: Data Sync
        </Button>
      </CardFooter>
    </Card>
  );
};

export default EntityCreationStep;
