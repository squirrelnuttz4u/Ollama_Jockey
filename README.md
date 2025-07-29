Colt's LLama Jockey v1.0 Beta
Copyright (c) 2025 Colt McVey. All rights reserved.

Introduction
Colt's LLama Jockey is a comprehensive, all-in-one performance analysis, prompt engineering, and model evaluation suite designed for local Large Language Models (LLMs) running on Ollama. It transforms the complex process of tuning and testing into a systematic, data-driven workflow, empowering developers, researchers, and AI enthusiasts to unlock the maximum potential of their hardware.

This application provides a unified environment to conduct sophisticated benchmarks, compare models head-to-head, visualize performance trends, and manage a version-controlled library of prompts, all while monitoring system resources in real-time.

Key Features
Parameterized Benchmarking: Systematically test every combination of Ollama parameters (temperature, num_ctx, num_gpu, etc.) to find optimal settings.

Multiple Test Suites: Go beyond speed tests with built-in suites for "Raw Performance" (TPS, TTFT), "Commonsense Reasoning," and "Instruction Following."

Jockey's Edge Recommender: Get intelligent recommendations for the best parameter set based on your specific optimization goals (e.g., "Maximize TPS").

Jockey Arena with Elo Leaderboard: Pit models against each other in a side-by-side comparison, and build a personalized leaderboard based on your votes using an Elo rating system.

Prompt Paddock: A dedicated workspace for prompt engineering with a persistent, version-controlled library to save, load, and iterate on your prompts.

Data Analysis & Visualization: An integrated "History Viewer" and "Analysis" tab with interactive charts to visualize performance trends and correlations.

Comprehensive Telemetry: Real-time monitoring of CPU, RAM, Disk I/O, and multi-GPU stats (Utilization, VRAM, Temp, Power).

Full Data Management: Export benchmark reports to Markdown and Excel, import/export application settings, and securely clear all historical data.

Customizable UI: A modern, polished user interface with multiple themes, including Light, Dark, and custom designs like "Neon Stalker" and "Vintage Terminal."

How to Use
1. Installation & Setup
Prerequisites:

Python 3.8+

An active Ollama server.

Dependencies:
The application requires several Python libraries. You can install them all with a single command:

pip install requests psutil pynvml xlsxwriter matplotlib

Note: pynvml is for NVIDIA GPU monitoring. The app will work without it, but GPU stats will be unavailable.

Running the Application:

Save the application code as a Python file (e.g., app.py).

Run it from your terminal: python app.py

First Run/Database Migration: If you are upgrading from a version prior to the "Instruction Following" test, you must delete the llama_jockey.db file in the same folder as app.py before starting the app. This allows the application to create a new database with the correct structure.

2. Getting Started: Configuration
Settings Tab: The first thing you should do is go to the Settings tab.

Ollama Server: Verify that the "Ollama Server Address" is correct for your setup. If you change it, click "Apply & Refresh".

Theme: Select your preferred UI theme from the dropdown.

3. Running Benchmarks
Navigate to the Benchmarking tab.

Select Test Suite: Choose the type of test you want to run (e.g., "Raw Performance").

Select Model: Choose the Ollama model you want to test.

Define Parameter Matrix: Enter the parameter values you want to test. For numeric fields, you can enter multiple values separated by commas (e.g., 2048, 4096 for num_ctx).

Run Test: Click the "Run Test" button. The progress will be displayed in the log window and the application title. You can cancel the test queue at any time by clicking "Stop Test".

Analyze Results:

View the raw log in the "Benchmark Log" window.

Go to the History Viewer tab to see a sortable table of all past results.

Go to the Analysis tab to generate charts visualizing the data.

Use the Jockey's Edge Recommender on the Benchmarking tab to find the best settings for a specific goal.

4. Using the Jockey Arena
Navigate to the Arena tab.

Select two models (or two different configurations of the same model) for "Model A" and "Model B".

Enter a prompt in the "Battle Prompt" box.

Click "Run Battle". The models will generate responses side-by-side.

After reviewing, cast your vote using the buttons at the bottom. Your vote updates the models' Elo ratings.

Check the Leaderboard tab to see the updated rankings.

5. Using the Prompt Paddock
Navigate to the Prompt Paddock tab.

Write: Write your prompt in the main editor on the right.

Test: Select a model and click "Run Prompt" to see the output.

Save:

To save a new prompt, click "Save/Update". You will be asked to give it a name.

To update a loaded prompt, make your edits and click "Save/Update".

To iterate while keeping the original, click "Save as New Version".

Manage: Use the "Prompt Library" on the left to Load existing prompts into the editor or Delete them.
