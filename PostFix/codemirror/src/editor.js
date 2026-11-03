// PostFix's Markdown editor: CodeMirror 6 with a live preview like Obsidian's. Markdown marks
// (# ** [ ]( ) ...) are hidden, and images, check boxes, bullets, rules and tables are drawn,
// as long as the cursor is not in that element; there the raw Markdown shows for editing.
// Bundled into one file (npm run build) and loaded by PostFix in QtWebEngine.

import { EditorState, StateField, RangeSetBuilder } from "@codemirror/state";
import { EditorView, Decoration, WidgetType, keymap, drawSelection } from "@codemirror/view";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { markdown, markdownLanguage, markdownKeymap } from "@codemirror/lang-markdown";
import { ensureSyntaxTree, syntaxHighlighting, HighlightStyle } from "@codemirror/language";
import { tags } from "@lezer/highlight";

// --- Widgets ----------------------------------------------------------------------------------

class ImageWidget extends WidgetType {
  constructor(src, alt, width) { super(); this.src = src; this.alt = alt; this.width = width; }
  eq(other) { return other.src === this.src && other.alt === this.alt && other.width === this.width; }
  toDOM() {
    const img = document.createElement("img");
    img.src = this.src;
    img.alt = this.alt;
    img.className = "cm-md-image";
    if (this.width) img.style.width = this.width + "px";
    return img;
  }
}

class CheckboxWidget extends WidgetType {
  constructor(checked, pos) { super(); this.checked = checked; this.pos = pos; }
  eq(other) { return other.checked === this.checked && other.pos === this.pos; }
  toDOM(view) {
    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = this.checked;
    box.className = "cm-md-task";
    box.addEventListener("mousedown", (event) => {
      event.preventDefault();  // toggles without moving the cursor into the marker
      view.dispatch({ changes: { from: this.pos + 1, to: this.pos + 2, insert: this.checked ? " " : "x" } });
    });
    return box;
  }
  ignoreEvent() { return false; }
}

class BulletWidget extends WidgetType {
  eq() { return true; }
  toDOM() { const s = document.createElement("span"); s.className = "cm-md-bullet"; s.textContent = "•"; return s; }
}

class RuleWidget extends WidgetType {
  eq() { return true; }
  toDOM() { const hr = document.createElement("span"); hr.className = "cm-md-rule"; return hr; }
}

class TableWidget extends WidgetType {
  constructor(source) { super(); this.source = source; }
  eq(other) { return other.source === this.source; }
  toDOM() {
    const cells = (line) => line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
    const lines = this.source.split("\n").filter((l) => l.trim());
    const table = document.createElement("table");
    table.className = "cm-md-table";
    lines.forEach((line, index) => {
      if (index === 1 && /^[\s|:-]+$/.test(line)) return;  // the |---|---| line
      const row = table.insertRow();
      for (const text of cells(line)) {
        const cell = document.createElement(index === 0 ? "th" : "td");
        cell.textContent = text;
        row.appendChild(cell);
      }
    });
    return table;
  }
  ignoreEvent() { return false; }  // a click goes to the editor: the cursor enters, raw shows
}

// --- The live preview -------------------------------------------------------------------------

const hidden = Decoration.replace({});

function touches(state, from, to) {
  // The cursor (or a selection) is in this element, or right at its edge.
  return state.selection.ranges.some((r) => r.from <= to && r.to >= from);
}

function lineTouched(state, pos) {
  const line = state.doc.lineAt(pos);
  return touches(state, line.from, line.to);
}

function linkTarget(state, node) {
  let url = "";
  for (let child = node.firstChild; child; child = child.nextSibling) {
    if (child.name === "URL") url = state.sliceDoc(child.from, child.to);
  }
  return url.replace(/^<|>$/g, "");
}

function buildDecorations(state) {
  const tree = ensureSyntaxTree(state, state.doc.length, 200);
  const found = [];  // [from, to, decoration]; sorted and added in order below
  const add = (from, to, deco) => found.push([from, to, deco]);
  if (!tree) return Decoration.none;

  tree.iterate({
    enter: (node) => {
      const { name, from, to } = node;
      const heading = /^ATXHeading(\d)$/.exec(name);
      if (heading) {
        add(from, from, Decoration.line({ class: "cm-md-h" + heading[1] }));
        return;
      }
      switch (name) {
        case "HeaderMark": {
          if (!lineTouched(state, from)) {
            const after = state.sliceDoc(to, to + 1) === " " ? to + 1 : to;  // "# " goes with its space
            add(from, after, hidden);
          }
          return;
        }
        case "EmphasisMark":
        case "CodeMark":
        case "StrikethroughMark": {
          const parent = node.node.parent;
          if (parent && parent.name !== "FencedCode" && !touches(state, parent.from, parent.to)) add(from, to, hidden);
          return;
        }
        case "Link": {
          if (touches(state, from, to)) return false;
          const href = linkTarget(state, node.node);
          const marks = [];
          for (let c = node.node.firstChild; c; c = c.nextSibling) if (c.name === "LinkMark") marks.push(c);
          if (marks.length >= 2) {
            add(from, marks[0].to, hidden);
            add(marks[0].to, marks[1].from, Decoration.mark({ class: "cm-md-link", attributes: { "data-href": href } }));
            add(marks[1].from, to, hidden);
          }
          return false;
        }
        case "Image": {
          if (touches(state, from, to)) return false;
          const text = state.sliceDoc(from, to);
          const match = /^!\[([^\]]*)\]\(\s*<?([^)>]*)>?\s*\)$/.exec(text);
          if (match) {
            const [alt, width] = match[1].split("|");  // Obsidian: ![alt|300](picture.png)
            add(from, to, Decoration.replace({ widget: new ImageWidget(match[2], alt, /^\d+$/.test(width || "") ? width : "") }));
          }
          return false;
        }
        case "Task": {
          const marker = node.node.firstChild;
          if (marker && marker.name === "TaskMarker" && !touches(state, marker.from, marker.to)) {
            const checked = /x/i.test(state.sliceDoc(marker.from, marker.to));
            add(marker.from, marker.to, Decoration.replace({ widget: new CheckboxWidget(checked, marker.from) }));
            if (checked) add(marker.to, to, Decoration.mark({ class: "cm-md-done" }));
          }
          return;
        }
        case "ListMark": {
          const item = node.node.parent;
          const isTask = item && item.getChild("Task");
          const bullet = /^[-*+]$/.test(state.sliceDoc(from, to));
          if (touches(state, from, to + 1)) return;
          if (isTask) add(from, Math.min(to + 1, state.doc.lineAt(from).to), hidden);
          else if (bullet) add(from, to, Decoration.replace({ widget: new BulletWidget() }));
          return;
        }
        case "QuoteMark": {
          add(state.doc.lineAt(from).from, state.doc.lineAt(from).from, Decoration.line({ class: "cm-md-quote" }));
          if (!lineTouched(state, from)) {
            const after = state.sliceDoc(to, to + 1) === " " ? to + 1 : to;
            add(from, after, hidden);
          }
          return;
        }
        case "Escape": {
          // \* shows as * - the backslash only while the cursor is there.
          if (!touches(state, from, to)) add(from, from + 1, hidden);
          return;
        }
        case "HorizontalRule": {
          if (!lineTouched(state, from)) add(from, to, Decoration.replace({ widget: new RuleWidget() }));
          return;
        }
        case "FencedCode": {
          for (let pos = from; pos <= to;) {
            const line = state.doc.lineAt(pos);
            add(line.from, line.from, Decoration.line({ class: "cm-md-codeblock" }));
            pos = line.to + 1;
          }
          return;
        }
        case "Table": {
          if (touches(state, from, to)) return false;
          add(from, to, Decoration.replace({ widget: new TableWidget(state.sliceDoc(from, to)), block: true }));
          return false;
        }
      }
    },
  });

  // Line decorations first at a position, then by start and end: RangeSetBuilder needs order.
  found.sort((a, b) => a[0] - b[0] || (a[2].startSide ?? 0) - (b[2].startSide ?? 0) || a[1] - b[1]);
  const builder = new RangeSetBuilder();
  let last = -1;
  for (const [from, to, deco] of found) {
    if (from < last && deco !== Decoration.none && !deco.spec.class) continue;  // skip overlaps
    builder.add(from, to, deco);
    if (to > from) last = Math.max(last, to);
  }
  return builder.finish();
}

const livePreview = StateField.define({
  create: (state) => buildDecorations(state),
  update: (decorations, tr) => (tr.docChanged || tr.selection ? buildDecorations(tr.state) : decorations),
  provide: (field) => EditorView.decorations.from(field),
});

// --- Look and keys ----------------------------------------------------------------------------

const markdownHighlight = HighlightStyle.define([
  { tag: tags.strong, fontWeight: "700" },
  { tag: tags.emphasis, fontStyle: "italic" },
  { tag: tags.strikethrough, textDecoration: "line-through" },
  { tag: tags.monospace, fontFamily: "var(--mono)", background: "var(--code-bg)", borderRadius: "3px" },
  { tag: tags.link, color: "var(--accent)" },
  { tag: tags.url, color: "var(--muted)" },
  { tag: [tags.processingInstruction, tags.meta], color: "var(--muted)" },
  { tag: tags.quote, color: "var(--muted)" },
]);

const theme = EditorView.theme({
  "&": { height: "100%", fontSize: "16px", color: "var(--fg)", backgroundColor: "transparent" },
  "&.cm-focused": { outline: "none" },
  ".cm-scroller": { fontFamily: "var(--body)", lineHeight: "1.65", overflow: "auto" },
  ".cm-content": { maxWidth: "720px", margin: "0 auto", padding: "28px 24px 120px", caretColor: "var(--accent)" },
  ".cm-line": { padding: "0" },
  ".cm-md-h1": { fontSize: "1.8em", fontWeight: "700", lineHeight: "1.3", paddingTop: "0.4em" },
  ".cm-md-h2": { fontSize: "1.45em", fontWeight: "700", lineHeight: "1.3", paddingTop: "0.35em" },
  ".cm-md-h3": { fontSize: "1.2em", fontWeight: "700", paddingTop: "0.3em" },
  ".cm-md-h4, .cm-md-h5, .cm-md-h6": { fontWeight: "700" },
  ".cm-md-link": { color: "var(--accent)", textDecoration: "underline", cursor: "pointer" },
  ".cm-md-image": { display: "inline-block", maxWidth: "100%", borderRadius: "4px", verticalAlign: "bottom" },
  ".cm-md-task": { margin: "0 0.45em 0 0", verticalAlign: "middle", cursor: "pointer" },
  ".cm-md-done": { color: "var(--muted)", textDecoration: "line-through" },
  ".cm-md-bullet": { color: "var(--muted)", padding: "0 0.25em" },
  ".cm-md-quote": { borderLeft: "3px solid var(--quote)", paddingLeft: "12px !important", color: "var(--muted)" },
  ".cm-md-rule": { display: "inline-block", width: "100%", borderTop: "1px solid var(--quote)", verticalAlign: "middle" },
  ".cm-md-codeblock": { fontFamily: "var(--mono)", fontSize: "0.92em", background: "var(--code-bg)" },
  ".cm-md-table": { borderCollapse: "collapse", margin: "6px 0" },
  ".cm-md-table th, .cm-md-table td": { border: "1px solid var(--quote)", padding: "4px 10px", textAlign: "left" },
  ".cm-md-table th": { background: "var(--code-bg)" },
});

function wrapWith(mark) {
  return (view) => {
    const changes = view.state.changeByRange((range) => {
      const text = view.state.sliceDoc(range.from, range.to);
      const wrapped = text.startsWith(mark) && text.endsWith(mark) && text.length >= 2 * mark.length;
      const insert = wrapped ? text.slice(mark.length, text.length - mark.length) : mark + text + mark;
      const anchor = range.empty ? range.from + mark.length : range.from;
      return { changes: { from: range.from, to: range.to, insert },
               range: range.empty ? { anchor, head: anchor } : { anchor: range.from, head: range.from + insert.length } };
    });
    view.dispatch(view.state.update(changes, { scrollIntoView: true, userEvent: "input" }));
    return true;
  };
}

// --- The editor PostFix talks to --------------------------------------------------------------

export function create(parent, { doc = "", onChange = () => {}, onLink = () => {} } = {}) {
  const view = new EditorView({
    parent,
    state: EditorState.create({
      doc,
      extensions: [
        history(),
        drawSelection(),
        EditorView.lineWrapping,
        markdown({ base: markdownLanguage }),
        syntaxHighlighting(markdownHighlight),
        livePreview,
        theme,
        keymap.of([{ key: "Mod-b", run: wrapWith("**") }, { key: "Mod-i", run: wrapWith("*") },
                   ...markdownKeymap, ...defaultKeymap, ...historyKeymap, indentWithTab]),
        EditorView.updateListener.of((update) => { if (update.docChanged) onChange(update.state.doc.toString()); }),
        EditorView.domEventHandlers({
          mousedown: (event) => {
            const link = event.target.closest && event.target.closest(".cm-md-link");
            if (!link) return false;
            event.preventDefault();  // a click follows the link; the cursor stays where it was
            onLink(link.getAttribute("data-href"));
            return true;
          },
        }),
      ],
    }),
  });
  return {
    view,
    getDoc: () => view.state.doc.toString(),
    // A change from outside: only the part that differs is replaced, so the cursor stays put.
    setDoc: (text) => {
      const current = view.state.doc.toString();
      if (text === current) return;
      let start = 0;
      while (start < current.length && start < text.length && current[start] === text[start]) start++;
      let endOld = current.length, endNew = text.length;
      while (endOld > start && endNew > start && current[endOld - 1] === text[endNew - 1]) { endOld--; endNew--; }
      view.dispatch({ changes: { from: start, to: endOld, insert: text.slice(start, endNew) }, userEvent: "outside" });
    },
    focus: () => view.focus(),
  };
}
