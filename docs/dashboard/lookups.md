# Web UI Specification: Document Lookup System

## 1. Overview

This specification outlines the UI components and interactions required to implement the lookup resolution system within the DocTypeGen dashboard. The system allows users to resolve lookups between generated documents and external data sources, with special attention to exception handling and entity creation.

## 2. Workflow Integration

### 2.1. Updated Workflow Steps

The workflow will be expanded to include the following steps:

1. **Import** - Upload CSV/Excel file
2. **Validate** - Validate data format
3. **Map** - Map fields to document template
4. **HTML** - Generate HTML documents
5. **PDF** - Generate PDF documents (optional)
6. **Lookups** - Resolve lookups against external data
7. **Entity Creation** - Create missing entities (future)
8. **Data Sync** - Sync to tenant database (future)
9. **Storage** - Move to S3 storage (future)
10. **Complete** - Process complete

## 3. Lookup Resolution Experience

### 3.1. Lookup Resolution Dashboard

The main lookup resolution interface will include four key sections:

1. **Status Overview** - Visual summary of lookup status
2. **Actions Panel** - Controls for initiating and managing lookups
3. **Results Tabs** - Categorized view of documents by lookup status
4. **Exception Management** - Interface for resolving exceptions

![Lookup Dashboard Mockup](../assets/lookup_dashboard_mockup.png)

### 3.2. Exception Resolution Interface

The exception resolution interface is designed for efficiency and clarity, allowing users to quickly process exceptions with minimal clicks:

#### 3.2.1. Quick Resolution Panel

A specialized interface for rapid exception handling that features:

1. **Keyboard Shortcuts** - Hotkeys for common actions (accept, reject, next, previous)
2. **Batch Operations** - Apply the same resolution to multiple similar exceptions
3. **Smart Suggestions** - AI-assisted suggestions for resolving similar exceptions 
4. **Context Preservation** - Remembers user decisions for similar patterns

#### 3.2.2. Resolution Workflow

1. Exceptions are presented in a queue-like interface
2. Each exception shows:
   - Source document data
   - Exception reason (no match, multiple matches, etc.)
   - Potential matches (when available)
   - Suggested action

3. Users can take one of these actions:
   - **Accept Match** - Accept one of the suggested matches
   - **Provide Value** - Enter a custom lookup value
   - **Create Entity** - Mark for entity creation in the next step
   - **Reject** - Mark as invalid/rejected
   - **Skip** - Defer decision to later

4. After each action, automatically advances to the next exception
   
#### 3.2.3. Visual Design

- **Split-Panel Layout**
   - Left: Source document data display
   - Right: Resolution options and actions
   - Bottom: Navigation and batch controls

- **Color-Coding System**
   - Green: Successful matches
   - Amber: Pending resolution
   - Red: Rejected
   - Blue: Marked for entity creation

## 4. Component Specifications

### 4.1. Lookup Resolution Step (`LookupResolutionStep.tsx`)

Primary component for handling lookups with the following sections:

```jsx
<Card>
  <CardHeader>
    <CardTitle>Lookup Resolution</CardTitle>
    <CardDescription>Match documents to external data sources</CardDescription>
  </CardHeader>
  
  {/* Status Overview */}
  <CardContent>
    <div className="grid grid-cols-4 gap-4 mb-6">
      <StatusCard title="Total Documents" value={stats.total} icon={<FileIcon />} />
      <StatusCard title="Resolved" value={stats.resolved} icon={<CheckIcon />} color="green" />
      <StatusCard title="Exceptions" value={stats.exceptions} icon={<AlertTriangleIcon />} color="amber" />
      <StatusCard title="For Creation" value={stats.forCreation} icon={<PlusCircleIcon />} color="blue" />
    </div>
    
    {/* Actions Panel */}
    <div className="flex space-x-4 mb-6">
      <Button 
        onClick={handleResolve} 
        disabled={isResolving || stats.total === 0}
      >
        {isResolving ? (
          <>
            <Spinner className="mr-2 h-4 w-4" />
            Resolving...
          </>
        ) : (
          <>
            <PlayIcon className="mr-2 h-4 w-4" />
            Resolve Lookups
          </>
        )}
      </Button>
      
      {stats.exceptions > 0 && (
        <Button variant="outline" onClick={openExceptionResolver}>
          <WrenchIcon className="mr-2 h-4 w-4" />
          Resolve Exceptions
        </Button>
      )}
    </div>
    
    {/* Results Tabs */}
    <Tabs defaultValue="all">
      <TabsList>
        <TabsTrigger value="all">All Documents ({stats.total})</TabsTrigger>
        <TabsTrigger value="resolved">Resolved ({stats.resolved})</TabsTrigger>
        <TabsTrigger value="exceptions">Exceptions ({stats.exceptions})</TabsTrigger>
        <TabsTrigger value="creation">For Creation ({stats.forCreation})</TabsTrigger>
      </TabsList>
      
      <TabsContent value="all">
        <DocumentsTable documents={allDocuments} />
      </TabsContent>
      
      <TabsContent value="resolved">
        <DocumentsTable documents={resolvedDocuments} />
      </TabsContent>
      
      <TabsContent value="exceptions">
        <ExceptionsTable 
          exceptions={exceptions} 
          onResolve={openExceptionResolverWithId} 
        />
      </TabsContent>
      
      <TabsContent value="creation">
        <ForCreationTable documents={forCreationDocuments} />
      </TabsContent>
    </Tabs>
  </CardContent>
  
  <CardFooter className="flex justify-between">
    <Button variant="outline" onClick={goBack}>Back</Button>
    <Button onClick={goNext} disabled={!canProceed}>Next</Button>
  </CardFooter>
</Card>
```

### 4.2. Exception Resolver (`ExceptionResolver.tsx`)

Specialized interface for efficient exception handling:

```jsx
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
    <DialogHeader>
      <DialogTitle>
        Exception Resolution ({currentIndex + 1}/{exceptions.length})
      </DialogTitle>
      <DialogDescription>
        Resolve lookup exceptions quickly with the tools below
      </DialogDescription>
    </DialogHeader>
    
    {/* Main content: split view */}
    <div className="flex-1 flex flex-col md:flex-row gap-4 overflow-hidden">
      {/* Left panel: Document data */}
      <div className="w-full md:w-1/2 bg-muted/30 rounded-md p-4 overflow-y-auto">
        <h3 className="text-sm font-medium mb-2">Document Data</h3>
        <div className="space-y-2">
          {Object.entries(currentException.data).map(([key, value]) => (
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
          <Alert>
            <AlertTriangleIcon className="h-4 w-4" />
            <AlertTitle>{currentException.action}</AlertTitle>
            <AlertDescription>{currentException.exception_message}</AlertDescription>
          </Alert>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <h3 className="text-sm font-medium mb-2">Potential Matches</h3>
          {potentialMatches.length > 0 ? (
            <div className="space-y-2">
              {potentialMatches.map(match => (
                <div 
                  key={match.id} 
                  className="p-3 border rounded-md cursor-pointer hover:bg-accent"
                  onClick={() => handleAcceptMatch(match.id)}
                >
                  <div className="flex justify-between">
                    <span className="font-medium">{match.name}</span>
                    <Badge>{match.matchScore}%</Badge>
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {Object.entries(match.preview).map(([k, v]) => (
                      <span key={k} className="mr-3">{k}: {v}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center p-4 text-muted-foreground">
              No potential matches found
            </div>
          )}
        </div>
        
        <div className="mt-4">
          <h3 className="text-sm font-medium mb-2">Custom Value</h3>
          <div className="flex space-x-2 mb-4">
            <Input 
              value={customValue} 
              onChange={e => setCustomValue(e.target.value)} 
              placeholder="Enter lookup value"
            />
            <Button 
              onClick={() => handleAcceptCustom(customValue)}
              disabled={!customValue}
            >
              Apply
            </Button>
          </div>
        </div>
        
        <div className="mt-4 flex space-x-2">
          <Button 
            variant="outline" 
            className="flex-1"
            onClick={handleCreateEntity}
          >
            <PlusCircleIcon className="mr-2 h-4 w-4" />
            Create Entity
          </Button>
          <Button 
            variant="outline" 
            className="flex-1"
            onClick={handleReject}
          >
            <XIcon className="mr-2 h-4 w-4" />
            Reject
          </Button>
        </div>
      </div>
    </div>
    
    {/* Bottom panel: Navigation and batch controls */}
    <div className="mt-4 border-t pt-4">
      <div className="flex justify-between items-center">
        <div className="flex space-x-2">
          <Button
            variant="outline" 
            size="sm"
            onClick={handlePrevious}
            disabled={currentIndex === 0}
          >
            <ChevronLeftIcon className="h-4 w-4" />
            Previous
          </Button>
          <Button
            variant="outline" 
            size="sm"
            onClick={handleNext}
            disabled={currentIndex === exceptions.length - 1}
          >
            Next
            <ChevronRightIcon className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="text-sm text-muted-foreground">
          <kbd className="px-2 py-1 bg-muted rounded">←/→</kbd> Navigate
          <span className="mx-2">|</span>
          <kbd className="px-2 py-1 bg-muted rounded">A</kbd> Accept
          <span className="mx-2">|</span>
          <kbd className="px-2 py-1 bg-muted rounded">R</kbd> Reject
          <span className="mx-2">|</span>
          <kbd className="px-2 py-1 bg-muted rounded">C</kbd> Create
        </div>
        
        <Button variant="outline" size="sm" onClick={handleBatchApply} disabled={!selectedBatch}>
          <CheckIcon className="mr-2 h-4 w-4" />
          Apply to Similar ({similarCount})
        </Button>
      </div>
    </div>
  </DialogContent>
</Dialog>
```

### 4.3. Entity Creation Step (`EntityCreationStep.tsx`)

Placeholder component for the entity creation step:

```jsx
<Card>
  <CardHeader>
    <CardTitle>Entity Creation</CardTitle>
    <CardDescription>Create missing entities from exceptions</CardDescription>
  </CardHeader>
  
  <CardContent>
    <div className="mb-6">
      <Alert>
        <InfoIcon className="h-4 w-4" />
        <AlertTitle>Create Missing Entities</AlertTitle>
        <AlertDescription>
          The following entities need to be created based on exceptions from the lookup step.
          Once created, you will be able to resolve the remaining lookups.
        </AlertDescription>
      </Alert>
    </div>
    
    <Tabs defaultValue="list">
      <TabsList>
        <TabsTrigger value="list">Entity List ({entitiesToCreate.length})</TabsTrigger>
        <TabsTrigger value="creation">Entity Creation</TabsTrigger>
      </TabsList>
      
      <TabsContent value="list">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Select</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Source Value</TableHead>
              <TableHead>Exception</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entitiesToCreate.map(entity => (
              <TableRow key={entity.id}>
                <TableCell>
                  <Checkbox 
                    checked={selectedEntities.includes(entity.id)}
                    onCheckedChange={() => toggleEntitySelection(entity.id)} 
                  />
                </TableCell>
                <TableCell>{entity.type}</TableCell>
                <TableCell>{entity.sourceValue}</TableCell>
                <TableCell>{entity.exceptionMessage}</TableCell>
                <TableCell>
                  <LookupBadge status={entity.status} />
                </TableCell>
                <TableCell>
                  <Button size="sm" onClick={() => handleCreateSingle(entity.id)}>
                    Create
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TabsContent>
      
      <TabsContent value="creation">
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Create New Entity</h3>
          <EntityCreationForm 
            entityType={selectedEntityType} 
            onSubmit={handleEntitySubmit} 
          />
        </div>
      </TabsContent>
    </Tabs>
  </CardContent>
  
  <CardFooter className="flex justify-between">
    <Button variant="outline" onClick={goToLookups}>Back to Lookups</Button>
    <Button 
      onClick={handleBatchCreate} 
      disabled={selectedEntities.length === 0}
    >
      Create Selected ({selectedEntities.length})
    </Button>
  </CardFooter>
</Card>
```

## 5. API Integration

### 5.1. API Endpoints

```typescript
// Add to commandService
export const commandService = {
  // ... existing methods
  
  resolveLookups: async (): Promise<LookupResolutionResult> => {
    const response = await apiClient.post<LookupResolutionResult>('/run/resolve-lookups');
    return response.data;
  },
  
  getLookupExceptions: async (
    filters?: { status?: number, type?: string }
  ): Promise<LookupExceptionsList> => {
    const response = await apiClient.get<LookupExceptionsList>(
      '/lookups/exceptions', 
      { params: filters }
    );
    return response.data;
  },
  
  resolveLookupException: async (
    exceptionId: number, 
    resolution: { accept: boolean, lookupValue?: string }
  ): Promise<CommandResponse> => {
    const response = await apiClient.post<CommandResponse>(
      `/lookups/exceptions/${exceptionId}/resolve`, 
      resolution
    );
    return response.data;
  },
  
  // Entity Creation APIs
  getEntitiesForCreation: async (): Promise<EntityCreationList> => {
    const response = await apiClient.get<EntityCreationList>('/entities/pending');
    return response.data;
  },
  
  createEntity: async (
    entityData: any
  ): Promise<CommandResponse> => {
    const response = await apiClient.post<CommandResponse>(
      '/entities/create', 
      entityData
    );
    return response.data;
  }
};
```

## 6. User Experience Details

### 6.1. Exception Resolution Flow

The exception resolution interface is designed to minimize friction and maximize efficiency:

1. **Single-key Actions**
   - Press `A` to accept the top match
   - Press `R` to reject the exception
   - Press `C` to send to entity creation
   - Press `→` and `←` to navigate between exceptions

2. **Smart Batching**
   - System identifies similar exceptions (same field, similar error)
   - "Apply to Similar" button applies the same resolution to all similar exceptions
   - Preview shows which exceptions will be affected

3. **Context Preservation**
   - The system remembers previous user decisions
   - Offers intelligent defaults based on previous choices
   - Recognizes patterns in user resolutions

### 6.2. Visual Contextual Cues

1. **Color-coded Status Indicators**
   - Green: Successful matches
   - Amber: Pending resolution
   - Red: Rejected/errors
   - Blue: For entity creation

2. **Progress Tracking**
   - Circular progress indicator shows overall completion
   - Mini-stats show counts by category
   - Notification badges highlight new exceptions

### 6.3. Performance Considerations

1. **Pagination & Virtualization**
   - Large exception lists use virtualized rendering
   - Results paginated in groups of 50
   - Background loading of next/previous pages

2. **Offline Capability**
   - Resolution decisions can be made offline
   - Changes queued and synced when connection restored
   - Local storage backup of in-progress resolutions

## 7. Mobile Responsiveness

The interface adapts to smaller screens with:

1. **Stacked Layouts**
   - Document data and resolution options stack vertically on mobile
   - Swipe gestures for navigating between exceptions
  
2. **Touch-friendly Controls**
   - Larger touch targets for mobile
   - Swipe actions for accept/reject
   - Bottom navigation bar for common actions

## 8. Accessibility Features

1. **Keyboard Navigation**
   - Complete keyboard control of resolution workflow
   - Focus management between panels
   - Screen reader announcements for resolutions

2. **High Contrast Mode**
   - Alternative color schemes for color-blind users
   - Text-based indicators alongside color coding
   - Adjustable text size throughout interface

## 9. Future Enhancements

1. **AI-assisted Resolution**
   - Machine learning to suggest resolutions based on patterns
   - Automatic categorization of similar exceptions
   - Proactive suggestions for entity creation fields

2. **Advanced Filtering**
   - Filter exceptions by field, value, or pattern
   - Save custom filter presets
   - Smart grouping of related exceptions

This specification provides a comprehensive plan for implementing an intuitive and efficient lookup resolution system in the DocTypeGen dashboard.
