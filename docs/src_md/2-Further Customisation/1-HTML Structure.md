# HTML Structure

This page is useful if you need to change the html structure for [every page](#every-page) or for [individual pages](#individual-page).

## Understanding the `src_html/` and `templates/` directory

### templates directory
There will usually be 2 html files and they are `layout_no_header.html` and `layout.html`. Lets take a while to understand what each file do.

when running `vai run` or `vai build`, it populates  `layout_no_header.html` with values from the `config.yaml` file, resulting in a `layout.html` file. Hence, if you want to make layout changes for all pages, you should only make changes in `layout_no_header.html` file. Any changes in `layout.html` will be futile as `vai build` will replace the structural changes with `layout_no_header.html` html structure.


### src_html directory
as you are running `vai run`, all the markdown files in `src_md/` gets converted to html in `src_html/`. The structure in `src_html/` is exactly the same as `src_md/` only except the numbers are gone (from the `number-Name` pattern system) and all md are in html.

As you make any changes to the HTML structure, you can see each html files and use it to debug as well. Useful if a certain strcuture is not working as intended (or styling and JS logic).

## How to change layout for every page?
read and understand the `layout_no_header.html` file from `templates/` and apply your desired changes.

## Individual page
Here it gets a bit tricky and **strongly not recommended** due to how tedious and difficult it is. You can techinically change the strucutre for each html page but it is impossible to view it with `vai run` as it will convert all markdown to html following your `layout_no_header.html`. There is almost no way to see that the individual changes is being applied. 

One bypass is to run the `src_html/` folder with [Python's http.server](https://docs.python.org/3/library/http.server.html) 

```python
python -m http.server 8000
```

 to see changes for individual site. But do take note that any changes done in `src_md/` will not be displayed in the corresponding `src_html/` files. This also means your `search_index.json` will not be updated (affects searching in your webiste as certain changes are not indexed) You can then do `vai build` as it only takes files from `src_html/` and minimise all of it.