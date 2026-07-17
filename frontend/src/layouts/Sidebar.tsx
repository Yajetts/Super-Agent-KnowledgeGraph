import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  History as HistoryIcon,
  Explore as ExploreIcon,
  SmartToy as SmartToyIcon,
  School as SchoolIcon,
  Dashboard as DashboardIcon,
  Monitor as MonitorIcon,
} from '@mui/icons-material';

const menuItems = [
  { text: 'Home', path: '/', icon: <DashboardIcon /> },
  { text: 'Workflow History', path: '/workflow-history', icon: <HistoryIcon /> },
  { text: 'GraphRAG Explorer', path: '/graphrag-explorer', icon: <ExploreIcon /> },
  { text: 'Agent Explorer', path: '/agent-explorer', icon: <SmartToyIcon /> },
  { text: 'Learning Center', path: '/learning-center', icon: <SchoolIcon /> },
  { text: 'System Monitor', path: '/system-monitor', icon: <MonitorIcon /> },
];

const drawerWidth = 240;

export const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};
