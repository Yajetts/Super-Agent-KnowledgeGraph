import { Box, Typography, Grid } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { memoryApi } from '../api/memoryApi';
import { graphApi } from '../api/graphApi';
import { graphragApi } from '../api/graphragApi';
import { vectorApi } from '../api/vectorApi';
import { learningApi } from '../api/learningApi';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';
import { MetricCard } from '../components/MetricCard';
import { Storage as StorageIcon, Memory as MemoryIcon, SmartToy as SmartToyIcon, School as SchoolIcon, Hub as HubIcon, TrendingUp as TrendingUpIcon } from '@mui/icons-material';

export const SystemMonitor = () => {
  const memoryQuery = useQuery({
    queryKey: ['memoryStats'],
    queryFn: memoryApi.getStats,
  });

  const graphQuery = useQuery({
    queryKey: ['graphStats'],
    queryFn: graphApi.getStats,
  });

  const graphragQuery = useQuery({
    queryKey: ['graphragStats'],
    queryFn: graphragApi.getStats,
  });

  const vectorQuery = useQuery({
    queryKey: ['vectorStats'],
    queryFn: vectorApi.getStats,
  });

  const learningQuery = useQuery({
    queryKey: ['learningStats'],
    queryFn: learningApi.getStats,
  });

  const isLoading = memoryQuery.isLoading || graphQuery.isLoading || graphragQuery.isLoading || 
                   vectorQuery.isLoading || learningQuery.isLoading;

  const isError = memoryQuery.isError || graphQuery.isError || graphragQuery.isError || 
                  vectorQuery.isError || learningQuery.isError;

  const error = memoryQuery.error || graphQuery.error || graphragQuery.error || 
                vectorQuery.error || learningQuery.error;

  const refetchAll = () => {
    memoryQuery.refetch();
    graphQuery.refetch();
    graphragQuery.refetch();
    vectorQuery.refetch();
    learningQuery.refetch();
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading system statistics..." />;
  }

  if (isError) {
    return <ErrorState message={error?.message || 'Failed to load system statistics'} onRetry={refetchAll} />;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Monitor
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Monitor system health and statistics across all components.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Total Workflows"
            value={memoryQuery.data?.workflows || 0}
            icon={<MemoryIcon />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Agent Executions"
            value={memoryQuery.data?.agent_executions || 0}
            icon={<SmartToyIcon />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Retrieval Records"
            value={memoryQuery.data?.retrieval_records || 0}
            icon={<StorageIcon />}
            color="#ed6c02"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Graph Nodes"
            value={graphQuery.data?.tasks || 0}
            icon={<HubIcon />}
            color="#9c27b0"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Vector Documents"
            value={vectorQuery.data?.documents || 0}
            icon={<StorageIcon />}
            color="#e91e63"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Learning Patterns"
            value={learningQuery.data?.patterns || 0}
            icon={<SchoolIcon />}
            color="#00bcd4"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Graph Available"
            value={graphragQuery.data?.graph_available ? 'Yes' : 'No'}
            icon={<HubIcon />}
            color={graphragQuery.data?.graph_available ? '#2e7d32' : '#d32f2f'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Vector Available"
            value={graphragQuery.data?.vector_available ? 'Yes' : 'No'}
            icon={<StorageIcon />}
            color={graphragQuery.data?.vector_available ? '#2e7d32' : '#d32f2f'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Successful Patterns"
            value={learningQuery.data?.successful_patterns || 0}
            icon={<TrendingUpIcon />}
            color="#ff9800"
          />
        </Grid>
      </Grid>
    </Box>
  );
};
