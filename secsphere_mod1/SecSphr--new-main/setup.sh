#!/bin/bash

echo "🔧 Setting up SecureSphere Web Application..."
echo "================================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"

# Install required packages
echo "📦 Installing required packages..."
pip3 install --break-system-packages -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "🎉 Setup completed successfully!"
echo "📝 To run your webapp, use: python3 run_webapp.py"
echo "🔗 Or use: python3 app.py"