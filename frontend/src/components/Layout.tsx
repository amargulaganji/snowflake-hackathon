import type { ReactNode } from 'react';

interface LayoutProps {
  nav: ReactNode;
  main: ReactNode;
  memberContext?: ReactNode;
}

export function Layout({ nav, main, memberContext }: LayoutProps) {
  return (
    <div className="layout">
      <aside className="app-sidebar">{nav}</aside>
      <div className="main-panel">
        {memberContext && <div className="member-context-bar">{memberContext}</div>}
        <main className="main-content">{main}</main>
      </div>
    </div>
  );
}
