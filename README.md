
# vai


## ✨ Key Features
 - 📱 **Responsive Design**: Looks great on any devices — no extra setup required.
- 🔎 **Full-Text Search**: Automatically builds a search index for all your pages and headings.
- 🎨 **Syntax Highlighting**: Beautiful code blocks out of the box.
- 💅 **Custom Blocks**: Create admonitions for notes, warnings, and tips.
- ⚙️ **Simple Configuration**: Control your site's navigation from a single `config.yaml` file.
- 📦 **Zero Dependencies**: The final site is just pure HTML, CSS, and JS. No backend needed.
- 🐢 **Live Reload Server**: See your changes instantly as you write. However, it is not as robust as other alternative such as VitePress. You may have to manually refersh at times. u can `Ctrl+r` for quick refresh though.

---

## ⚡ Quick Start Guide

### 1. Installation

```bash
pip install vai
````

### 2. Initialize Your Project

This command creates the necessary folder structure in your current directory.

```bash
vai init
```

This will create the following structure:

```
src_md/       # Markdown content
static/       # CSS, JS, and image assets
templates/    # HTML templates
config.yaml   # Site configuration
```

### 3. Start the Development Server

```bash
vai run
```

Your site is now running at `http://localhost:6600`. The server will automatically rebuild and refresh the browser when changes are made to `src_md/`, `static/`, or `config.yaml`.

### 4. Build for Production

```bash
vai build
```

This will generate your final static site in the `dist/` folder. You can host this on any static web server.

---

## 🧠 Understanding the Stucture

### Writing Content in `src_md/`

Vai uses folder and file names to build the site structure and sidebar.

* Uses a `number-Name` pattern for ordering.
* Folders = sidebar section.
* Markdown files = pages.

**Example:**

```
src_md/
├── 1-Introduction/
│   ├── 1-Welcome.md
│   └── 2-Installation-Guide.md
└── 2-Advanced-Features/
    └── 1-Search.md
```

**Resulting URLs:**

* `/introduction/welcome/`
* `/introduction/installation-guide/`
* `/advanced-features/search/`

### Configuring the Site with `config.yaml`

This file controls the header, navigation, and metadata (e.g., GitHub repo link). It's easy to understand and modify.

---

## 🎨 Customizing the Look

* Modify the site's CSS in `static/style.css`.
* Replace images/logos in the `static/` folder.


## 📚 Special Markdown Features

### Page Metadata

Add a title and date to any page by including a metadata block at the top:

```
+++
title: My Custom Page Title
date: January 1, 2024
+++

# Welcome to my page
...
```

### Admonition Blocks

Use call-out blocks for notes, warnings, and expandable content.

```markdown
:::note
This is a helpful note for the reader.
:::

:::warning Custom Warning Title
This is a critical warning with a custom title.
:::

:::details Click to Expand
This content is hidden by default and can be expanded.
:::
```

more example and visual showcase in the [documentation]()

---

## 🚀 Deployment

### General Hosting (Netlify, Vercel, etc.)

1. Run:

   ```bash
   vai build
   ```

2. Upload the contents of the `dist/` folder to your host.

### GitHub Pages

1. In `config.yaml`, set:

   ```yaml
   github_repo_name: YOUR_REPO_NAME # Note: it is case sensitive
   ```

2. Run:

   ```bash
   vai build --github
   ```

3. Push the contents of the `dist/` folder to the `github-pages` branch.
