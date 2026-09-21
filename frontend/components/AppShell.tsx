import Link from "next/link";

export default function AppShell({
  role,
  children,
}: {
  role?: "Student" | "Instructor";
  children: React.ReactNode;
}) {
  return (
    <>
      <nav className="app-nav">
        <div className="app-nav-inner">
          <Link href="/" className="app-nav-brand">
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
            <span className="app-nav-wordmark">FDE Lab</span>
          </Link>
          {role && <span className="app-nav-role">{role} view</span>}
        </div>
      </nav>
      {children}
    </>
  );
}
