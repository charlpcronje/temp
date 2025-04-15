// src/components/lookup/LookupExceptionResolver.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { commandService } from '@/api/services';
import { LookupException, ExceptionResolutionRequest } from '@/types';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Spinner } from '@/components/ui/spinner';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, ArrowRight, CheckCircle, XCircle, Plus, Info, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface LookupExceptionResolverProps {
  isOpen: boolean;
  onClose: () => void;
  exceptionId: number | null;
  onResolved: () => void;
}

const KeyboardShortcutHelp: React.FC = () => (
  <div className="text-xs text-muted-foreground mt-4 border-t pt-2">
    <h4 className="font-medium mb-1">Keyboard Shortcuts:</h4>
    <div className="grid grid-cols-2 gap-1">
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">a</kbd>
        <span className="ml-1">Accept with value</span>
      </div>
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">r</kbd>
        <span className="ml-1">Reject exception</span>
      </div>
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">c</kbd>
        <span className="ml-1">Mark for creation</span>
      </div>
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">&#8592;</kbd>
        <span className="ml-1">Previous exception</span>
      </div>
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">&#8594;</kbd>
        <span className="ml-1">Next exception</span>
      </div>
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">b</kbd>
        <span className="ml-1">Apply to similar</span>
      </div>
    </div>
  </div>
);

const LookupExceptionResolver: React.FC<LookupExceptionResolverProps> = ({ 
  isOpen, 
  onClose, 
  exceptionId,
  onResolved 
}) => {
  const [exceptions, setExceptions] = useState<LookupException[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Resolution form state
  const [resolutionAction, setResolutionAction] = useState<'accept' | 'reject' | 'for_creation'>('accept');
  const [lookupValue, setLookupValue] = useState('');
  const [applyToSimilar, setApplyToSimilar] = useState(false);
  const [similarityOptions, setSimilarityOptions] = useState({
    lookup_type: true,
    lookup_field: true,
    exception_message: false
  });
  
  // Load exceptions on initial open
  useEffect(() => {
    if (isOpen) {
      loadExceptions();
    }
  }, [isOpen]);
  
  // Set current exception when exceptionId changes
  useEffect(() => {
    if (exceptionId && exceptions.length > 0) {
      const index = exceptions.findIndex(e => e.id === exceptionId);
      if (index !== -1) {
        setCurrentIndex(index);
      }
    }
  }, [exceptionId, exceptions]);
  
  // Reset form when current exception changes
  useEffect(() => {
    if (exceptions.length > 0) {
      const currentException = exceptions[currentIndex];
      setLookupValue(currentException.lookup_value || '');
      setResolutionAction('accept');
      setApplyToSimilar(false);
      
      // If we have potential matches, pre-populate with the first one
      if (currentException.potential_matches?.length) {
        setLookupValue(String(currentException.potential_matches[0].display));
      }
    }
  }, [currentIndex, exceptions]);
  
  const loadExceptions = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Only get pending exceptions
      const result = await commandService.getLookupExceptions('pending');
      setExceptions(result.exceptions || []);
      
      if (result.exceptions.length === 0) {
        setError('No pending exceptions to resolve');
      }
    } catch (err: any) {
      console.error('Error loading exceptions:', err);
      setError(err.message || 'Failed to load exceptions');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleNext = () => {
    if (currentIndex < exceptions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };
  
  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };
  
  const handleResolve = async () => {
    if (exceptions.length === 0) return;
    
    const currentException = exceptions[currentIndex];
    setIsResolving(true);
    setError(null);
    
    const resolution: ExceptionResolutionRequest = {
      accept: resolutionAction === 'accept',
      mark_for_creation: resolutionAction === 'for_creation',
      lookup_value: resolutionAction === 'accept' ? lookupValue : undefined,
      apply_to_similar: applyToSimilar,
      similarity_criteria: applyToSimilar ? similarityOptions : undefined
    };
    
    try {
      const result = await commandService.resolveLookupException(currentException.id, resolution);
      
      if (result.status === 'success') {
        // Update the local state to remove resolved exceptions
        setExceptions(prev => prev.filter(e => e.id !== currentException.id));
        
        // Show success message with count if batch resolved
        if (result.affected_count > 1) {
          toast({
            title: 'Exceptions Resolved',
            description: `Successfully resolved ${result.affected_count} similar exceptions`,
            duration: 3000
          });
        } else {
          toast({
            title: 'Exception Resolved',
            description: 'Successfully resolved the exception',
            duration: 2000
          });
        }
        
        // Notify parent component
        onResolved();
        
        // Move to next exception or close if done
        if (currentIndex >= exceptions.length - 1) {
          if (exceptions.length <= 1) {
            // If this was the last exception, close the dialog
            onClose();
          } else {
            // Otherwise, set the index to the new last item
            setCurrentIndex(exceptions.length - 2);
          }
        }
      } else {
        setError(result.message);
      }
    } catch (err: any) {
      console.error('Error resolving exception:', err);
      setError(err.message || 'Failed to resolve exception');
    } finally {
      setIsResolving(false);
    }
  };
  
  // Keyboard shortcut handler
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!isOpen) return;
    
    // Don't trigger shortcuts when typing in input fields
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
      return;
    }
    
    switch (e.key) {
      case 'ArrowRight':
        handleNext();
        break;
      case 'ArrowLeft':
        handlePrevious();
        break;
      case 'a':
        setResolutionAction('accept');
        // Focus the input field
        document.getElementById('lookup-value')?.focus();
        break;
      case 'r':
        setResolutionAction('reject');
        handleResolve();
        break;
      case 'c':
        setResolutionAction('for_creation');
        handleResolve();
        break;
      case 'b':
        setApplyToSimilar(!applyToSimilar);
        break;
      default:
        break;
    }
  }, [isOpen, handleNext, handlePrevious, resolutionAction, applyToSimilar, handleResolve]);
  
  // Set up keyboard shortcuts
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
  
  const currentException = exceptions[currentIndex];
  
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>
            Exception Resolution {exceptions.length > 0 && `(${currentIndex + 1}/${exceptions.length})`}
          </DialogTitle>
          <DialogDescription>
            Resolve lookup exceptions quickly with the tools below
          </DialogDescription>
        </DialogHeader>
        
        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <Spinner size="lg" />
            <span className="ml-2">Loading exceptions...</span>
          </div>
        ) : error && exceptions.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <AlertTriangle className="h-12 w-12 text-amber-500 mb-4" />
            <h3 className="text-lg font-medium mb-2">No Exceptions to Resolve</h3>
            <p className="text-muted-foreground mb-6">{error}</p>
            <Button onClick={onClose}>Close</Button>
          </div>
        ) : exceptions.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mb-4" />
            <h3 className="text-lg font-medium mb-2">All Exceptions Resolved</h3>
            <p className="text-muted-foreground mb-6">Great job! There are no more exceptions to resolve.</p>
            <Button onClick={onClose}>Close</Button>
          </div>
        ) : (
          <>
            {/* Main content: split view */}
            <div className="flex-1 flex flex-col md:flex-row gap-4 overflow-hidden">
              {/* Left panel: Document data */}
              <div className="w-full md:w-1/2 bg-muted/30 rounded-md p-4 overflow-y-auto">
                <h3 className="text-sm font-medium mb-2">Document Data</h3>
                <div className="space-y-2">
                  {currentException && Object.entries(currentException.data || {}).map(([key, value]) => (
                    <div key={key} className="grid grid-cols-2 text-sm">
                      <span className="font-medium">{key}</span>
                      <span>{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Right panel: Resolution options */}
              <div className="w-full md:w-1/2 flex flex-col overflow-hidden">
                <div className="mb-4">
                  <h3 className="text-sm font-medium mb-2">Exception Details</h3>
                  {currentException && (
                    <div className="space-y-2 text-sm">
                      <div className="grid grid-cols-2">
                        <span className="font-medium">Exception ID</span>
                        <span>{currentException.id}</span>
                      </div>
                      <div className="grid grid-cols-2">
                        <span className="font-medium">Lookup Type</span>
                        <span>{currentException.lookup_type}</span>
                      </div>
                      <div className="grid grid-cols-2">
                        <span className="font-medium">Lookup Field</span>
                        <span>{currentException.lookup_field}</span>
                      </div>
                      <div className="grid grid-cols-2">
                        <span className="font-medium">Lookup Value</span>
                        <span>{currentException.lookup_value}</span>
                      </div>
                      <div className="grid grid-cols-2">
                        <span className="font-medium">Error</span>
                        <span className="text-red-500">{currentException.exception_message}</span>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Potential matches */}
                {currentException && currentException.potential_matches && currentException.potential_matches.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium mb-2">Potential Matches</h3>
                    <div className="space-y-2">
                      {currentException.potential_matches.map((match, idx) => (
                        <div 
                          key={idx} 
                          className="flex items-center justify-between p-2 border rounded-md cursor-pointer hover:bg-muted/50"
                          onClick={() => {
                            setResolutionAction('accept');
                            setLookupValue(String(match.display));
                          }}
                        >
                          <span>{match.display}</span>
                          {match.score && (
                            <Badge variant="outline">{Math.round(match.score * 100)}%</Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Resolution form */}
                <div className="flex-1 overflow-y-auto">
                  <h3 className="text-sm font-medium mb-2">Resolve Exception</h3>
                  
                  <RadioGroup 
                    value={resolutionAction} 
                    onValueChange={(value) => setResolutionAction(value as any)}
                    className="mb-4"
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="accept" id="accept" />
                      <Label htmlFor="accept" className="cursor-pointer">Accept with value</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="reject" id="reject" />
                      <Label htmlFor="reject" className="cursor-pointer">Reject</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="for_creation" id="for_creation" />
                      <Label htmlFor="for_creation" className="cursor-pointer">Mark for entity creation</Label>
                    </div>
                  </RadioGroup>
                  
                  {resolutionAction === 'accept' && (
                    <div className="mb-4">
                      <Label htmlFor="lookup-value">Lookup Value</Label>
                      <Input 
                        id="lookup-value"
                        value={lookupValue}
                        onChange={(e) => setLookupValue(e.target.value)}
                        placeholder="Enter lookup value"
                        className="mt-1"
                        autoFocus
                      />
                    </div>
                  )}
                  
                  {/* Batch options */}
                  <div className="space-y-2 border-t pt-3 mt-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox 
                        id="apply-to-similar" 
                        checked={applyToSimilar}
                        onCheckedChange={(checked) => setApplyToSimilar(!!checked)}
                      />
                      <Label htmlFor="apply-to-similar" className="cursor-pointer">
                        Apply to similar exceptions
                      </Label>
                    </div>
                    
                    {applyToSimilar && (
                      <div className="pl-6 space-y-2 text-sm">
                        <div className="flex items-center space-x-2">
                          <Checkbox 
                            id="similarity-type" 
                            checked={similarityOptions.lookup_type}
                            onCheckedChange={(checked) => 
                              setSimilarityOptions({
                                ...similarityOptions,
                                lookup_type: !!checked
                              })
                            }
                          />
                          <Label htmlFor="similarity-type" className="cursor-pointer">
                            Same lookup type
                          </Label>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Checkbox 
                            id="similarity-field" 
                            checked={similarityOptions.lookup_field}
                            onCheckedChange={(checked) => 
                              setSimilarityOptions({
                                ...similarityOptions,
                                lookup_field: !!checked
                              })
                            }
                          />
                          <Label htmlFor="similarity-field" className="cursor-pointer">
                            Same lookup field
                          </Label>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Checkbox 
                            id="similarity-message" 
                            checked={similarityOptions.exception_message}
                            onCheckedChange={(checked) => 
                              setSimilarityOptions({
                                ...similarityOptions,
                                exception_message: !!checked
                              })
                            }
                          />
                          <Label htmlFor="similarity-message" className="cursor-pointer">
                            Same exception message
                          </Label>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <KeyboardShortcutHelp />
                </div>
              </div>
            </div>
            
            {/* Error message */}
            {error && (
              <div className="text-sm text-red-500 mt-2 mb-2">
                {error}
              </div>
            )}
            
            {/* Footer with navigation */}
            <DialogFooter className="flex items-center justify-between space-x-2">
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handlePrevious}
                  disabled={currentIndex <= 0}
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-muted-foreground">
                  {currentIndex + 1} of {exceptions.length}
                </span>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleNext}
                  disabled={currentIndex >= exceptions.length - 1}
                >
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleResolve} 
                  disabled={
                    isResolving || 
                    (resolutionAction === 'accept' && !lookupValue.trim())
                  }
                >
                  {isResolving ? (
                    <>
                      <Spinner className="mr-2 h-4 w-4" />
                      Resolving...
                    </>
                  ) : (
                    <>
                      {resolutionAction === 'accept' && <CheckCircle className="mr-2 h-4 w-4" />}
                      {resolutionAction === 'reject' && <XCircle className="mr-2 h-4 w-4" />}
                      {resolutionAction === 'for_creation' && <Plus className="mr-2 h-4 w-4" />}
                      {resolutionAction === 'accept' ? 'Accept' : 
                       resolutionAction === 'reject' ? 'Reject' : 'Mark for Creation'}
                    </>
                  )}
                </Button>
              </div>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default LookupExceptionResolver;
