#!/bin/bash

# AGGRESSIVE DISK CLEANUP FOR CLOUDOPS AI
# This script aggressively frees disk space on your Mac

set -e

echo "🚨 AGGRESSIVE DISK CLEANUP IN PROGRESS 🚨"
echo ""

# Show current disk usage
echo "📊 Current Disk Usage:"
df -h / | tail -1
echo ""

# Step 1: Remove Xcode cache (5-10GB typical)
echo "1️⃣  Removing Xcode DerivedData (can be 5-10GB)..."
rm -rf ~/Library/Developer/Xcode/DerivedData/*
echo "   ✅ Xcode cache cleared"

# Step 2: Remove Homebrew cache
echo "2️⃣  Cleaning Homebrew cache..."
brew cleanup -s 2>/dev/null || echo "   ⓘ Homebrew not found or already clean"
echo "   ✅ Homebrew cleaned"

# Step 3: Remove old Python installations
echo "3️⃣  Removing old Python installations..."
rm -rf ~/Library/Caches/pip 2>/dev/null || true
rm -rf ~/.cache/pip 2>/dev/null || true
echo "   ✅ Python pip cache cleared"

# Step 4: Remove Rust compilation cache
echo "4️⃣  Removing Rust compilation cache..."
rm -rf ~/Library/Caches/puccinialin
rm -rf ~/.rustup/toolchains/stable-*
echo "   ✅ Rust cache cleared"

# Step 5: Empty trash
echo "5️⃣  Emptying Trash..."
rm -rf ~/.Trash/*
echo "   ✅ Trash emptied"

# Step 6: Remove temp files
echo "6️⃣  Removing temporary files..."
rm -rf /var/tmp/*
rm -rf /tmp/*
rm -rf /var/log/*.log
echo "   ✅ Temp files cleared"

# Step 7: Remove iOS simulators cache (can be 20GB+!)
echo "7️⃣  Removing iOS simulator cache (if present)..."
rm -rf ~/Library/Developer/CoreSimulator/Caches/* 2>/dev/null || echo "   ⓘ No simulators found"
echo "   ✅ Simulator cache cleared"

# Step 8: Remove Docker stuff (if Docker is installed)
echo "8️⃣  Cleaning Docker (if installed)..."
docker system prune -af 2>/dev/null || echo "   ⓘ Docker not running or not installed"
echo "   ✅ Docker cleaned"

# Step 9: Remove node_modules if present (can be 100MB+)
echo "9️⃣  Cleaning node_modules if present..."
find ~/.npm -type d -name "*" -delete 2>/dev/null || true
echo "   ✅ npm cache cleaned"

# Step 10: Show what's taking up space
echo ""
echo "🔍 Largest directories (top 10):"
du -sh ~/* 2>/dev/null | sort -rh | head -10
echo ""

# Show new disk usage
echo "📊 New Disk Usage:"
df -h / | tail -1
echo ""

# Calculate freed space
echo "✅ CLEANUP COMPLETE!"
echo ""
echo "If you still need more space:"
echo "  • Remove: ~/Downloads/* (if safe to delete)"
echo "  • Remove: ~/Library/Application Support/* (non-essential apps)"
echo "  • Run: brew uninstall --all (only if you don't need Homebrew)"
echo ""
