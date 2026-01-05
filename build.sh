#!/bin/bash
# Build script for Render

# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
