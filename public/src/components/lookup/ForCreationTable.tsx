// src/components/lookup/ForCreationTable.tsx
import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { LookupException } from '@/types';

interface ForCreationTableProps {
  documents: LookupException[];
}

const ForCreationTable: React.FC<ForCreationTableProps> = ({ documents }) => {
  if (!documents || documents.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Plus className="inline-block mb-2 h-8 w-8 text-blue-500" />
        <p>No documents marked for entity creation.</p>
      </div>
    );
  }

  // Group documents by lookup type and value for more efficient display
  const groupedDocuments = documents.reduce((acc, doc) => {
    const key = `${doc.lookup_type}:${doc.lookup_value}`;
    if (!acc[key]) {
      acc[key] = {
        lookup_type: doc.lookup_type,
        lookup_value: doc.lookup_value,
        count: 0,
        documents: []
      };
    }
    acc[key].count += 1;
    acc[key].documents.push(doc);
    return acc;
  }, {} as Record<string, { lookup_type: string; lookup_value: string; count: number; documents: LookupException[] }>);

  return (
    <div className="border rounded-md overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Entity Type</TableHead>
            <TableHead>Value</TableHead>
            <TableHead className="w-24">Count</TableHead>
            <TableHead className="w-[180px]">Sample Data</TableHead>
            <TableHead className="w-[100px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.values(groupedDocuments).map((group, index) => (
            <TableRow key={index}>
              <TableCell className="font-medium">{group.lookup_type}</TableCell>
              <TableCell className="max-w-[180px] truncate" title={group.lookup_value}>
                {group.lookup_value}
              </TableCell>
              <TableCell>
                <Badge variant="secondary">{group.count}</Badge>
              </TableCell>
              <TableCell>
                {group.documents[0] && (
                  <div className="max-w-[180px] max-h-[100px] overflow-auto text-xs">
                    <pre className="whitespace-pre-wrap">
                      {JSON.stringify(
                        Object.fromEntries(
                          Object.entries(group.documents[0].data).slice(0, 3)
                        ), 
                        null, 
                        1
                      )}
                      {Object.keys(group.documents[0].data).length > 3 && '...'}
                    </pre>
                  </div>
                )}
              </TableCell>
              <TableCell>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="h-8 px-2 flex items-center"
                >
                  <Plus className="mr-1 h-3 w-3" />
                  Create
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default ForCreationTable;
