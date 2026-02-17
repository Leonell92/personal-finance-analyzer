# Deploying Personal Finance Analyzer to Streamlit Cloud

This guide will help you deploy your application to Streamlit Community Cloud so you can share it with others.

## Prerequisites

1.  **GitHub Account**: You need a GitHub account. If you don't have one, sign up at [github.com](https://github.com).
2.  **Streamlit Cloud Account**: Sign up at [streamlit.io/cloud](https://streamlit.io/cloud) using your GitHub account.

## Step 1: Push Your Code to GitHub

You need to have your code in a GitHub repository.

1.  **Initialize Git** (if not already done):
    Open your terminal in the project folder and run:
    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    ```

2.  **Create a New Repository on GitHub**:
    *   Go to [GitHub.com](https://github.com) and click the "**+**" icon in the top right -> **New repository**.
    *   Name it `personal-finance-analyzer`.
    *   Make it **Public** (Streamlit Cloud is free for public repos).
    *   Do **not** check "Initialize with README", .gitignore, or license (you already have these).
    *   Click **Create repository**.

3.  **Push Code**:
    *   Copy the commands under value **"…or push an existing repository from the command line"**.
    *   Run them in your terminal. They will look something like this:
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/personal-finance-analyzer.git
    git branch -M main
    git push -u origin main
    ```

## Step 2: Deploy on Streamlit Cloud

1.  **Log in to Streamlit Cloud**: Go to [share.streamlit.io](https://share.streamlit.io).
2.  **New App**: Click the **New app** button.
3.  **Select Repository**:
    *   **Repository**: Choose `YOUR_USERNAME/personal-finance-analyzer`.
    *   **Branch**: `main`.
    *   **Main file path**: `app.py`.
4.  **Deploy**: Click **Deploy!**

## Step 3: Wait & Verify

*   Streamlit will start building your app. You can verify the logs in the bottom right corner (the "Manage app" section).
*   Once finished, you will see your app's URL (usually `https://personal-finance-analyzer.streamlit.app`).

## Troubleshooting

*   **ModuleNotFoundError**: If you see an error saying a module is missing, check `requirements.txt`. It must list all libraries you use (like `pandas`, `plotly`, `rapidfuzz`).
*   **Data File Errors**: Ensure your `data/` folder is committed if you have default data, OR verify that the app handles empty states gracefully (which your code does!).

---
**Enjoy your deployed app! 🚀**
