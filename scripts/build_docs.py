#!/usr/bin/env python3
"""
Documentation build script for StreamWatch.

Generates API documentation and builds HTML output.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Build documentation."""
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"
    
    print("🔧 Building StreamWatch documentation...")
    
    try:
        # Generate API documentation
        print("📝 Generating API documentation...")
        subprocess.run([
            "sphinx-apidoc",
            "-f", "-o", str(docs_dir),
            str(project_root / "src" / "streamwatch"),
            "--separate"
        ], check=True)
        
        # Build HTML documentation
        print("🏗️ Building HTML documentation...")
        subprocess.run([
            "sphinx-build",
            "-b", "html",
            str(docs_dir),
            str(docs_dir / "_build" / "html")
        ], check=True)
        
        print("✅ Documentation built successfully!")
        print(f"📖 Open: {docs_dir / '_build' / 'html' / 'index.html'}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Documentation build failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Sphinx not found. Install with: pip install sphinx sphinx-rtd-theme")
        sys.exit(1)


if __name__ == "__main__":
    main()
