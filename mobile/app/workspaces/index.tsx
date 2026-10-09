import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Alert, FlatList, Platform, Pressable, Text, TextInput, View } from "react-native";
import { Button, Card, EmptyState, ErrorNote, Loading, Screen } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { formatDate } from "@/lib/format";
import { workspaceService } from "@/services/workspaces";
import { colors, radius } from "@/theme";
import type { Workspace } from "@/types/api";

export default function WorkspacesScreen() {
  const router = useRouter();
  const { workspaces, current, loading, error: loadError, select, refresh, create } = useWorkspace();
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const confirmDelete = (w: Workspace) => {
    const go = () => void run(async () => { await workspaceService.remove(w.id); await refresh(); });
    if (Platform.OS === "web") {
      if (window.confirm(`Delete “${w.name}” and all its documents?`)) go();
    } else Alert.alert(`Delete “${w.name}”?`, "All of its documents are deleted too. This can’t be undone.", [{ text: "Cancel", style: "cancel" }, { text: "Delete", style: "destructive", onPress: go }]);
  };

  return (
    <Screen topInset={false}>
      <FlatList
        data={workspaces}
        keyExtractor={(w) => w.id}
        contentContainerStyle={{ padding: 16, gap: 12 }}
        ListHeaderComponent={
          <View style={{ gap: 12, marginBottom: 4 }}>
            <Card style={{ padding: 14, gap: 10 }}>
              <Text style={{ color: colors.fg, fontWeight: "600", fontSize: 14 }}>New workspace</Text>
              <TextInput
                value={name}
                onChangeText={setName}
                placeholder="Networking course"
                placeholderTextColor={colors.faint}
                maxLength={255}
                accessibilityLabel="New workspace name"
                onSubmitEditing={() => name.trim() && void run(async () => { await create(name.trim()); setName(""); })}
                style={[{ backgroundColor: colors.sunken, borderRadius: radius.md, borderWidth: 1, borderColor: colors.line, color: colors.fg, paddingHorizontal: 14, height: 46, fontSize: 16 }, { outlineStyle: "none" } as object]}
              />
              <Button title="Create workspace" disabled={!name.trim()} loading={busy} onPress={() => void run(async () => { await create(name.trim()); setName(""); })} />
            </Card>
            {(error || loadError) && <ErrorNote message={(error ?? loadError)!} />}
          </View>
        }
        ListEmptyComponent={loading ? <Loading /> : <EmptyState title="No workspaces yet" body="Create one above, then add documents to it." />}
        renderItem={({ item: w }) => (
          <Card style={{ padding: 14 }}>
            <Pressable onPress={() => { select(w.id); router.push({ pathname: "/workspaces/[id]", params: { id: w.id } }); }} style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
              <View style={{ width: 40, height: 40, borderRadius: 12, backgroundColor: colors.sunken, alignItems: "center", justifyContent: "center" }}>
                <Ionicons name="layers-outline" size={20} color={colors.web} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ color: colors.fg, fontSize: 16.5, fontWeight: "700" }} numberOfLines={1}>{w.name}</Text>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginTop: 2 }}>
                  <Text style={{ color: colors.muted, fontSize: 13 }}>Created {formatDate(w.created_at)}</Text>
                  {w.id === current?.id && <Text style={{ color: colors.green, fontSize: 13, fontWeight: "600" }}>● Active</Text>}
                </View>
              </View>
              <Ionicons name="chevron-forward" size={18} color={colors.faint} />
            </Pressable>
            <View style={{ flexDirection: "row", gap: 8, marginTop: 12 }}>
              {w.id !== current?.id && <Button title="Make active" variant="secondary" small onPress={() => select(w.id)} />}
              <Button title="Delete" variant="danger" small onPress={() => confirmDelete(w)} />
            </View>
          </Card>
        )}
      />
    </Screen>
  );
}
