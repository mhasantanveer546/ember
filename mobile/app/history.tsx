import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { FlatList, Pressable, Text, View } from "react-native";
import { EmptyState, ErrorNote, Loading, Screen } from "@/components/ui";
import { useWorkspace } from "@/context/WorkspaceContext";
import { formatRelative } from "@/lib/format";
import { searchService } from "@/services/search";
import { colors } from "@/theme";
import type { SearchHistoryItem } from "@/types/api";

export default function HistoryScreen() {
  const router = useRouter();
  const { current } = useWorkspace();
  const [items, setItems] = useState<SearchHistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!current) return;
    let cancelled = false;
    searchService.history(current.id, 100).then((h) => !cancelled && setItems(h)).catch((e) => !cancelled && setError((e as Error).message));
    return () => {
      cancelled = true;
    };
  }, [current]);

  return (
    <Screen topInset={false}>
      <FlatList
        data={items ?? []}
        keyExtractor={(h) => h.id}
        contentContainerStyle={{ padding: 16 }}
        ListHeaderComponent={error ? <ErrorNote message={error} /> : null}
        ListEmptyComponent={!current ? <EmptyState title="Create a workspace first" body="Search history is kept per workspace." /> : items === null && !error ? <Loading /> : <EmptyState title="No searches yet" body="Searches you run appear here so you can repeat them with one tap." />}
        renderItem={({ item: h, index }) => (
          <Pressable
            onPress={() => router.navigate({ pathname: "/search", params: { q: h.query_text } })}
            style={({ pressed }) => ({ flexDirection: "row", alignItems: "center", gap: 14, padding: 14, backgroundColor: pressed ? colors.sunken : colors.surface, borderTopWidth: index ? 1 : 0, borderTopColor: colors.lineSoft, borderTopLeftRadius: index === 0 ? 16 : 0, borderTopRightRadius: index === 0 ? 16 : 0, borderBottomLeftRadius: index === (items?.length ?? 0) - 1 ? 16 : 0, borderBottomRightRadius: index === (items?.length ?? 0) - 1 ? 16 : 0 })}
          >
            <View style={{ width: 34, height: 34, borderRadius: 10, backgroundColor: colors.sunken, alignItems: "center", justifyContent: "center" }}>
              <Ionicons name="time-outline" size={17} color={colors.muted} />
            </View>
            <Text style={{ color: colors.fg, flex: 1, fontSize: 15.5, fontWeight: "500" }} numberOfLines={1}>{h.query_text}</Text>
            <Text style={{ color: colors.faint, fontSize: 12 }}>{formatRelative(h.created_at)}</Text>
          </Pressable>
        )}
      />
    </Screen>
  );
}
