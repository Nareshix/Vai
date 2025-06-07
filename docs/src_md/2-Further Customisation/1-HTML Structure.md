Of course. Based on the structure and functionality of the `vai/main.py` script, here is a simple but comprehensive `CONTRIBUTING.md` file. It's designed to help a new contributor understand how to set up their environment, grasp the project's architecture, and start making meaningful changes.

---

# Contributing to Vai

First off, thank you for considering contributing to Vai! We're excited to have you. Every contribution, from a small typo fix to a major new feature, is valuable.

This document will guide you through the process of setting up your development environment and understanding the project's structure so you can start contributing.

## How You Can Contribute

There are many ways to contribute to the project:

*   **Reporting Bugs:** If you find a bug, please open an issue on GitHub. Describe the issue clearly, including steps to reproduce it.
*   **Suggesting Enhancements:** Have an idea for a new feature or an improvement to an existing one? Open an issue to discuss it.
*   **Improving Documentation:** Our documentation is built with Vai itself! If you see areas for improvement, feel free to submit a pull request.
*   **Writing Code:** If you're ready to dive into the code, you can fix bugs or implement new features.

## Setting Up Your Development Environment

To work on the Vai source code, you'll need to set it up locally.

1.  **Fork & Clone the Repository**
    *   Fork the repository on GitHub.
    *   Clone your fork locally: `git clone https://github.com/YOUR-USERNAME/vai.git`

2.  **Create a Virtual Environment**
    It's best practice to work in a Python virtual environment.
    ```bash
    cd vai
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**
    Install the necessary Python packages.
    ```bash
    pip install markdown pyyaml jinja2 livereload beautifulsoup4 minify-html rcssmin rjsmin
    ```

4.  **Create a Test Project**
    The `vai` tool needs a project directory to operate on. The `init` command is perfect for creating a sample project to test your changes against.
    ```bash
    # From the root of your cloned repository, create a test directory
    mkdir test-project
    cd test-project

    # Run the init command using the local vai script
    python ../vai/main.py init
    ```
    This will populate `test-project/` with the necessary `src_md`, `static`, `templates`, and `config.yaml` files. You can now use this directory to test your code changes.

## Development Workflow

The typical workflow for making a change is:

1.  Navigate into your `test-project` directory.
2.  Run the development server using your local version of the script:
    ```bash
    python ../vai/main.py run
    ```
3.  The server will start at `http://localhost:6600`. It will automatically watch for changes in the `src_md`, `templates`, `static`, and `config.yaml` files and rebuild the site.
4.  Now, go back to the root of the cloned repository and open `vai/main.py` in your editor.
5.  Make your desired code changes. When you save the file, the `livereload` server **will not** automatically restart the Python process. You will need to **manually stop (Ctrl+C) and restart the `run` command** to see your Python code changes take effect.
6.  Once you are satisfied with your changes, test the production build:
    ```bash
    # In the test-project directory
    python ../vai/main.py build
    ```
7.  Check the generated `dist/` folder to ensure everything is minified and working as expected.

## Project Structure Explained

To contribute effectively, it's helpful to understand how Vai is organized.

*   `vai/main.py`: This is the heart of the application. It contains all the logic for parsing commands, scanning source files, converting Markdown, and building the final site.
*   `vai/package_defaults/`: This directory holds the default `static/`, `templates/`, and `config.yaml` files that are copied into a user's project when they run `vai init`. If you want to change the default starter template, this is the place to do it.

### The Build Process

Understanding the build flow is key:

1.  **`vai run` or `vai build` is executed.**
2.  `build()` is called.
3.  `setup_header_in_layout_html()`: Reads `config.yaml` and `templates/layout_no_header.html` to generate a complete `templates/layout.html` with the navigation bar.
4.  `scan_src()`: Scans the `src_md/` directory, respecting the `01-` numbering for sorting, and builds a data structure for the sidebar.
5.  `process_md_files()`:
    *   Iterates through each Markdown file found by `scan_src()`.
    *   Parses frontmatter (`+++ ... +++`).
    *   Converts Markdown to HTML using custom extensions (`AdmonitionProcessorCorrected`, `HeadingIdAdder`).
    *   Generates a page-specific Table of Contents.
    *   Builds up a `search_index.json`.
    *   Renders the final HTML for each page into the `src_html/` directory using the Jinja2 template.
6.  **For `vai run`**: The `livereload` server serves files directly from the `src_html/` directory.
7.  **For `vai build`**: The `cli_build()` function takes the contents of `src_html/`, minifies all HTML, CSS, and JS, and places the final, optimized site into the `dist/` folder. The `--github` flag modifies asset paths to work with GitHub Pages.

### Key Concepts

*   **Content Convention:** Content lives in `src_md/`. The structure `##-SectionName/##-PageName.md` is important. The numbers control sorting, and the names are cleaned up for display and URL slugs.
*   **Admonitions:** Vai supports a custom admonition syntax (`:::note`, `:::warning`, etc.). The logic is in `AdmonitionProcessorCorrected`.
*   **Templating:** All pages are rendered through `templates/layout.html`. You can see the variables passed to it (like `body_content`, `sidebar_data`, `toc_table_link`) in the `process_md_files` function.

## Submitting Your Contribution

1.  Create a new branch for your feature or bugfix: `git checkout -b my-awesome-feature`.
2.  Make your changes and commit them with a clear, descriptive message.
3.  Push your branch to your fork on GitHub: `git push origin my-awesome-feature`.
4.  Open a Pull Request (PR) from your fork to the main `vai` repository.
5.  In your PR description, explain the changes you made and link to any relevant issues.

Thank you again for your interest in making Vai better! We look forward to your contributions.