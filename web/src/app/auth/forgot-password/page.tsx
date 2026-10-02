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
      <h1 className="font-serif text-xl font-semibold">Forgot your password?</h1>
      <p className="text-sm text-muted">
        Password reset by email isn&apos;t available yet. It&apos;s planned together with email delivery in a later
        release. Until then, please contact the administrator of your Ember instance.
      </p>
      <Link href="/auth/login" className="text-sm text-accent hover:underline">
        ← Back to sign in
      </Link>
    </div>
  );
}
