from setuptools import setup, find_packages

setup(
    name="SparkyAI",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.21.1",
        "jinja2>=3.1.2",
        "aiohttp>=3.8.4",
        "python-dotenv>=1.0.0",
        "playwright>=1.32.1",
        "websockets>=11.0.2",
        "httpx>=0.24.0",
        "beautifulsoup4>=4.12.0",
        "Pillow>=9.5.0",
    ],
    python_requires=">=3.9",
)