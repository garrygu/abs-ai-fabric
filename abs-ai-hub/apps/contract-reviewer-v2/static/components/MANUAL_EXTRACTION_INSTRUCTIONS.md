# Manual Extraction Instructions for Document Review Tab

## Line Range to Extract

**From index.html: Lines 56-1491**

## Steps:

1. Open `index.html`
2. Copy lines **56-1491** (the entire Document Review tab content)
3. Create file `components/document-review.html`
4. Paste the copied content into the new file
5. Wrap it with the Document Review Tab comment:
   ```html
   <!-- Document Review Tab -->
   <div x-show="mainTab === 'documents'" x-cloak class="flex h-screen">
   <!-- Paste lines 56-1491 here -->
   </div>
   ```

## What Gets Extracted

- Left Panel (Document Navigation)
- Middle Panel (Analysis results)
- Right Panel (Chat & Insights - simplified version)

## After Extraction

In index.html, lines 56-1491 should be replaced with:
```html
<div id="document-review-container"></div>
```

The content is currently between lines 56-1491 and marked with comments showing where extraction boundaries are.




