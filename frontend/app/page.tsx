import { GraduationCap, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import AppShell from "../components/AppShell";

export default function HomePage() {
  return (
    <AppShell>
      <main className="page">
        <div className="hub-hero">
          <svg className="app-nav-mark" viewBox="0 0 32 32" aria-hidden="true">
            <rect width="32" height="32" rx="7" fill="#16283F" />
            <path
              d="M11 8L20 16L11 24"
              stroke="#DE6A22"
              strokeWidth="3.4"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          </svg>
          <h1>FDE Lab</h1>
          <p>
            A simulated forward-deployed engineering engagement — ambiguous asks, messy data, and a
            skeptical stakeholder, run on your cohort&apos;s clock.
          </p>
        </div>

        <div className="hub-cards">
          <div className="hub-card">
            <div className="hub-card-icon">
              <GraduationCap size={20} />
            </div>
            <h2>Student workspace</h2>
            <p>
              Students arrive at their scenario instance from a link in their course. There&apos;s no
              separate login — if you have an instance URL, open{" "}
              <code>/workspace/&lt;instanceId&gt;</code> directly.
            </p>
          </div>

          <div className="hub-card">
            <div className="hub-card-icon">
              <LayoutDashboard size={20} />
            </div>
            <h2>Instructor console</h2>
            <p>Schedule a cohort&apos;s scenario, monitor student status, and review submissions.</p>
            <Link href="/instructor" className="btn-link">
              Open instructor console
            </Link>
          </div>
        </div>
      </main>
    </AppShell>
  );
}
