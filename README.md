# AI Chat Assistant

A Streamlit-based chat interface that uses OpenAI's API to provide conversational AI responses.

## Features

- 🤖 Interactive chat interface
- 🔄 Conversation history maintained during session
- ⚙️ Configurable AI model selection (GPT-3.5, GPT-4, etc.)
- 🎛️ Adjustable response creativity (temperature setting)
- 🗑️ Clear chat functionality
- 📱 Responsive design

## Setup Instructions

### 1. Virtual Environment
The project uses a Python virtual environment. To activate it:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 2. Install Dependencies
All required packages are already installed in the virtual environment:
- streamlit
- openai
- python-dotenv

### 3. OpenAI API Key Setup
1. Get your OpenAI API key from: https://platform.openai.com/api-keys
2. Create a `.env` file in the project root directory
3. Add your API key to the `.env` file:
```
OPENAI_API_KEY=your_actual_api_key_here
```

**Note:** Use the `env_template.txt` file as a reference for the `.env` file format.

### 4. Run the Application
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## Usage

1. **Ask Questions**: Type your question in the chat input at the bottom
2. **Follow-up Questions**: The AI remembers the conversation context, so you can ask follow-up questions
3. **Model Selection**: Choose between different AI models in the sidebar
4. **Adjust Creativity**: Use the temperature slider to control response creativity
5. **Clear Chat**: Use the "Clear Chat" button to start a new conversation

## Project Structure

```
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── env_template.txt   # Environment variables template
├── README.md          # This file
└── venv/              # Virtual environment directory
```

## Troubleshooting

- **API Key Error**: Make sure your `.env` file exists and contains a valid OpenAI API key
- **Import Errors**: Ensure the virtual environment is activated and dependencies are installed
- **Connection Issues**: Check your internet connection and OpenAI API status

## Notes

- The application maintains conversation history during the session
- Each new session starts with a clean chat history
- API usage is subject to OpenAI's pricing and rate limits
