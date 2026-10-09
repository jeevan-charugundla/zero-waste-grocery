import { useState, useRef, useEffect } from "react";
import { Sparkles, SendHorizonal, CircleAlert, Info } from "lucide-react";
import { PageHeader, Panel, Badge, GhostButton } from "../components/ui";
import { DemoBadge } from "../components/ui";

interface Message {
  id: number;
  role: "user" | "assistant";
  text: string;
  facts?: string[];
  recommendation?: string;
  evidence?: string;
}

const suggestions = [
  "Which products expire soon?",
  "What inventory is at risk?",
  "Which items may stock out?",
  "What should I review today?",
  "How can I reduce today's waste?",
];

/* Illustrative canned answers (demo mode) — none of these query a real backend. */
function demoAnswer(q: string): Message {
  const lower = q.toLowerCase();
  if (lower.includes("expire")) {
    return {
      id: 0,
      role: "assistant",
      text: "Two batches are expiring within 48 hours: whole milk batch M-104 (20 units, expires tomorrow) and strawberries batch S-221 (14 units, expires in 2 days). Both are highlighted in the freshness watch panel.",
      facts: ["Whole milk M-104: 20 units, expires tomorrow", "Strawberries S-221: 14 units, expires in 2 days"],
      recommendation: "Review the pending markdown recommendation for the milk batch before today's close.",
      evidence: "Illustrative demo response — not generated from live inventory data.",
    };
  }
  if (lower.includes("stock out") || lower.includes("stockout")) {
    return {
      id: 0,
      role: "assistant",
      text: "Baby spinach and free-range eggs may stock out earliest: spinach has 3 packs against a forecast of 7 packs/day, and eggs have 4 cartons against recurring demand.",
      facts: ["Spinach: 3 packs on hand vs 7/day predicted", "Eggs: 4 cartons on hand"],
      recommendation: "Expedite replenishment or cap display quantity to protect high-demand SKUs.",
      evidence: "Illustrative demo response — not generated from live inventory data.",
    };
  }
  if (lower.includes("review")) {
    return {
      id: 0,
      role: "assistant",
      text: "Today you have 4 recommendations awaiting review, led by the milk markdown proposal. Disposal decisions for 2 expired batch groups are also pending.",
      facts: ["4 pending recommendations", "10 units across 2 batches flagged for disposal"],
      recommendation: "Start with the markdown for whole milk — impact estimate is ₹340.",
      evidence: "Illustrative demo response — not generated from live inventory data.",
    };
  }
  if (lower.includes("waste") || lower.includes("reduce")) {
    return {
      id: 0,
      role: "assistant",
      text: "The quickest waste reductions today are promoting the breakfast bundle and transferring surplus leafy greens to Store South, which has forecasted demand.",
      facts: ["Bundle potential: ₹810 estimated recovery", "Transfer saves ≈ ₹620 in avoided waste"],
      recommendation: "Approve the greens transfer first — it expires fastest after milk.",
      evidence: "Illustrative demo response — not generated from live inventory data.",
    };
  }
  return {
    id: 0,
    role: "assistant",
    text: "I'm running in demo mode, so my answers are illustrative. Try asking about expiring products, stockout risk, or what to review today.",
    evidence: "Demo mode — no live data queried.",
  };
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nextId = useRef(1);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, thinking]);

  const ask = (q: string) => {
    const text = q.trim();
    if (!text || thinking) return;
    setError(null);
    const userMsg: Message = { id: nextId.current++, role: "user", text };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setThinking(true);
    window.setTimeout(() => {
      setThinking(false);
      const answer = demoAnswer(text);
      setMessages((m) => [...m, { ...answer, id: nextId.current++ }]);
    }, 900);
  };

  return (
    <>
      <PageHeader
        eyebrow="DEMO WORKSPACE"
        title="AI Store Copilot"
        subtitle="Ask about freshness, stock risk, and daily priorities. This interface is in demo mode — responses are illustrative and ready to connect to the live Copilot endpoint in a future milestone."
        action={<DemoBadge />}
      />

      <div className="grid gap-4 xl:grid-cols-[1.5fr_0.5fr]">
        {/* Conversation panel */}
        <Panel
          title="Conversation"
          subtitle="Demo mode · no live data is queried"
          bodyClassName="flex flex-col"
        >
          <div
            ref={scrollRef}
            className="flex min-h-[380px] flex-col gap-3 overflow-y-auto pr-1"
            aria-live="polite"
          >
            {messages.length === 0 && !thinking && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-[#eaf4ed] text-[#287452]">
                  <Sparkles size={22} />
                </span>
                <p className="mt-3 text-[13px] font-semibold text-[#39473d]">
                  Ask your store Copilot a question
                </p>
                <p className="mt-1 max-w-sm text-[11px] text-[#9aa39b]">
                  Example: “Which products expire soon?” — answers in demo mode are illustrative
                  and clearly labelled.
                </p>
              </div>
            )}

            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-[12px] leading-relaxed ${
                    m.role === "user"
                      ? "bg-[#287452] text-white"
                      : "border border-[#eef0ec] bg-[#f8f9f6] text-[#39473d]"
                  }`}
                >
                  <p>{m.text}</p>
                  {m.facts && m.facts.length > 0 && (
                    <div className="mt-2 border-l-2 border-[#c3d9cc] pl-2.5">
                      <p className="text-[9px] font-bold tracking-widest text-[#8a958d]">FACTS</p>
                      <ul className="mt-1 flex flex-col gap-0.5">
                        {m.facts.map((f, i) => (
                          <li key={i} className="text-[11px] text-[#5c6b62]">• {f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {m.recommendation && (
                    <div className="mt-2 border-l-2 border-[#d9c9ef] pl-2.5">
                      <p className="text-[9px] font-bold tracking-widest text-[#816ac1]">
                        SUGGESTED ACTION
                      </p>
                      <p className="mt-1 text-[11px] text-[#5c6b62]">{m.recommendation}</p>
                    </div>
                  )}
                  {m.evidence && (
                    <p className="mt-2 flex items-center gap-1 text-[9.5px] italic text-[#a9b1a9]">
                      <Info size={10} /> {m.evidence}
                    </p>
                  )}
                </div>
              </div>
            ))}

            {thinking && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 rounded-2xl border border-[#eef0ec] bg-[#f8f9f6] px-4 py-3">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#37866a] [animation-delay:0ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#37866a] [animation-delay:150ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#37866a] [animation-delay:300ms]" />
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2 rounded-xl border border-[#f2d8d0] bg-[#fdf1ee] px-3 py-2 text-[11px] text-[#8f4a37]">
                <CircleAlert size={13} /> {error}
              </div>
            )}
          </div>

          {/* Chips */}
          <div className="mt-3 flex flex-wrap gap-1.5">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => ask(s)}
                disabled={thinking}
                className="rounded-full border border-[#e4e9e2] bg-white px-2.5 py-1 text-[10.5px] font-semibold text-[#45614e] transition hover:border-[#227952] hover:text-[#1b6143] disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40"
              >
                {s}
              </button>
            ))}
          </div>

          {/* Input */}
          <form
            className="mt-3 flex items-center gap-2 border-t border-[#eff1ed] pt-3"
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about expiring stock, at-risk inventory, or today's priorities…"
              aria-label="Ask the Copilot a question"
              className="min-w-0 flex-1 rounded-xl border border-[#e4e9e2] bg-white px-3.5 py-2.5 text-[12px] text-[#39473d] placeholder:text-[#a9b1a9] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40"
            />
            <button
              type="submit"
              disabled={!input.trim() || thinking}
              className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#287452] text-white transition hover:bg-[#1b6143] disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40"
              aria-label="Send question"
            >
              <SendHorizonal size={15} />
            </button>
          </form>
        </Panel>

        {/* Side panel */}
        <div className="flex flex-col gap-4">
          <Panel title="Demo mode" subtitle="What this means">
            <ul className="flex flex-col gap-2.5 text-[11px] leading-relaxed text-[#5c6b62]">
              <li>• Responses are illustrative and not generated from live store data.</li>
              <li>• No Supabase or Groq request is made from this page.</li>
              <li>• The UI is ready to connect to the real Copilot endpoint once integrated.</li>
            </ul>
          </Panel>
          <Panel title="Answer structure" subtitle="How responses are organized">
            <ul className="flex flex-col gap-2 text-[11px] text-[#5c6b62]">
              <li>
                <Badge tone="green">FACTS</Badge> <span className="ml-1.5">Numerical observations</span>
              </li>
              <li>
                <Badge tone="violet">SUGGESTED ACTION</Badge>{" "}
                <span className="ml-1.5">Recommendation to review</span>
              </li>
              <li>
                <Info size={11} className="mr-1 inline text-[#a9b1a9]" />
                <span className="text-[10.5px] italic text-[#9aa39b]">Source note</span>
              </li>
            </ul>
          </Panel>
          <Panel title="Retry demo" subtitle="Local UI states">
            <GhostButton
              className="justify-center"
              onClick={() => {
                setMessages([]);
                setInput("");
                setError("Simulated error cleared — try asking again. (Demo state only.)");
                window.setTimeout(() => setError(null), 2400);
              }}
            >
              Reset conversation
            </GhostButton>
          </Panel>
        </div>
      </div>
    </>
  );
}
