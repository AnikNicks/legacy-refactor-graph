import { useMemo } from "react";
import { marked } from "marked";

// Content is our own pipeline's output (synthesis_report.md, written by the
// synthesizer step against this repo), not third-party/user-submitted text
// - rendered trusted, no separate sanitizer pass.
marked.setOptions({ gfm: true });

export function SynthesisPanel({ text }: { text: string | null }) {
  const html = useMemo(() => (text ? marked.parse(text, { async: false }) : ""), [text]);

  if (!text) {
    return (
      <div className="panel">
        <h2>Synthesis / roadmap</h2>
        <p className="empty">No output/synthesis_report.md yet — Phase 6 hasn't run.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h2>Synthesis / roadmap</h2>
      <div className="markdown-body" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
