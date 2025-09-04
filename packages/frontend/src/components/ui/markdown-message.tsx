import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Copy, Check } from 'lucide-react'
import { Button } from './button'
import { toast } from 'sonner'

interface MarkdownMessageProps {
  content: string
  className?: string
}

export function MarkdownMessage({ content, className = '' }: MarkdownMessageProps) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      toast.success('Message copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      toast.error('Failed to copy message')
    }
  }

  return (
    <div className={`relative group ${className}`}>
      <div className="prose prose-sm dark:prose-invert max-w-none prose-pre:bg-muted prose-pre:border prose-pre:border-border prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-none prose-code:after:content-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Custom styling for code blocks
            pre: ({ children, ...props }) => (
              <pre
                {...props}
                className="bg-muted border border-border rounded-lg p-4 overflow-x-auto text-sm"
              >
                {children}
              </pre>
            ),
            // Custom styling for inline code
            code: ({ children, className, ...props }) => {
              const isInline = !className
              if (isInline) {
                return (
                  <code
                    {...props}
                    className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono"
                  >
                    {children}
                  </code>
                )
              }
              return (
                <code {...props} className={className}>
                  {children}
                </code>
              )
            },
            // Custom styling for tables
            table: ({ children, ...props }) => (
              <div className="overflow-x-auto">
                <table
                  {...props}
                  className="min-w-full border-collapse border border-border"
                >
                  {children}
                </table>
              </div>
            ),
            th: ({ children, ...props }) => (
              <th
                {...props}
                className="border border-border bg-muted px-3 py-2 text-left font-semibold"
              >
                {children}
              </th>
            ),
            td: ({ children, ...props }) => (
              <td {...props} className="border border-border px-3 py-2">
                {children}
              </td>
            ),
            // Custom styling for blockquotes
            blockquote: ({ children, ...props }) => (
              <blockquote
                {...props}
                className="border-l-4 border-primary pl-4 italic text-muted-foreground"
              >
                {children}
              </blockquote>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
      
      {/* Copy button - appears on hover */}
      <Button
        variant="ghost"
        size="sm"
        onClick={copyToClipboard}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 h-8 w-8 p-0 bg-background/80 backdrop-blur-sm hover:bg-accent"
      >
        {copied ? (
          <Check className="w-3.5 h-3.5 text-green-600" />
        ) : (
          <Copy className="w-3.5 h-3.5" />
        )}
      </Button>
    </div>
  )
}