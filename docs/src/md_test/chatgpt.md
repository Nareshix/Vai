# Markdown Features Demo

testing ok la lol

## 1. Headings

# H1
## H2
### H3
#### H4
##### H5
###### H6

---


- pok
- asd
- 123
- ads


## 2. Text Formatting

**Bold**  
*Italic*  
***Bold and Italic***  
~~Strikethrough~~  
<ins>Underlined (HTML)</ins>  
<sup>Superscript</sup> and <sub>Subscript</sub>

---

## 3. Lists

### Unordered List
- Item 1
  - Subitem 1
- Item 2

### Ordered List
1. First
2. Second
   1. Sub-second
3. Third

---

## 4. Links

  ### or am i

im a non link

[Inline Link](https://example.com)  
[Reference Link][example]  
<https://example.com>

[example]: https://example.com "Example Site"

---

## 5. Images

![Alt Text](/logo_test/logo.png)

---

## 6. Blockquote

> This is a blockquote.  
>> Nested blockquote.

---

## 7. Code

### Inline Code
Use `code()` inline.
ngl it looks weird but maybe cuz its too little ig hahaha true imma do it my own way test writing some random wrods to make it longerrrr hehehehehe heeeeeeeee hawwwwww-wwww
### Code Block (example)

```python
def hello_world():
    print("Hello, world!")
```


## 8. Horizontal Rule

---

## 9. Tables

### why hello there

| Syntax | Description |
|--------|-------------|
| Header | Title       |
| Cell   | Content     |
| Row 2  | More data   |

---

## 10. Task Lists

- [x] Write Markdown
- [x] Test rendering
- [ ] Add to GitHub
- [ ] Celebrate

---

## 11. Footnotes

Here is a footnote reference[^1] and another[^2].

[^1]: This is the first footnote.
[^2]: This is the second footnote, with **bold** text.

---

## 12. Escaping Characters

To display a literal character, prefix it with a backslash:

\*asterisks\*  
\_underscores\_  
\`backticks\`  
\#hash  
\[brackets\]

---

## 13. HTML in Markdown

<div style="background: black; padding: 10px;">
  You can use <strong>raw HTML</strong> if the renderer allows.
</div>

---

## 14. Definition Lists (CommonMark / GFM Extension)

Term 1  
: Definition of term 1

Term 2  
: Definition of term 2

Term 3  
: Another definition

---

## 15. Math (MathJax or KaTeX support required)

Inline math: \( E = mc^2 \)

Block math:

$$
f(x) = \int_{-\infty}^{\infty} e^{-x^2} dx
$$

---

## 16. Emojis (GitHub Flavored Markdown)

I love Markdown! :heart:  
Let's write more code! :computer: :coffee:

---

## 17. Syntax Highlighting (Code Fences)

```javascript
function greet(name) {
  return `Hello, ${name}!`;
}




#!/bin/bash
echo "Running script..."

{
  "name": "Markdown Demo",
  "version": "1.0.0"
}

```