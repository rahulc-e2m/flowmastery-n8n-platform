# 🛟 FlowMastery Troubleshooting Guide

This guide will help you resolve common issues when running FlowMastery with n8n integration.

## 🚀 Quick Start Instructions

### Option 1: Using Scripts
1. **Windows Batch**: Double-click `start-dev.bat`
2. **PowerShell**: Run `.\start-dev.ps1` in PowerShell

### Option 2: Manual Start
1. **Start Backend** (in first terminal):
   ```
   cd backend
   python app.py
   ```
   Should show: `Uvicorn running on http://127.0.0.1:8000`

2. **Start Frontend** (in second terminal):
   ```
   npm start
   ```
   Should show: `Local: http://localhost:5173/`

3. **Open Browser**: Navigate to `http://localhost:5173`

## 🔧 Common Issues & Solutions

### Issue 1: "Cannot see anything on the website"

**Symptoms**: 
- Browser shows white/blank page
- No content visible
- Console errors

**Solutions**:
1. **Check if servers are running**:
   - Backend: Visit `http://localhost:8000` - should show JSON response
   - Frontend: Visit `http://localhost:5173` - should show FlowMastery site

2. **Clear browser cache**:
   - Hard refresh: `Ctrl + F5` (Windows) or `Cmd + Shift + R` (Mac)
   - Clear cache in browser settings

3. **Check browser console**:
   - Press `F12` to open DevTools
   - Look for errors in Console tab
   - Common errors and fixes below

### Issue 2: Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

**Error**: `Cannot find config.py or n8n_chatbot.py`

**Solution**:
```bash
cd backend
copy "../To integrate/config.py" .
copy "../To integrate/n8n_chatbot.py" .
```

### Issue 3: Frontend won't start

**Error**: `npm error Missing script: "start"`

**Solution**: Already fixed in package.json, but if you see this:
```bash
npm run dev
```

**Error**: Module resolution errors

**Solution**:
```bash
npm install
npm start
```

### Issue 4: CORS Errors

**Error**: `Access to fetch blocked by CORS policy`

**Solution**: Ensure backend is running on port 8000 and includes CORS headers (already configured).

### Issue 5: n8n Integration Issues

**Error**: Configuration not working

**Steps**:
1. Click "View n8n Metrics" button
2. Click "Configure n8n Instance" 
3. Enter your n8n details:
   - **API URL**: `https://your-n8n-instance.com` (without /api/v1)
   - **API Key**: Your n8n API key
   - **Instance Name**: Any name you prefer
4. Click "Test Connection" - should show success
5. Click "Save Configuration"

### Issue 6: Port Conflicts

**Error**: `Port 8000 is already in use`

**Solutions**:
1. Kill existing process:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID [PID_NUMBER] /F
   
   # Or change port in backend/app.py line ~340:
   uvicorn.run("app:app", host="127.0.0.1", port=8001)
   ```

## 📋 Verification Checklist

### ✅ Backend Health Check
Visit: `http://localhost:8000/health`

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-22T09:00:00.000Z",
  "n8n_integration": true
}
```

### ✅ Frontend Loading
Visit: `http://localhost:5173`

You should see:
- FlowMastery homepage with purple gradient background
- "Centralize Your n8n Workflows" title
- Navigation bar with WorkflowHub logo
- Stats section showing workflow metrics
- "View n8n Metrics" button

### ✅ Full Integration Test
1. Go to `http://localhost:5173`
2. Click "View n8n Metrics" 
3. Should navigate to metrics dashboard
4. If not configured, shows configuration form
5. After configuration, shows live metrics

## 🐞 Still Having Issues?

### Check These Files Exist and Have Content:
- `src/App.tsx` (should be ~20 lines)
- `src/pages/Homepage.tsx` (should be ~300+ lines)  
- `src/components/N8nMetricsDashboard.tsx` (should be ~400+ lines)
- `backend/app.py` (should be ~500+ lines)
- `backend/n8n_metrics.py` (should be ~200+ lines)

### Log Analysis:
1. **Backend logs**: Check terminal running `python app.py`
2. **Frontend logs**: Check terminal running `npm start`
3. **Browser logs**: F12 → Console tab

### Network Issues:
1. Check if `localhost:8000` is accessible
2. Try `127.0.0.1:8000` instead
3. Disable firewall temporarily

### Dependencies:
```bash
# Backend
cd backend
pip list | findstr fastapi
pip list | findstr uvicorn

# Frontend  
npm list react
npm list react-router-dom
```

## 🆘 Emergency Reset

If nothing works, try this complete reset:

```bash
# Stop all servers (Ctrl+C in terminals)

# Reset frontend
npm install --force
npm start

# Reset backend (in new terminal)
cd backend
pip install -r requirements.txt --force-reinstall
python app.py
```

## 📞 Additional Help

- Check `INTEGRATION_GUIDE.md` for setup details
- Verify all files are in correct locations
- Ensure both Node.js and Python are properly installed
- Try different browser (Chrome, Firefox, Edge)

---

**Expected URLs after successful setup:**
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000  
- **API Health**: http://localhost:8000/health
