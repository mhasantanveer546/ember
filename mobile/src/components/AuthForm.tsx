import { Link } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, Text, TextInput, View } from "react-native";
import { HeroArt } from "@/components/HeroArt";
import { EmberMark } from "@/components/Logo";
import { Button, ErrorNote, Screen } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import { colors, radius } from "@/theme";

function Field({ label, ...props }: { label: string } & React.ComponentProps<typeof TextInput>) {
  const [focused, setFocused] = useState(false);
  return (
    <View style={{ gap: 6 }}>
      <Text style={{ color: colors.fg, fontWeight: "600", fontSize: 14 }}>{label}</Text>
      <TextInput
        {...props}
        accessibilityLabel={label}
        placeholderTextColor={colors.faint}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={[{ backgroundColor: colors.sunken, borderRadius: radius.md, borderWidth: 1, borderColor: focused ? colors.web : colors.line, color: colors.fg, paddingHorizontal: 14, height: 48, fontSize: 16 }, { outlineStyle: "none" } as object]}
      />
    </View>
  );
}

/** Shared sign-in / register screen. */
export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const { login, register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const isLogin = mode === "login";

  const submit = async () => {
    setError(null);
    if (!isLogin) {
      if (password.length < 8) return setError("Use at least 8 characters for your password.");
      if (password !== confirm) return setError("Those passwords don’t match.");
    }
    setBusy(true);
    try {
      if (isLogin) await login(email.trim(), password);
      else await register(email.trim(), password);
      // The auth gate in the root layout navigates to the app.
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Screen topInset={false}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ flexGrow: 1 }}>
          <View style={{ height: 270, alignItems: "center", justifyContent: "center", gap: 6 }}>
            <HeroArt />
            <EmberMark size={52} />
            <Text style={{ color: "#fff", fontSize: 38, fontWeight: "800", letterSpacing: -1 }}>Ember</Text>
            <Text style={{ color: "rgba(255,255,255,0.8)", fontSize: 15 }}>Find what you forgot you knew.</Text>
          </View>
          <View style={{ padding: 24, gap: 16 }}>
            <Text accessibilityRole="header" style={{ color: colors.fg, fontSize: 26, fontWeight: "700", letterSpacing: -0.4 }}>
              {isLogin ? "Sign in" : "Create your account"}
            </Text>
            {error && <ErrorNote message={error} />}
            <Field label="Email" value={email} onChangeText={setEmail} autoCapitalize="none" autoComplete="email" keyboardType="email-address" textContentType="emailAddress" />
            <Field label="Password" value={password} onChangeText={setPassword} secureTextEntry autoComplete={isLogin ? "current-password" : "new-password"} textContentType={isLogin ? "password" : "newPassword"} onSubmitEditing={isLogin ? submit : undefined} />
            {!isLogin && <Field label="Confirm password" value={confirm} onChangeText={setConfirm} secureTextEntry textContentType="newPassword" onSubmitEditing={submit} />}
            <Button title={isLogin ? "Sign in" : "Create account"} onPress={submit} loading={busy} disabled={!email.trim() || !password} />
            <Text style={{ color: colors.muted, textAlign: "center", fontSize: 14 }}>
              {isLogin ? "New to Ember? " : "Already have an account? "}
              <Link href={isLogin ? "/register" : "/login"} style={{ color: colors.web, fontWeight: "600" }}>
                {isLogin ? "Create an account" : "Sign in"}
              </Link>
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </Screen>
  );
}
