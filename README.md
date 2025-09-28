🎙️ Voice Agent – Quick One-Off Voice Interactions

This project sets up a voice-enabled AI agent that accepts a single user input (via text), generates a spoken response, and then shuts down.
It’s ideal for fast, precise, one-off interactions without maintaining a long-running conversation.

🚀 Features

Accepts single input and returns spoken response

Lightweight, no persistent sessions

Powered by Google Generative AI

⚙️ Setup Guide

Follow these steps to get the project running locally:

1️⃣ Clone or Download the Repository

git clone https://github.com/nishitasridhar/Voice-model


If downloaded as a ZIP → extract and open the folder.

2️⃣ Open in VS Code

Navigate into the project folder

Open with Visual Studio Code

3️⃣ Create Environment File

Create a .env file in the root directory and add:

API_KEY=your_api_key_here

4️⃣ Create a Virtual Environment

python -m venv .venv

5️⃣ Activate the Virtual Environment

Windows (PowerShell):

.venv\Scripts\Activate


Mac/Linux:

source .venv/bin/activate

6️⃣ Install Dependencies

pip install -r requirements.txt

7️⃣ Install Google Generative AI Library

pip install google-generativeai

8️⃣ Run the Application

python -m app.main

🎧 Usage

Provide input via text

Agent generates a voice output

App automatically shuts down
