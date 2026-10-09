import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { HeroArt } from "@/components/HeroArt";
import { EmberMark } from "@/components/Logo";
import { SearchInput } from "@/components/SearchInput";
import { Button, Card, ErrorNote, FileTag, Loading, StatusBadge, type IconName } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDocuments } from "@/hooks/useDocuments";
import { formatRelative } from "@/lib/format";
import { searchService } from "@/services/search";
import { workspaceService } from "@/services/workspaces";
import { colors, radius, space } from "@/theme";
import type { IndexMetadata, SearchHistoryItem } from "@/types/api";

const PILLS: { label: string; icon: IconName; href: "/search" | "/knowledge" | "/workspaces" | "/history"; primary?: boolean }[] = [
  { label: "My Knowledge", icon: "document-text-outline", href: "/search", primary: true },
  { label: "Upload", icon: "cloud-upload-outline", href: "/knowledge" },
  { label: "Workspaces", icon: "layers-outline", href: "/workspaces" },
  { label: "History", icon: "time-outline", href: "/history" },
];

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card style={{ flex: 1, padding: space.md }}>
      <Text style={{ color: colors.muted, fontSize: 12.5 }}>{label}</Text>
      <Text style={{ color: colors.fg, fontSize: 22, fontWeight: "700", marginTop: 2 }}>{value}</Text>
    </Card>
  );
}

export default function HomeScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { current, loading, error } = useWorkspace();
  const { documents } = useDocuments(current?.id ?? null);
  const [meta, setMeta] = useState<IndexMetadata | null>(null);
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);

  useEffect(() => {
    if (!current) return;
    let cancelled = false;
    workspaceService.indexMetadata(current.id).then((m) => !cancelled && setMeta(m)).catch(() => !cancelled && setMeta(null));
    searchService.history(current.id, 4).then((h) => !cancelled && setHistory(h)).catch(() => !cancelled && setHistory([]));
    return () => {
      cancelled = true;
    };
  }, [current]);

  const ready = documents.filter((d) => d.status === "READY").length;
  const recent = [...documents].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 4);

  return (
    <ScrollView style={{ flex: 1, backgroundColor: colors.bg }} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: space.xxl }}>
      <View style={{ minHeight: 560, paddingTop: insets.top + 56, paddingHorizontal: 20, alignItems: "center" }}>
        <HeroArt />
        {current && (
          <Pressable
            onPress={() => router.push("/workspaces")}
            accessibilityRole="button"
            accessibilityLabel={`Workspace ${current.name}. Tap to manage workspaces`}
            style={{ position: "absolute", top: insets.top + 12, left: 16, flexDirection: "row", alignItems: "center", gap: 6, backgroundColor: "rgba(11,22,35,0.7)", borderRadius: radius.pill, paddingHorizontal: 12, paddingVertical: 7, borderWidth: 1, borderColor: "rgba(255,255,255,0.12)" }}
          >
            <Ionicons name="layers-outline" size={14} color="#fff" />
            <Text style={{ color: "#fff", fontWeight: "600", fontSize: 13, maxWidth: 180 }} numberOfLines={1}>{current.name}</Text>
            <Ionicons name="chevron-forward" size={13} color="rgba(255,255,255,0.7)" />
          </Pressable>
        )}
        <EmberMark size={56} />
        <Text accessibilityRole="header" style={{ color: "#fff", fontSize: 54, fontWeight: "800", letterSpacing: -1.5, marginTop: 6 }}>Ember</Text>
        <Text style={{ color: "rgba(255,255,255,0.82)", fontSize: 17, marginTop: 6 }}>Find what you forgot you knew.</Text>

        <View style={{ marginTop: 96, width: "100%", gap: 18 }}>
          {current ? (
            <>
              <SearchInput hero workspaceId={current.id} onSubmit={(q) => router.push({ pathname: "/search", params: { q } })} />
              <View style={{ flexDirection: "row", flexWrap: "wrap", justifyContent: "center", gap: 10 }}>
                {PILLS.map((p) => (
                  <Pressable
                    key={p.label}
                    accessibilityRole="button"
                    onPress={() => router.push(p.href)}
                    style={{ flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 16, paddingVertical: 11, borderRadius: 16, borderWidth: 1, borderColor: p.primary ? "rgba(90,169,255,0.6)" : "rgba(255,255,255,0.14)", backgroundColor: p.primary ? "rgba(47,116,180,0.35)" : "rgba(11,22,35,0.62)" }}
                  >
                    <Ionicons name={p.icon} size={17} color="#fff" />
                    <Text style={{ color: "#fff", fontWeight: "600", fontSize: 14 }}>{p.label}</Text>
                  </Pressable>
                ))}
              </View>
            </>
          ) : loading ? (
            <Loading />
          ) : (
            <View style={{ alignItems: "center", gap: 14 }}>
              <Text style={{ color: "rgba(255,255,255,0.85)", textAlign: "center" }}>Create a workspace to start adding documents.</Text>
              <Button title="Create your first workspace" onPress={() => router.push("/workspaces")} />
            </View>
          )}
        </View>
      </View>

      <View style={{ padding: 16, gap: 16 }}>
        {error && <ErrorNote message={error} />}
        {current && (
          <>
            <View style={{ flexDirection: "row", gap: 12 }}>
              <Stat label="Documents ready" value={String(ready)} />
              <Stat label="Words indexed" value={meta ? meta.vocabulary_size.toLocaleString() : "–"} />
            </View>

            {history.length > 0 && (
              <Card style={{ padding: space.lg }}>
                <Text style={{ color: colors.fg, fontSize: 17, fontWeight: "600", marginBottom: 4 }}>Recent searches</Text>
                {history.map((h, i) => (
                  <Pressable key={h.id} onPress={() => router.push({ pathname: "/search", params: { q: h.query_text } })} style={{ flexDirection: "row", alignItems: "center", gap: 10, paddingVertical: 11, borderTopWidth: i ? 1 : 0, borderTopColor: colors.lineSoft }}>
                    <Ionicons name="time-outline" size={16} color={colors.faint} />
                    <Text style={{ color: colors.fg, flex: 1, fontSize: 15 }} numberOfLines={1}>{h.query_text}</Text>
                    <Text style={{ color: colors.faint, fontSize: 12 }}>{formatRelative(h.created_at)}</Text>
                  </Pressable>
                ))}
              </Card>
            )}

            {recent.length > 0 && (
              <Card style={{ padding: space.lg }}>
                <Text style={{ color: colors.fg, fontSize: 17, fontWeight: "600", marginBottom: 4 }}>Recently added</Text>
                {recent.map((d, i) => (
                  <Pressable key={d.id} onPress={() => router.push({ pathname: "/document/[id]", params: { id: d.id } })} style={{ flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 10, borderTopWidth: i ? 1 : 0, borderTopColor: colors.lineSoft }}>
                    <FileTag filename={d.filename} />
                    <Text style={{ color: colors.fg, flex: 1, fontSize: 15 }} numberOfLines={1}>{d.filename}</Text>
                    <StatusBadge status={d.status} />
                  </Pressable>
                ))}
              </Card>
            )}
          </>
        )}
      </View>
    </ScrollView>
  );
}
