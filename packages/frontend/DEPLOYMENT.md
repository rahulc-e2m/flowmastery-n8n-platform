# FlowMastery Frontend Deployment Guide

This guide covers deploying the FlowMastery React frontend independently from the backend.

## Prerequisites

- Node.js 18 or higher
- npm or yarn package manager
- Backend API already deployed and accessible

## Environment Setup

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables:**
   Edit `.env` with your production settings:

   ```bash
   # API Configuration (Required)
   VITE_API_URL=https://your-backend-api.com
   
   # App Configuration
   VITE_APP_NAME=FlowMastery
   VITE_APP_VERSION=2.0.0
   VITE_DEV_MODE=false
   
   # Optional configurations
   VITE_SOURCE_MAPS=false
   VITE_DEFAULT_THEME=light
   ```

## Deployment Options

### Option 1: Static Hosting (Recommended)

Build the application and deploy to a static hosting service:

```bash
# Install dependencies
npm install

# Build for production
npm run build

# The build output will be in the 'dist' directory
```

#### Netlify
1. Connect your Git repository to Netlify
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Add environment variables in Netlify dashboard
5. Deploy automatically on push

#### Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Follow the prompts
4. Set environment variables in Vercel dashboard

#### AWS S3 + CloudFront
```bash
# Build the app
npm run build

# Upload to S3 bucket
aws s3 sync dist/ s3://your-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

### Option 2: Docker Deployment

1. **Build Docker image:**
   ```bash
   docker build -t flowmastery-frontend .
   ```

2. **Run container:**
   ```bash
   docker run -p 80:80 flowmastery-frontend
   ```

3. **Docker Compose example:**
   ```yaml
   version: '3.8'
   services:
     frontend:
       image: flowmastery-frontend
       ports:
         - "80:80"
       environment:
         - VITE_API_URL=https://your-backend-api.com
   ```

### Option 3: Node.js Server

For dynamic configuration or server-side rendering:

```bash
# Install dependencies
npm install

# Build the application
npm run build

# Serve using a static server
npx serve -s dist -l 3000
```

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_URL` | ✅ | Backend API base URL | `https://api.yourdomain.com` |
| `VITE_APP_NAME` | ❌ | Application name | `FlowMastery` |
| `VITE_APP_VERSION` | ❌ | Application version | `2.0.0` |
| `VITE_DEV_MODE` | ❌ | Development mode flag | `false` |
| `VITE_SOURCE_MAPS` | ❌ | Enable source maps | `false` |
| `VITE_DEFAULT_THEME` | ❌ | Default UI theme | `light` or `dark` |
| `VITE_ENABLE_CHAT` | ❌ | Enable chat feature | `true` |
| `VITE_ENABLE_METRICS` | ❌ | Enable metrics feature | `true` |
| `VITE_ENABLE_ADMIN_PANEL` | ❌ | Enable admin panel | `true` |

## Build Configuration

### Production Optimizations

The `vite.config.ts` includes production optimizations:
- Code splitting for better caching
- Asset optimization
- Bundle analysis

### Custom Build Settings

You can customize the build by modifying `vite.config.ts`:

```typescript
export default defineConfig({
  build: {
    outDir: 'dist',
    sourcemap: process.env.VITE_SOURCE_MAPS === 'true',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@radix-ui/react-dialog', 'lucide-react']
        }
      }
    }
  }
})
```

## Nginx Configuration

For custom server deployment, use this Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Serve static files
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Proxy API requests to backend
    location /api {
        proxy_pass https://your-backend-api.com;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Performance Considerations

1. **Bundle Size:** Monitor bundle size with `npm run build`
2. **Lazy Loading:** Components are loaded on demand
3. **Caching:** Configure proper cache headers
4. **CDN:** Use a CDN for global distribution
5. **Compression:** Enable gzip/brotli compression

## Security Considerations

1. **HTTPS Only:** Always serve over HTTPS in production
2. **CSP Headers:** Configure Content Security Policy
3. **Environment Variables:** Never expose sensitive data in frontend
4. **API Keys:** Only use public/client-side API keys
5. **Dependencies:** Regularly audit and update dependencies

## Monitoring and Analytics

### Error Tracking
Add Sentry for error tracking:
```bash
npm install @sentry/react @sentry/tracing
```

Then configure in your main.tsx:
```typescript
import * as Sentry from '@sentry/react'

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.MODE
  })
}
```

### Analytics
Add your preferred analytics service:
```typescript
// Google Analytics example
if (import.meta.env.VITE_GA_ID) {
  // Initialize Google Analytics
}
```

## Troubleshooting

1. **API Connection Issues:**
   - Verify `VITE_API_URL` is correct
   - Check CORS configuration on backend
   - Ensure backend is accessible from frontend domain

2. **Build Failures:**
   - Clear node_modules: `rm -rf node_modules package-lock.json && npm install`
   - Check for TypeScript errors: `npm run type-check`
   - Verify all dependencies are installed

3. **Runtime Errors:**
   - Check browser console for errors
   - Verify environment variables are set correctly
   - Check network requests in browser dev tools

4. **Routing Issues:**
   - Ensure server is configured for SPA routing
   - Check that `try_files` includes `/index.html` fallback

For more help, check the browser console or create an issue in the repository.