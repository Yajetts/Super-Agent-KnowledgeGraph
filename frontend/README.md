# SuperAgent Knowledge Graph Frontend

A modern React + Vite + TypeScript frontend for the SuperAgent Knowledge Graph platform.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **TypeScript** - Type safety
- **Material UI (MUI)** - Component library
- **React Router DOM** - Routing
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **TanStack Query** - Data fetching and caching
- **Notistack** - Notifications

## Getting Started

### Prerequisites

- Node.js 18+ installed
- FastAPI backend running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API service layer
│   │   ├── axios.ts      # Axios configuration
│   │   ├── workflowApi.ts
│   │   ├── graphApi.ts
│   │   ├── graphragApi.ts
│   │   ├── memoryApi.ts
│   │   ├── learningApi.ts
│   │   ├── agentApi.ts
│   │   └── vectorApi.ts
│   ├── components/       # Reusable components
│   │   ├── LoadingSpinner.tsx
│   │   ├── ErrorState.tsx
│   │   ├── StatusIndicator.tsx
│   │   ├── MetricCard.tsx
│   │   ├── AgentCard.tsx
│   │   └── WorkflowResult.tsx
│   ├── layouts/          # Layout components
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── MainLayout.tsx
│   ├── pages/            # Page components
│   │   ├── Dashboard.tsx
│   │   ├── WorkflowHistory.tsx
│   │   ├── GraphRAGExplorer.tsx
│   │   ├── AgentExplorer.tsx
│   │   ├── LearningCenter.tsx
│   │   └── SystemMonitor.tsx
│   ├── routes/           # Route configuration
│   │   └── AppRoutes.tsx
│   ├── theme/            # Material UI theme
│   │   └── index.tsx
│   ├── types/            # TypeScript types
│   │   └── index.ts
│   ├── hooks/            # Custom hooks
│   ├── App.tsx           # Root component
│   └── main.tsx          # Entry point
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .gitignore
```

## Features

### Dashboard
- Execute multi-agent workflows
- View findings, risks, and recommendations
- Display workflow execution results with detailed information

### Workflow History
- View past workflow executions
- Search and filter workflows
- Sort by various criteria
- View detailed workflow information

### GraphRAG Explorer
- Retrieve context using GraphRAG fusion
- View graph retrieval results
- View vector retrieval results
- View fusion results with merged findings, risks, and recommendations

### Agent Explorer
- View dynamic agents
- Search and filter agents by name, description, or skills
- View agent details including skills and usage statistics

### Learning Center
- View learned workflow patterns
- Visualize most successful workflows
- View workflow reuse frequency
- Display pattern metrics

### System Monitor
- Monitor system health and statistics
- View memory, graph, vector, and learning system stats
- Real-time system status

## Theme

The application supports light and dark modes with the Lato font:
- Light mode: White background with black text
- Dark mode: Black background with white text
- Theme preference is persisted in localStorage

## API Configuration

The frontend is configured to communicate with the FastAPI backend at `http://localhost:8000`. This can be changed by setting the `VITE_API_BASE_URL` environment variable.

## Error Handling

The application includes comprehensive error handling:
- Network errors
- Timeout errors
- Invalid responses
- Missing data
- User-friendly error messages with retry options

## Loading States

All pages include:
- Loading spinners
- Skeleton loaders
- Empty states
- Error states

## Responsiveness

The application is responsive and supports:
- Desktop
- Laptop
- Tablet

Using Material UI's Grid system for layout.
