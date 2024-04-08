# Alphageist
A cross platform desktop app that allows you to efficiently navigate your internal documents by asking questions about them. The app provides instant answers based on the information contained in your files.

https://github.com/Visendi-Labs/alphageist/assets/7818582/507d4fb2-1dbe-456e-8e26-2474b3bd3c2d

Such a desktop tool is convenient when you want to grant access to a disorganized folder structure with many files on your computer or server, without the need to drag and drop specific files into a web browser. Another advantage is that you don't need to know the specific file where the information you're searching for is located. The app displays the sources used in the answer; simply click on them to open the source files.

The software is free and open source but you need to use your own OpenAI API key in order to use this software.

## Install
For Mac and Windows, download the installer and follow the instructions from [here](https://www.visendi.ai/download).

## Contributions
We accept pull requests! 

### Dev. Setup
Use whatever virtual environment you want. Here is the most simply way to get it up and running using pythons builtins virtual environment:
1. Clone repo
2. `$ python -m venv venv`
3. `$ source venv/Scripts/activate`
4. `$ pip install -r requirements.txt`
5. `$ python main.py`

To run tests, simply run `$ pytest` 
