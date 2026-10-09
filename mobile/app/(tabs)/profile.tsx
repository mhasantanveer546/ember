import { Ionicons } from "@expo/vector-icons";
import Constants from "expo-constants";
import { useRouter } from "expo-router";
import { Pressable, ScrollView, Text, View } from "react-native";
import { Button, Card, Screen, ScreenTitle, type IconName } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";
import { useWorkspace } from "@/context/WorkspaceContext";
import { API_BASE_URL } from "@/lib/config";
import { colors } from "@/theme";

function Row({ icon, label, value, onPress }: { icon: IconName; label: string; value?: string; onPress?: () => void }) {
  return (
    <Pressable accessibilityRole={onPress ? "button" : undefined} onPress={onPress} disabled={!onPress} style={({ pressed }) => ({ flexDirection: "row", alignItems: "center", gap: 14, paddingVertical: 14, paddingHorizontal: 16, backgroundColor: pressed ? colors.sunken : "transparent" })}>
      <View style={{ width: 34, height: 34, borderRadius: 10, backgroundColor: colors.sunken, alignItems: "center", justifyContent: "center" }}>
        <Ionicons name={icon} size={18} color={colors.web} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={{ color: colors.fg, fontSize: 15.5, fontWeight: "600" }}>{label}</Text>
        {value && <Text style={{ color: colors.muted, fontSize: 13, marginTop: 1 }} numberOfLines={1}>{value}</Text>}
      </View>
      {onPress && <Ionicons name="chevron-forward" size={18} color={colors.faint} />}
    </Pressable>
  );
}

export default function ProfileScreen() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const { current } = useWorkspace();
  if (!user) return null;

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 16, paddingBottom: 40 }}>
        <ScreenTitle title="Profile" />
        <Card style={{ padding: 18, flexDirection: "row", alignItems: "center", gap: 14 }}>
          <View style={{ width: 56, height: 56, borderRadius: 28, backgroundColor: "#ff8f6b", alignItems: "center", justifyContent: "center" }}>
            <Text style={{ color: "#3a1308", fontSize: 22, fontWeight: "700" }}>{user.email[0].toUpperCase()}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ color: colors.fg, fontSize: 17, fontWeight: "700" }} numberOfLines={1}>{user.email}</Text>
            <Text style={{ color: colors.muted, fontSize: 13, marginTop: 2 }}>Signed in</Text>
          </View>
        </Card>

        <Card style={{ overflow: "hidden" }}>
          <Row icon="layers-outline" label="Workspaces" value={current ? `Active: ${current.name}` : "Create your first workspace"} onPress={() => router.push("/workspaces")} />
          <View style={{ height: 1, backgroundColor: colors.lineSoft }} />
          <Row icon="time-outline" label="Search history" onPress={() => router.push("/history")} />
        </Card>

        <Card style={{ overflow: "hidden" }}>
          <Row icon="server-outline" label="Server" value={API_BASE_URL} />
          <View style={{ height: 1, backgroundColor: colors.lineSoft }} />
          <Row icon="information-circle-outline" label="Version" value={Constants.expoConfig?.version ?? "0.1.0"} />
        </Card>

        <Button title="Sign out" variant="secondary" icon="log-out-outline" onPress={() => void logout()} />
      </ScrollView>
    </Screen>
  );
}
