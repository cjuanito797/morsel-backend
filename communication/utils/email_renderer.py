import subprocess
from premailer import transform
import subprocess
import tempfile
import os

def render_mjml_template(mjml_content):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.mjml', delete=False) as temp_file:
        temp_file.write(mjml_content)
        temp_file.flush()
        temp_file_path = temp_file.name

    try:
        result = subprocess.run(
            ['mjml', temp_file_path, '-s'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("MJML Error:", e.stderr)
        raise RuntimeError(f"Failed to render MJML: {e.stderr}")
    finally:
        os.remove(temp_file_path)

def render_mjml(mjml_content: str) -> str:
    try:
        if not mjml_content.strip():
            raise ValueError("MJML content is empty.")

        # Call MJML CLI and pipe content in via stdin
        process = subprocess.Popen(
            ["mjml", "-s"],                  # -s = stdout output
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True         # ensures proper string encoding for stdin/stdout
        )

        stdout, stderr = process.communicate(input=mjml_content)

        if process.returncode != 0:
            raise RuntimeError(f"MJML Error: {stderr.strip()}")

        # Inline styles for better email compatibility
        return transform(stdout)

    except Exception as e:
        raise RuntimeError(f"Failed to render MJML: {e}")