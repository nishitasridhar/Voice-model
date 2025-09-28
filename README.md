This model is used here as a voice agent. It accepts a single user input via text, voices a specific output, and then shuts down. This setup makes it ideal for quick, one-off voice interactions where you need a fast and precise response without maintaining a long-running conversation.

STEPS TO SET-UP THE MODEL:
1. Clone or Download the Repository
git clone https://github.com/your-username/your-repo-name.git

If you downloaded it as a ZIP file, extract it and open the folder.

2. Open in VS Code
Navigate into the project folder and open it in Visual Studio Code.

3. Create Environment File
In the root directory, create a .env file and add the required environment variables.
Example:
API_KEY=your_api_key_here

4. Create a Virtual Environment
python -m venv .venv

5. Activate the Virtual Environment
Windows (PowerShell): .venv\Scripts\Activate
Mac/Linux: source .venv/bin/activate

6. Install Dependencies
pip install -r requirements.txt

7. Install Google Generative AI Library
pip install google-generativeai

8. Run the Application
python -m app.main
