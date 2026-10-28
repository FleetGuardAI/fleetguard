import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/utils/cn';

/**
 * MarkdownMessage
 * Renders assistant messages formatted in GitHub-Flavored Markdown.
 * Safe by default: raw HTML execution is disabled to prevent XSS.
 * Supports headings, bold/italic, ordered/unordered lists, code blocks,
 * blockquotes, and responsive styled tables.
 *
 * @param {string} content - Markdown text content
 * @param {boolean} suppressTables - When true, suppresses redundant markdown tables
 *                                   when structured interactive cards are already displayed.
 * @param {string} className - Optional container styling
 */
export default function MarkdownMessage({ content, suppressTables = false, className = '' }) {
  if (!content) return null;

  return (
    <div className={cn("markdown-content text-sm leading-relaxed text-content space-y-2", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ node, ...props }) => (
            <h1 className="text-base font-bold text-content mt-3 mb-1.5 first:mt-0 pb-1 border-b border-border/40" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-sm font-semibold text-content mt-2.5 mb-1 first:mt-0" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-xs font-semibold text-content mt-2 mb-1 first:mt-0" {...props} />
          ),
          p: ({ node, ...props }) => (
            <p className="text-sm leading-relaxed mb-2 last:mb-0 font-light" {...props} />
          ),
          strong: ({ node, ...props }) => (
            <strong className="font-semibold text-content" {...props} />
          ),
          em: ({ node, ...props }) => (
            <em className="italic" {...props} />
          ),
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-outside pl-4 space-y-1 mb-2 last:mb-0 text-sm font-light" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-outside pl-4 space-y-1 mb-2 last:mb-0 text-sm font-light" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="text-sm leading-relaxed" {...props} />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-2 border-brand-400 pl-3 italic text-content-secondary my-2 text-xs" {...props} />
          ),
          pre: ({ node, ...props }) => (
            <pre className="p-3 rounded-xl bg-surface-secondary/80 border border-border overflow-x-auto text-xs font-mono my-2 text-content" {...props} />
          ),
          code: ({ node, inline, className: codeClassName, children, ...props }) => {
            if (inline) {
              return (
                <code className="px-1.5 py-0.5 rounded bg-surface-secondary text-brand-600 font-mono text-xs border border-border/50" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={cn("text-xs font-mono", codeClassName)} {...props}>
                {children}
              </code>
            );
          },
          table: ({ node, ...props }) => {
            if (suppressTables) return null;
            return (
              <div className="overflow-x-auto my-2.5 rounded-xl border border-border shadow-xs bg-surface/40">
                <table className="min-w-full divide-y divide-border text-xs text-left" {...props} />
              </div>
            );
          },
          thead: ({ node, ...props }) => (
            <thead className="bg-surface-secondary/70 text-content font-semibold" {...props} />
          ),
          tbody: ({ node, ...props }) => (
            <tbody className="divide-y divide-border/60 bg-surface/30" {...props} />
          ),
          tr: ({ node, ...props }) => (
            <tr className="hover:bg-surface-secondary/30 transition-colors" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th className="px-3 py-2 text-[11px] font-semibold text-content uppercase tracking-wider" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="px-3 py-2 text-content text-xs font-light" {...props} />
          ),
          hr: ({ node, ...props }) => (
            <hr className="my-3 border-border/60" {...props} />
          ),
          a: ({ node, href, children, ...props }) => {
            const rawHref = (href || '').trim().toLowerCase();
            const isUnsafe = rawHref.startsWith('javascript:') || rawHref.startsWith('data:') || rawHref.startsWith('vbscript:');
            if (isUnsafe) {
              return <span>{children}</span>;
            }
            return (
              <a href={href} className="text-brand-500 underline hover:text-brand-600" target="_blank" rel="noopener noreferrer" {...props}>
                {children}
              </a>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
