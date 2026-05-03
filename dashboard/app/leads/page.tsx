"use client";
import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import dayjs from 'dayjs';
import { Search, Download, ChevronDown, Check } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

const STATUS_OPTIONS = ["yangi", "qo'ng'iroq_qilindi", "yakunlandi"] as const;
type LeadStatus = typeof STATUS_OPTIONS[number];

const STATUS_STYLES: Record<LeadStatus, string> = {
  yangi:               "bg-emerald-500/10 text-emerald-400",
  "qo'ng'iroq_qilindi": "bg-yellow-500/10 text-yellow-400",
  yakunlandi:          "bg-zinc-500/10 text-zinc-400",
};

export default function LeadsPage() {
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [openDropdown, setOpenDropdown] = useState<number | null>(null);

  useEffect(() => {
    fetchLeads();
  }, []);

  async function fetchLeads() {
    try {
      const res = await axios.get(`${API_BASE}/leads`);
      setLeads(res.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    if (!q) return leads;
    return leads.filter(
      (l) =>
        l.phone?.toLowerCase().includes(q) ||
        l.item?.toLowerCase().includes(q) ||
        l.status?.toLowerCase().includes(q)
    );
  }, [leads, query]);

  async function handleStatusChange(leadId: number, status: LeadStatus) {
    setOpenDropdown(null);
    try {
      await axios.patch(`${API_BASE}/leads/${leadId}`, { status });
      setLeads((prev) =>
        prev.map((l) => (l.id === leadId ? { ...l, status } : l))
      );
    } catch (e) {
      console.error("Status yangilashda xato:", e);
    }
  }

  function exportCSV() {
    const header = ["Sana", "Telefon", "Mahsulot", "Status"];
    const rows = leads.map((l) => [
      dayjs(l.created_at).format("DD.MM.YYYY HH:mm"),
      l.phone,
      l.item,
      l.status,
    ]);
    const csv = [header, ...rows].map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `arzonchi-leads-${dayjs().format("YYYY-MM-DD")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-8" onClick={() => setOpenDropdown(null)}>
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Leadlar</h1>
          <p className="text-zinc-500 mt-1">
            Sotib olishga qiziqish bildirgan mijozlar ro'yxati.
          </p>
        </div>
        <button
          onClick={exportCSV}
          className="bg-white/5 hover:bg-white/10 px-4 py-2 rounded-xl flex items-center gap-2 border border-white/5 transition-colors"
        >
          <Download className="w-4 h-4" /> Export CSV
        </button>
      </div>

      <div className="bg-zinc-900/50 border border-white/5 rounded-3xl overflow-hidden">
        <div className="p-6 border-b border-white/5">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Telefon yoki mahsulot nomi..."
              className="w-full bg-white/5 border border-white/10 rounded-xl py-2 pl-11 pr-4 focus:outline-none focus:border-blue-500/50 transition-colors"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-zinc-500 text-sm border-b border-white/5">
                <th className="px-6 py-4 font-medium">Sana</th>
                <th className="px-6 py-4 font-medium">Telefon</th>
                <th className="px-6 py-4 font-medium">Mahsulot</th>
                <th className="px-6 py-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filtered.map((lead) => (
                <tr key={lead.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 text-sm text-zinc-400">
                    {dayjs(lead.created_at).format("DD.MM.YYYY HH:mm")}
                  </td>
                  <td className="px-6 py-4 font-medium">{lead.phone}</td>
                  <td className="px-6 py-4 text-sm">{lead.item}</td>
                  <td className="px-6 py-4">
                    <div className="relative inline-block" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() =>
                          setOpenDropdown(openDropdown === lead.id ? null : lead.id)
                        }
                        className={`text-[10px] px-3 py-1 rounded-full font-bold uppercase tracking-wider flex items-center gap-1 transition-all hover:opacity-80 ${
                          STATUS_STYLES[lead.status as LeadStatus] ?? "bg-zinc-700 text-zinc-300"
                        }`}
                      >
                        {lead.status}
                        <ChevronDown className="w-3 h-3" />
                      </button>

                      {openDropdown === lead.id && (
                        <div className="absolute left-0 top-8 z-10 bg-zinc-900 border border-white/10 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden min-w-[180px]">
                          {STATUS_OPTIONS.map((s) => (
                            <button
                              key={s}
                              onClick={() => handleStatusChange(lead.id, s)}
                              className="w-full text-left px-4 py-3 text-sm hover:bg-white/5 flex items-center justify-between gap-4 transition-colors"
                            >
                              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${STATUS_STYLES[s]}`}>
                                {s}
                              </span>
                              {lead.status === s && <Check className="w-3 h-3 text-blue-400" />}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && !loading && (
            <div className="py-20 text-center text-zinc-600">
              {query ? "Qidiruv bo'yicha natija topilmadi." : "Ma'lumotlar mavjud emas."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
