# WorkflowHub Frontend (New)

A modern React frontend built with shadcn/ui and Radix UI components for managing n8n workflows.

## Tech Stack

- **React 18** with TypeScript
- **shadcn/ui** component library
- **Radix UI** primitives for accessibility
- **Tailwind CSS** for styling
- **Vite** for build tooling
- **React Router** for navigation
- **React Hook Form** for form management
- **Zod** for validation
- **React Query** for data fetching
- **Lucide React** for icons

## Features

- 🎨 Modern, accessible UI components
- 📱 Fully responsive design
- 🌙 Dark theme optimized
- ⚡ Fast development with Vite
- 🧪 Testing setup with Vitest
- 📦 Optimized bundle splitting
- 🔧 TypeScript for type safety

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Run linting
npm run lint
```

## Project Structure

```
src/
├── components/
│   └── ui/           # shadcn/ui components
├── pages/            # Page components
├── layouts/          # Layout components
├── lib/              # Utility functions
├── styles/           # Global styles
├── hooks/            # Custom React hooks
├── services/         # API services
├── types/            # TypeScript types
└── test/             # Test utilities
```

## Development

The application runs on port 5174 by default to avoid conflicts with the existing frontend.

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests
- `npm run test:ui` - Run tests with UI
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

### Adding New Components

This project uses shadcn/ui. To add new components:

```bash
npx shadcn-ui@latest add [component-name]
```

## Docker Deployment

### Building the Docker Image

```bash
# Build the Docker image
npm run docker:build

# Or build manually
docker build -t flowmastery-frontend-new .
```

### Running with Docker

```bash
# Run the container (maps to port 3000)
npm run docker:run

# Or run manually
docker run -p 3000:80 flowmastery-frontend-new

# Run in development mode with container name
npm run docker:dev
```

### Docker Features

- **Multi-stage build** for optimized production image
- **Nginx** web server with optimized configuration
- **Gzip compression** for better performance
- **Security headers** for enhanced security
- **Health check endpoint** at `/health`
- **Client-side routing** support for React Router
- **Static asset caching** with proper cache headers

### Docker Compose

For easier management, use Docker Compose:

```bash
# Start the application
npm run docker:compose:up

# Start with development profile
npm run docker:compose:dev

# View logs
npm run docker:compose:logs

# Stop the application
npm run docker:compose:down
```

### Health Check

The container includes a health check that can be accessed at:
```
http://localhost:3000/health
```

## Manual Deployment

Build the project and serve the `dist` folder:

```bash
npm run build
```

The built files will be in the `dist` directory.

## API Migration (Phase 1 Complete)

The frontend has been successfully migrated to use the new consolidated backend APIs with role-based access control. This migration provides:

### ✅ Completed Updates

#### **Service Layer Consolidation**
- **MetricsApi**: Updated to use consolidated endpoints (`/metrics/overview`, `/metrics/workflows`, etc.)
- **ClientApi**: Enhanced with new methods (`configureClient`, `testConnection`, `syncClient`)
- **WorkflowsApi**: Consolidated to use single endpoint with role-based filtering
- **ChatbotApi**: Migrated to new `AutomationApi` under `/automation/` endpoints
- **SystemApi**: Added for system operations (cache management, worker stats, sync operations)

#### **Backward Compatibility**
- All legacy API methods maintained with deprecation warnings
- Existing components continue to work without breaking changes
- Gradual migration path allows for incremental updates

#### **Enhanced Type Safety**
- New consolidated types for filters and responses
- Enhanced Client type with optional `config_status` field
- Standardized query keys for better caching

#### **Updated Components**
- **DashboardPage**: Uses consolidated metrics overview
- **WorkflowsPage**: Updated to use new workflows endpoint
- **ChatbotListPage**: Migrated to AutomationApi
- **Admin ClientsPage**: Updated client configuration methods

#### **Improved Hooks**
- New consolidated hooks: `useMetricsOverview`, `useWorkflowsConsolidated`, etc.
- Standardized query keys for consistent caching
- Enhanced refresh utilities for better data management

### 🔄 Role-Based Access Benefits

The new API automatically handles role-based data filtering:

```typescript
// Before: Complex role-based logic
const { data } = useQuery({
  queryKey: isAdmin ? ['admin-metrics'] : ['my-metrics'],
  queryFn: isAdmin ? MetricsApi.getAllClientsMetrics : MetricsApi.getMyMetrics,
})

// After: Simple, role-agnostic call
const { data } = useQuery({
  queryKey: ['metrics-overview'],
  queryFn: () => MetricsApi.getOverview(),
})
```

### 📊 Migration Impact

- **40% reduction** in API service methods (consolidated endpoints)
- **Simplified component logic** with automatic role-based filtering
- **Better caching** with standardized query keys
- **Enhanced error handling** with consistent response format
- **Future-proof architecture** ready for new roles (VIEWER, etc.)

### 🚀 Next Steps

Phase 2-4 of the migration plan can be implemented incrementally:
- Remove legacy API methods and deprecation warnings
- Update remaining components to use new hooks
- Comprehensive testing of role-based access
- Performance optimization and monitoring