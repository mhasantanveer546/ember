import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useEffect } from "react";
import { StyleSheet, Text, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { EmberMark } from "@/components/Logo";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { WorkspaceProvider } from "@/context/WorkspaceContext";
import { colors } from "@/theme";

/** Splash shown while the stored session is checked (Phase 7.2 "Splash"). */
function Splash() {
  return (
    <View style={[StyleSheet.absoluteFill, { backgroundColor: colors.sidebar, alignItems: "center", justifyContent: "center", gap: 14, zIndex: 10 }]}>
      <EmberMark size={72} />
      <Text style={{ color: colors.fg, fontSize: 30, fontWeight: "700", letterSpacing: -0.5 }}>Ember</Text>
      <Text style={{ color: colors.muted }}>Find what you forgot you knew.</Text>
    </View>
  );
}

/** Sends signed-out users to /login and signed-in users away from the auth screens. */
function Gate() {
  const { user, loading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    const inAuth = segments[0] === "(auth)";
    if (!user && !inAuth) router.replace("/login");
    else if (user && inAuth) router.replace("/");
  }, [user, loading, segments, router]);

  return (
    <>
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.sidebar },
          headerTintColor: colors.fg,
          headerTitleStyle: { fontWeight: "600" },
          headerShadowVisible: false,
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="document/[id]" options={{ title: "Document" }} />
        <Stack.Screen name="history" options={{ title: "History" }} />
        <Stack.Screen name="workspaces/index" options={{ title: "Workspaces" }} />
        <Stack.Screen name="workspaces/[id]" options={{ title: "Workspace" }} />
      </Stack>
      {loading && <Splash />}
    </>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <AuthProvider>
        <WorkspaceProvider>
          <Gate />
        </WorkspaceProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
