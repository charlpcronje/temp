// src/components/lookup/ExceptionsTable.tsx
import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Wrench } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { LookupException } from '@/types';

interface ExceptionsTableProps {
  exceptions: LookupException[];
  onResolve: (exceptionId: number) => void;
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const statusMap: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    'pending': { label: 'Pending', variant: 'outline' },
    'accepted': { label: 'Accepted', variant: 'default' },
    'rejected': { label: 'Rejected', variant: 'destructive' },
    'for_creation': { label: 'For Creation', variant: 'secondary' },
  };

  const { label, variant } = statusMap[status] || { label: status, variant: 'outline' };

  return <Badge variant={variant}>{label}</Badge>;
};

const ExceptionsTable: React.FC<ExceptionsTableProps> = ({ exceptions, onResolve }) => {
  if (!exceptions || exceptions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <AlertTriangle className="inline-block mb-2 h-8 w-8 text-amber-500" />
        <p>No exceptions to resolve.</p>
      </div>
    );
  }

  return (
    <div className="border rounded-md overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">ID</TableHead>
            <TableHead>Input File</TableHead>
            <TableHead>Row</TableHead>
            <TableHead>Lookup Type</TableHead>
            <TableHead>Lookup Value</TableHead>
            <TableHead>Exception</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-[100px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {exceptions.map((exception) => (
            <TableRow key={exception.id}>
              <TableCell className="font-medium">{exception.id}</TableCell>
              <TableCell className="max-w-[180px] truncate" title={exception.input_file}>
                {exception.input_file ? exception.input_file.split('/').pop() : '-'}
              </TableCell>
              <TableCell>{exception.row}</TableCell>
              <TableCell>{exception.lookup_type}</TableCell>
              <TableCell className="max-w-[180px] truncate" title={exception.lookup_value}>
                {exception.lookup_value}
              </TableCell>
              <TableCell className="max-w-[200px] truncate" title={exception.exception_message}>
                {exception.exception_message}
              </TableCell>
              <TableCell>
                <StatusBadge status={exception.status} />
              </TableCell>
              <TableCell>
                <Button 
                  onClick={() => onResolve(exception.id)}
                  variant="outline" 
                  size="sm" 
                  className="h-8 px-2 flex items-center"
                >
                  <Wrench className="mr-1 h-3 w-3" />
                  Resolve
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default ExceptionsTable;
