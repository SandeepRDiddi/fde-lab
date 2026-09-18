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
                d="M16 7L24.5 25H20.9L19.1 21H12.9L11.1 25H7.5L16 7ZM16 13.4L14.1 17.6H17.9L16 13.4Z"
                fill="#DE6A22"
              />
            </svg>
            <span className="app-nav-wordmark">
              <strong>Anvtrac</strong>
              <span>FDE Lab</span>
            </span>
          </Link>
          {role && <span className="app-nav-role">{role} view</span>}
        </div>
      </nav>
      {children}
    </>
  );
}
