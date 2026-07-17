import { useState } from 'react';
import { Box, Typography, TextField, Button, Paper, Tab, Tabs } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { graphragApi } from '../api/graphragApi';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';
import { GraphRAGContextResponse } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const GraphRAGExplorer = () => {
  const [query, setQuery] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const { enqueueSnackbar } = useSnackbar();

  const retrieveMutation = useMutation({
    mutationFn: graphragApi.getContext,
    onSuccess: () => {
      enqueueSnackbar('Context retrieved successfully', { variant: 'success' });
    },
    onError: (error: Error) => {
      enqueueSnackbar(error.message, { variant: 'error' });
    },
  });

  const handleRetrieve = () => {
    if (!query.trim()) {
      enqueueSnackbar('Please enter a query', { variant: 'warning' });
      return;
    }
    retrieveMutation.mutate(query);
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        GraphRAG Explorer
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Retrieve context using GraphRAG fusion of graph and vector retrieval.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <TextField
          fullWidth
          multiline
          rows={3}
          label="Search Query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={retrieveMutation.isPending}
          sx={{ mb: 2 }}
        />
        <Button
          variant="contained"
          startIcon={<SearchIcon />}
          onClick={handleRetrieve}
          disabled={retrieveMutation.isPending}
        >
          Retrieve Context
        </Button>
      </Paper>

      {retrieveMutation.isPending && <LoadingSpinner message="Retrieving context..." />}

      {retrieveMutation.isError && (
        <ErrorState
          message={retrieveMutation.error?.message || 'Failed to retrieve context'}
          onRetry={handleRetrieve}
        />
      )}

      {retrieveMutation.isSuccess && retrieveMutation.data && (
        <Paper>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Graph Retrieval" />
            <Tab label="Vector Retrieval" />
            <Tab label="Fusion Results" />
            <Tab label="Summary" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <Typography variant="h6" gutterBottom>
              Graph Results ({retrieveMutation.data.graph_results.length})
            </Typography>
            {retrieveMutation.data.graph_results.length > 0 ? (
              retrieveMutation.data.graph_results.map((result, idx) => (
                <Box key={idx} mb={2} p={2} sx={{ bgcolor: 'background.paper', borderRadius: 1 }}>
                  <Typography variant="body2" whiteSpace="pre-wrap">
                    {JSON.stringify(result, null, 2)}
                  </Typography>
                </Box>
              ))
            ) : (
              <Typography variant="body2" color="textSecondary">
                No graph results found.
              </Typography>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Typography variant="h6" gutterBottom>
              Vector Results ({retrieveMutation.data.vector_results.length})
            </Typography>
            {retrieveMutation.data.vector_results.length > 0 ? (
              retrieveMutation.data.vector_results.map((result, idx) => (
                <Box key={idx} mb={2} p={2} sx={{ bgcolor: 'background.paper', borderRadius: 1 }}>
                  <Typography variant="body2" whiteSpace="pre-wrap">
                    {JSON.stringify(result, null, 2)}
                  </Typography>
                </Box>
              ))
            ) : (
              <Typography variant="body2" color="textSecondary">
                No vector results found.
              </Typography>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Typography variant="h6" gutterBottom>
              Fusion Results
            </Typography>
            <Box mb={2}>
              <Typography variant="subtitle1">Merged Findings ({retrieveMutation.data.merged_findings.length})</Typography>
              {retrieveMutation.data.merged_findings.map((finding, idx) => (
                <Box key={idx} mb={1} p={2} sx={{ bgcolor: 'background.paper', borderRadius: 1 }}>
                  <Typography variant="body2" whiteSpace="pre-wrap">
                    {JSON.stringify(finding, null, 2)}
                  </Typography>
                </Box>
              ))}
            </Box>
            <Box mb={2}>
              <Typography variant="subtitle1">Merged Risks ({retrieveMutation.data.merged_risks.length})</Typography>
              {retrieveMutation.data.merged_risks.map((risk, idx) => (
                <Box key={idx} mb={1} p={2} sx={{ bgcolor: 'background.paper', borderRadius: 1 }}>
                  <Typography variant="body2" whiteSpace="pre-wrap">
                    {JSON.stringify(risk, null, 2)}
                  </Typography>
                </Box>
              ))}
            </Box>
            <Box>
              <Typography variant="subtitle1">Merged Recommendations ({retrieveMutation.data.merged_recommendations.length})</Typography>
              {retrieveMutation.data.merged_recommendations.map((rec, idx) => (
                <Box key={idx} mb={1} p={2} sx={{ bgcolor: 'background.paper', borderRadius: 1 }}>
                  <Typography variant="body2" whiteSpace="pre-wrap">
                    {JSON.stringify(rec, null, 2)}
                  </Typography>
                </Box>
              ))}
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Typography variant="h6" gutterBottom>
              Context Summary
            </Typography>
            <Typography variant="body1" whiteSpace="pre-wrap">
              {retrieveMutation.data.context_summary || 'No summary available.'}
            </Typography>
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
              Retrieval Metadata
            </Typography>
            <Typography variant="body2" whiteSpace="pre-wrap">
              {JSON.stringify(retrieveMutation.data.retrieval_metadata, null, 2)}
            </Typography>
          </TabPanel>
        </Paper>
      )}
    </Box>
  );
};
