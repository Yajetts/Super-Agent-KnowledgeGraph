import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { Dashboard } from '../pages/Dashboard';
import { WorkflowHistory } from '../pages/WorkflowHistory';
import { GraphRAGExplorer } from '../pages/GraphRAGExplorer';
import { AgentExplorer } from '../pages/AgentExplorer';
import { LearningCenter } from '../pages/LearningCenter';
import { SystemMonitor } from '../pages/SystemMonitor';

export const AppRoutes = () => {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/workflow-history" element={<WorkflowHistory />} />
        <Route path="/graphrag-explorer" element={<GraphRAGExplorer />} />
        <Route path="/agent-explorer" element={<AgentExplorer />} />
        <Route path="/learning-center" element={<LearningCenter />} />
        <Route path="/system-monitor" element={<SystemMonitor />} />
      </Routes>
    </MainLayout>
  );
};
