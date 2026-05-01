"use client";

import { useEffect, useState } from "react";

import type { ChatMessage } from "@/lib/types";

import { SourcePills } from "./SourcePills";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const [html, setHtml] = useState("");

  useEffect(() => {
    if (isUser || !message.content) {
      setHtml("");
      return;
    }
    let cancelled = false;
    import("@agentos/ui/markdown").then(({ renderMarkdown }) => {
      renderMarkdown(message.content).then((rendered) => {
        if (!cancelled) setHtml(rendered);
      });
    });
    return () => {
      cancelled = true;
    };
  }, [isUser, message.content]);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "bg-accent-blue text-white"
            : "assistant-bubble border border-bg-elevated bg-bg-card text-text-primary"
        }`}
      >
        {message.attachments?.length ? (
          <div className="mb-2 flex flex-wrap gap-1">
            {message.attachments.map((att) => (
              <span
                key={att.filename}
                className="rounded-md bg-bg-elevated px-2 py-0.5 font-mono text-[10px] text-text-secondary"
              >
                {att.filename}
              </span>
            ))}
          </div>
        ) : null}

        {isUser ? (
          message.content ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : null
        ) : message.content ? (
          <>
            {html ? (
              <div dangerouslySetInnerHTML={{ __html: html }} />
            ) : (
              <p className="whitespace-pre-wrap">{message.content}</p>
            )}
            <SourcePills web={message.webSources} rag={message.ragSources} />
          </>
        ) : (
          <span className="inline-flex items-center gap-1 text-text-muted">
            <span className="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted" />
            <span className="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted" />
            <span className="thinking-dot inline-block h-1.5 w-1.5 rounded-full bg-text-muted" />
          </span>
        )}
      </div>
    </div>
  );
}
