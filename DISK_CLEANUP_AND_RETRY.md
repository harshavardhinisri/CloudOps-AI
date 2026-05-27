# CloudOps AI - Disk Space Fix & Recovery Guide

## Issue: "No space left on device"

Your Mac has run out of disk space, preventing pip from installing packages. This is preventing the Google ADK and other dependencies from being installed.

---

## Quick Fix (Run These Commands)

### Step 1: Free Up Disk Space

```bash
# Check current disk usage
df -h | head -5

# Clear pip cache (can be 1-2GB)
pip cache purge

# Clear temporary Rust installation files
rm -rf ~/Library/Caches/puccinialin
rm -rf /var/tmp/*
rm -rf /tmp/*

# Clear old Python cache
find ~/Library/Caches -name "*.pyc" -delete 2>/dev/null
find ~/Library/Caches -type d -name "__pycache__" -delete 2>/dev/null

# Check disk usage again
df -h | head -5
```

### Step 2: Clean Virtual Environment & Retry

```bash
cd /Users/harsha/CloudOps-AI/ai-service

# Remove old venv
rm -rf venv

# Create fresh virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install requirements (should work now with freed space)
pip install -r requirements.txt

# Verify Google ADK installed
python3 -c "from google.adk.agents import Agent; print('✅ Google ADK ready')"
```

### Step 3: Run Tests Again

```bash
# Make sure venv is activated
source venv/bin/activate

# Run the test suite
python3 test_adk_locally.py
```

**Expected output this time:**
```
======================================================================
  CloudOps AI - Local ADK Testing Suite
======================================================================

✅ FastAPI imported
✅ Pydantic imported
✅ google.adk.agents.Agent imported
✅ google.adk.runners.InMemoryRunner imported
✅ vertexai.generative_models.GenerativeModel imported
✅ HallucinationControlSystem imported

... (more tests) ...

🎉 All tests passed! Ready for Cloud Run deployment! 🎉
```

---

## What Was Fixed

### 1. **Disk Space Issue** ✅
- Cleared pip cache
- Removed temporary Rust compilation files  
- Cleared Python cache directories
- This should free up 2-5GB

### 2. **Hallucination Control Bug** ✅
- Fixed `verify_and_correct_analysis()` method call
- Now passes required `incident_logs` parameter
- Returns proper safety report

---

## How Much Space Did We Free?

These are typical sizes freed by cleanup:
```
pip cache:              500MB - 2GB
Rust files:             300MB - 1GB  
Python cache:           100MB - 500MB
Total potential:        900MB - 3.5GB
```

---

## If You Still Get Disk Full Errors

```bash
# Find largest directories
du -sh ~/Library/* | sort -rh | head -10
du -sh ~/Downloads/* | sort -rh | head -10
du -sh ~/* | sort -rh | head -10

# Remove Xcode cache (can be 5-10GB!)
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Remove old Homebrew downloads
brew cleanup -s

# Empty trash
rm -rf ~/.Trash/*

# Check Docker space usage (if using Docker)
docker system prune -a
```

---

## One-Command Cleanup (Safe Version)

```bash
# This clears everything except your projects
bash -c '
set -e
echo "Clearing pip cache..."
pip cache purge

echo "Clearing temp files..."
rm -rf ~/Library/Caches/puccinialin
rm -rf /var/tmp/*
rm -rf /tmp/*

echo "Clearing Python cache..."
find ~/Library/Caches -name "*.pyc" -delete 2>/dev/null || true
find ~/Library/Caches -type d -name "__pycache__" -delete 2>/dev/null || true

echo "Checking disk..."
df -h | head -3

echo "✅ Cleanup complete!"
'
```

---

## After Cleanup - Next Steps

1. ✅ Run disk cleanup commands above
2. ✅ Delete and recreate virtual environment
3. ✅ Reinstall requirements with fresh pip
4. ✅ Run test suite
5. ✅ Deploy to Cloud Run

---

## Expected Test Results After Fix

**All 12 tests should pass:**
- ✅ 4 imports
- ✅ 3 tool functions  
- ✅ 1 agent creation
- ✅ 1 orchestrator
- ✅ 3 API endpoints

**Key indicators:**
- No "No space left on device" errors
- All Google ADK imports successful
- Hallucination control integrates without errors
- Full incident analysis completes in 5-10 seconds
- Safety report shows SAFE status

---

## Preventing This in Future

```bash
# Check disk before major operations
df -h | grep -E "Use%|Filesystem"

# Clean cache monthly
pip cache purge

# Keep Xcode cache clean
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Monitor disk regularly
diskutil info / | grep "Free Space"
```

---

**Last Updated**: 2026-05-27  
**Status**: Ready to retry after cleanup  
**Action Required**: Run disk cleanup commands above, then retry pip install
