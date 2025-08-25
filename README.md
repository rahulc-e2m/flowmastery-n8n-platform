# FlowMastery - Enterprise Workflow Automation Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-blue)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2-61dafb)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)](https://fastapi.tiangolo.com/)

## 🚀 Overview

FlowMastery is an enterprise-grade workflow automation platform that seamlessly integrates with n8n to provide intelligent automation, chatbot capabilities, and comprehensive workflow management. Built with modern architecture patterns and best practices, it offers a robust solution for businesses looking to streamline their operations.

## ✨ Key Features

- **🤖 AI-Powered Chatbots**: Intelligent conversational agents with natural language processing
- **📊 Real-time Metrics Dashboard**: Comprehensive analytics and monitoring of workflow executions
- **🔄 n8n Integration**: Seamless integration with n8n workflow automation platform
- **🎯 SEO Auditor**: Advanced SEO analysis and optimization tools
- **💼 Lead Generation**: Automated lead capture and nurturing workflows
- **📝 Meeting Summarizer**: AI-powered meeting notes and action item extraction
- **🔐 Enterprise Security**: Built-in security features and authentication
- **📈 Scalable Architecture**: Microservices-based architecture for horizontal scaling

## 🏗️ Architecture

```
flowmastery-n8n-platform/
├── packages/
│   ├── frontend/          # React TypeScript application
│   │   ├── src/
│   │   │   ├── components/   # Reusable UI components
│   │   │   │   ├── AnimatedBackground/
│   │   │   │   └── N8nMetricsDashboard/
│   │   │   ├── pages/        # Page components
│   │   │   │   ├── ChatbotCategory/
│   │   │   │   └── Homepage/
│   │   │   ├── styles/       # Global styles
│   │   │   └── tests/        # Component tests
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── package.json
│   │
│   └── backend/           # FastAPI Python application
│       ├── app/
│       │   ├── main.py       # FastAPI application entry point
│       │   ├── config.py     # Configuration settings
│       │   ├── config_service.py # Configuration management
│       │   ├── n8n_chatbot.py    # n8n chatbot integration
│       │   ├── n8n_metrics.py    # n8n metrics collection
│       │   └── data/         # Data storage
│       │       └── n8n_config.json
│       ├── tests/           # Backend tests
│       ├── Dockerfile
│       ├── requirements.txt
│       └── pyproject.toml
│
├── docker-compose.yml     # Container orchestration
├── package.json          # Root workspace configuration
├── start-dev.bat         # Windows dev script
├── start-dev.ps1         # PowerShell dev script
├── CONTRIBUTING.md       # Contribution guidelines
├── INTEGRATION_GUIDE.md  # Integration documentation
├── TROUBLESHOOTING.md    # Troubleshooting guide
└── README.md            # This file
```

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18.2 with TypeScript
- **Build Tool**: Vite 5.2
- **Styling**: CSS Modules + Tailwind CSS
- **State Management**: React Context + Custom Hooks
- **Testing**: Jest + React Testing Library
- **Code Quality**: ESLint + Prettier

### Backend
- **Framework**: FastAPI 0.104
- **Language**: Python 3.11+
- **Database**: PostgreSQL / SQLite
- **ORM**: SQLAlchemy
- **Testing**: Pytest
- **API Documentation**: OpenAPI / Swagger

### DevOps
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm/yarn/pnpm
- Python 3.11+
- Docker and Docker Compose (optional)
- n8n instance (for full functionality)

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/flowmastery-n8n-platform.git
cd flowmastery-n8n-platform
```

2. **Install dependencies**
```bash
# Install frontend dependencies
cd packages/frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Copy example environment files
cp .env.example .env
cp packages/frontend/.env.example packages/frontend/.env
cp packages/backend/.env.example packages/backend/.env
```

4. **Start development servers**
```bash
# Start both frontend and backend (from root)
npm run dev

# Or start individually:
# Frontend
cd packages/frontend && npm run dev

# Backend
cd packages/backend && uvicorn app.main:app --reload
```

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in production mode
docker-compose -f docker-compose.prod.yml up -d
```

## 🧪 Testing

```bash
# Run all tests
npm run test

# Frontend tests
cd packages/frontend && npm run test

# Backend tests  
cd packages/backend && pytest

# E2E tests
npm run test:e2e

# Generate coverage report
npm run test:coverage
```

## 📚 Documentation

- [API Documentation](./docs/api/README.md)
- [Architecture Guide](./docs/architecture/README.md)
- [Development Guide](./docs/guides/development.md)
- [Deployment Guide](./docs/guides/deployment.md)
- [Contributing Guide](./CONTRIBUTING.md)

## 🚀 Deployment

### Production Build

```bash
# Build for production
npm run build

# Frontend build
cd packages/frontend && npm run build

# Backend build
cd packages/backend && python -m build
```

### Environment Configuration

Configure the following environment variables for production:

```env
# Backend
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379
N8N_API_URL=https://your-n8n-instance.com
N8N_API_KEY=your-api-key
SECRET_KEY=your-secret-key

# Frontend
VITE_API_URL=https://api.yourdomain.com
VITE_N8N_WEBHOOK_URL=https://n8n.yourdomain.com/webhook
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- [n8n](https://n8n.io/) - Workflow automation platform
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web API framework
- [React](https://reactjs.org/) - UI library
- [Vite](https://vitejs.dev/) - Build tool

## 📞 Support

- **Documentation**: [https://docs.flowmastery.io](https://docs.flowmastery.io)
- **Issues**: [GitHub Issues](https://github.com/yourusername/flowMastery/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/flowMastery/discussions)
- **Email**: support@flowmastery.io

---

Built with ❤️ by the FlowMastery Team
