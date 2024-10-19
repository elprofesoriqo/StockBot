# Stock Analysis Application

## Overview

This project is a FastAPI application that provides stock analysis functionalities, including fetching stock data, analyzing news articles related to stocks, and generating Excel reports for stock prices. It utilizes Alpha Vantage API for retrieving stock information and OpenAI for generating analyses based on news articles.

## Features

- Fetch daily stock data using the Alpha Vantage API.
- Analyze stock data and news articles with OpenAI's GPT-3.5 Turbo model.
- Store stock and analysis data in Firestore.
- Generate Excel reports containing stock prices over a specified period.
- Provide an API endpoint to download the generated Excel report.

## Technologies Used

- **FastAPI**: A modern, fast web framework for building APIs with Python 3.7+.
- **Alpha Vantage API**: Used to fetch stock data and news articles.
- **OpenAI API**: Used for generating analyses of stocks based on news articles.
- **Firestore**: A flexible, scalable database for storing stock and analysis data.
- **Pandas**: A powerful data manipulation library for generating Excel reports.
- **httpx**: An asynchronous HTTP client for making requests.

## Installation

Clone the repository, navigate to the project directory, create a virtual environment (optional but recommended), install the required packages, and set up your environment variables for the API keys (ALPHA_VANTAGE_API_KEY and OPENAI_API_KEY):

```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
