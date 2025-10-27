"""Build script for creating LUMA distributable package."""

import PyInstaller.__main__
import os
import shutil
import zipfile

def build_exe():
    """Build the LUMA executable."""
    PyInstaller.__main__.run([
        'main.py',
        '--name=LUMA',
        '--noconsole',
        '--onefile',
        '--clean'
    ])

def create_distribution():
    """Create a ZIP distribution package."""
    # Create dist directory if it doesn't exist
    if not os.path.exists('dist'):
        os.makedirs('dist')
    
    # Create a temporary directory for the package
    package_dir = 'dist/LUMA_package'
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Copy the executable
    shutil.copy('dist/LUMA.exe', package_dir)
    
    # Create an example config file
    with open(f'{package_dir}/build_config.py.example', 'w') as f:
        f.write('''"""Build configuration with embedded API keys."""

# Replace these with your actual API keys
GROQ_API_KEY = "your-groq-api-key-here"
GEMINI_API_KEY = "your-google-api-key-here"  # Optional
''')
    
    # Create the ZIP file
    with zipfile.ZipFile('dist/LUMA.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)

if __name__ == '__main__':
    build_exe()
    create_distribution()