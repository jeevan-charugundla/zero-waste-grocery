import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { supabaseConfigured } from "./lib/supabase";
import { getHealth } from "./lib/api";

const chartData = [
  { day: "Mon", sold: 112, waste: 14 }, { day: "Tue", sold: 126, waste: 11 },
  { day: "Wed", sold: 118, waste: 12 }, { day: "Thu", sold: 142, waste: 9 },
  { day: "Fri", sold: 154, waste: 8 }, { day: "Sat", sold: 171, waste: 7 },
  { day: "Sun", sold: 149, waste: 6 }
];
const navigation = ["Overview", "Inventory & expiry", "Demand forecasts", "AI recommendations", "Smart bundles", "Customer campaigns", "Donations & disposal", "AI Store Copilot", "Impact & analytics"];

export default function App() {
  const [active, setActive] = useState("Overview");
  const [apiStatus, setApiStatus] = useState("Checking API…");
  useEffect(() => { getHealth().then(() => setApiStatus("API connected")).catch(() => setApiStatus("API not connected")); }, []);
  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-icon">f</div><div><strong>freshwise</strong><small>ZERO-WASTE INTELLIGENCE</small></div></div>
      <div className="workspace"><span className="dot"/><div><small>WORKSPACE</small><strong>Demo Grocery Network</strong></div></div>
      <p className="nav-heading">WORKSPACE</p>
      <nav>{navigation.map((item, i) => <button key={item} className={active === item ? "nav active" : "nav"} onClick={() => setActive(item)}><span>{["⌂","▦","⌁","✳","◇","↗","♡","✧","◷"][i]}</span>{item}{item === "AI recommendations" && <i>4</i>}</button>)}</nav>
      <div className="sidebar-footer"><div className="api-status"><span className="dot"/><div><strong>{apiStatus}</strong><small>{supabaseConfigured ? "Supabase configured" : "Supabase needs setup"}</small></div></div><div className="user"><div className="avatar">JM</div><div><strong>Jordan Miller</strong><small>Store manager · Demo</small></div></div></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="crumb">Workspace <span>/</span> <strong>{active}</strong></div><div className="topbar-right"><span className="demo">● SIMULATED DATA</span><span>♧</span><div className="avatar">JM</div></div></header>
      <div className="page">
        <div className="page-heading"><div><small className="eyebrow">THURSDAY · DEMO WORKSPACE</small><h1>{active === "Overview" ? "Good morning, Jordan" : active}</h1><p>{active === "Overview" ? "Here's your freshness and waste snapshot across the grocery network." : "Module scaffolded — connect its Supabase-backed workflow in the next milestone."}</p></div><button className="primary" onClick={() => setActive("AI recommendations")}>✳ Review recommendations <b>4</b></button></div>
        <div className="alert"><span className="alert-icon">!</span><div><strong>Action needed: 4 recommendations await review</strong><p>3 batches are approaching expiry within 48 hours. Review suggested actions before today's close.</p></div><button onClick={() => setActive("AI recommendations")}>Review now →</button></div>
        <div className="section-heading"><div><h2>Network overview</h2><p>Illustrative demo values, not live measurements.</p></div><button className="filter">Last 7 days⌄</button></div>
        <div className="metrics">
          <Metric label="Inventory at risk" value="₹24,680" change="12.4%" note="vs. previous week" icon="◷"/>
          <Metric label="Waste rate" value="4.8%" change="1.2 pts" note="vs. previous week" icon="↘"/>
          <Metric label="Stockout risk" value="7 SKUs" change="2 new" note="need attention" icon="▤"/>
          <Metric label="Potential savings" value="₹18,420" change="Estimated" note="open proposals" icon="₹"/>
        </div>
        <div className="content-grid">
          <section className="panel"><div className="panel-heading"><div><h3>Sales & waste trend</h3><p>Illustrative demo data · not live measurements</p></div><span>•••</span></div><div className="legend"><span>● Units sold</span><span className="waste-legend">● Waste units</span></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{top:10,right:8,left:-20,bottom:0}}><defs><linearGradient id="soldFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#37866a" stopOpacity={0.2}/><stop offset="95%" stopColor="#37866a" stopOpacity={0.01}/></linearGradient></defs><CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#e8ece7"/><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill:"#818b83",fontSize:12}}/><YAxis axisLine={false} tickLine={false} tick={{fill:"#818b83",fontSize:12}}/><Tooltip/><Area type="monotone" dataKey="sold" name="Units sold" stroke="#37866a" strokeWidth={2.5} fill="url(#soldFill)"/><Area type="monotone" dataKey="waste" name="Waste units" stroke="#df9860" strokeWidth={2} fill="none"/></AreaChart></ResponsiveContainer></div></section>
          <section className="panel"><div className="panel-heading"><div><h3>Freshness watch</h3><p>Example batches requiring attention</p></div><button className="link" onClick={() => setActive("Inventory & expiry")}>View all →</button></div>
            <Freshness emoji="🥛" name="Whole milk · 1L" store="Store Central · Batch M-104" qty="20 units" expiry="Expires tomorrow" risk="High"/>
            <Freshness emoji="🍓" name="Strawberries · 250g" store="Store North · Batch S-221" qty="14 units" expiry="Expires in 2 days" risk="High"/>
            <Freshness emoji="🥣" name="Greek yogurt · 500g" store="Store Central · Batch Y-089" qty="32 units" expiry="Expires in 3 days" risk="Medium"/>
            <button className="secondary full" onClick={() => setActive("Inventory & expiry")}>Open inventory →</button>
          </section>
        </div>
        <section className="panel rec-panel"><div className="panel-heading"><div><h3>Priority recommendations</h3><p>Illustrative proposals only — no actions have been executed.</p></div><button className="link" onClick={() => setActive("AI recommendations")}>View all 4 →</button></div>
          <Recommendation icon="%" tone="orange" title="Markdown whole milk at Store Central" desc="20 units expire tomorrow · expected demand is below batch quantity." tag="Markdown" value="15% off" onReview={() => setActive("AI recommendations")}/>
          <Recommendation icon="⇄" tone="green" title="Transfer leafy greens to Store South" desc="Surplus at Store North · receiving store has forecasted demand." tag="Transfer" value="18 units" onReview={() => setActive("AI recommendations")}/>
          <Recommendation icon="＋" tone="purple" title="Reduce next yogurt replenishment" desc="Current stock and inbound receipt may exceed expected demand." tag="Replenish" value="−12 units" onReview={() => setActive("AI recommendations")}/>
        </section>
        <footer>Freshwise · Agentic AI for perishable inventory <span>Replace demo values with validated backend results.</span></footer>
      </div>
    </main>
  </div>;
}
function Metric({label,value,change,note,icon}:{label:string;value:string;change:string;note:string;icon:string}) {
 return <div className="metric"><div className="metric-top">{label}<span>{icon}</span></div><strong className="metric-value">{value}</strong><div className="metric-bottom"><b>{change}</b><span>{note}</span></div></div>;
}
function Freshness({emoji,name,store,qty,expiry,risk}:{emoji:string;name:string;store:string;qty:string;expiry:string;risk:string}) {
 return <div className="freshness"><div className="product-emoji">{emoji}</div><div className="freshness-text"><strong>{name}</strong><small>{store}</small><p>{qty} · {expiry}</p></div><span className={`risk ${risk.toLowerCase()}`}>{risk}</span></div>;
}
function Recommendation({icon,tone,title,desc,tag,value,onReview}:{icon:string;tone:string;title:string;desc:string;tag:string;value:string;onReview:()=>void}) {
 return <div className="recommendation"><div className={`rec-icon ${tone}`}>{icon}</div><div className="rec-text"><strong>{title}</strong><p>{desc}</p></div><span className={`tag ${tone}`}>{tag}</span><div className="rec-value"><strong>{value}</strong><small>Proposed</small></div><button className="review" onClick={onReview}>Review</button></div>;
}
