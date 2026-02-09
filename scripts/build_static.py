import os
import shutil
from jinja2 import Environment, FileSystemLoader

# Configuration
TEMPLATE_DIR = "templates"
STATIC_DIR = "static"
OUTPUT_DIR = "_site"


def build_static_site():
    """Builds the static site from Jinja2 templates."""
    print("Starting Static Site Build...")

    # 1. Prepare Output Directory
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    print(f"Created output directory: {OUTPUT_DIR}")

    # 2. Copy Static Assets
    # Copy contents of 'static' folder to '_site' root (so css/style.css works as expected)
    # The template expects 'css/' and 'js/' to be at the root relative to the HTML file

    # Copy individual subdirectories to maintain structure
    if os.path.exists(STATIC_DIR):
        for item in os.listdir(STATIC_DIR):
            s = os.path.join(STATIC_DIR, item)
            d = os.path.join(OUTPUT_DIR, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        print(f"Copied static assets from {STATIC_DIR} to {OUTPUT_DIR}")
    else:
        print(f"Warning: Static directory '{STATIC_DIR}' not found.")

    # 3. Render Templates
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    # List of pages to render
    pages = [
        {"template": "index.html", "output": "index.html"},
        {"template": "history.html", "output": "history.html"},
        {"template": "help.html", "output": "help.html"},
    ]

    for page in pages:
        try:
            template = env.get_template(page["template"])
            output_content = template.render(request=None, is_static=True)

            output_path = os.path.join(OUTPUT_DIR, page["output"])
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_content)

            print(f"Rendered: {page['template']} -> {page['output']}")
        except Exception as e:
            print(f"Error rendering {page['template']}: {e}")

    print("Build Complete!")


if __name__ == "__main__":
    build_static_site()
