"use client";
import React, { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import dayjs from 'dayjs';
import { MessageSquare, User, Clock, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export default function UsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  useEffect(() => {
    async function fetchUsers() {
      try {
        const res = await axios.get(`${API_BASE}/users`);
        setUsers(res.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }
    fetchUsers();
  }, []);

  useEffect(() => {
    if (selectedUser) {
      async function fetchLogs() {
        try {
          const res = await axios.get(`${API_BASE}/messages?user_id=${selectedUser}`);
          setLogs(res.data);
        } catch (error) {
          console.error(error);
        }
      }
      fetchLogs();
    }
  }, [selectedUser]);

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    if (!q) return users;
    return users.filter((u) => u.id?.toLowerCase().includes(q));
  }, [users, query]);

  return (
    <div className="h-full flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Foydalanuvchilar</h1>
        <p className="text-zinc-500 mt-1">Bot bilan muloqot qilgan barcha mijozlar.</p>
      </div>

      <div className="flex-1 flex gap-8 overflow-hidden">
        {/* User List */}
        <div className="w-1/3 bg-zinc-900/50 border border-white/5 rounded-3xl overflow-hidden flex flex-col">
          <div className="p-4 border-b border-white/5">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="ID bo'yicha qidirish..."
                className="w-full bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filtered.map((user) => (
              <button
                key={user.id}
                onClick={() => setSelectedUser(user.id)}
                className={`w-full text-left p-4 rounded-2xl transition-all duration-200 flex items-center gap-4 ${
                  selectedUser === user.id
                    ? 'bg-blue-500/10 border border-blue-500/20'
                    : 'hover:bg-white/5 border border-transparent'
                }`}
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  selectedUser === user.id ? 'bg-blue-500 text-white' : 'bg-zinc-800 text-zinc-400'
                }`}>
                  <User className="w-6 h-6" />
                </div>
                <div className="flex-1 overflow-hidden">
                  <p className="font-bold truncate text-zinc-200 text-sm">ID: {user.id}</p>
                  <span className="text-xs text-zinc-500">
                    {dayjs(user.created_at).format('DD MMM, HH:mm')}
                  </span>
                </div>
              </button>
            ))}
            {filtered.length === 0 && !loading && (
              <p className="text-center text-zinc-600 py-10 text-sm">
                {query ? "Natija topilmadi." : "Foydalanuvchilar yo'q."}
              </p>
            )}
          </div>
        </div>

        {/* Chat History */}
        <div className="flex-1 bg-zinc-900/50 border border-white/5 rounded-3xl flex flex-col overflow-hidden relative">
          <AnimatePresence mode="wait">
            {selectedUser ? (
              <motion.div
                key={selectedUser}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex-1 flex flex-col h-full"
              >
                <div className="p-6 border-b border-white/5 bg-white/[0.02] flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center">
                    <User className="w-5 h-5 text-zinc-400" />
                  </div>
                  <div>
                    <h2 className="font-bold text-zinc-200">ID: {selectedUser}</h2>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {logs.map((log) => (
                    <div
                      key={log.id}
                      className={`flex ${log.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-[80%] space-y-1 ${log.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
                        <div className={`px-5 py-3 rounded-2xl text-sm leading-relaxed ${
                          log.role === 'user'
                            ? 'bg-blue-600 text-white rounded-tr-none shadow-lg shadow-blue-900/20'
                            : 'bg-zinc-800 text-zinc-200 rounded-tl-none'
                        }`}>
                          {log.content}
                        </div>
                        <span className="text-[10px] text-zinc-500 px-2 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {dayjs(log.created_at).format('HH:mm')}
                        </span>
                      </div>
                    </div>
                  ))}
                  {logs.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-4">
                      <MessageSquare className="w-12 h-12 opacity-20" />
                      <p>Suhbat tarixi mavjud emas.</p>
                    </div>
                  )}
                </div>
              </motion.div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-6 p-10 text-center">
                <div className="w-20 h-20 bg-zinc-800 rounded-full flex items-center justify-center">
                  <MessageSquare className="w-10 h-10" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-zinc-400">Suhbatni tanlang</h3>
                  <p className="text-sm mt-2 max-w-xs">Xabarlar tarixini ko'rish uchun chap tomondagi foydalanuvchilardan birini tanlang.</p>
                </div>
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
