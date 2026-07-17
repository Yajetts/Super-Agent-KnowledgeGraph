import { Box, Typography, Grid, Card, CardContent } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { learningApi } from '../api/learningApi';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';
import { MetricCard } from '../components/MetricCard';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { School as SchoolIcon, TrendingUp as TrendingUpIcon, AutoGraph as AutoGraphIcon } from '@mui/icons-material';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const LearningCenter = () => {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['learningPatterns'],
    queryFn: () => learningApi.getPatterns(50),
  });

  const patterns = data?.patterns || [];

  const mostSuccessfulPatterns = patterns
    .sort((a, b) => b.success_score - a.success_score)
    .slice(0, 10);

  const reuseFrequencyData = patterns
    .sort((a, b) => b.usage_count - a.usage_count)
    .slice(0, 10)
    .map((p) => ({
      name: p.task_type,
      count: p.usage_count,
    }));

  const successScoreData = patterns
    .slice(0, 10)
    .map((p) => ({
      name: p.task_type,
      score: p.success_score * 100,
    }));

  const totalPatterns = patterns.length;
  const avgSuccessScore = patterns.length > 0
    ? patterns.reduce((sum, p) => sum + p.success_score, 0) / patterns.length
    : 0;
  const totalUsage = patterns.reduce((sum, p) => sum + p.usage_count, 0);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Learning Center
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        View learned workflow patterns and their performance metrics.
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Total Patterns"
            value={totalPatterns}
            icon={<SchoolIcon />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Avg Success Score"
            value={`${(avgSuccessScore * 100).toFixed(1)}%`}
            icon={<TrendingUpIcon />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <MetricCard
            title="Total Usage"
            value={totalUsage}
            icon={<AutoGraphIcon />}
            color="#ed6c02"
          />
        </Grid>
      </Grid>

      {isLoading && <LoadingSpinner />}

      {isError && (
        <ErrorState
          message={error?.message || 'Failed to load learning data'}
          onRetry={() => refetch()}
        />
      )}

      {data && patterns.length > 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Most Successful Workflows
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={successScoreData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="score" fill="#8884d8" name="Success Score (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Workflow Reuse Frequency
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={reuseFrequencyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#82ca9d" name="Usage Count" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Top Workflow Patterns by Success Score
                </Typography>
                {mostSuccessfulPatterns.map((pattern, index) => (
                  <Box key={index} mb={2} p={2} sx={{ bgcolor: 'background.paper', borderRadius: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {pattern.task_type}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Success Score: {(pattern.success_score * 100).toFixed(1)}% | Usage: {pattern.usage_count}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Agents: {pattern.workflow_pattern.join(', ')}
                    </Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {data && patterns.length === 0 && (
        <Card>
          <CardContent>
            <Typography variant="body1" color="textSecondary" align="center">
              No learning patterns available yet. Execute workflows to generate learning data.
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};
