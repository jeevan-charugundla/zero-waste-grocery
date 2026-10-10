import { useState } from "react";
import { Sliders, Bell, Check } from "lucide-react";

export default function SettingsPage() {
  const [autoApprove, setAutoApprove] = useState(false);
  const [maxMarkdown, setMaxMarkdown] = useState(50);
  const [telegramAlerts, setTelegramAlerts] = useState(true);

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#16271e] sm:text-3xl">
          System & Simulation Settings
        </h1>
        <p className="mt-1 text-sm text-[#5e7165]">
          Configure autonomous agent policy guardrails, Telegram push notifications, and network parameters.
        </p>
      </div>

      <div className="rounded-3xl border border-[#dfe5df] bg-white p-6 shadow-sm space-y-6">
        <div>
          <h3 className="text-base font-bold text-[#1a2d21] flex items-center gap-2">
            <Sliders size={18} className="text-[#10b981]" />
            <span>Agent Guardrails & Approval Rules</span>
          </h3>
          <p className="mt-1 text-xs text-[#63776a]">
            Define upper bounds for automated agent proposals before requiring store manager sign-off.
          </p>

          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between border-b border-[#f0f4ef] pb-3 text-xs">
              <div>
                <strong className="block text-[#1d2f23]">Autonomous Auto-Approval</strong>
                <span className="text-[#6d8073]">Allow proposals with confidence &gt; 95% to execute without manual click</span>
              </div>
              <input
                type="checkbox"
                checked={autoApprove}
                onChange={(e) => setAutoApprove(e.target.checked)}
                className="rounded accent-[#10b981] h-4 w-4 cursor-pointer"
              />
            </div>

            <div className="border-b border-[#f0f4ef] pb-3 text-xs">
              <div className="flex justify-between font-semibold text-[#1d2f23]">
                <span>Maximum Allowed Markdown Limit</span>
                <span>{maxMarkdown}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="75"
                value={maxMarkdown}
                onChange={(e) => setMaxMarkdown(Number(e.target.value))}
                className="mt-2 w-full accent-[#10b981]"
              />
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-base font-bold text-[#1a2d21] flex items-center gap-2">
            <Bell size={18} className="text-[#10b981]" />
            <span>Telegram Bot & Mobile Alerts</span>
          </h3>
          <p className="mt-1 text-xs text-[#63776a]">
            Connected Telegram Bot: <strong>@FreshwiseZeroWasteBot</strong> (Status: Connected)
          </p>

          <div className="mt-4 flex items-center justify-between text-xs">
            <div>
              <strong className="block text-[#1d2f23]">Proactive Morning Briefings</strong>
              <span className="text-[#6d8073]">Dispatch daily 8:00 AM summary to manager chat</span>
            </div>
            <input
              type="checkbox"
              checked={telegramAlerts}
              onChange={(e) => setTelegramAlerts(e.target.checked)}
              className="rounded accent-[#10b981] h-4 w-4 cursor-pointer"
            />
          </div>
        </div>

        <div className="pt-2">
          <button
            onClick={() => alert("Settings saved successfully!")}
            className="inline-flex items-center gap-2 rounded-xl bg-[#186441] px-5 py-2 text-xs font-bold text-white shadow hover:bg-[#135134] transition"
          >
            <Check size={14} />
            <span>Save Configuration</span>
          </button>
        </div>
      </div>
    </div>
  );
}
