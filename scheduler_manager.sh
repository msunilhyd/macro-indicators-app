#!/bin/bash
# Universal Data Collection Scheduler Management Script
# Manages the data collection scheduler daemon

SCRIPT_DIR="/Users/s0m13i5/linus/macro-indicators-app"
SCHEDULER_SCRIPT="universal_data_scheduler.py"
PID_FILE="$SCRIPT_DIR/logs/scheduler.pid"
LOG_FILE="$SCRIPT_DIR/logs/scheduler.log"

cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "⚠️  Scheduler is already running (PID: $(cat "$PID_FILE"))"
            exit 1
        fi
        
        echo "🚀 Starting Data Collection Scheduler..."
        source venv/bin/activate
        nohup python "$SCHEDULER_SCRIPT" > "$LOG_FILE" 2>&1 & echo $! > "$PID_FILE"
        
        if [ $? -eq 0 ]; then
            echo "✅ Scheduler started successfully (PID: $(cat "$PID_FILE"))"
            echo "📄 Logs: $LOG_FILE"
        else
            echo "❌ Failed to start scheduler"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
    
    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "⚠️  Scheduler is not running"
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        echo "⏹️  Stopping Data Collection Scheduler (PID: $PID)..."
        
        if kill "$PID" 2>/dev/null; then
            echo "✅ Scheduler stopped successfully"
        else
            echo "⚠️  Force killing scheduler process..."
            kill -9 "$PID" 2>/dev/null
        fi
        
        rm -f "$PID_FILE"
        ;;
    
    restart)
        "$0" stop
        sleep 2
        "$0" start
        ;;
    
    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            PID=$(cat "$PID_FILE")
            echo "✅ Scheduler is running (PID: $PID)"
            
            # Show recent log entries
            if [ -f "$LOG_FILE" ]; then
                echo "📄 Recent log entries:"
                tail -10 "$LOG_FILE"
            fi
        else
            echo "❌ Scheduler is not running"
            [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
        fi
        ;;
    
    collect)
        echo "🔄 Running data collection once..."
        source venv/bin/activate
        python "$SCHEDULER_SCRIPT" --run-once
        ;;
    
    logs)
        if [ -f "$LOG_FILE" ]; then
            echo "📄 Scheduler logs:"
            tail -f "$LOG_FILE"
        else
            echo "❌ No log file found"
        fi
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|collect|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the data collection scheduler daemon"
        echo "  stop     - Stop the data collection scheduler daemon"
        echo "  restart  - Restart the data collection scheduler daemon"
        echo "  status   - Show scheduler status and recent logs"
        echo "  collect  - Run data collection once (for testing)"
        echo "  logs     - Follow scheduler logs in real-time"
        exit 1
        ;;
esac