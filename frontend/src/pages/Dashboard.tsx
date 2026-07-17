import { useState } from 'react';
import { Box, TextField, Button, Typography, Paper } from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { workflowApi } from '../api/workflowApi';
import { WorkflowResult } from '../components/WorkflowResult';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';

export const Dashboard = () => {
  const [query, setQuery] = useState('');
  const { enqueueSnackbar } = useSnackbar();

  const executeMutation = useMutation({
    mutationFn: workflowApi.execute,
    onSuccess: (data) => {
      enqueueSnackbar('Workflow executed successfully', { variant: 'success' });
    },
    onError: (error: Error) => {
      enqueueSnackbar(error.message, { variant: 'error' });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      enqueueSnackbar('Please enter a query', { variant: 'warning' });
      return;
    }
    executeMutation.mutate({ query });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Ask Something
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Enter your query to execute the super-agent workflow and receive findings, risks, and recommendations.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Enter your query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={executeMutation.isPending}
            sx={{ mb: 2 }}
          />
          <Button
            type="submit"
            variant="contained"
            size="large"
            startIcon={<SendIcon />}
            disabled={executeMutation.isPending}
            fullWidth
          >
            Execute 
          </Button>
        </form>
      </Paper>

      {executeMutation.isPending && <LoadingSpinner message="Working..." />}

      {executeMutation.isError && (
        <ErrorState
          message={executeMutation.error?.message || 'Failed to execute workflow'}
          onRetry={() => executeMutation.mutate({ query })}
        />
      )}

      {executeMutation.isSuccess && executeMutation.data && (
        <WorkflowResult result={executeMutation.data} />
      )}
    </Box>
  );
};
