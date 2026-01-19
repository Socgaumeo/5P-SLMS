#!/bin/bash
# SLMS Development Server Startup Script
# Runs both Backend and Frontend

echo "🚀 Starting SLMS Development Environment..."

# Kill existing processes on ports 8000 and 5173
echo "Stopping any existing services..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true

# Start Backend (FastAPI)
echo "🔧 Starting Backend (FastAPI) on port 8000..."
cd /Users/bear1108/Documents/GitHub/5P-SLMS/backend
nohup python3 -m uvicorn main:app --port 8000 --host 0.0.0.0 > /tmp/slms_backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Check backend health
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "   ✅ Backend is running!"
else
    echo "   ❌ Backend failed to start. Check /tmp/slms_backend.log"
    exit 1
fi

# Start Frontend (Vite React)
echo "💻 Starting Frontend (React) on port 5173..."
cd /Users/bear1108/Documents/GitHub/5P-SLMS/frontend
nohup npm run dev -- --host 0.0.0.0 --port 5173 > /tmp/slms_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 3

echo ""
echo "=========================================="
echo "✅ SLMS Development Environment Running!"
echo "=========================================="
echo ""
echo "📍 Frontend:  http://localhost:5173"
echo "📍 Backend:   http://localhost:8000"
echo "📍 API Docs:  http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Backend:  /tmp/slms_backend.log"
echo "   Frontend: /tmp/slms_frontend.log"
echo ""
echo "🛑 To stop: pkill -f uvicorn && pkill -f vite"
echo ""
