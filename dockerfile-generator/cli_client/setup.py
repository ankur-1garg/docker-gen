# cli_client/setup.py
from setuptools import setup, find_packages

setup(
    name='mcp-dockergen-cli', # The name used for pip install
    version='0.1.0',
    packages=find_packages(), # Automatically find the 'dockerfile_generator_cli' package
    include_package_data=True,
    install_requires=[
        'typer[all]',
        'requests',
        'python-dotenv',
        # Add other dependencies as needed
    ],
    entry_points='''
        [console_scripts]
        mcp-dockergen=dockerfile_generator_cli.cli:app
    ''',
    author='Your Name / Team Name', # CHANGE THIS
    author_email='your.email@example.com', # CHANGE THIS
    description='CLI tool for generating Dockerfiles via MCP Server.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='<your_project_repository_url>', # Optional: Add your repo URL
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", # Choose appropriate license
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8', # Specify minimum Python version
)