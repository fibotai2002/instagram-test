"use client";
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import StatsCards from '@/components/StatsCards';
import { motion } from 'framer-motion';
import { UserPlus, Clock, ArrowRight } from 'lucide-react';
import dayjs from 'dayjs';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [recentLeads, setRecentLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsRes, leadsRes] = await Promise.all([
          axios.get(`${API_BASE}/stats`),
          axios.get(`${API_BASE}/leads`)
        ]);
        setStats(statsRes.data);
        setRecentLeads(leadsRes.data.slice(0, 5));
      } catch (error) {
        console.error("Data fetch error:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    const timer = setInterval(fetchData, 30_000);
    return () => clearInterval(timer);
  }, []);

  if (loading) return (
    <div className="h-full flex items-center justify-center">
      <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Xayrli kun!</h1>
        <p className="text-zinc-500 mt-1">Arzonchi AI Chat tizimining umumiy statistikasi.</p>
      </div>

      <StatsCards stats={stats} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Leads */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-zinc-900/50 border border-white/5 rounded-3xl p-6"
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-blue-400" />
              So'nggi Leadlar
            </h2>
            <button className="text-sm text-blue-400 hover:underline flex items-center gap-1">
              Hammasini ko'rish <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-4">
            {recentLeads.map((lead) => (
              <div key={lead.id} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl hover:bg-white/10 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center">
                    <span className="text-blue-400 font-bold">L</span>
                  </div>
                  <div>
                    <p className="font-medium text-zinc-200">{lead.phone}</p>
                    <p className="text-xs text-zinc-500">{lead.item}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs text-zinc-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {dayjs(lead.created_at).format('HH:mm')}
                  </span>
                  <div className="mt-1">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 uppercase font-bold">
                      {lead.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            {recentLeads.length === 0 && (
              <p className="text-center text-zinc-600 py-10">Leadlar hali mavjud emas.</p>
            )}
          </div>
        </motion.div>

        {/* System Health / Tips */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-3xl p-8"
        >
          <h2 className="text-xl font-bold mb-4">AI Maslahatchi</h2>
          <p className="text-zinc-400 leading-relaxed">
            Bugun mijozlar ko'proq **muzlatgichlar** haqida so'rashmoqda. 
            Gemini AI ularga do'stona tarzda javob bermoqda. 
            Leadlar sonini oshirish uchun inventarni yangilab turing.
          </p>
          <div className="mt-8 space-y-4">
            <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
              <p className="text-sm font-medium">Server holati</p>
              <div className="flex items-center gap-2 mt-1">
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-xs text-zinc-400">99.9% Up-time</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
