from setuptools import setup, find_packages

setup(
    name="assistant",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot',
        'pandas',
        'natasha',
        'openai',
        'sqlalchemy',
        'flask',
        'apscheduler',
    ],
) 