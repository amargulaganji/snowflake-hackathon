import type { ReactNode } from 'react';

interface LayoutProps {
  sidebar: ReactNode;
  main: ReactNode;
}

export function Layout({ sidebar, main }: LayoutProps) {
  return (
    <div className="layout">
      <aside className="sidebar">{sidebar}</aside>
      <main className="main-panel">{main}</main>
    </div>
  );
}
