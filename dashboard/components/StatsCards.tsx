"use client";
import React from 'react';
import { motion } from 'framer-motion';
import { UserPlus, Users, MessageSquare, TrendingUp } from 'lucide-react';

interface Stat {
  label: string;
  value: string | number;
  icon: any;
  trend?: string;
  color: string;
}

export default function StatsCards({ stats }: { stats: any }) {
  const items: Stat[] = [
    {
      label: 'Jami Leadlar',
      value: stats?.total_leads ?? 0,
      icon: UserPlus,
      color: 'text-blue-400',
      trend: stats?.daily_leads?.length
        ? `+${stats.daily_leads[stats.daily_leads.length - 1]?.count ?? 0} bugun`
        : undefined,
    },
    {
      label: 'Foydalanuvchilar',
      value: stats?.total_users ?? 0,
      icon: Users,
      color: 'text-purple-400',
    },
    {
      label: 'Xabarlar',
      value: stats?.total_messages ?? 0,
      icon: MessageSquare,
      color: 'text-emerald-400',
    },
    {
      label: 'Konversiya',
      value: stats?.total_users
        ? ((stats.total_leads / stats.total_users) * 100).toFixed(1) + '%'
        : '0%',
      icon: TrendingUp,
      color: 'text-orange-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {items.map((stat, i) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="bg-zinc-900/50 border border-white/5 p-6 rounded-3xl hover:border-white/10 transition-colors group"
        >
          <div className="flex justify-between items-start mb-4">
            <div className="p-3 rounded-2xl bg-zinc-800 group-hover:scale-110 transition-transform">
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
            </div>
            {stat.trend && (
              <span className="text-xs font-medium text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-full">
                {stat.trend}
              </span>
            )}
          </div>
          <h3 className="text-zinc-400 text-sm font-medium">{stat.label}</h3>
          <p className="text-3xl font-bold mt-1 tracking-tight">{stat.value}</p>
        </motion.div>
      ))}
    </div>
  );
}
