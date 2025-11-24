// Lightweight Markdown renderer (basic support for headings, lists, bold/italic, code, links, line breaks)
(function(global) {
  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function inlineFormat(text) {
    let out = escapeHtml(text);
    out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
    out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    out = out.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    return out;
  }

  function renderMarkdown(text) {
    if (!text) return '';
    const lines = text.replace(/\r\n/g, '\n').split('\n');
    let html = '';
    let inList = false;
    let inCode = false;

    const closeList = () => {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
    };

    lines.forEach((line, idx) => {
      // Code block fence
      if (line.trim().startsWith('```')) {
        if (inCode) {
          html += '</code></pre>';
          inCode = false;
        } else {
          closeList();
          inCode = true;
          html += '<pre><code>';
        }
        return;
      }

      if (inCode) {
        html += escapeHtml(line) + '\n';
        return;
      }

      // List item
      if (/^(\s*[-*+]\s+)/.test(line)) {
        if (!inList) {
          closeList();
          inList = true;
          html += '<ul>';
        }
        const content = line.replace(/^(\s*[-*+]\s+)/, '');
        html += `<li>${inlineFormat(content)}</li>`;
        return;
      } else {
        closeList();
      }

      // Heading
      const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
      if (headingMatch) {
        const level = headingMatch[1].length;
        const content = headingMatch[2];
        html += `<h${level}>${inlineFormat(content)}</h${level}>`;
        return;
      }

      // Blank line
      if (line.trim() === '') {
        html += '<br>';
        return;
      }

      // Paragraph/normal text
      html += `<p>${inlineFormat(line)}</p>`;
    });

    closeList();
    if (inCode) html += '</code></pre>';
    return html;
  }

  global.memoMarkdownRender = renderMarkdown;
})(window);
