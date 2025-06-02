'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
    const pathname = usePathname();

    const getIconColor = (path) => {
        return pathname === path ? 'text-[#4b87cc]' : 'text-[#82bee2]';
    }; return (
        <div className="fixed bottom-0 left-0 right-0 bg-[#0f203e] p-4 flex justify-around items-center border-t-2 border-[#4f6f97] py-4 z-50 h-20">
            <Link href="/" className={getIconColor('/')}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon icon-tabler icons-tabler-outline icon-tabler-home">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none" />
                    <path d="M5 12l-2 0l9 -9l9 9l-2 0" />
                    <path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-7" />
                    <path d="M9 21v-6a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v6" />
                </svg>
            </Link>
            <Link href="/status" className={getIconColor('/status')}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon icon-tabler icons-tabler-outline icon-tabler-adjustments-alt">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none" />
                    <path d="M4 8h4v4h-4z" />
                    <path d="M6 4l0 4" />
                    <path d="M6 12l0 8" />
                    <path d="M10 14h4v4h-4z" />
                    <path d="M12 4l0 10" />
                    <path d="M12 18l0 2" />
                    <path d="M16 5h4v4h-4z" />
                    <path d="M18 4l0 1" />
                    <path d="M18 9l0 11" />
                </svg>
            </Link>
            <a href="https://t.me/your_telegram_channel" target="_blank" rel="noopener noreferrer" className="text-white bg-[#3681c3] p-3 rounded-2xl">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon icon-tabler icons-tabler-outline icon-tabler-brand-telegram">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none" />
                    <path d="M15 10l-4 4l6 6l4 -16l-18 7l4 2l2 6l3 -4" />
                </svg>
            </a>
            <Link href="/leaderboard" className={getIconColor('/leaderboard')}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon icon-tabler icons-tabler-outline icon-tabler-trophy">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none" />
                    <path d="M8 21l8 0" />
                    <path d="M12 17l0 4" />
                    <path d="M7 4l10 0" />
                    <path d="M17 4v8a5 5 0 0 1 -10 0v-8" />
                    <path d="M5 9m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />
                    <path d="M19 9m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />
                </svg>
            </Link>
            <Link href="/tutorial" className={getIconColor('/tutorial')}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="icon icon-tabler icons-tabler-filled icon-tabler-help-octagon">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none" />
                    <path d="M14.897 1a4 4 0 0 1 2.664 1.016l.165 .156l4.1 4.1a4 4 0 0 1 1.168 2.605l.006 .227v5.794a4 4 0 0 1 -1.016 2.664l-.156 .165l-4.1 4.1a4 4 0 0 1 -2.603 1.168l-.227 .006h-5.795a3.999 3.999 0 0 1 -2.664 -1.017l-.165 -.156l-4.1 -4.1a4 4 0 0 1 -1.168 -2.604l-.006 -.227v-5.794a4 4 0 0 1 1.016 -2.664l.156 -.165l4.1 -4.1a4 4 0 0 1 2.605 -1.168l.227 -.006h5.793zm-2.897 14a1 1 0 0 0 -.993 .883l-.007 .117l.007 .127a1 1 0 0 0 1.986 0l.007 -.117l-.007 -.127a1 1 0 0 0 -.993 -.883zm1.368 -6.673a2.98 2.98 0 0 0 -3.631 .728a1 1 0 0 0 1.44 1.383l.171 -.18a.98 .98 0 0 1 1.11 -.15a1 1 0 0 1 -.34 1.886l-.232 .012a1 1 0 0 0 .111 1.994a3 3 0 0 0 1.371 -5.673z" />
                </svg>
            </Link>
        </div>
    );
}