import { Box, Chip } from '@mui/material';

interface StatusIndicatorProps {
  status: 'success' | 'error' | 'warning' | 'info';
  label: string;
}

export const StatusIndicator = ({ status, label }: StatusIndicatorProps) => {
  const getColor = () => {
    switch (status) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Chip label={label} color={getColor() as any} size="small" />
    </Box>
  );
};
