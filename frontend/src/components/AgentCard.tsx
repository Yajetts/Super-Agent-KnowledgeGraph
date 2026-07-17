import { Card, CardContent, Typography, Chip, Box } from '@mui/material';

interface AgentCardProps {
  name: string;
  description: string;
  skills: string[];
  usageCount: number;
  isDynamic: boolean;
  onClick?: () => void;
}

export const AgentCard = ({ name, description, skills, usageCount, isDynamic, onClick }: AgentCardProps) => {
  return (
    <Card sx={{ height: '100%', cursor: onClick ? 'pointer' : 'default' }} onClick={onClick}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Typography variant="h6" component="div">
            {name}
          </Typography>
          <Chip
            label={isDynamic ? 'Dynamic' : 'Static'}
            size="small"
            color={isDynamic ? 'primary' : 'secondary'}
          />
        </Box>
        <Typography variant="body2" color="textSecondary" gutterBottom>
          {description}
        </Typography>
        <Box mt={2}>
          <Typography variant="caption" color="textSecondary">
            Skills:
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
            {skills.slice(0, 3).map((skill) => (
              <Chip key={skill} label={skill} size="small" variant="outlined" />
            ))}
            {skills.length > 3 && (
              <Chip label={`+${skills.length - 3}`} size="small" variant="outlined" />
            )}
          </Box>
        </Box>
        <Box mt={2}>
          <Typography variant="caption" color="textSecondary">
            Usage: {usageCount}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};
