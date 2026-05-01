"use client";

import { useRef, useState, type ChangeEvent, type KeyboardEvent } from "react";

import { useChatStore } from "@/lib/store";

type Mode = "chat" | "analysis" | "research";

const ACCEPT = ".pdf,.docx,.csv,.xlsx,.json,.md,.html,.txt,.tsv,.xml,.parquet";

export function ChatComposer() {
  const [value, setValue] = useState("");
  const [mode, setMode] = useState<Mode>("chat");
  const [uploading, setUploading] = useState(false);
  const send = useChatStore((s) => s.send);
  const ingestFile = useChatStore((s) => s.ingestFile);
  const streaming = useChatStore((s) => s.streaming);
  const useRag = useChatStore((s) => s.useRag);
  const useWeb = useChatStore((s) => s.useWeb);
  const setUseRag = useChatStore((s) => s.setUseRag);
  const setUseWeb = useChatStore((s) => s.setUseWeb);
  const ref = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const submit = async () => {
    const text = value.trim();
    if (!text || streaming) return;
    setValue("");
    autosize();
    await send(text, { contextType: mode });
  };

  const autosize = () => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await ingestFile(file);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const ragBtn = `rounded-md border px-2 py-1 text-[11px] font-medium transition-colors ${
    useRag
      ? "border-accent-blue bg-accent-blue/10 text-accent-blue"
      : "border-bg-elevated text-text-secondary hover:border-accent-blue hover:text-accent-blue"
  }`;
  const webBtn = `rounded-md border px-2 py-1 text-[11px] font-medium transition-colors ${
    useWeb
      ? "border-accent-blue bg-accent-blue/10 text-accent-blue"
      : "border-bg-elevated text-text-secondary hover:border-accent-blue hover:text-accent-blue"
  }`;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 px-1">
        <button type="button" className={ragBtn} onClick={() => setUseRag(!useRag)}>
          RAG
        </button>
        <button type="button" className={webBtn} onClick={() => setUseWeb(!useWeb)}>
          Web
        </button>
        <span className="text-[11px] text-text-muted">
          {useRag || useWeb ? "El agente investigará antes de responder" : "Respuesta directa"}
        </span>
      </div>

      <div className="flex items-end gap-2 rounded-2xl border border-bg-elevated bg-bg-card px-3 py-2 transition-colors focus-within:border-accent-blue">
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as Mode)}
          disabled={streaming}
          aria-label="Modo"
          className="rounded-lg bg-transparent px-2 py-2 text-xs font-medium text-text-secondary hover:bg-bg-elevated focus:outline-none"
        >
          <option value="chat">Chat</option>
          <option value="analysis">Análisis</option>
          <option value="research">Investigación</option>
        </select>

        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={streaming || uploading}
          className="rounded-lg border border-bg-elevated px-2 py-1.5 text-xs text-text-secondary transition-colors hover:border-accent-blue hover:text-accent-blue disabled:opacity-40"
          title="Adjuntar archivo (PDF, DOCX, CSV, XLSX, JSON, MD, HTML, TXT)"
        >
          {uploading ? "…" : "📎"}
        </button>
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          accept={ACCEPT}
          onChange={onFile}
        />

        <textarea
          ref={ref}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            autosize();
          }}
          onKeyDown={onKeyDown}
          placeholder="Escribe tu pregunta…"
          rows={1}
          disabled={streaming}
          className="flex-1 resize-none bg-transparent px-2 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
        />

        <button
          type="button"
          onClick={submit}
          disabled={!value.trim() || streaming}
          className="rounded-xl bg-accent-blue px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-blue-hover disabled:cursor-not-allowed disabled:bg-bg-elevated disabled:text-text-muted"
        >
          {streaming ? "…" : "Enviar"}
        </button>
      </div>
    </div>
  );
}
