# 🚀 Render Deployment Guide

Follow these steps to deploy your GST Reconciliation Tool to Render.

## Prerequisites
- A GitHub account
- A Render account (free) - Sign up at https://render.com

## Step 1: Push Your Code to GitHub

1. **Initialize Git Repository** (if not already done):
   ```bash
   cd "c:\Users\Hamada Salim G-Trd\OneDrive\Desktop\Time pass\Antigravity\Creation\2"
   git init
   git add .
   git commit -m "Initial commit - GST Reconciliation Tool"
   ```

2. **Create a New Repository on GitHub**:
   - Go to https://github.com/new
   - Name it: `gst-reconciliation-tool`
   - Keep it Public (required for Render free tier)
   - Don't initialize with README (you already have one)
   - Click "Create repository"

3. **Push Your Code**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/gst-reconciliation-tool.git
   git branch -M main
   git push -u origin main
   ```
   Replace `YOUR_USERNAME` with your actual GitHub username.

## Step 2: Deploy on Render

1. **Go to Render Dashboard**:
   - Visit https://dashboard.render.com
   - Click "New +" button
   - Select "Web Service"

2. **Connect Your Repository**:
   - Click "Connect account" to link your GitHub
   - Find and select `gst-reconciliation-tool` repository
   - Click "Connect"

3. **Configure Your Service**:
   Fill in the following settings:
   
   - **Name**: `gst-reconciliation-tool` (or any name you prefer)
   - **Region**: Choose closest to your location
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`

4. **Click "Create Web Service"**

## Step 3: Wait for Deployment

- Render will automatically:
  - Install Python dependencies
  - Create necessary directories
  - Start your application
  
- This takes about 2-5 minutes
- You'll see build logs in real-time

## Step 4: Access Your App

Once deployment is complete:
- Your app will be live at: `https://gst-reconciliation-tool.onrender.com`
- Click the URL to test it
- Share this link on WhatsApp! 🎉

## Important Notes

⚠️ **Free Tier Limitations**:
- App sleeps after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds to wake up
- 750 hours/month of runtime (plenty for personal use)

💡 **Tips**:
- The URL is permanent - save it!
- You can update by pushing to GitHub (auto-deploys)
- Check logs in Render dashboard if issues occur

## Troubleshooting

If deployment fails:
1. Check the build logs in Render dashboard
2. Ensure all files are committed to GitHub
3. Verify `requirements.txt` is in the root directory
4. Check that `backend/temp` directory exists

## Updating Your App

To make changes:
```bash
# Make your changes
git add .
git commit -m "Description of changes"
git push
```

Render will automatically redeploy! ✨

---

Need help? Check Render documentation: https://render.com/docs
