# URGENT: Fix Disk Space Issue - 3 Solutions

Your Mac is completely out of disk space. Here are 3 escalating solutions:

---

## ⚡ SOLUTION 1: Aggressive Cleanup (Do This First!)

Run this script to free 10-30GB:

```bash
chmod +x /Users/harsha/CloudOps-AI/AGGRESSIVE_CLEANUP.sh
/Users/harsha/CloudOps-AI/AGGRESSIVE_CLEANUP.sh
```

**What it does:**
- Removes Xcode cache (5-10GB)
- Clears Homebrew cache
- Deletes Rust compilation cache
- Empties trash
- Clears iOS simulator cache (can be 20GB+)
- Cleans Docker images

**After cleanup:**
```bash
# Check free space
df -h /

# Should show significantly more available space
```

---

## 🔄 SOLUTION 2: Use Simplified Requirements (Avoids Rust Compilation)

The issue is `pydantic-core` trying to compile with Rust on Python 3.14.

We've created a **minimal requirements file** that uses pre-built wheels:

```bash
cd /Users/harsha/CloudOps-AI/ai-service

# Remove old venv
rm -rf venv

# Create fresh venv
python3 -m venv venv
source venv/bin/activate

# Install MINIMAL requirements (no Rust needed!)
pip install --upgrade pip
pip install -r requirements_minimal.txt

# Verify
python3 -c "from google.adk.agents import Agent; print('✅ Google ADK ready')"

# Run tests
python3 test_adk_locally.py
```

**requirements_minimal.txt includes:**
- ✅ FastAPI & Uvicorn
- ✅ Pydantic (pre-built version)
- ✅ Google ADK
- ✅ Vertex AI
- ✅ All essential dependencies
- ❌ NOT: Rust compilation (avoids disk issue)

---

## 💾 SOLUTION 3: Switch to Python 3.11 (Safest Option)

If you have Python 3.11 available, use it instead of 3.14:

```bash
# Check if Python 3.11 is installed
python3.11 --version

# If not installed via Homebrew:
brew install python@3.11

# Use Python 3.11 instead
python3.11 -m venv venv
source venv/bin/activate

# Install normally (no Rust compilation issues on 3.11)
pip install -r requirements.txt

# Run tests
python3 test_adk_locally.py
```

**Why Python 3.11?**
- Has pre-built wheels for all dependencies
- No Rust compilation needed
- Fully supported by Google ADK
- More stable than Python 3.14 (which is very new)

---

## 📋 Full Recovery Procedure

Choose ONE of these paths:

### Path A: Aggressive Cleanup + Minimal Requirements (5 min)
```bash
# 1. Run aggressive cleanup
/Users/harsha/CloudOps-AI/AGGRESSIVE_CLEANUP.sh

# 2. Check free space
df -h /

# 3. If >1GB free, proceed to fresh install
cd /Users/harsha/CloudOps-AI/ai-service
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_minimal.txt

# 4. Test
python3 test_adk_locally.py
```

### Path B: Switch to Python 3.11 (3 min)
```bash
# 1. Check if Python 3.11 available
python3.11 --version

# 2. If yes:
cd /Users/harsha/CloudOps-AI/ai-service
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Test
python3 test_adk_locally.py

# 4. If no, install first:
# brew install python@3.11
```

### Path C: Nuclear Option (Maximum Space Recovery)
```bash
# WARNING: This is aggressive. Only if above doesn't work.

# 1. Free maximum space
rm -rf ~/Downloads/*
rm -rf ~/Library/Caches/*
rm -rf ~/Library/Application\ Support/CrashReporter/*
docker system prune -af 2>/dev/null || true
brew cleanup --all 2>/dev/null || true

# 2. Fresh Python 3.11
brew install python@3.11 --force

# 3. Clean install
cd /Users/harsha/CloudOps-AI/ai-service
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🎯 Recommended Approach

**I recommend Path B: Switch to Python 3.11**

Here's why:
1. Fastest solution (3 minutes)
2. Most reliable (pre-built wheels available)
3. Most stable (3.14 is very new, may have bugs)
4. Avoids disk issues entirely

**Commands:**
```bash
# Check if available
python3.11 --version

# If yes, use it:
cd /Users/harsha/CloudOps-AI/ai-service
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Test
python3 test_adk_locally.py
```

---

## After Any Solution

Once you get past the installation, you should see:

```
✅ All tests passed! Ready for Cloud Run deployment! 🎉
```

Then proceed with:
```bash
# Deploy to Cloud Run
gcloud builds submit ./ai-service \
  --tag=gcr.io/possible-point-497521-g1/cloudops-ai-ai-service
```

---

## Verification Commands

```bash
# After cleanup, check disk
df -h /

# After install, verify imports
python3 -c "from google.adk.agents import Agent; print('✅ ADK')"
python3 -c "from vertexai.generative_models import GenerativeModel; print('✅ Vertex')"
python3 -c "from fastapi import FastAPI; print('✅ FastAPI')"

# Run full test suite
python3 test_adk_locally.py
```

---

## Status Check

| Step | Status | Fix |
|------|--------|-----|
| Disk Space | ❌ FULL | Run aggressive cleanup or switch Python |
| Python Version | 3.14 | Consider using 3.11 instead |
| Requirements | Rust issue | Use `requirements_minimal.txt` |
| Google ADK | ✅ Ready | Once disk fixed |
| Tests | ✅ Ready | Once packages installed |

---

## If You Still Have Issues

```bash
# Show what's taking up space
du -sh ~/* | sort -rh

# Show disk details
diskutil info /

# Show largest files
find ~ -type f -size +500M 2>/dev/null | head -10
```

Then delete the largest non-essential items and retry.

---

**Start with the AGGRESSIVE_CLEANUP.sh script NOW, then choose Path A or B above.**

You should be up and running in 5-10 minutes! 🚀
