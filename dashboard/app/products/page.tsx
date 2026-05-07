"use client";

import { useEffect, useState } from "react";
import { Plus, Edit2, Trash2 } from "lucide-react";

type Product = {
  id: number;
  name: string;
  category: string;
  price: string;
  stock: number;
  specs: string;
  image_url: string;
};

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState<Partial<Product>>({
    name: "", category: "Boshqa", price: "", stock: 0, specs: "", image_url: ""
  });

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchProducts = async () => {
    try {
      const res = await fetch(`${baseUrl}/api/products`);
      const data = await res.json();
      setProducts(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const url = editMode ? `${baseUrl}/api/products/${formData.id}` : `${baseUrl}/api/products`;
    const method = editMode ? "PUT" : "POST";

    await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });

    setShowModal(false);
    fetchProducts();
  };

  const handleDelete = async (id: number) => {
    if (confirm("Rostdan ham o'chirasizmi?")) {
      await fetch(`${baseUrl}/api/products/${id}`, { method: "DELETE" });
      fetchProducts();
    }
  };

  const openModal = (p?: Product) => {
    if (p) {
      setFormData(p);
      setEditMode(true);
    } else {
      setFormData({ name: "", category: "Boshqa", price: "", stock: 0, specs: "", image_url: "" });
      setEditMode(false);
    }
    setShowModal(true);
  };

  if (loading) return <div>Yuklanmoqda...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Sklad (Mahsulotlar)</h1>
        <button
          onClick={() => openModal()}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition"
        >
          <Plus size={16} />
          Yangi qo'shish
        </button>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((p) => (
          <div key={p.id} className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50 flex flex-col">
            {p.image_url ? (
              <img src={p.image_url} alt={p.name} className="h-48 w-full object-cover" />
            ) : (
              <div className="h-48 w-full bg-zinc-800 flex items-center justify-center text-zinc-500">
                Rasm yo'q
              </div>
            )}
            <div className="p-4 flex-1">
              <h3 className="font-semibold text-lg text-white">{p.name}</h3>
              <p className="text-sm text-zinc-400">{p.category}</p>
              <div className="mt-4 space-y-1 text-sm text-zinc-300">
                <p><span className="text-zinc-500">Narxi:</span> {p.price}</p>
                <p><span className="text-zinc-500">Qoldiq:</span> {p.stock} ta</p>
                <p className="truncate"><span className="text-zinc-500">Sifati:</span> {p.specs}</p>
              </div>
            </div>
            <div className="p-4 border-t border-zinc-800 flex justify-end space-x-3">
              <button onClick={() => openModal(p)} className="flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm transition">
                <Edit2 size={14} /> Tahrirlash
              </button>
              <button onClick={() => handleDelete(p.id)} className="flex items-center gap-1 text-red-400 hover:text-red-300 text-sm transition">
                <Trash2 size={14} /> O'chirish
              </button>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-950 p-6">
            <h2 className="mb-4 text-xl font-bold text-white">{editMode ? "Tahrirlash" : "Yangi mahsulot"}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm text-zinc-400">Nomi</label>
                <input required type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 p-2 text-white outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-zinc-400">Kategoriya</label>
                  <input type="text" value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})} className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 p-2 text-white outline-none" />
                </div>
                <div>
                  <label className="text-sm text-zinc-400">Narxi</label>
                  <input type="text" value={formData.price} onChange={e => setFormData({...formData, price: e.target.value})} className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 p-2 text-white outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-zinc-400">Soni (Stock)</label>
                  <input required type="number" value={formData.stock} onChange={e => setFormData({...formData, stock: parseInt(e.target.value)})} className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 p-2 text-white outline-none" />
                </div>
                <div>
                  <label className="text-sm text-zinc-400">Rasm ssilkasi (URL)</label>
                  <input type="url" value={formData.image_url} onChange={e => setFormData({...formData, image_url: e.target.value})} className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 p-2 text-white outline-none" />
                </div>
              </div>
              <div>
                <label className="text-sm text-zinc-400">Sifati / Xususiyatlari</label>
                <textarea rows={3} value={formData.specs} onChange={e => setFormData({...formData, specs: e.target.value})} className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 p-2 text-white outline-none" />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="rounded-lg px-4 py-2 text-sm text-zinc-400 hover:text-white">Bekor qilish</button>
                <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">Saqlash</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
