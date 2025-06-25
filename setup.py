# setup.py
import os
from setuptools import setup, find_packages

# --- Helper function to read files ---
def read(fname):
    """Reads the content of a file."""
    try:
        with open(os.path.join(os.path.dirname(__file__), fname), encoding='utf-8') as f:
            return f.read()
    except IOError:
        return "" # Return empty string if file doesn't exist

# --- Package Metadata ---
NAME = 'streamwatch'
VERSION = '0.3.0' # Incremented version as features were added
AUTHOR = 'Johny Snow'
EMAIL = 'snowballons@protonmail.com' 
DESCRIPTION = 'A CLI tool to manage, check status, and play favorite live streams.'
URL = 'https://github.com/snowballons/streamwatch-cli'
LICENSE_TYPE = 'MIT License' 
PYTHON_REQUIRES = '>=3.7' 

# --- Define dependencies ---
# Read dependencies from requirements.txt, ignore comments/empty lines
INSTALL_REQUIRES = [
    req for req in read('requirements.txt').splitlines()
    if req and not req.strip().startswith('#')
]

# --- Setup Configuration ---
setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION,
    long_description=read('README.md'), # Read README for PyPI description
    long_description_content_type='text/markdown',
    url=URL,
    license=LICENSE_TYPE, # Use the string name from LICENSE file
    python_requires=PYTHON_REQUIRES,

    # Automatically find the package directory (stream_manager_cli/)
    # This looks for directories containing an __init__.py file
    packages=find_packages(where='.'),
    # If find_packages doesn't work reliably, you can specify manually:
    # packages=['stream_manager_cli'],
    # package_dir={'': '.'}, # Tells setuptools packages start from the root

    # Specify required packages needed for installation
    install_requires=INSTALL_REQUIRES,

    # Define the command-line script entry point
    entry_points={
        'console_scripts': [
            # command_name = package_name.module_name:function_name
            'streamwatch = streamwatch.main:main',
        ],
    },

    # Metadata classifiers for PyPI (helps users find your package)
    classifiers=[
        'Development Status :: 4 - Beta', # Or 3 - Alpha, 5 - Production/Stable
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License', # Make sure this matches license file
        'Operating System :: OS Independent', # Works on Win, Linux, macOS
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Multimedia :: Video',
        'Topic :: Terminals',
        'Topic :: Utilities',
    ],

    # Optional: Specify project keywords
    keywords='stream streamlink twitch youtube live cli manager player interactive',

    # Optional: If you have data files to include (e.g., default config), use this
    # include_package_data=True,
    # package_data={
    #     'stream_manager_cli': ['data/default_config.json'],
    # },
)