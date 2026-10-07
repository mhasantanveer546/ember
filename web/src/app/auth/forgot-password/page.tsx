import Link from "next/link";

export const metadata = { title: "Forgot password" };

/**
 * The backend has no password-reset flow yet (it needs an email provider and
 * single-use reset tokens). This page says so honestly instead of pretending
 * to send an email.
 */
export default function ForgotPasswordPage() {
  return (
    <div className="space-y-4">
      <h1 className="display text-[28px]">Forgot your password?</h1>
      <p className="text-sm text-muted">
        Resetting a password by email isn’t available yet. It needs email delivery, which is planned for a later release. Until then, ask the administrator of your Ember instance to reset it.
      </p>
      <Link href="/auth/login" className="text-sm font-medium underline decoration-ember decoration-2 underline-offset-4">
        ← Back to sign in
      </Link>
    </div>
  );
}
