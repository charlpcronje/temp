// src/components/lookup/DocumentsTable.tsx
import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Document {
  id: number;
  document_id: number;
  input_file: string;
  row: number;
  lookup_type: string;
  lookup_field: string;
  lookup_value: string;
  lookup_match?: string | null;
  status: string;
  [key: string]: any; // For other dynamic fields
}

interface DocumentsTableProps {
  documents: Document[];
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const statusMap: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    'pending': { label: 'Pending', variant: 'outline' },
    'matched': { label: 'Matched', variant: 'default' },
    'exception': { label: 'Exception', variant: 'destructive' },
    'accepted': { label: 'Accepted', variant: 'default' },
    'rejected': { label: 'Rejected', variant: 'destructive' },
    'for_creation': { label: 'For Creation', variant: 'secondary' },
  };

  const { label, variant } = statusMap[status] || { label: status, variant: 'outline' };

  return <Badge variant={variant}>{label}</Badge>;
};

const DocumentsTable: React.FC<DocumentsTableProps> = ({ documents }) => {
  if (!documents || documents.length === 0) {
    return <div className="text-center py-8 text-muted-foreground">No documents found.</div>;
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
            <TableHead>Match</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-12">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.map((doc) => (
            <TableRow key={doc.id}>
              <TableCell className="font-medium">{doc.document_id || doc.id}</TableCell>
              <TableCell className="max-w-[180px] truncate" title={doc.input_file}>
                {doc.input_file ? doc.input_file.split('/').pop() : '-'}
              </TableCell>
              <TableCell>{doc.row}</TableCell>
              <TableCell>{doc.lookup_type}</TableCell>
              <TableCell className="max-w-[180px] truncate" title={doc.lookup_value}>
                {doc.lookup_value}
              </TableCell>
              <TableCell className="max-w-[180px] truncate" title={doc.lookup_match || ''}>
                {doc.lookup_match || '-'}
              </TableCell>
              <TableCell>
                <StatusBadge status={doc.status} />
              </TableCell>
              <TableCell>
                <Button variant="ghost" size="icon" title="View Document">
                  <Eye className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default DocumentsTable;
