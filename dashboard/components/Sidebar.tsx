"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { href: "/",             label: "今日總覽",   icon: "🏠" },
  { href: "/agents",       label: "員工控制台", icon: "🤖" },
  { href: "/review",       label: "內容審核",   icon: "✅" },
  { href: "/inventory",    label: "庫存管理",   icon: "📦" },
  { href: "/performance",  label: "帶貨成效",   icon: "📈" },
  { href: "/intelligence", label: "市場情報",   icon: "🔍" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
      <div className="p-5 border-b border-gray-800">
        <div className="text-lg font-bold text-purple-400">騏藝逸品</div>
        <div className="text-xs text-gray-500 mt-0.5">AI 員工控制中心</div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {nav.map(({ href, label, icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-purple-700 text-white font-medium"
                  : "text-gray-400 hover:bg-gray-800 hover:text-gray-100"
              }`}
            >
              <span>{icon}</span>
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-gray-800 text-xs text-gray-600">
        QiYi Crystal AI v1.0
      </div>
    </aside>
  );
}
