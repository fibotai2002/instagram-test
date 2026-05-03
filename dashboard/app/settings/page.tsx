"use client";
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Save, RefreshCw, Sparkles, Store, Truck } from 'lucide-react';
import { motion } from 'framer-motion';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export default function SettingsPage() {
  const [config, setConfig] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  useEffect(() => {
    async function fetchConfig() {
      try {
        const res = await axios.get(`${API_BASE}/config`);
        setConfig(res.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }
    fetchConfig();
  }, []);

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3000);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.post(`${API_BASE}/config`, config);
      showToast('success', 'Sozlamalar muvaffaqiyatli saqlandi!');
    } catch {
      showToast('error', 'Xato yuz berdi. Qayta urinib ko\'ring.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div className="h-full flex items-center justify-center">
      <div className="w-10 h-10 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="max-w-4xl space-y-8">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-6 right-6 z-50 px-5 py-3 rounded-2xl text-sm font-medium shadow-xl transition-all ${
          toast.type === 'success'
            ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
            : 'bg-red-500/10 border border-red-500/30 text-red-400'
        }`}>
          {toast.msg}
        </div>
      )}

      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Sozlamalari</h1>
        <p className="text-zinc-500 mt-1">Botning xarakteri va javob berish qoidalarini shu yerdan boshqaring.</p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Shop Name */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900/50 border border-white/5 rounded-3xl p-8 space-y-6"
        >
          <div className="flex items-center gap-3 text-blue-400 mb-2">
            <Store className="w-5 h-5" />
            <h2 className="font-bold text-lg text-zinc-100">Do'kon ma'lumotlari</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-zinc-500 mb-2">Do'kon nomi</label>
              <input
                type="text"
                value={config.shop_name || ''}
                onChange={(e) => setConfig({ ...config, shop_name: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-2xl py-3 px-4 focus:border-blue-500/50 outline-none transition-colors"
                placeholder="Masalan: Arzonchi Maishiy Texnika"
              />
            </div>

            <div>
              <label className="block text-sm text-zinc-500 mb-2">Muloqot ohangi</label>
              <select
                value={config.bot_tone || ''}
                onChange={(e) => setConfig({ ...config, bot_tone: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-2xl py-3 px-4 focus:border-blue-500/50 outline-none transition-colors"
              >
                <option value="Do'stona va professional">Do'stona va professional</option>
                <option value="Rasmiy va jiddiy">Rasmiy va jiddiy</option>
                <option value="Hazilkash va quvnoq">Hazilkash va quvnoq</option>
                <option value="Faqat qisqa va aniq">Faqat qisqa va aniq</option>
              </select>
            </div>
          </div>
        </motion.div>

        {/* Business Logic */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-zinc-900/50 border border-white/5 rounded-3xl p-8 space-y-6"
        >
          <div className="flex items-center gap-3 text-emerald-400 mb-2">
            <Truck className="w-5 h-5" />
            <h2 className="font-bold text-lg text-zinc-100">Xizmat ko'rsatish qoidalari</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-zinc-500 mb-2">Yetkazib berish haqida ma'lumot</label>
              <textarea
                rows={3}
                value={config.delivery_info || ''}
                onChange={(e) => setConfig({ ...config, delivery_info: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-2xl py-3 px-4 focus:border-blue-500/50 outline-none transition-colors"
                placeholder="Masalan: Toshkent shahrida bepul, viloyatlarga 50 ming so'm."
              />
            </div>

            <div>
              <label className="block text-sm text-zinc-500 mb-2">Asosiy til</label>
              <div className="flex gap-4">
                {["O'zbek", "Ruscha", "Inglizcha"].map((l) => (
                  <button
                    key={l}
                    onClick={() => setConfig({ ...config, language: l })}
                    className={`px-6 py-2 rounded-xl border transition-all ${
                      config.language === l
                        ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400'
                        : 'border-white/10 text-zinc-500 hover:border-white/20'
                    }`}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Save Button */}
        <div className="flex justify-end gap-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-8 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 font-bold flex items-center gap-2 shadow-lg shadow-blue-900/20 transition-all disabled:opacity-50"
          >
            {saving ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
            Saqlash
          </button>
        </div>
      </div>

      {/* AI Preview */}
      <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-3xl p-8">
        <div className="flex items-center gap-2 text-blue-400 mb-4">
          <Sparkles className="w-5 h-5" />
          <span className="font-bold text-sm uppercase tracking-wider">AI Prompt Preview</span>
        </div>
        <p className="text-sm text-zinc-400 leading-relaxed italic">
          "Salom! Men <strong>{config.shop_name}</strong> do'konining yordamchisiman.
          Sizga <strong>{config.language}</strong> tilida, <strong>{config.bot_tone}</strong> tarzda xizmat ko'rsataman.
          Yetkazib berish: <strong>{config.delivery_info}</strong>"
        </p>
      </div>
    </div>
  );
}
