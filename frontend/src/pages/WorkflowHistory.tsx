import { useState } from 'react';
import { Box, Typography, TextField, Card, CardContent } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useQuery } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { memoryApi } from '../api/memoryApi';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';
import { WorkflowMemoryItem } from '../types';

export const WorkflowHistory = () => {
  const [search, setSearch] = useState('');
  const { enqueueSnackbar } = useSnackbar();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['workflowHistory', search],
    queryFn: () => memoryApi.getRecentWorkflows(50, search || undefined),
  });

  const columns: GridColDef<WorkflowMemoryItem>[] = [
    { field: 'id', headerName: 'Workflow ID', width: 120 },
    { field: 'query', headerName: 'Query', width: 300, flex: 1 },
    { field: 'task_type', headerName: 'Task Type', width: 150 },
    { field: 'timestamp', headerName: 'Timestamp', width: 180 },
    { field: 'execution_time', headerName: 'Execution Time (s)', width: 140, type: 'number' },
    { field: 'agents_used', headerName: 'Agents', width: 200, renderCell: (params) => params.value.join(', ') },
    { field: 'graph_results_count', headerName: 'Graph Results', width: 120, type: 'number' },
    { field: 'vector_results_count', headerName: 'Vector Results', width: 120, type: 'number' },
    { field: 'fusion_results_count', headerName: 'Fusion Results', width: 120, type: 'number' },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Workflow History
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        View and search through your past workflow executions.
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <TextField
            fullWidth
            label="Search workflows"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by query or task type..."
          />
        </CardContent>
      </Card>

      {isLoading && <LoadingSpinner />}

      {isError && (
        <ErrorState
          message={error?.message || 'Failed to load workflow history'}
          onRetry={() => refetch()}
        />
      )}

      {data && (
        <Box sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={data.workflows}
            columns={columns}
            pageSizeOptions={[10, 25, 50]}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 25 },
              },
            }}
            disableRowSelectionOnClick
          />
        </Box>
      )}
    </Box>
  );
};
