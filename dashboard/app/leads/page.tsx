"use client";

import { useEffect, useState } from "react";

type Lead = {
  id: number;
  phone: string;
  item: string;
  source: string;
  status: string;
  created_at: string;
};

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchLeads = async () => {
    try {
      const res = await fetch(`${baseUrl}/api/leads`);
      const data = await res.json();
      setLeads(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, []);

  const updateStatus = async (id: number, status: string) => {
    await fetch(`${baseUrl}/api/leads/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    fetchLeads();
  };

  if (loading) return <div>Yuklanmoqda...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Mijozlar (Leads)</h1>

      <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/50">
        <table className="w-full text-left text-sm text-zinc-300">
          <thead className="border-b border-zinc-800 bg-zinc-900 text-xs uppercase text-zinc-500">
            <tr>
              <th className="px-6 py-4 font-medium">Sana</th>
              <th className="px-6 py-4 font-medium">Manba</th>
              <th className="px-6 py-4 font-medium">Telefon</th>
              <th className="px-6 py-4 font-medium">Mahsulot</th>
              <th className="px-6 py-4 font-medium">Holat</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {leads.map((lead) => (
              <tr key={lead.id} className="hover:bg-zinc-800/50">
                <td className="px-6 py-4 whitespace-nowrap text-zinc-400">
                  {new Date(lead.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
                    lead.source === 'telegram' ? 'bg-blue-400/10 text-blue-400 ring-blue-400/30' : 
                    lead.source === 'instagram' ? 'bg-pink-400/10 text-pink-400 ring-pink-400/30' : 
                    'bg-zinc-400/10 text-zinc-400 ring-zinc-400/30'
                  }`}>
                    {lead.source}
                  </span>
                </td>
                <td className="px-6 py-4 font-medium text-white">{lead.phone}</td>
                <td className="px-6 py-4 max-w-xs truncate" title={lead.item}>{lead.item}</td>
                <td className="px-6 py-4">
                  <select
                    value={lead.status}
                    onChange={(e) => updateStatus(lead.id, e.target.value)}
                    className="rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-sm text-white outline-none focus:border-blue-500"
                  >
                    <option value="yangi">Yangi</option>
                    <option value="qo'ng'iroq_qilindi">Qo'ng'iroq qilindi</option>
                    <option value="yakunlandi">Sotildi / Yakunlandi</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {leads.length === 0 && (
          <div className="p-8 text-center text-zinc-500">
            Hali mijozlar yo'q
          </div>
        )}
      </div>
    </div>
  );
}
