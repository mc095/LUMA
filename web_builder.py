"""LUMA Web Builder Server
Handles the web interface for generating LUMA executables with custom API keys."""

from flask import Flask, request, send_file, render_template
import os
import tempfile
import subprocess
from pathlib import Path

app = Flask(__name__, 
            static_folder='web',
            static_url_path='')

@app.route('/')
def index():
    """Serve the configuration page."""
    return app.send_static_file('index.html')

@app.route('/generate', methods=['POST'])
def generate_exe():
    """Generate a customized LUMA executable."""
    try:
        # Get API keys from request
        data = request.get_json()
        groq_key = data.get('groqKey')
        google_key = data.get('googleKey', '')  # Optional
        
        if not groq_key:
            return 'GROQ API key is required', 400
            
        # Create temporary build config
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create build_config.py with API keys
            build_config_content = f'''"""Build configuration with embedded API keys."""
GROQ_API_KEY = "{groq_key}"
GEMINI_API_KEY = "{google_key}"
'''
            build_config_path = Path(temp_dir) / 'build_config.py'
            with open(build_config_path, 'w') as f:
                f.write(build_config_content)
            
            # Copy necessary files to temp directory
            project_files = [
                'main.py', 'agent.py', 'audio_processor.py',
                'config.py', 'transcriber.py', 'tts_handler.py',
                'tools.py', 'terminal_style.py', 'database.py',
                'requirements.txt'
            ]
            
            for file in project_files:
                if os.path.exists(file):
                    with open(file, 'r') as src, open(Path(temp_dir) / file, 'w') as dst:
                        dst.write(src.read())
            
            # Create PyInstaller spec
            spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['main.py'],
             pathex=[r'{temp_dir}'],
             binaries=[],
             datas=[('build_config.py', '.')],
             hiddenimports=['build_config'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='LUMA',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False)
'''
            
            spec_path = Path(temp_dir) / 'LUMA.spec'
            with open(spec_path, 'w') as f:
                f.write(spec_content)
            
            # Run PyInstaller
            subprocess.run([
                'pyinstaller',
                '--clean',
                '--workpath', str(Path(temp_dir) / 'build'),
                '--distpath', str(Path(temp_dir) / 'dist'),
                str(spec_path)
            ], cwd=temp_dir, check=True)
            
            # Send the generated executable
            exe_path = Path(temp_dir) / 'dist' / 'LUMA.exe'
            if exe_path.exists():
                return send_file(
                    exe_path,
                    as_attachment=True,
                    download_name='LUMA.exe'
                )
            else:
                return 'Failed to generate executable', 500
    
    except Exception as e:
        return f'Error: {str(e)}', 500

if __name__ == '__main__':
    app.run(debug=True)