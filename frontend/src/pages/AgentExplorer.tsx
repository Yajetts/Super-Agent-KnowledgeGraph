import { useState } from 'react';
import { Box, Typography, TextField, Grid, InputLabel, MenuItem, FormControl, Select } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { agentApi } from '../api/agentApi';
import { AgentCard } from '../components/AgentCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';
import { AgentItem } from '../types';

export const AgentExplorer = () => {
  const [search, setSearch] = useState('');
  const [skillFilter, setSkillFilter] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['dynamicAgents'],
    queryFn: agentApi.getDynamicAgents,
  });

  const filteredAgents = data?.agents.filter((agent) => {
    const matchesSearch = agent.name.toLowerCase().includes(search.toLowerCase()) ||
      agent.description.toLowerCase().includes(search.toLowerCase());
    const matchesSkill = skillFilter === '' || agent.skills.includes(skillFilter);
    return matchesSearch && matchesSkill;
  }) || [];

  const allSkills = data?.agents.flatMap((agent) => agent.skills) || [];
  const uniqueSkills = Array.from(new Set(allSkills));

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Agent Explorer
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Explore dynamically created agents and their capabilities.
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Search agents"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or description..."
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>Filter by Skill</InputLabel>
            <Select
              value={skillFilter}
              label="Filter by Skill"
              onChange={(e) => setSkillFilter(e.target.value)}
            >
              <MenuItem value="">All Skills</MenuItem>
              {uniqueSkills.map((skill) => (
                <MenuItem key={skill} value={skill}>
                  {skill}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {isLoading && <LoadingSpinner />}

      {isError && (
        <ErrorState
          message={error?.message || 'Failed to load agents'}
          onRetry={() => refetch()}
        />
      )}

      {data && (
        <Grid container spacing={3}>
          {filteredAgents.length > 0 ? (
            filteredAgents.map((agent) => (
              <Grid item xs={12} sm={6} md={4} key={agent.name}>
                <AgentCard
                  name={agent.name}
                  description={agent.description}
                  skills={agent.skills}
                  usageCount={agent.usage_count}
                  isDynamic={agent.is_dynamic}
                />
              </Grid>
            ))
          ) : (
            <Grid item xs={12}>
              <Typography variant="body1" color="textSecondary" align="center">
                No agents found matching your criteria.
              </Typography>
            </Grid>
          )}
        </Grid>
      )}
    </Box>
  );
};
